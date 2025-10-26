from fastapi import APIRouter, HTTPException
from typing import List
from models.schemas import PlaceSearch, PlaceResponse

router = APIRouter()

@router.post("/search", response_model=List[PlaceResponse])
async def search_places(search: PlaceSearch):
    """Search for places (attractions, restaurants, etc.) in a location"""
    try:
        # Mock data has been removed - return empty list
        # TODO: Integrate with real data sources (Google Places API, etc.)
        return []
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search places: {str(e)}")

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
    try:
        # Mock data has been removed
        raise HTTPException(status_code=404, detail="Place not found")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get place details: {str(e)}")
