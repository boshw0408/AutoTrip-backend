from fastapi import APIRouter, HTTPException
from typing import List
from models.schemas import ItineraryGenerate, ItineraryResponse, RouteRequest, RouteResponse
from services.mock_data import MockDataService
from services.llm_service import LLMService
import uuid
from datetime import datetime, timedelta

router = APIRouter()
mock_service = MockDataService()
llm_service = LLMService()

@router.post("/generate", response_model=ItineraryResponse)
async def generate_itinerary(request: ItineraryGenerate):
    """Generate a personalized itinerary for a trip"""
    try:
        # Calculate duration
        duration = (request.end_date - request.start_date).days
        
        # Generate mock itinerary
        itinerary_data = mock_service.generate_mock_itinerary(
            location=request.location,
            duration=duration,
            interests=request.interests,
            budget=request.budget,
            travelers=request.travelers
        )
        
        # Generate AI summary using LangChain
        summary = await llm_service.summarize_itinerary(itinerary_data)
        
        itinerary_response = {
            "id": str(uuid.uuid4()),
            "location": request.location,
            "duration": duration,
            "days": itinerary_data["days"],
            "summary": summary,
            "total_estimated_cost": itinerary_data.get("total_cost", 0)
        }
        
        return ItineraryResponse(**itinerary_response)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate itinerary: {str(e)}")

@router.post("/routes", response_model=RouteResponse)
async def get_route(request: RouteRequest):
    """Get optimized route between locations"""
    try:
        # For now, return mock route data
        route_data = mock_service.get_mock_route(
            origin=request.origin,
            destination=request.destination,
            waypoints=request.waypoints,
            mode=request.mode
        )
        
        return RouteResponse(**route_data)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get route: {str(e)}")

@router.post("/optimize")
async def optimize_itinerary(itinerary_data: dict):
    """Optimize an existing itinerary for better route efficiency"""
    try:
        # This would integrate with Google Maps Directions API
        # For now, return the same itinerary
        return {
            "message": "Itinerary optimization coming soon",
            "original_itinerary": itinerary_data,
            "optimized_itinerary": itinerary_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to optimize itinerary: {str(e)}")

@router.get("/templates")
async def get_itinerary_templates():
    """Get pre-made itinerary templates for popular destinations"""
    return {
        "templates": [
            {
                "id": "paris_classic",
                "name": "Classic Paris",
                "location": "Paris, France",
                "duration": 3,
                "description": "Essential Parisian experiences"
            },
            {
                "id": "tokyo_adventure",
                "name": "Tokyo Adventure",
                "location": "Tokyo, Japan", 
                "duration": 4,
                "description": "Modern and traditional Tokyo"
            },
            {
                "id": "nyc_weekend",
                "name": "NYC Weekend",
                "location": "New York City, USA",
                "duration": 2,
                "description": "Perfect NYC weekend getaway"
            }
        ]
    }
