from fastapi import APIRouter, HTTPException
from typing import List
from models.schemas import PlaceSearch, PlaceResponse

router = APIRouter()

@router.post("/search", response_model=List[PlaceResponse])
async def search_places(search: PlaceSearch):
    """Search for places (attractions, restaurants, etc.) in a location"""
    # This endpoint is not currently used - returns empty list
    # Future enhancement: Integrate with Google Places API
    return []

@router.get("/types")
async def get_place_types():
    """Get available place types"""
    return {
        "types": [
            "attractions",
            "restaurants", 
            "shopping",
            "entertainment",
            "nightlife",
            "museums",
            "parks",
            "landmarks"
        ]
    }

@router.get("/{place_id}", response_model=PlaceResponse)
async def get_place_details(place_id: str):
    """Get detailed information about a specific place"""
    # This endpoint is not currently used
    raise HTTPException(status_code=404, detail="Place not found")
