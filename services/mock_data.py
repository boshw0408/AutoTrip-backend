import random
from typing import List, Dict, Any
from datetime import datetime, timedelta
from models.schemas import PlaceResponse, HotelResponse

class MockDataService:
    def __init__(self):
        self.mock_places = {
            "Paris": [
                {
                    "id": "eiffel_tower",
                    "name": "Eiffel Tower",
                    "address": "Champ de Mars, 7th arrondissement, Paris",
                    "rating": 4.6,
                    "price_level": 2,
                    "types": ["tourist_attraction", "landmark"],
                    "location": {"lat": 48.8584, "lng": 2.2945},
                    "photos": ["eiffel_tower_1.jpg"],
                    "description": "Iconic iron tower and symbol of Paris"
                },
                {
                    "id": "louvre",
                    "name": "Louvre Museum",
                    "address": "Rue de Rivoli, 1st arrondissement, Paris",
                    "rating": 4.5,
                    "price_level": 3,
                    "types": ["museum", "art_gallery"],
                    "location": {"lat": 48.8606, "lng": 2.3376},
                    "photos": ["louvre_1.jpg"],
                    "description": "World's largest art museum and historic monument"
                },
                {
                    "id": "notre_dame",
                    "name": "Notre-Dame Cathedral",
                    "address": "6 Parvis Notre-Dame, 4th arrondissement, Paris",
                    "rating": 4.7,
                    "price_level": 1,
                    "types": ["church", "cathedral", "landmark"],
                    "location": {"lat": 48.8530, "lng": 2.3499},
                    "photos": ["notre_dame_1.jpg"],
                    "description": "Medieval Catholic cathedral"
                }
            ],
            "Tokyo": [
                {
                    "id": "sensoji",
                    "name": "Senso-ji Temple",
                    "address": "2-3-1 Asakusa, Taito City, Tokyo",
                    "rating": 4.4,
                    "price_level": 1,
                    "types": ["temple", "religious_site"],
                    "location": {"lat": 35.7148, "lng": 139.7967},
                    "photos": ["sensoji_1.jpg"],
                    "description": "Tokyo's oldest temple"
                },
                {
                    "id": "tsukiji",
                    "name": "Tsukiji Outer Market",
                    "address": "4-16-2 Tsukiji, Chuo City, Tokyo",
                    "rating": 4.3,
                    "price_level": 2,
                    "types": ["market", "food"],
                    "location": {"lat": 35.6654, "lng": 139.7706},
                    "photos": ["tsukiji_1.jpg"],
                    "description": "Famous fish market and food stalls"
                }
            ]
        }
        
        self.mock_hotels = {
            "Paris": [
                {
                    "id": "hotel_paris_1",
                    "name": "Hotel des Grands Boulevards",
                    "address": "17 Boulevard Poissonnière, 75002 Paris",
                    "rating": 4.5,
                    "price_per_night": 180.0,
                    "amenities": ["WiFi", "Restaurant", "Room Service", "Concierge"],
                    "photos": ["hotel_1.jpg"],
                    "location": {"lat": 48.8722, "lng": 2.3444},
                    "distance_from_center": "1.2 km",
                    "availability": True
                },
                {
                    "id": "hotel_paris_2", 
                    "name": "Hotel Le Marais",
                    "address": "20 Rue de Rivoli, 75004 Paris",
                    "rating": 4.3,
                    "price_per_night": 220.0,
                    "amenities": ["WiFi", "Pool", "Gym", "Spa"],
                    "photos": ["hotel_2.jpg"],
                    "location": {"lat": 48.8566, "lng": 2.3522},
                    "distance_from_center": "0.8 km",
                    "availability": True
                }
            ],
            "Tokyo": [
                {
                    "id": "hotel_tokyo_1",
                    "name": "Park Hyatt Tokyo",
                    "address": "3-7-1-2 Nishi-Shinjuku, Shinjuku City, Tokyo",
                    "rating": 4.7,
                    "price_per_night": 450.0,
                    "amenities": ["WiFi", "Restaurant", "Pool", "Spa", "Concierge"],
                    "photos": ["hotel_tokyo_1.jpg"],
                    "location": {"lat": 35.6852, "lng": 139.6917},
                    "distance_from_center": "2.1 km",
                    "availability": True
                }
            ]
        }
    
    def get_mock_places(self, location: str, place_type: str = "attractions") -> List[PlaceResponse]:
        """Get mock places for a location"""
        location_key = location.split(',')[0].strip()
        places = self.mock_places.get(location_key, [])
        
        # Filter by type if needed
        if place_type != "attractions":
            places = [p for p in places if place_type in p.get("types", [])]
        
        return [PlaceResponse(**place) for place in places]
    
    def get_mock_place_details(self, place_id: str) -> PlaceResponse:
        """Get mock place details by ID"""
        for location_places in self.mock_places.values():
            for place in location_places:
                if place["id"] == place_id:
                    return PlaceResponse(**place)
        return None
    
    def get_mock_hotels(self, location: str) -> List[HotelResponse]:
        """Get mock hotels for a location"""
        location_key = location.split(',')[0].strip()
        hotels = self.mock_hotels.get(location_key, [])
        
        # Add some random hotels if location not found
        if not hotels:
            hotels = [
                {
                    "id": f"hotel_{random.randint(1000, 9999)}",
                    "name": f"Grand Hotel {location_key}",
                    "address": f"123 Main Street, {location_key}",
                    "rating": round(random.uniform(3.5, 4.8), 1),
                    "price_per_night": round(random.uniform(100, 300), 2),
                    "amenities": random.sample(["WiFi", "Parking", "Restaurant", "Pool", "Gym"], 3),
                    "photos": ["hotel_default.jpg"],
                    "location": {"lat": random.uniform(35.0, 50.0), "lng": random.uniform(-5.0, 140.0)},
                    "distance_from_center": f"{random.randint(1, 5)} km",
                    "availability": True
                }
            ]
        
        return [HotelResponse(**hotel) for hotel in hotels]
    
    def get_mock_hotel_details(self, hotel_id: str) -> HotelResponse:
        """Get mock hotel details by ID"""
        for location_hotels in self.mock_hotels.values():
            for hotel in location_hotels:
                if hotel["id"] == hotel_id:
                    return HotelResponse(**hotel)
        return None
    
    def generate_mock_itinerary(self, location: str, duration: int, interests: List[str], budget: float, travelers: int) -> Dict[str, Any]:
        """Generate a mock itinerary"""
        itinerary_days = []
        
        for day in range(1, duration + 1):
            day_items = []
            
            # Morning activity
            day_items.append({
                "id": f"day_{day}_morning",
                "time": "09:00",
                "title": f"Morning Activity - Day {day}",
                "description": f"Start your day with a visit to a local attraction in {location}",
                "location": f"{location}",
                "duration": "2 hours",
                "type": "attraction",
                "rating": round(random.uniform(4.0, 4.8), 1),
                "cost": round(random.uniform(20, 50), 2)
            })
            
            # Lunch
            day_items.append({
                "id": f"day_{day}_lunch",
                "time": "12:00",
                "title": f"Lunch - Day {day}",
                "description": f"Enjoy local cuisine at a recommended restaurant",
                "location": f"{location}",
                "duration": "1 hour",
                "type": "restaurant",
                "rating": round(random.uniform(4.0, 4.8), 1),
                "cost": round(random.uniform(30, 80), 2)
            })
            
            # Afternoon activity
            day_items.append({
                "id": f"day_{day}_afternoon",
                "time": "14:00",
                "title": f"Afternoon Activity - Day {day}",
                "description": f"Explore more of {location} with cultural activities",
                "location": f"{location}",
                "duration": "3 hours",
                "type": "attraction",
                "rating": round(random.uniform(4.0, 4.8), 1),
                "cost": round(random.uniform(25, 60), 2)
            })
            
            # Dinner
            day_items.append({
                "id": f"day_{day}_dinner",
                "time": "19:00",
                "title": f"Dinner - Day {day}",
                "description": f"End your day with a memorable dining experience",
                "location": f"{location}",
                "duration": "1.5 hours",
                "type": "restaurant",
                "rating": round(random.uniform(4.0, 4.8), 1),
                "cost": round(random.uniform(40, 100), 2)
            })
            
            itinerary_days.append({
                "day": day,
                "date": (datetime.now() + timedelta(days=day-1)).strftime("%Y-%m-%d"),
                "items": day_items
            })
        
        # Calculate total cost
        total_cost = sum(
            sum(item["cost"] for item in day["items"]) 
            for day in itinerary_days
        ) * travelers
        
        return {
            "location": location,
            "duration": duration,
            "days": itinerary_days,
            "total_cost": total_cost,
            "interests": interests,
            "budget": budget,
            "travelers": travelers
        }
    
    def get_mock_route(self, origin: str, destination: str, waypoints: List[str] = None, mode: str = "driving") -> Dict[str, Any]:
        """Get mock route data"""
        return {
            "distance": f"{random.randint(5, 50)} km",
            "duration": f"{random.randint(15, 120)} mins",
            "polyline": "mock_polyline_data",
            "steps": [
                {
                    "instruction": f"Start from {origin}",
                    "distance": "0 km",
                    "duration": "0 mins"
                },
                {
                    "instruction": f"Drive to {destination}",
                    "distance": f"{random.randint(5, 50)} km", 
                    "duration": f"{random.randint(15, 120)} mins"
                }
            ]
        }
