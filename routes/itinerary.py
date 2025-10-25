from fastapi import APIRouter, HTTPException
from typing import List
from models.schemas import ItineraryGenerate, ItineraryResponse, RouteRequest, RouteResponse
from services.mock_data import MockDataService
from services.llm_service import LLMService
from services.data_aggregation import data_aggregation_service
import uuid
from datetime import datetime, timedelta

router = APIRouter()
mock_service = MockDataService()
llm_service = LLMService()

@router.post("/generate", response_model=ItineraryResponse)
async def generate_itinerary(request: ItineraryGenerate):
    """Generate a personalized itinerary for a trip using Data Aggregation Layer"""
    try:
        # Calculate duration
        duration = (request.end_date - request.start_date).days
        
        # Get comprehensive location data using Data Aggregation Layer
        location_data = await data_aggregation_service.get_comprehensive_location_data(
            location=request.location,
            interests=request.interests,
            budget=request.budget,
            travelers=request.travelers,
            duration=duration
        )
        
        # Generate itinerary using aggregated data
        itinerary_data = await _generate_itinerary_from_aggregated_data(
            location_data=location_data,
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
            "total_estimated_cost": itinerary_data.get("total_cost", 0),
            "data_sources": location_data.get("aggregated_at", "unknown")
        }
        
        return ItineraryResponse(**itinerary_response)
        
    except Exception as e:
        # Fallback to mock data if aggregation fails
        try:
            duration = (request.end_date - request.start_date).days
            itinerary_data = mock_service.generate_mock_itinerary(
                location=request.location,
                duration=duration,
                interests=request.interests,
                budget=request.budget,
                travelers=request.travelers
            )
            
            summary = await llm_service.summarize_itinerary(itinerary_data)
            
            itinerary_response = {
                "id": str(uuid.uuid4()),
                "location": request.location,
                "duration": duration,
                "days": itinerary_data["days"],
                "summary": summary,
                "total_estimated_cost": itinerary_data.get("total_cost", 0),
                "data_sources": "fallback_mock_data"
            }
            
            return ItineraryResponse(**itinerary_response)
            
        except Exception as fallback_error:
            raise HTTPException(status_code=500, detail=f"Failed to generate itinerary: {str(e)}. Fallback also failed: {str(fallback_error)}")

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

async def _generate_itinerary_from_aggregated_data(
    location_data: dict,
    duration: int,
    interests: List[str],
    budget: float,
    travelers: int
) -> dict:
    """Generate itinerary using aggregated data from multiple sources"""
    
    hotels = location_data.get("hotels", [])
    attractions = location_data.get("attractions", [])
    restaurants = location_data.get("restaurants", [])
    
    itinerary_days = []
    total_cost = 0
    
    for day in range(1, duration + 1):
        day_items = []
        
        # Morning activity - select from attractions
        if attractions:
            morning_activity = attractions[day % len(attractions)]
            day_items.append({
                "id": f"day_{day}_morning",
                "time": "09:00",
                "title": morning_activity["name"],
                "description": morning_activity.get("description", f"Visit {morning_activity['name']}"),
                "location": morning_activity["address"],
                "duration": "2 hours",
                "type": "attraction",
                "rating": morning_activity.get("rating", 4.0),
                "cost": 25.0,
                "source": morning_activity.get("source", "unknown")
            })
            total_cost += 25.0
        
        # Lunch - select from restaurants
        if restaurants:
            lunch_restaurant = restaurants[day % len(restaurants)]
            day_items.append({
                "id": f"day_{day}_lunch",
                "time": "12:00",
                "title": f"Lunch at {lunch_restaurant['name']}",
                "description": f"Enjoy local cuisine at {lunch_restaurant['name']}",
                "location": lunch_restaurant["address"],
                "duration": "1 hour",
                "type": "restaurant",
                "rating": lunch_restaurant.get("rating", 4.0),
                "cost": 35.0,
                "source": lunch_restaurant.get("source", "unknown")
            })
            total_cost += 35.0
        
        # Afternoon activity - select different attraction
        if attractions and len(attractions) > 1:
            afternoon_activity = attractions[(day + 1) % len(attractions)]
            day_items.append({
                "id": f"day_{day}_afternoon",
                "time": "14:00",
                "title": afternoon_activity["name"],
                "description": afternoon_activity.get("description", f"Explore {afternoon_activity['name']}"),
                "location": afternoon_activity["address"],
                "duration": "3 hours",
                "type": "attraction",
                "rating": afternoon_activity.get("rating", 4.0),
                "cost": 30.0,
                "source": afternoon_activity.get("source", "unknown")
            })
            total_cost += 30.0
        
        # Dinner - select different restaurant
        if restaurants and len(restaurants) > 1:
            dinner_restaurant = restaurants[(day + 1) % len(restaurants)]
            day_items.append({
                "id": f"day_{day}_dinner",
                "time": "19:00",
                "title": f"Dinner at {dinner_restaurant['name']}",
                "description": f"End your day with a memorable dining experience at {dinner_restaurant['name']}",
                "location": dinner_restaurant["address"],
                "duration": "1.5 hours",
                "type": "restaurant",
                "rating": dinner_restaurant.get("rating", 4.0),
                "cost": 50.0,
                "source": dinner_restaurant.get("source", "unknown")
            })
            total_cost += 50.0
        
        itinerary_days.append({
            "day": day,
            "date": (datetime.now() + timedelta(days=day-1)).strftime("%Y-%m-%d"),
            "items": day_items
        })
    
    # Calculate total cost per traveler
    total_cost_per_traveler = total_cost * travelers
    
    return {
        "location": location_data.get("location", "Unknown Location"),
        "duration": duration,
        "days": itinerary_days,
        "total_cost": total_cost_per_traveler,
        "interests": interests,
        "budget": budget,
        "travelers": travelers,
        "data_sources": location_data.get("aggregated_at", "unknown"),
        "hotels_available": len(hotels),
        "attractions_found": len(attractions),
        "restaurants_found": len(restaurants)
    }
