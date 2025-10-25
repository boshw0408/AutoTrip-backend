import requests
from core.config import settings
from typing import List, Dict, Any, Optional

class YelpAPIService:
    def __init__(self):
        self.api_key = settings.yelp_api_key
        self.base_url = "https://api.yelp.com/v3"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def search_restaurants(self, location: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search for restaurants using Yelp API"""
        if not self.api_key:
            return []
        
        try:
            url = f"{self.base_url}/businesses/search"
            params = {
                "location": location,
                "categories": "restaurants",
                "limit": limit,
                "sort_by": "rating"
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            restaurants = []
            
            for business in data.get('businesses', []):
                restaurants.append({
                    'id': business['id'],
                    'name': business['name'],
                    'address': ', '.join(business['location']['display_address']),
                    'rating': business['rating'],
                    'price_level': len(business.get('price', '')),
                    'types': business.get('categories', []),
                    'location': {
                        'lat': business['coordinates']['latitude'],
                        'lng': business['coordinates']['longitude']
                    },
                    'photos': business.get('photos', []),
                    'description': f"Restaurant with {business.get('review_count', 0)} reviews",
                    'source': 'yelp'
                })
            
            return restaurants
            
        except Exception as e:
            print(f"Error searching restaurants: {e}")
            return []
    
    async def search_hotels(self, location: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search for hotels using Yelp API"""
        if not self.api_key:
            return []
        
        try:
            url = f"{self.base_url}/businesses/search"
            params = {
                "location": location,
                "categories": "hotels",
                "limit": limit,
                "sort_by": "rating"
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            hotels = []
            
            for business in data.get('businesses', []):
                hotels.append({
                    'id': business['id'],
                    'name': business['name'],
                    'address': ', '.join(business['location']['display_address']),
                    'rating': business['rating'],
                    'price_per_night': self._estimate_hotel_price(business.get('price', '')),
                    'amenities': [],  # Yelp doesn't provide amenities directly
                    'photos': business.get('photos', []),
                    'location': {
                        'lat': business['coordinates']['latitude'],
                        'lng': business['coordinates']['longitude']
                    },
                    'distance_from_center': 'N/A',
                    'availability': True,
                    'source': 'yelp'
                })
            
            return hotels
            
        except Exception as e:
            print(f"Error searching hotels: {e}")
            return []
    
    def _estimate_hotel_price(self, price_symbol: str) -> float:
        """Estimate hotel price based on Yelp price symbol"""
        price_map = {
            '$': 100.0,
            '$$': 200.0,
            '$$$': 300.0,
            '$$$$': 500.0
        }
        return price_map.get(price_symbol, 150.0)
    
    async def get_business_details(self, business_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific business"""
        if not self.api_key:
            return None
        
        try:
            url = f"{self.base_url}/businesses/{business_id}"
            
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            business = response.json()
            
            return {
                'id': business['id'],
                'name': business['name'],
                'address': ', '.join(business['location']['display_address']),
                'rating': business['rating'],
                'price_level': len(business.get('price', '')),
                'types': business.get('categories', []),
                'location': {
                    'lat': business['coordinates']['latitude'],
                    'lng': business['coordinates']['longitude']
                },
                'photos': business.get('photos', []),
                'description': business.get('review_count', 0),
                'phone': business.get('phone', ''),
                'website': business.get('url', ''),
                'hours': business.get('hours', [])
            }
            
        except Exception as e:
            print(f"Error getting business details: {e}")
            return None
