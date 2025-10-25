import googlemaps
from core.config import settings
from typing import List, Dict, Any, Optional

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
