import asyncio
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

from services.google_maps import GoogleMapsService
from services.yelp_api import YelpAPIService
from services.llm_service import LLMService
from core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataAggregationService:
    """
    Data Aggregation Layer - Orchestrates multiple API calls and provides unified data interface
    """
    
    def __init__(self):
        self.google_maps = GoogleMapsService()
        self.yelp = YelpAPIService()
        self.llm_service = LLMService()
        
        # Cache for storing aggregated data (in-memory for now, will add Redis later)
        self._cache = {}
        self._cache_ttl = 3600  # 1 hour cache TTL
    
    async def get_comprehensive_location_data(
        self, 
        location: str, 
        interests: List[str], 
        budget: float,
        travelers: int = 1,
        duration: int = 3
    ) -> Dict[str, Any]:
        """
        Main aggregation method - orchestrates all API calls for a location
        
        Args:
            location: Destination location (e.g., "Paris, France")
            interests: List of user interests
            budget: Total budget for the trip
            travelers: Number of travelers
            duration: Trip duration in days
            
        Returns:
            Comprehensive location data from all sources
        """
        logger.info(f"Starting data aggregation for {location}")
        
        # Check cache first
        cache_key = self._generate_cache_key(location, interests, budget, travelers, duration)
        cached_data = self._get_from_cache(cache_key)
        if cached_data:
            logger.info(f"Returning cached data for {location}")
            return cached_data
        
        try:
            # Parallel API calls for better performance
            tasks = [
                self._get_hotels_data(location, budget, travelers),
                self._get_attractions_data(location, interests),
                self._get_restaurants_data(location, interests, budget),
                self._get_transportation_data(location),
                self._get_location_metadata(location)
            ]
            
            hotels, attractions, restaurants, transportation, metadata = await asyncio.gather(*tasks)
            
            # Combine and normalize data
            aggregated_data = {
                "location": location,
                "basic_info": metadata,
                "hotels": self._normalize_hotels(hotels),
                "attractions": self._normalize_attractions(attractions),
                "restaurants": self._normalize_restaurants(restaurants),
                "transportation": transportation,
                "aggregated_at": datetime.now().isoformat(),
                "cache_key": cache_key
            }
            
            # Cache the result
            self._set_cache(cache_key, aggregated_data)
            
            logger.info(f"Successfully aggregated data for {location}")
            return aggregated_data
            
        except Exception as e:
            logger.error(f"Error aggregating data for {location}: {str(e)}")
            # Return fallback data structure
            return self._get_fallback_data(location, interests, budget)
    
    async def _get_hotels_data(self, location: str, budget: float, travelers: int) -> List[Dict]:
        """Aggregate hotel data from multiple sources"""
        logger.info(f"Fetching hotel data for {location}")
        
        tasks = []
        
        # Add Yelp hotel search
        if self.yelp.api_key:
            tasks.append(self.yelp.search_hotels(location))
        
        # Add Google Maps lodging search
        if self.google_maps.client:
            tasks.append(self.google_maps.search_places(location, "lodging"))
        
        if not tasks:
            logger.warning("No hotel API keys available, using fallback")
            return self._get_fallback_hotels(location)
        
        try:
            hotel_lists = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter out exceptions and combine results
            valid_results = [result for result in hotel_lists if not isinstance(result, Exception)]
            
            if not valid_results:
                return self._get_fallback_hotels(location)
            
            # Merge and deduplicate hotels
            return self._merge_hotel_data(valid_results, budget, travelers)
            
        except Exception as e:
            logger.error(f"Error fetching hotel data: {str(e)}")
            return self._get_fallback_hotels(location)
    
    async def _get_attractions_data(self, location: str, interests: List[str]) -> List[Dict]:
        """Aggregate attraction data from multiple sources"""
        logger.info(f"Fetching attraction data for {location}")
        
        if not self.google_maps.client:
            logger.warning("Google Maps API not available, using fallback")
            return self._get_fallback_attractions(location)
        
        try:
            tasks = []
            
            # Map interests to Google Places types
            place_types = self._map_interests_to_place_types(interests)
            
            # Add tourist attractions by default
            place_types.append("tourist_attraction")
            
            # Create tasks for each place type
            for place_type in place_types:
                tasks.append(self.google_maps.search_places(location, place_type))
            
            attraction_lists = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter out exceptions and combine results
            valid_results = [result for result in attraction_lists if not isinstance(result, Exception)]
            
            if not valid_results:
                return self._get_fallback_attractions(location)
            
            # Flatten and deduplicate attractions
            return self._merge_attraction_data(valid_results)
            
        except Exception as e:
            logger.error(f"Error fetching attraction data: {str(e)}")
            return self._get_fallback_attractions(location)
    
    async def _get_restaurants_data(self, location: str, interests: List[str], budget: float) -> List[Dict]:
        """Aggregate restaurant data from multiple sources"""
        logger.info(f"Fetching restaurant data for {location}")
        
        tasks = []
        
        # Add Yelp restaurant search
        if self.yelp.api_key:
            tasks.append(self.yelp.search_restaurants(location))
        
        # Add Google Maps restaurant search
        if self.google_maps.client:
            tasks.append(self.google_maps.search_places(location, "restaurant"))
        
        if not tasks:
            logger.warning("No restaurant API keys available, using fallback")
            return self._get_fallback_restaurants(location)
        
        try:
            restaurant_lists = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter out exceptions and combine results
            valid_results = [result for result in restaurant_lists if not isinstance(result, Exception)]
            
            if not valid_results:
                return self._get_fallback_restaurants(location)
            
            # Merge and deduplicate restaurants
            return self._merge_restaurant_data(valid_results, budget)
            
        except Exception as e:
            logger.error(f"Error fetching restaurant data: {str(e)}")
            return self._get_fallback_restaurants(location)
    
    async def _get_transportation_data(self, location: str) -> Dict[str, Any]:
        """Get transportation information for the location"""
        logger.info(f"Fetching transportation data for {location}")
        
        if not self.google_maps.client:
            return self._get_fallback_transportation(location)
        
        try:
            # Get coordinates for the location
            coordinates = await self.google_maps.geocode_address(location)
            
            if not coordinates:
                return self._get_fallback_transportation(location)
            
            return {
                "coordinates": coordinates,
                "location": location,
                "transportation_options": [
                    "Public Transit",
                    "Taxi/Rideshare",
                    "Car Rental",
                    "Walking",
                    "Bicycle"
                ],
                "airports": await self._get_nearby_airports(coordinates),
                "transit_info": "Public transportation available in most areas"
            }
            
        except Exception as e:
            logger.error(f"Error fetching transportation data: {str(e)}")
            return self._get_fallback_transportation(location)
    
    async def _get_location_metadata(self, location: str) -> Dict[str, Any]:
        """Get basic location information (minimal metadata)"""
        logger.info(f"Getting basic info for {location}")
        
        return {
            "name": location,
            "coordinates": await self._get_coordinates(location),
            "timestamp": datetime.now().isoformat()
        }
    
    async def _get_coordinates(self, location: str) -> Optional[Dict[str, float]]:
        """Get coordinates for the location"""
        if self.google_maps.client:
            return await self.google_maps.geocode_address(location)
        return {"lat": 0, "lng": 0}
    
    async def _get_nearby_airports(self, coordinates: Dict[str, float]) -> List[Dict]:
        """Get nearby airports (placeholder for now)"""
        return [
            {
                "name": "Main International Airport",
                "distance": "15 km",
                "code": "XXX",
                "transportation": "Taxi, Bus, Train"
            }
        ]
    
    def _map_interests_to_place_types(self, interests: List[str]) -> List[str]:
        """Map user interests to Google Places API types"""
        interest_mapping = {
            "Culture & History": ["museum", "church", "historical_site"],
            "Food & Dining": ["restaurant", "food"],
            "Nature & Outdoor": ["park", "zoo", "aquarium"],
            "Nightlife": ["bar", "night_club"],
            "Shopping": ["shopping_mall", "store"],
            "Adventure": ["amusement_park", "tourist_attraction"],
            "Relaxation": ["spa", "park"],
            "Art & Museums": ["museum", "art_gallery"]
        }
        
        place_types = []
        for interest in interests:
            if interest in interest_mapping:
                place_types.extend(interest_mapping[interest])
        
        return list(set(place_types))  # Remove duplicates
    
    def _merge_hotel_data(self, hotel_lists: List[List[Dict]], budget: float, travelers: int) -> List[Dict]:
        """Merge hotel data from different sources and deduplicate"""
        all_hotels = []
        seen_names = set()
        
        for hotel_list in hotel_lists:
            for hotel in hotel_list:
                # Basic deduplication by name
                hotel_name = hotel.get("name", "").lower().strip()
                if hotel_name and hotel_name not in seen_names:
                    seen_names.add(hotel_name)
                    
                    # Normalize hotel data
                    normalized_hotel = {
                        "id": hotel.get("id", f"hotel_{len(all_hotels)}"),
                        "name": hotel.get("name", "Unknown Hotel"),
                        "address": hotel.get("address", ""),
                        "rating": float(hotel.get("rating", 0)),
                        "price_per_night": float(hotel.get("price_per_night", 0)),
                        "amenities": hotel.get("amenities", []),
                        "location": hotel.get("location", {}),
                        "photos": hotel.get("photos", []),
                        "source": hotel.get("source", "unknown"),
                        "availability": hotel.get("availability", True)
                    }
                    
                    # Filter by budget if price is available
                    if normalized_hotel["price_per_night"] == 0 or normalized_hotel["price_per_night"] <= budget / travelers:
                        all_hotels.append(normalized_hotel)
        
        # Sort by rating and return top results
        return sorted(all_hotels, key=lambda x: x["rating"], reverse=True)[:20]
    
    def _merge_attraction_data(self, attraction_lists: List[List[Dict]]) -> List[Dict]:
        """Merge attraction data from different sources and deduplicate"""
        all_attractions = []
        seen_names = set()
        
        for attraction_list in attraction_lists:
            for attraction in attraction_list:
                attraction_name = attraction.get("name", "").lower().strip()
                if attraction_name and attraction_name not in seen_names:
                    seen_names.add(attraction_name)
                    
                    normalized_attraction = {
                        "id": attraction.get("id", f"attraction_{len(all_attractions)}"),
                        "name": attraction.get("name", "Unknown Attraction"),
                        "address": attraction.get("address", ""),
                        "rating": float(attraction.get("rating", 0)),
                        "price_level": attraction.get("price_level", 0),
                        "types": attraction.get("types", []),
                        "location": attraction.get("location", {}),
                        "photos": attraction.get("photos", []),
                        "description": attraction.get("description", ""),
                        "source": attraction.get("source", "unknown")
                    }
                    
                    all_attractions.append(normalized_attraction)
        
        return sorted(all_attractions, key=lambda x: x["rating"], reverse=True)[:30]
    
    def _merge_restaurant_data(self, restaurant_lists: List[List[Dict]], budget: float) -> List[Dict]:
        """Merge restaurant data from different sources and deduplicate"""
        all_restaurants = []
        seen_names = set()
        
        for restaurant_list in restaurant_lists:
            for restaurant in restaurant_list:
                restaurant_name = restaurant.get("name", "").lower().strip()
                if restaurant_name and restaurant_name not in seen_names:
                    seen_names.add(restaurant_name)
                    
                    normalized_restaurant = {
                        "id": restaurant.get("id", f"restaurant_{len(all_restaurants)}"),
                        "name": restaurant.get("name", "Unknown Restaurant"),
                        "address": restaurant.get("address", ""),
                        "rating": float(restaurant.get("rating", 0)),
                        "price_level": restaurant.get("price_level", 0),
                        "types": restaurant.get("types", []),
                        "location": restaurant.get("location", {}),
                        "photos": restaurant.get("photos", []),
                        "description": restaurant.get("description", ""),
                        "source": restaurant.get("source", "unknown")
                    }
                    
                    all_restaurants.append(normalized_restaurant)
        
        return sorted(all_restaurants, key=lambda x: x["rating"], reverse=True)[:25]
    
    def _normalize_hotels(self, hotels: List[Dict]) -> List[Dict]:
        """Normalize hotel data to common format"""
        return hotels  # Already normalized in merge method
    
    def _normalize_attractions(self, attractions: List[Dict]) -> List[Dict]:
        """Normalize attraction data to common format"""
        return attractions  # Already normalized in merge method
    
    def _normalize_restaurants(self, restaurants: List[Dict]) -> List[Dict]:
        """Normalize restaurant data to common format"""
        return restaurants  # Already normalized in merge method
    
    def _generate_cache_key(self, location: str, interests: List[str], budget: float, travelers: int, duration: int) -> str:
        """Generate cache key for aggregated data"""
        key_data = f"{location}:{sorted(interests)}:{budget}:{travelers}:{duration}"
        return f"location_data:{hash(key_data)}"
    
    def _get_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get data from cache (in-memory for now)"""
        if cache_key in self._cache:
            cached_item = self._cache[cache_key]
            if datetime.now() < cached_item["expires_at"]:
                return cached_item["data"]
            else:
                del self._cache[cache_key]
        return None
    
    def _set_cache(self, cache_key: str, data: Dict[str, Any]) -> None:
        """Set data in cache (in-memory for now)"""
        self._cache[cache_key] = {
            "data": data,
            "expires_at": datetime.now() + timedelta(seconds=self._cache_ttl)
        }
    
    def _get_fallback_data(self, location: str, interests: List[str], budget: float) -> Dict[str, Any]:
        """Get fallback data when aggregation fails"""
        return {
            "location": location,
            "basic_info": {
                "name": location,
                "coordinates": {"lat": 0, "lng": 0},
                "timestamp": datetime.now().isoformat()
            },
            "hotels": self._get_fallback_hotels(location),
            "attractions": self._get_fallback_attractions(location),
            "restaurants": self._get_fallback_restaurants(location),
            "transportation": self._get_fallback_transportation(location),
            "aggregated_at": datetime.now().isoformat(),
            "fallback": True
        }
    
    def _get_fallback_hotels(self, location: str) -> List[Dict]:
        """Fallback hotel data"""
        return [
            {
                "id": "fallback_hotel_1",
                "name": f"Grand Hotel {location.split(',')[0]}",
                "address": f"123 Main Street, {location}",
                "rating": 4.2,
                "price_per_night": 150.0,
                "amenities": ["WiFi", "Restaurant", "Room Service"],
                "location": {"lat": 0, "lng": 0},
                "photos": [],
                "source": "fallback",
                "availability": True
            }
        ]
    
    def _get_fallback_attractions(self, location: str) -> List[Dict]:
        """Fallback attraction data"""
        return [
            {
                "id": "fallback_attraction_1",
                "name": f"Historic Center of {location.split(',')[0]}",
                "address": f"Downtown {location}",
                "rating": 4.5,
                "price_level": 1,
                "types": ["tourist_attraction", "historical_site"],
                "location": {"lat": 0, "lng": 0},
                "photos": [],
                "description": f"Explore the historic center of {location}",
                "source": "fallback"
            }
        ]
    
    def _get_fallback_restaurants(self, location: str) -> List[Dict]:
        """Fallback restaurant data"""
        return [
            {
                "id": "fallback_restaurant_1",
                "name": f"Local Cuisine Restaurant",
                "address": f"456 Food Street, {location}",
                "rating": 4.3,
                "price_level": 2,
                "types": ["restaurant", "local_cuisine"],
                "location": {"lat": 0, "lng": 0},
                "photos": [],
                "description": f"Experience authentic local cuisine in {location}",
                "source": "fallback"
            }
        ]
    
    def _get_fallback_transportation(self, location: str) -> Dict[str, Any]:
        """Fallback transportation data"""
        return {
            "coordinates": {"lat": 0, "lng": 0},
            "location": location,
            "transportation_options": [
                "Public Transit",
                "Taxi/Rideshare",
                "Car Rental",
                "Walking"
            ],
            "airports": [
                {
                    "name": "Main Airport",
                    "distance": "15 km",
                    "code": "XXX",
                    "transportation": "Taxi, Bus"
                }
            ],
            "transit_info": "Public transportation available",
            "source": "fallback"
        }

# Global instance
data_aggregation_service = DataAggregationService()
