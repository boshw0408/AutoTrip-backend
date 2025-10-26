from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
from datetime import date
from models.schemas import (
    HotelSearchRequest, 
    HotelSearchResponse, 
    HotelComparisonRequest,
    HotelComparisonResponse,
    BudgetBreakdownResponse
)
from services.amadeus import amadeus_service
from services.google_maps import GoogleMapsService
import logging
import math

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize Google Maps service for geocoding
google_maps_service = GoogleMapsService()


def get_coordinates_from_location(location: str) -> Optional[Dict[str, float]]:
    """
    Get latitude and longitude from a location string using Google Maps geocoding
    """
    try:
        if google_maps_service.client:
            geocode_result = google_maps_service.client.geocode(location)
            if geocode_result:
                loc = geocode_result[0]['geometry']['location']
                return {"lat": loc['lat'], "lng": loc['lng']}
        return None
    except Exception as e:
        logger.error(f"Failed to geocode location {location}: {str(e)}")
        return None


def calculate_midpoint(loc1: Dict[str, float], loc2: Dict[str, float]) -> Dict[str, float]:
    """
    Calculate the midpoint between two coordinates
    """
    return {
        "lat": (loc1["lat"] + loc2["lat"]) / 2,
        "lng": (loc1["lng"] + loc2["lng"]) / 2
    }


def calculate_distance(loc1: Dict[str, float], loc2: Dict[str, float]) -> float:
    """
    Calculate distance between two coordinates using Haversine formula (in km)
    """
    # Earth's radius in km
    R = 6371
    
    lat1_rad = math.radians(loc1["lat"])
    lat2_rad = math.radians(loc2["lat"])
    delta_lat = math.radians(loc2["lat"] - loc1["lat"])
    delta_lng = math.radians(loc2["lng"] - loc1["lng"])
    
    a = math.sin(delta_lat / 2) ** 2 + \
        math.cos(lat1_rad) * math.cos(lat2_rad) * \
        math.sin(delta_lng / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c


def transform_amadeus_offer_to_hotel(offer: Dict[str, Any], check_in: str = None, check_out: str = None, midpoint: Optional[Dict[str, float]] = None, google_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Transform Amadeus hotel offer to frontend-compatible format
    Enriches with Google Maps data for ratings and photos
    """
    hotel_info = offer.get("hotel", {})
    best_offer = offer.get("offers", [{}])[0] if offer.get("offers") else {}
    price_info = best_offer.get("price", {})
    
    # Extract price per night
    price_total = float(price_info.get("total", 0))
    
    # Calculate number of nights from check_in/check_out dates
    nights = 1  # Default to 1 night
    if check_in and check_out:
        try:
            from datetime import datetime, date
            
            # Handle both string and date objects
            if isinstance(check_in, str):
                check_in_date = datetime.strptime(check_in, "%Y-%m-%d").date()
            elif isinstance(check_in, date):
                check_in_date = check_in
            else:
                check_in_date = None
                
            if isinstance(check_out, str):
                check_out_date = datetime.strptime(check_out, "%Y-%m-%d").date()
            elif isinstance(check_out, date):
                check_out_date = check_out
            else:
                check_out_date = None
            
            if check_in_date and check_out_date:
                nights = max(1, (check_out_date - check_in_date).days)
        except Exception as e:
            logger.warning(f"Failed to calculate nights from dates: {e}")
    
    price_per_night = price_total / nights if nights > 0 else price_total
    
    # Extract amenities from room description or other fields
    amenities = []
    room_info = best_offer.get("room", {})
    if room_info.get("typeEstimated"):
        amenities.append("Room Service")
    
    # Mock some common amenities
    amenities.extend(["WiFi", "Air Conditioning", "24-hour Front Desk"])
    
    # Construct address
    address = f"{hotel_info.get('latitude', '')}, {hotel_info.get('longitude', '')}"
    
    # Calculate distance from midpoint if provided
    distance_from_midpoint = None
    if midpoint and hotel_info.get("latitude") and hotel_info.get("longitude"):
        hotel_location = {
            "lat": hotel_info.get("latitude"),
            "lng": hotel_info.get("longitude")
        }
        distance_km = calculate_distance(midpoint, hotel_location)
        distance_from_midpoint = f"{distance_km:.1f} km"
    
    # Get rating and photos from Google Maps data if available
    hotel_id = hotel_info.get("hotelId", "")
    rating = 0.0
    photos = []
    
    if google_data:
        rating = google_data.get("rating", 0.0)
        photos = google_data.get("photos", [])
    else:
        # Fallback: no stars if no Google Maps data
        rating = 0.0
    
    # Use Google Maps address if available, otherwise use coordinates
    final_address = address
    if google_data and google_data.get("address"):
        final_address = google_data.get("address")
    
    return {
        "id": hotel_id,
        "name": hotel_info.get("name", "Unknown Hotel"),
        "rating": rating,
        "price": price_per_night,
        "price_per_night": price_per_night,
        "address": final_address,
        "amenities": amenities,
        "image": photos[0] if photos else "",  # Use first photo as main image
        "photos": photos,
        "distance": distance_from_midpoint or "",
        "distance_from_center": distance_from_midpoint or "",
        "available": offer.get("available", False),
        "city_code": hotel_info.get("cityCode", ""),
        "latitude": hotel_info.get("latitude"),
        "longitude": hotel_info.get("longitude"),
        "offers": offer.get("offers", []),
        "_distance_km": distance_km if midpoint and hotel_info.get("latitude") and hotel_info.get("longitude") else float('inf')
    }


@router.post("/search", response_model=List[dict])
async def search_hotels(search_request: HotelSearchRequest):
    """
    Search for hotels using Amadeus API - returns transformed data compatible with frontend
    If starting_location is provided, searches around the midpoint between start and destination
    Returns top 5 hotels closest to the midpoint
    """
    try:
        midpoint = None
        
        # If starting location is provided, calculate midpoint
        if search_request.starting_location:
            start_coords = get_coordinates_from_location(search_request.starting_location)
            dest_coords = get_coordinates_from_location(search_request.destination)
            
            if start_coords and dest_coords:
                midpoint = calculate_midpoint(start_coords, dest_coords)
                logger.info(f"Calculated midpoint: {midpoint} between {search_request.starting_location} and {search_request.destination}")
            else:
                logger.warning(f"Could not geocode locations for midpoint calculation")
        
        # Try to search around multiple possible cities near the destination
        cities_to_try = [search_request.destination]
        
        # Always add SF and Oakland as fallbacks since they have city codes
        cities_to_try.extend([
            "San Francisco",
            "Oakland"
        ])
        
        all_hotels = []
        
        # Try each city until we find hotels
        for city in cities_to_try:
            # Get city code from destination
            city_code = amadeus_service.get_city_code(city)
            
            if not city_code:
                logger.warning(f"Could not find city code for {city}")
                continue
            
            # Search for hotels in the city
            hotels = amadeus_service.search_hotels_by_city(
                city_code=city_code,
                check_in=search_request.check_in,
                check_out=search_request.check_out,
                adults=search_request.travelers,
                max_results=50
            )
            
            if not hotels:
                logger.warning(f"No hotels found via Amadeus for {city}")
                continue
            
            # Get hotel IDs
            hotel_ids = [hotel.get("hotelId") for hotel in hotels if hotel.get("hotelId")]
            
            # Get offers for these hotels
            offers = amadeus_service.search_hotel_offers(
                hotel_ids=hotel_ids,
                check_in=search_request.check_in,
                check_out=search_request.check_out,
                adults=search_request.travelers,
                currency="USD"
            )
            
            # Transform Amadeus offers to frontend-compatible format
            # We'll fetch Google Maps data for each hotel
            transformed_hotels = []
            for offer in offers:
                hotel_google_data = None
                hotel_name = offer.get("hotel", {}).get("name", "")
                
                # Fetch rating and photos from Google Maps
                if hotel_name:
                    try:
                        hotel_google_data = await google_maps_service.get_hotel_details_by_name(
                            hotel_name=hotel_name,
                            location=search_request.destination
                        )
                        if hotel_google_data:
                            logger.info(f"Found Google Maps data for {hotel_name}")
                    except Exception as e:
                        logger.warning(f"Failed to fetch Google Maps data for {hotel_name}: {str(e)}")
                
                transformed_hotel = transform_amadeus_offer_to_hotel(
                    offer, 
                    check_in=search_request.check_in, 
                    check_out=search_request.check_out,
                    midpoint=midpoint,
                    google_data=hotel_google_data
                )
                transformed_hotels.append(transformed_hotel)
            
            all_hotels.extend(transformed_hotels)
            
            # If we found hotels, continue searching to get more options
            if transformed_hotels:
                logger.info(f"Found {len(transformed_hotels)} hotels in {city}")
        
        if not all_hotels:
            logger.warning(f"No hotels found for any cities near {search_request.destination}")
            return []
        
        # Sort by distance from midpoint (if available) and return top 5
        if midpoint:
            all_hotels.sort(key=lambda h: h.get("_distance_km", float('inf')))
            top_hotels = all_hotels[:5]
            logger.info(f"Returning top 5 hotels closest to midpoint")
        else:
            top_hotels = all_hotels[:5]
            logger.info(f"Returning top 5 hotels")
        
        # Remove the internal _distance_km field before returning
        for hotel in top_hotels:
            hotel.pop("_distance_km", None)
        
        return top_hotels
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to search hotels: {str(e)}")
        # Return empty list instead of raising error
        return []


@router.get("/{hotel_id}")
async def get_hotel_details(
    hotel_id: str,
    check_in: date = Query(..., description="Check-in date"),
    check_out: date = Query(..., description="Check-out date"),
    adults: int = Query(1, description="Number of adults")
):
    """
    Get hotel offers by hotel ID - returns raw Amadeus data
    """
    try:
        # Get hotel offers
        offer_data = amadeus_service.get_hotel_offers_by_hotel(
            hotel_id=hotel_id,
            check_in=check_in,
            check_out=check_out,
            adults=adults
        )
        
        if not offer_data:
            raise HTTPException(status_code=404, detail="Hotel not found or no offers available")
        
        # Return raw Amadeus data
        return offer_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get hotel details: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get hotel details: {str(e)}")


@router.post("/offers")
async def get_hotel_offers(
    hotel_ids: List[str],
    check_in: date,
    check_out: date,
    adults: int = 1,
    room_quantity: int = 1,
    currency: str = "USD"
):
    """
    Get hotel offers for multiple hotels - returns raw Amadeus data
    """
    try:
        offers = amadeus_service.search_hotel_offers(
            hotel_ids=hotel_ids,
            check_in=check_in,
            check_out=check_out,
            adults=adults,
            room_quantity=room_quantity,
            currency=currency
        )
        
        # Return raw Amadeus data
        return offers
        
    except Exception as e:
        logger.error(f"Failed to get hotel offers: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get hotel offers: {str(e)}")


@router.get("/city-code/{city_name}")
async def get_city_code(city_name: str):
    """
    Get IATA city code from city name
    """
    try:
        city_code = amadeus_service.get_city_code(city_name)
        
        if not city_code:
            raise HTTPException(status_code=404, detail=f"City code not found for: {city_name}")
        
        return {
            "city_name": city_name,
            "city_code": city_code
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get city code: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get city code: {str(e)}")


@router.get("/ratings/{hotel_id}")
async def get_hotel_ratings(hotel_id: str):
    """
    Get hotel ratings and sentiment - returns raw Amadeus data
    """
    try:
        ratings = amadeus_service.get_hotel_ratings([hotel_id])
        
        if not ratings:
            return {
                "hotel_id": hotel_id,
                "message": "No ratings available"
            }
        
        # Return raw Amadeus data
        return ratings[0] if ratings else {}
        
    except Exception as e:
        logger.error(f"Failed to get hotel ratings: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get ratings: {str(e)}")


@router.post("/book")
async def book_hotel(
    offer_id: str,
    guests: List[dict],
    payments: List[dict]
):
    """
    Book a hotel using Amadeus API
    
    This endpoint connects to Amadeus booking API.
    Your LLM will handle the booking logic and call this endpoint.
    
    Example request body:
    {
        "offer_id": "XXXX",
        "guests": [
            {
                "name": {
                    "firstName": "John",
                    "lastName": "Doe"
                },
                "contact": {
                    "email": "john@example.com",
                    "phone": "+1234567890"
                }
            }
        ],
        "payments": [
            {
                "method": "creditCard",
                "card": {
                    "vendorCode": "VI",
                    "cardNumber": "4111111111111111",
                    "expiryDate": "2025-12"
                }
            }
        ]
    }
    """
    try:
        # Prepare guest info
        guest_info = guests
        
        # Prepare payment info
        payment_info = payments
        
        # Call Amadeus booking API
        booking_result = amadeus_service.book_hotel(
            offer_id=offer_id,
            guest_info=guest_info,
            payment_info=payment_info
        )
        
        # Return raw Amadeus booking response
        return booking_result
        
    except Exception as e:
        logger.error(f"Failed to book hotel: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to book hotel: {str(e)}")


@router.get("/amenities/list")
async def get_hotel_amenities():
    """Get list of common hotel amenities"""
    return {
        "amenities": [
            "WiFi",
            "Parking",
            "Restaurant",
            "Pool",
            "Gym",
            "Spa",
            "Room Service",
            "Concierge",
            "Business Center",
            "Pet Friendly",
            "Airport Shuttle",
            "Bar/Lounge",
            "Air Conditioning",
            "Breakfast Included",
            "Laundry Service",
            "24-hour Front Desk"
        ]
    }