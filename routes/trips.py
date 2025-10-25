from fastapi import APIRouter, HTTPException
from typing import List
from models.schemas import TripCreate, TripResponse, PlaceSearch, PlaceResponse
from services.mock_data import MockDataService
from core.firebase import db
import uuid
from datetime import datetime

router = APIRouter()
mock_service = MockDataService()

@router.post("/", response_model=TripResponse)
async def create_trip(trip: TripCreate):
    """Create a new trip"""
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
        
        # Save to Firebase (or mock)
        trips_ref = db.collection('trips')
        trips_ref.document(trip_id).set(trip_data)
        
        return TripResponse(**trip_data)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create trip: {str(e)}")

@router.get("/{trip_id}", response_model=TripResponse)
async def get_trip(trip_id: str):
    """Get a specific trip by ID"""
    try:
        trip_doc = db.collection('trips').document(trip_id).get()
        
        if not trip_doc.exists:
            raise HTTPException(status_code=404, detail="Trip not found")
        
        trip_data = trip_doc.to_dict()
        return TripResponse(**trip_data)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get trip: {str(e)}")

@router.get("/", response_model=List[TripResponse])
async def get_trips():
    """Get all trips"""
    try:
        trips_ref = db.collection('trips')
        trips = trips_ref.get()
        
        trip_list = []
        for trip in trips:
            trip_data = trip.to_dict()
            trip_list.append(TripResponse(**trip_data))
        
        return trip_list
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get trips: {str(e)}")

@router.put("/{trip_id}", response_model=TripResponse)
async def update_trip(trip_id: str, trip: TripCreate):
    """Update an existing trip"""
    try:
        trip_doc = db.collection('trips').document(trip_id)
        existing_trip = trip_doc.get()
        
        if not existing_trip.exists:
            raise HTTPException(status_code=404, detail="Trip not found")
        
        duration = (trip.end_date - trip.start_date).days
        
        update_data = {
            "location": trip.location,
            "start_date": trip.start_date.isoformat(),
            "end_date": trip.end_date.isoformat(),
            "duration": duration,
            "budget": trip.budget,
            "travelers": trip.travelers,
            "interests": [interest.value for interest in trip.interests],
            "trip_type": trip.trip_type.value,
            "updated_at": datetime.now().isoformat()
        }
        
        trip_doc.update(update_data)
        
        # Get updated trip data
        updated_trip = trip_doc.get().to_dict()
        return TripResponse(**updated_trip)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update trip: {str(e)}")

@router.delete("/{trip_id}")
async def delete_trip(trip_id: str):
    """Delete a trip"""
    try:
        trip_doc = db.collection('trips').document(trip_id)
        existing_trip = trip_doc.get()
        
        if not existing_trip.exists:
            raise HTTPException(status_code=404, detail="Trip not found")
        
        trip_doc.delete()
        
        return {"message": "Trip deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete trip: {str(e)}")
