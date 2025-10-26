from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import StreamingResponse
from typing import List
from models.schemas import ItineraryGenerate, ItineraryResponse, RouteRequest, RouteResponse
from services.mock_data import MockDataService
from services.llm_service import LLMService
from services.data_aggregation import data_aggregation_service
from services.pdf_service import PDFService
from services.ical_service import ICalService
import uuid
from datetime import datetime, timedelta

router = APIRouter()
mock_service = MockDataService()
llm_service = LLMService()
pdf_service = PDFService()
ical_service = ICalService()

@router.post("/generate", response_model=ItineraryResponse)
async def generate_itinerary(request: ItineraryGenerate):
    """Generate a personalized itinerary for a trip using Data Aggregation Layer and TravelAI"""
    try:
        # Calculate duration
        duration = (request.end_date - request.start_date).days
        
        # Use origin if provided, otherwise default to location
        search_location = request.origin if request.origin else request.location
        
        # Get comprehensive location data using Data Aggregation Layer
        location_data = await data_aggregation_service.get_comprehensive_location_data(
            location=search_location,
            interests=request.interests,
            budget=request.budget,
            travelers=request.travelers,
            duration=duration
        )
        
        # For 2-day trips, use the comprehensive TravelAI itinerary generator
        if duration == 2:
            comprehensive_itinerary = await llm_service.generate_comprehensive_2day_itinerary(
                aggregated_data=location_data,
                start_location=request.origin or request.location,
                destination=request.location,
                interests=request.interests,
                budget=request.budget,
                travelers=request.travelers,
                user_preferences=""
            )
            
            # Convert comprehensive itinerary to ItineraryResponse format
            itinerary_days = []
            
            # Track selected places to prevent duplicates
            selected_places = set()
            
            # Process Day 1
            day1_items = []
            for item in comprehensive_itinerary.get("day1", []):
                activity_name = item.get("activity", "").lower().strip()
                
                # Skip if we've already selected this place
                if activity_name in selected_places:
                    print(f"⚠️ Skipping duplicate: {item.get('activity')}")
                    continue
                
                selected_places.add(activity_name)
                
                day1_items.append({
                    "id": f"day1_{len(day1_items)}",
                    "time": item.get("time", ""),
                    "title": item.get("activity", ""),
                    "description": item.get("description", ""),
                    "location": item.get("location", ""),
                    "duration": item.get("duration", ""),
                    "type": item.get("type", "activity"),
                    "rating": None,
                    "cost": item.get("cost", 0)
                })
            
            itinerary_days.append({
                "day": 1,
                "date": request.start_date.strftime("%Y-%m-%d"),
                "items": day1_items
            })
            
            # Process Day 2
            day2_items = []
            for item in comprehensive_itinerary.get("day2", []):
                activity_name = item.get("activity", "").lower().strip()
                
                # Skip if we've already selected this place
                if activity_name in selected_places:
                    print(f"⚠️ Skipping duplicate: {item.get('activity')}")
                    continue
                
                selected_places.add(activity_name)
                
                day2_items.append({
                    "id": f"day2_{len(day2_items)}",
                    "time": item.get("time", ""),
                    "title": item.get("activity", ""),
                    "description": item.get("description", ""),
                    "location": item.get("location", ""),
                    "duration": item.get("duration", ""),
                    "type": item.get("type", "activity"),
                    "rating": None,
                    "cost": item.get("cost", 0)
                })
            
            itinerary_days.append({
                "day": 2,
                "date": (request.start_date + timedelta(days=1)).strftime("%Y-%m-%d"),
                "items": day2_items
            })
            
            # Get summary from comprehensive itinerary
            summary = comprehensive_itinerary.get("summary", "")
            
            # Calculate total cost from budget breakdown
            budget_breakdown = comprehensive_itinerary.get("budget_breakdown", {})
            total_cost = budget_breakdown.get("total", request.budget)
            
            itinerary_response = {
                "id": str(uuid.uuid4()),
                "location": request.location,
                "origin": request.origin,
                "duration": duration,
                "days": itinerary_days,
                "summary": summary,
                "total_estimated_cost": total_cost * request.travelers,
                "data_sources": location_data.get("aggregated_at", "unknown")
            }
            
            return ItineraryResponse(**itinerary_response)
        
        # For trips longer than 2 days, use the traditional method
        else:
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
                "origin": request.origin,
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
                "origin": request.origin,
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

@router.post("/export-pdf")
async def export_itinerary_pdf(itinerary: ItineraryResponse):
    """Export itinerary as PDF"""
    try:
        # Convert itinerary to dict
        itinerary_dict = itinerary.dict()
        
        # Generate PDF
        pdf_buffer = pdf_service.generate_itinerary_pdf(itinerary_dict)
        
        # Create filename
        location = itinerary.location.replace(" ", "_")
        filename = f"itinerary_{location}_{datetime.now().strftime('%Y%m%d')}.pdf"
        
        # Use Response with proper headers
        headers = {
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Type": "application/pdf"
        }
        
        return Response(
            content=pdf_buffer.read(),
            media_type="application/pdf",
            headers=headers
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating PDF: {str(e)}")

@router.post("/export-calendar")
async def export_itinerary_calendar(itinerary: ItineraryResponse):
    """Export itinerary as iCalendar (.ics) file"""
    try:
        # Convert itinerary to dict
        itinerary_dict = itinerary.dict()
        
        # Generate iCal content
        ical_content = ical_service.generate_ical_from_itinerary(itinerary_dict)
        
        # Create filename
        location = itinerary.location.replace(" ", "_")
        filename = f"itinerary_{location}_{datetime.now().strftime('%Y%m%d')}.ics"
        
        # Return iCal file
        headers = {
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Type": "text/calendar"
        }
        
        return Response(
            content=ical_content,
            media_type="text/calendar",
            headers=headers
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating calendar: {str(e)}")

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
