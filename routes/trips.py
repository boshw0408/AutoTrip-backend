from fastapi import APIRouter, HTTPException
from typing import List
from models.schemas import TripCreate, TripResponse, PlaceSearch, PlaceResponse
from services.mock_data import MockDataService
from services.google_maps import GoogleMapsService
from pydantic import BaseModel
import uuid
from datetime import datetime

router = APIRouter()
mock_service = MockDataService()
google_maps_service = GoogleMapsService()

# Trip Planning Models
class TripPlanRequest(BaseModel):
    origin: str
    destination: str
    waypoints: List[str]

class LocationResponse(BaseModel):
    name: str
    address: str
    coordinates: dict
    place_type: str

class SegmentResponse(BaseModel):
    from_location: LocationResponse
    to_location: LocationResponse
    distance: str
    duration: str

class TripPlanResponse(BaseModel):
    optimized_order: List[LocationResponse]
    total_distance: str
    total_duration: str
    polyline: str
    segments: List[SegmentResponse]

class RouteVisualizationResponse(BaseModel):
    polyline: str
    markers: List[LocationResponse]
    bounds: dict

class TripSummaryResponse(BaseModel):
    total_distance: str
    total_duration: str
    location_count: int
    estimated_cost: str = None

class MapBoundsResponse(BaseModel):
    northeast: dict
    southwest: dict
    center: dict

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

# Enhanced Trip Planning Endpoints

@router.post("/plan", response_model=TripPlanResponse)
async def plan_trip(request: TripPlanRequest):
    """Plan a complete trip with optimized waypoint ordering"""
    try:
        trip_plan = await google_maps_service.plan_trip(
            origin=request.origin,
            destination=request.destination,
            waypoints=request.waypoints
        )
        
        if not trip_plan:
            raise HTTPException(status_code=400, detail="Failed to plan trip")
        
        # Convert to response format
        optimized_order = [
            LocationResponse(
                name=loc.name,
                address=loc.address,
                coordinates=loc.coordinates,
                place_type=loc.place_type
            ) for loc in trip_plan.optimized_order
        ]
        
        segments = [
            SegmentResponse(
                from_location=LocationResponse(
                    name=seg.from_location.name,
                    address=seg.from_location.address,
                    coordinates=seg.from_location.coordinates,
                    place_type=seg.from_location.place_type
                ),
                to_location=LocationResponse(
                    name=seg.to_location.name,
                    address=seg.to_location.address,
                    coordinates=seg.to_location.coordinates,
                    place_type=seg.to_location.place_type
                ),
                distance=seg.distance,
                duration=seg.duration
            ) for seg in trip_plan.segments
        ]
        
        return TripPlanResponse(
            optimized_order=optimized_order,
            total_distance=trip_plan.total_distance,
            total_duration=trip_plan.total_duration,
            polyline=trip_plan.polyline,
            segments=segments
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to plan trip: {str(e)}")

@router.post("/route-visualization", response_model=RouteVisualizationResponse)
async def get_route_visualization(request: TripPlanRequest):
    """Get route visualization data for map display"""
    try:
        route_viz = await google_maps_service.get_route_polyline(
            origin=request.origin,
            destination=request.destination,
            waypoints=request.waypoints
        )
        
        if not route_viz:
            raise HTTPException(status_code=400, detail="Failed to get route visualization")
        
        markers = [
            LocationResponse(
                name=marker.name,
                address=marker.address,
                coordinates=marker.coordinates,
                place_type=marker.place_type
            ) for marker in route_viz.markers
        ]
        
        return RouteVisualizationResponse(
            polyline=route_viz.polyline,
            markers=markers,
            bounds=route_viz.bounds
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get route visualization: {str(e)}")

@router.post("/summary", response_model=TripSummaryResponse)
async def get_trip_summary(request: TripPlanRequest):
    """Calculate trip summary statistics"""
    try:
        locations = [request.origin] + request.waypoints + [request.destination]
        summary = await google_maps_service.calculate_trip_summary(locations)
        
        if not summary:
            raise HTTPException(status_code=400, detail="Failed to calculate trip summary")
        
        return TripSummaryResponse(
            total_distance=summary.total_distance,
            total_duration=summary.total_duration,
            location_count=summary.location_count,
            estimated_cost=summary.estimated_cost
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate trip summary: {str(e)}")

@router.post("/map-bounds", response_model=MapBoundsResponse)
async def get_map_bounds(request: TripPlanRequest):
    """Get map bounds for all locations"""
    try:
        locations = [request.origin] + request.waypoints + [request.destination]
        bounds = await google_maps_service.get_map_bounds(locations)
        
        if not bounds:
            raise HTTPException(status_code=400, detail="Failed to get map bounds")
        
        return MapBoundsResponse(
            northeast=bounds.northeast,
            southwest=bounds.southwest,
            center=bounds.center
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get map bounds: {str(e)}")
