from fastapi import APIRouter, HTTPException
from typing import List
from models.schemas import TripCreate, TripResponse, PlaceSearch, PlaceResponse
from services.mock_data import MockDataService
import uuid
from datetime import datetime

router = APIRouter()
mock_service = MockDataService()

@router.post("/", response_model=TripResponse)
async def create_trip(trip: TripCreate):
    """Create a new trip (stateless - no persistence)"""
    try:
        trip_id = str(uuid.uuid4())
        duration = (trip.end_date - trip.start_date).days
        
        trip_data = {
            "id": trip_id,
            "location": trip.location,
            "start_date": trip.start_date.isoformat(),
            "end_date": trip.end_date.isoformat(),
            "duration": duration,
            "budget": trip.budget,
            "travelers": trip.travelers,
            "interests": [interest.value for interest in trip.interests],
            "trip_type": trip.trip_type.value,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        # Return trip data without persistence (stateless)
        return TripResponse(**trip_data)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create trip: {str(e)}")

@router.get("/{trip_id}", response_model=TripResponse)
async def get_trip(trip_id: str):
    """Get a specific trip by ID (stateless - returns mock data)"""
    try:
        # Since we're stateless, return a mock trip
        mock_trip = {
            "id": trip_id,
            "location": "Paris, France",
            "start_date": "2024-06-01",
            "end_date": "2024-06-03",
            "duration": 2,
            "budget": 2000.0,
            "travelers": 2,
            "interests": ["Culture & History", "Food & Dining"],
            "trip_type": "leisure",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        return TripResponse(**mock_trip)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get trip: {str(e)}")

@router.get("/", response_model=List[TripResponse])
async def get_trips():
    """Get all trips (stateless - returns empty list)"""
    try:
        # Since we're stateless, return empty list
        return []
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get trips: {str(e)}")

@router.put("/{trip_id}", response_model=TripResponse)
async def update_trip(trip_id: str, trip: TripCreate):
    """Update an existing trip (stateless - returns updated mock data)"""
    try:
        duration = (trip.end_date - trip.start_date).days
        
        update_data = {
            "id": trip_id,
            "location": trip.location,
            "start_date": trip.start_date.isoformat(),
            "end_date": trip.end_date.isoformat(),
            "duration": duration,
            "budget": trip.budget,
            "travelers": trip.travelers,
            "interests": [interest.value for interest in trip.interests],
            "trip_type": trip.trip_type.value,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        return TripResponse(**update_data)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update trip: {str(e)}")

@router.delete("/{trip_id}")
async def delete_trip(trip_id: str):
    """Delete a trip (stateless - always succeeds)"""
    try:
        return {"message": "Trip deleted successfully (stateless operation)"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete trip: {str(e)}")
