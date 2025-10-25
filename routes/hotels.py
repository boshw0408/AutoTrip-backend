from fastapi import APIRouter, HTTPException
from typing import List
from models.schemas import HotelSearch, HotelResponse
from services.mock_data import MockDataService

router = APIRouter()
mock_service = MockDataService()

@router.post("/search", response_model=List[HotelResponse])
async def search_hotels(search: HotelSearch):
    """Search for hotels in a location"""
    try:
        # For now, return mock data
        hotels = mock_service.get_mock_hotels(search.location)
        
        return hotels
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search hotels: {str(e)}")

@router.get("/{hotel_id}", response_model=HotelResponse)
async def get_hotel_details(hotel_id: str):
    """Get detailed information about a specific hotel"""
    try:
        # For now, return mock data
        hotel = mock_service.get_mock_hotel_details(hotel_id)
        
        if not hotel:
            raise HTTPException(status_code=404, detail="Hotel not found")
        
        return hotel
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get hotel details: {str(e)}")

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
            "Bar/Lounge"
        ]
    }
