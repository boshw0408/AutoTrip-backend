import requests
from typing import List, Dict, Any, Optional
from datetime import datetime, date
import logging
from core.config import settings

logger = logging.getLogger(__name__)


class AmadeusService:
    """Service class for interacting with Amadeus API"""
    
    BASE_URL = "https://test.api.amadeus.com"  # Use production URL for live: https://api.amadeus.com
    
    def __init__(self):
        self.api_key = settings.amadeus_api_key
        self.api_secret = settings.amadeus_api_secret
        self.access_token = None
        self.token_expiry = None
        
    def _get_access_token(self) -> str:
        """Get OAuth access token from Amadeus API"""
        # Check if we have a valid token
        if self.access_token and self.token_expiry:
            if datetime.now().timestamp() < self.token_expiry:
                return self.access_token
        
        # Request new token
        url = f"{self.BASE_URL}/v1/security/oauth2/token"
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {
            "grant_type": "client_credentials",
            "client_id": self.api_key,
            "client_secret": self.api_secret
        }
        
        try:
            response = requests.post(url, headers=headers, data=data)
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data["access_token"]
            # Token typically expires in 1799 seconds, set expiry with buffer
            expires_in = token_data.get("expires_in", 1799)
            self.token_expiry = datetime.now().timestamp() + expires_in - 60
            
            logger.info("Successfully obtained Amadeus access token")
            return self.access_token
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get Amadeus access token: {str(e)}")
            raise Exception(f"Authentication failed: {str(e)}")
    
    def _make_request(self, method: str, endpoint: str, params: Dict = None, data: Dict = None) -> Dict:
        """Make authenticated request to Amadeus API"""
        token = self._get_access_token()
        url = f"{self.BASE_URL}{endpoint}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, params=params)
            elif method.upper() == "POST":
                response = requests.post(url, headers=headers, json=data, params=params)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error from Amadeus API: {e.response.text}")
            raise Exception(f"API request failed: {e.response.text}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {str(e)}")
            raise Exception(f"Request failed: {str(e)}")
    
    def get_city_code(self, city_name: str) -> Optional[str]:
        """Get IATA city code from city name using Amadeus Location API"""
        endpoint = "/v1/reference-data/locations"
        params = {
            "keyword": city_name,
            "subType": "CITY"
        }
        
        try:
            result = self._make_request("GET", endpoint, params=params)
            if result.get("data") and len(result["data"]) > 0:
                return result["data"][0].get("iataCode")
            return None
        except Exception as e:
            logger.error(f"Failed to get city code for {city_name}: {str(e)}")
            return None
    
    def search_hotels_by_city(
        self,
        city_code: str,
        check_in: date,
        check_out: date,
        adults: int = 1,
        radius: int = 50,
        currency: str = "USD",
        max_results: int = 50
    ) -> List[Dict[str, Any]]:
        """Search for hotels in a city using Amadeus Hotel List API"""
        endpoint = "/v1/reference-data/locations/hotels/by-city"
        params = {
            "cityCode": city_code,
            "radius": radius,
            "radiusUnit": "KM",
            "hotelSource": "ALL"
        }
        
        try:
            result = self._make_request("GET", endpoint, params=params)
            hotels = result.get("data", [])
            
            # Limit results
            return hotels[:max_results]
            
        except Exception as e:
            logger.error(f"Failed to search hotels: {str(e)}")
            raise
    
    def search_hotel_offers(
        self,
        hotel_ids: List[str],
        check_in: date,
        check_out: date,
        adults: int = 1,
        room_quantity: int = 1,
        currency: str = "USD",
        payment_policy: str = "NONE",
        best_rate_only: bool = True
    ) -> List[Dict[str, Any]]:
        """Get hotel offers with pricing using Amadeus Hotel Search API"""
        endpoint = "/v3/shopping/hotel-offers"
        
        # Amadeus API accepts max 100 hotel IDs per request
        hotel_ids_batch = hotel_ids[:100]
        
        params = {
            "hotelIds": ",".join(hotel_ids_batch),
            "checkInDate": check_in.isoformat(),
            "checkOutDate": check_out.isoformat(),
            "adults": adults,
            "roomQuantity": room_quantity,
            "currency": currency,
            "paymentPolicy": payment_policy,
            "bestRateOnly": str(best_rate_only).lower()
        }
        
        try:
            result = self._make_request("GET", endpoint, params=params)
            return result.get("data", [])
            
        except Exception as e:
            logger.error(f"Failed to get hotel offers: {str(e)}")
            raise
    
    def get_hotel_offers_by_hotel(
        self,
        hotel_id: str,
        check_in: date,
        check_out: date,
        adults: int = 1,
        room_quantity: int = 1,
        currency: str = "USD"
    ) -> Dict[str, Any]:
        """Get offers for a specific hotel"""
        endpoint = f"/v3/shopping/hotel-offers/by-hotel"
        params = {
            "hotelId": hotel_id,
            "checkInDate": check_in.isoformat(),
            "checkOutDate": check_out.isoformat(),
            "adults": adults,
            "roomQuantity": room_quantity,
            "currency": currency
        }
        
        try:
            result = self._make_request("GET", endpoint, params=params)
            return result.get("data", {})
            
        except Exception as e:
            logger.error(f"Failed to get hotel offers for hotel {hotel_id}: {str(e)}")
            raise
    
    def book_hotel(
        self,
        offer_id: str,
        guest_info: Dict[str, Any],
        payment_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Book a hotel using Amadeus Hotel Booking API
        
        This is a passthrough method - the actual booking logic 
        will be handled by LLM integration
        """
        endpoint = "/v1/booking/hotel-bookings"
        
        data = {
            "data": {
                "offerId": offer_id,
                "guests": guest_info,
                "payments": payment_info
            }
        }
        
        try:
            result = self._make_request("POST", endpoint, data=data)
            return result.get("data", {})
            
        except Exception as e:
            logger.error(f"Failed to book hotel: {str(e)}")
            raise
    
    def get_hotel_ratings(self, hotel_ids: List[str]) -> Dict[str, Any]:
        """Get hotel ratings and sentiments"""
        endpoint = "/v2/e-reputation/hotel-sentiments"
        
        params = {
            "hotelIds": ",".join(hotel_ids[:100])  # Max 100 hotels
        }
        
        try:
            result = self._make_request("GET", endpoint, params=params)
            return result.get("data", [])
            
        except Exception as e:
            logger.error(f"Failed to get hotel ratings: {str(e)}")
            return []


# Singleton instance
amadeus_service = AmadeusService()