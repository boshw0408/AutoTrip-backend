from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from models.schemas import TripCreate, TripResponse, PlaceSearch, PlaceResponse
from services.google_maps import GoogleMapsService
from pydantic import BaseModel, Field, validator
import uuid
from datetime import datetime

router = APIRouter()

# Dependency injection for services
def get_google_maps_service() -> GoogleMapsService:
    """Dependency to get Google Maps service instance"""
    return GoogleMapsService()


# Trip Planning Models with Validation
class TripPlanRequest(BaseModel):
    origin: str = Field(..., min_length=3, max_length=200, description="Starting location")
    destination: str = Field(..., min_length=3, max_length=200, description="Ending location")
    waypoints: List[str] = Field(default=[], max_items=23, description="Intermediate stops (max 23 for Google Maps)")
    
    @validator('waypoints')
    def validate_waypoints(cls, v):
        """Ensure waypoints are not empty strings"""
        return [wp.strip() for wp in v if wp.strip()]
    
    @validator('destination')
    def validate_different_locations(cls, v, values):
        """Ensure origin and destination are different"""
        if 'origin' in values and v.strip().lower() == values['origin'].strip().lower():
            raise ValueError("Origin and destination must be different")
        return v

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
    waypoints_reordered: bool = Field(description="Whether waypoints were reordered for optimization")
    original_waypoint_order: Optional[List[int]] = Field(None, description="Original waypoint indices in optimized order")

class RouteVisualizationResponse(BaseModel):
    polyline: str
    markers: List[LocationResponse]
    bounds: dict

class TripSummaryResponse(BaseModel):
    total_distance: str
    total_duration: str
    location_count: int
    estimated_cost: Optional[str] = None

class MapBoundsResponse(BaseModel):
    northeast: dict
    southwest: dict
    center: dict


# ============================================
# Basic Trip CRUD Operations (Stateless)
# =================================

@router.post("/", response_model=TripResponse)
async def create_trip(
    trip: TripCreate
):
    """Create a new trip (stateless - no persistence)"""
    try:
        trip_id = str(uuid.uuid4())
        duration = (trip.end_date - trip.start_date).days
        
        trip_data = {
            "id": trip_id,
            "origin": trip.origin,
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
        
        return TripResponse(**trip_data)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create trip: {str(e)}")

@router.get("/{trip_id}", response_model=TripResponse)
async def get_trip(
    trip_id: str
):
    """Get a specific trip by ID (stateless - returns mock data)"""
    try:
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
        return []
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get trips: {str(e)}")

@router.put("/{trip_id}", response_model=TripResponse)
async def update_trip(
    trip_id: str,
    trip: TripCreate
):
    """Update an existing trip (stateless - returns updated mock data)"""
    try:
        duration = (trip.end_date - trip.start_date).days
        
        update_data = {
            "id": trip_id,
            "origin": trip.origin,
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
async def delete_trip(
    trip_id: str
):
    """Delete a trip (stateless - always succeeds)"""
    try:
        return {"message": "Trip deleted successfully (stateless operation)"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete trip: {str(e)}")


# ============================================
# Enhanced Trip Planning Endpoints (Google Maps Integration)
# ============================================

@router.post("/plan", response_model=TripPlanResponse)
async def plan_trip(
    request: TripPlanRequest,
    google_maps_service: GoogleMapsService = Depends(get_google_maps_service)
):
    """
    Plan a complete trip with optimized waypoint ordering.
    
    Google Maps will automatically reorder waypoints to find the shortest/fastest route.
    The response includes the optimized order and detailed segments.
    """
    try:
        # Validate that we have at least an origin and destination
        if not request.origin or not request.destination:
            raise HTTPException(
                status_code=400,
                detail="Origin and destination are required"
            )
        
        # Call Google Maps service with optimization enabled
        trip_plan = await google_maps_service.plan_trip(
            origin=request.origin,
            destination=request.destination,
            waypoints=request.waypoints
        )
        
        if not trip_plan:
            raise HTTPException(
                status_code=400,
                detail="Failed to plan trip. Please check that all locations are valid."
            )
        
        # Convert dataclasses to Pydantic models for response
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
        
        # Check if waypoints were reordered
        waypoints_reordered = len(request.waypoints) > 1
        
        return TripPlanResponse(
            optimized_order=optimized_order,
            total_distance=trip_plan.total_distance,
            total_duration=trip_plan.total_duration,
            polyline=trip_plan.polyline,
            segments=segments,
            waypoints_reordered=waypoints_reordered
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to plan trip: {str(e)}"
        )

@router.post("/route-visualization", response_model=RouteVisualizationResponse)
async def get_route_visualization(
    request: TripPlanRequest,
    google_maps_service: GoogleMapsService = Depends(get_google_maps_service)
):
    """
    Get route visualization data for map display.
    
    Returns polyline for drawing the route on a map, markers for all locations,
    and bounds for setting the map viewport.
    """
    try:
        if not request.origin or not request.destination:
            raise HTTPException(
                status_code=400,
                detail="Origin and destination are required"
            )
        
        route_viz = await google_maps_service.get_route_polyline(
            origin=request.origin,
            destination=request.destination,
            waypoints=request.waypoints
        )
        
        if not route_viz:
            raise HTTPException(
                status_code=400,
                detail="Failed to get route visualization. Please check that all locations are valid."
            )
        
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
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get route visualization: {str(e)}"
        )

@router.post("/map-bounds", response_model=MapBoundsResponse)
async def get_map_bounds(
    request: TripPlanRequest,
    google_maps_service: GoogleMapsService = Depends(get_google_maps_service)
):
    """
    Get map bounds for all locations.
    
    Returns the bounding box coordinates that contain all locations in the trip.
    Useful for setting the initial map viewport.
    """
    try:
        locations = [request.origin] + request.waypoints + [request.destination]
        
        if not locations:
            raise HTTPException(
                status_code=400,
                detail="At least one location is required"
            )
        
        bounds = await google_maps_service.get_map_bounds(locations)
        
        if not bounds:
            raise HTTPException(
                status_code=400,
                detail="Failed to get map bounds. Please check that all locations are valid."
            )
        
        return MapBoundsResponse(
            northeast=bounds.northeast,
            southwest=bounds.southwest,
            center=bounds.center
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get map bounds: {str(e)}"
        )


# ============================================
# Utility Endpoint
# ============================================

@router.get("/health")
async def health_check(
    google_maps_service: GoogleMapsService = Depends(get_google_maps_service)
):
    """Check if the trips API and Google Maps service are working"""
    return {
        "status": "healthy",
        "google_maps_initialized": google_maps_service.client is not None,
        "timestamp": datetime.now().isoformat()
    }