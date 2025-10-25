import googlemaps
from core.config import settings
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class Location:
    name: str
    address: str
    coordinates: Dict[str, float]  # {lat, lng}
    place_type: str = "tourist_attraction"

@dataclass
class Segment:
    from_location: Location
    to_location: Location
    distance: str
    duration: str

@dataclass
class TripPlan:
    optimized_order: List[Location]
    total_distance: str
    total_duration: str
    polyline: str
    segments: List[Segment]

@dataclass
class RouteVisualization:
    polyline: str
    markers: List[Location]
    bounds: Dict[str, Dict[str, float]]  # {northeast: {lat, lng}, southwest: {lat, lng}}

@dataclass
class TripSummary:
    total_distance: str
    total_duration: str
    location_count: int
    estimated_cost: Optional[str] = None

@dataclass
class MapBounds:
    northeast: Dict[str, float]
    southwest: Dict[str, float]
    center: Dict[str, float]

class GoogleMapsService:
    def __init__(self):
        self.client = None
        if settings.google_maps_api_key:
            try:
                self.client = googlemaps.Client(key=settings.google_maps_api_key)
                print("✅ Google Maps API initialized")
            except Exception as e:
                print(f"❌ Google Maps API initialization failed: {e}")
    
    async def search_places(self, location: str, place_type: str = "tourist_attraction", radius: int = 5000) -> List[Dict[str, Any]]:
        """Search for places using Google Places API"""
        if not self.client:
            return []
        
        try:
            # Geocode the location first
            geocode_result = self.client.geocode(location)
            if not geocode_result:
                return []
            
            lat_lng = geocode_result[0]['geometry']['location']
            
            # Search for places
            places_result = self.client.places_nearby(
                location=lat_lng,
                radius=radius,
                type=place_type
            )
            
            places = []
            for place in places_result.get('results', []):
                place_details = self.client.place(
                    place_id=place['place_id'],
                    fields=['name', 'formatted_address', 'rating', 'price_level', 'types', 'geometry', 'photos']
                )
                
                places.append({
                    'id': place['place_id'],
                    'name': place_details['result'].get('name', ''),
                    'address': place_details['result'].get('formatted_address', ''),
                    'rating': place_details['result'].get('rating', 0),
                    'price_level': place_details['result'].get('price_level'),
                    'types': place_details['result'].get('types', []),
                    'location': place_details['result']['geometry']['location'],
                    'photos': [photo.get('photo_reference', '') for photo in place_details['result'].get('photos', [])],
                    'description': place_details['result'].get('name', ''),
                    'source': 'google_maps'
                })
            
            return places
            
        except Exception as e:
            print(f"Error searching places: {e}")
            return []
    
    async def get_directions(self, origin: str, destination: str, waypoints: List[str] = None, mode: str = "driving") -> Dict[str, Any]:
        """Get directions between locations"""
        if not self.client:
            return {}
        
        try:
            directions_result = self.client.directions(
                origin=origin,
                destination=destination,
                waypoints=waypoints,
                mode=mode,
                optimize_waypoints=True
            )
            
            if not directions_result:
                return {}
            
            route = directions_result[0]
            leg = route['legs'][0]
            
            return {
                'distance': leg['distance']['text'],
                'duration': leg['duration']['text'],
                'polyline': route['overview_polyline']['points'],
                'steps': [
                    {
                        'instruction': step['html_instructions'],
                        'distance': step['distance']['text'],
                        'duration': step['duration']['text']
                    }
                    for step in leg['steps']
                ]
            }
            
        except Exception as e:
            print(f"Error getting directions: {e}")
            return {}
    
    async def geocode_address(self, address: str) -> Optional[Dict[str, float]]:
        """Geocode an address to get coordinates"""
        if not self.client:
            return None
        
        try:
            geocode_result = self.client.geocode(address)
            if geocode_result:
                return geocode_result[0]['geometry']['location']
            return None
            
        except Exception as e:
            print(f"Error geocoding address: {e}")
            return None
    
    # Enhanced Trip Planning Methods
    
    async def plan_trip(self, origin: str, destination: str, waypoints: List[str]) -> TripPlan:
        """Plan a complete trip with multiple stops"""
        if not self.client:
            return None
        
        try:
            # Get directions with optimized waypoints
            directions_result = self.client.directions(
                origin=origin,
                destination=destination,
                waypoints=waypoints,
                mode="driving",
                optimize_waypoints=True
            )
            
            if not directions_result:
                return None
            
            route = directions_result[0]
            
            # Extract optimized order
            optimized_order = []
            segments = []
            
            # Add origin
            origin_coords = await self.geocode_address(origin)
            optimized_order.append(Location(
                name="Origin",
                address=origin,
                coordinates=origin_coords or {"lat": 0, "lng": 0},
                place_type="origin"
            ))
            
            # Add waypoints in optimized order
            for i, leg in enumerate(route['legs']):
                if i < len(route['waypoint_order']):
                    waypoint_index = route['waypoint_order'][i]
                    waypoint_name = waypoints[waypoint_index]
                    waypoint_coords = await self.geocode_address(waypoint_name)
                    
                    optimized_order.append(Location(
                        name=waypoint_name,
                        address=waypoint_name,
                        coordinates=waypoint_coords or {"lat": 0, "lng": 0},
                        place_type="waypoint"
                    ))
                    
                    # Create segment
                    if i > 0:
                        segments.append(Segment(
                            from_location=optimized_order[-2],
                            to_location=optimized_order[-1],
                            distance=leg['distance']['text'],
                            duration=leg['duration']['text']
                        ))
            
            # Add destination
            dest_coords = await self.geocode_address(destination)
            optimized_order.append(Location(
                name="Destination",
                address=destination,
                coordinates=dest_coords or {"lat": 0, "lng": 0},
                place_type="destination"
            ))
            
            # Add final segment
            if route['legs']:
                final_leg = route['legs'][-1]
                segments.append(Segment(
                    from_location=optimized_order[-2],
                    to_location=optimized_order[-1],
                    distance=final_leg['distance']['text'],
                    duration=final_leg['duration']['text']
                ))
            
            return TripPlan(
                optimized_order=optimized_order,
                total_distance=route['legs'][0]['distance']['text'] if route['legs'] else "0 mi",
                total_duration=route['legs'][0]['duration']['text'] if route['legs'] else "0 min",
                polyline=route['overview_polyline']['points'],
                segments=segments
            )
            
        except Exception as e:
            print(f"Error planning trip: {e}")
            return None
    
    async def get_route_polyline(self, origin: str, destination: str, waypoints: List[str]) -> RouteVisualization:
        """Get route visualization data"""
        if not self.client:
            return None
        
        try:
            directions_result = self.client.directions(
                origin=origin,
                destination=destination,
                waypoints=waypoints,
                mode="driving",
                optimize_waypoints=True
            )
            
            if not directions_result:
                return None
            
            route = directions_result[0]
            
            # Create markers for all locations
            markers = []
            
            # Add origin marker
            origin_coords = await self.geocode_address(origin)
            markers.append(Location(
                name="Origin",
                address=origin,
                coordinates=origin_coords or {"lat": 0, "lng": 0},
                place_type="origin"
            ))
            
            # Add waypoint markers
            for waypoint in waypoints:
                waypoint_coords = await self.geocode_address(waypoint)
                markers.append(Location(
                    name=waypoint,
                    address=waypoint,
                    coordinates=waypoint_coords or {"lat": 0, "lng": 0},
                    place_type="waypoint"
                ))
            
            # Add destination marker
            dest_coords = await self.geocode_address(destination)
            markers.append(Location(
                name="Destination",
                address=destination,
                coordinates=dest_coords or {"lat": 0, "lng": 0},
                place_type="destination"
            ))
            
            # Calculate bounds
            bounds = route.get('bounds', {})
            
            return RouteVisualization(
                polyline=route['overview_polyline']['points'],
                markers=markers,
                bounds={
                    "northeast": bounds.get('northeast', {}),
                    "southwest": bounds.get('southwest', {})
                }
            )
            
        except Exception as e:
            print(f"Error getting route polyline: {e}")
            return None
    
    async def calculate_trip_summary(self, locations: List[str]) -> TripSummary:
        """Calculate trip summary"""
        if not self.client or len(locations) < 2:
            return None
        
        try:
            # Get directions for the full trip
            origin = locations[0]
            destination = locations[-1]
            waypoints = locations[1:-1] if len(locations) > 2 else []
            
            directions_result = self.client.directions(
                origin=origin,
                destination=destination,
                waypoints=waypoints,
                mode="driving",
                optimize_waypoints=True
            )
            
            if not directions_result:
                return None
            
            route = directions_result[0]
            total_distance = route['legs'][0]['distance']['text'] if route['legs'] else "0 mi"
            total_duration = route['legs'][0]['duration']['text'] if route['legs'] else "0 min"
            
            return TripSummary(
                total_distance=total_distance,
                total_duration=total_duration,
                location_count=len(locations),
                estimated_cost=None  # Could be calculated based on distance/fuel costs
            )
            
        except Exception as e:
            print(f"Error calculating trip summary: {e}")
            return None
    
    async def get_map_bounds(self, locations: List[str]) -> MapBounds:
        """Get map bounds for all locations"""
        if not self.client:
            return None
        
        try:
            # Geocode all locations
            coordinates = []
            for location in locations:
                coords = await self.geocode_address(location)
                if coords:
                    coordinates.append(coords)
            
            if not coordinates:
                return None
            
            # Calculate bounds
            lats = [coord['lat'] for coord in coordinates]
            lngs = [coord['lng'] for coord in coordinates]
            
            northeast = {
                "lat": max(lats),
                "lng": max(lngs)
            }
            southwest = {
                "lat": min(lats),
                "lng": min(lngs)
            }
            center = {
                "lat": sum(lats) / len(lats),
                "lng": sum(lngs) / len(lngs)
            }
            
            return MapBounds(
                northeast=northeast,
                southwest=southwest,
                center=center
            )
            
        except Exception as e:
            print(f"Error getting map bounds: {e}")
            return None
