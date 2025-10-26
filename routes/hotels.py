 from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import date
from schemas import (
    HotelSearchRequest, 
    HotelSearchResponse, 
    HotelComparisonRequest,
    HotelComparisonResponse,
    BudgetBreakdownResponse
)
from amadeus_service import amadeus_service
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/search", response_model=List[dict])
async def search_hotels(search_request: HotelSearchRequest):
    """
    Search for hotels using Amadeus API - returns raw Amadeus data
    """
    try:
        # Get city code from destination
        city_code = amadeus_service.get_city_code(search_request.destination)
        
        if not city_code:
            raise HTTPException(
                status_code=404, 
                detail=f"Could not find city code for destination: {search_request.destination}"
            )
        
        # Search for hotels in the city
        hotels = amadeus_service.search_hotels_by_city(
            city_code=city_code,
            check_in=search_request.check_in,
            check_out=search_request.check_out,
            adults=search_request.travelers,
            max_results=50
        )
        
        if not hotels:
            return []
        
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
        
        # Return raw Amadeus data
        return offers
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to search hotels: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to search hotels: {str(e)}")


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