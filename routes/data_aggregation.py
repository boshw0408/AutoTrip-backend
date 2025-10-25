from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from pydantic import BaseModel
from services.data_aggregation import data_aggregation_service
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

class LocationDataRequest(BaseModel):
    location: str
    interests: List[str]
    budget: float
    travelers: int = 1
    duration: int = 3

class LocationDataResponse(BaseModel):
    location: str
    basic_info: Dict[str, Any]
    hotels: List[Dict[str, Any]]
    attractions: List[Dict[str, Any]]
    restaurants: List[Dict[str, Any]]
    transportation: Dict[str, Any]
    aggregated_at: str
    cache_key: str

@router.post("/location-data", response_model=LocationDataResponse)
async def get_location_data(request: LocationDataRequest):
    """
    Get comprehensive location data using Data Aggregation Layer
    
    This endpoint demonstrates the Data Aggregation Layer by:
    - Fetching data from multiple APIs (Google Maps, Yelp)
    - Combining and normalizing the data
    - Providing a unified response
    - Including caching information
    """
    try:
        logger.info(f"Fetching comprehensive data for {request.location}")
        
        # Use the Data Aggregation Service
        location_data = await data_aggregation_service.get_comprehensive_location_data(
            location=request.location,
            interests=request.interests,
            budget=request.budget,
            travelers=request.travelers,
            duration=request.duration
        )
        
        return LocationDataResponse(**location_data)
        
    except Exception as e:
        logger.error(f"Error fetching location data: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to fetch location data: {str(e)}"
        )

@router.get("/location-data/{location}")
async def get_location_data_by_name(
    location: str,
    interests: str = "Culture & History,Food & Dining",
    budget: float = 2000,
    travelers: int = 1,
    duration: int = 3
):
    """
    Get location data by location name (query parameters)
    
    This is a simpler endpoint for testing the Data Aggregation Layer
    """
    try:
        # Parse interests from comma-separated string
        interests_list = [interest.strip() for interest in interests.split(",")]
        
        logger.info(f"Fetching data for {location} with interests: {interests_list}")
        
        location_data = await data_aggregation_service.get_comprehensive_location_data(
            location=location,
            interests=interests_list,
            budget=budget,
            travelers=travelers,
            duration=duration
        )
        
        return {
            "status": "success",
            "location": location,
            "data": location_data,
            "summary": {
                "hotels_found": len(location_data.get("hotels", [])),
                "attractions_found": len(location_data.get("attractions", [])),
                "restaurants_found": len(location_data.get("restaurants", [])),
                "data_sources": location_data.get("aggregated_at", "unknown"),
                "cached": location_data.get("cache_key") is not None
            }
        }
        
    except Exception as e:
        logger.error(f"Error fetching location data: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "location": location
        }

@router.get("/health")
async def aggregation_health_check():
    """Health check for Data Aggregation Layer"""
    try:
        # Test with a simple location
        test_data = await data_aggregation_service.get_comprehensive_location_data(
            location="Paris, France",
            interests=["Culture & History"],
            budget=1000,
            travelers=1,
            duration=1
        )
        
        return {
            "status": "healthy",
            "service": "Data Aggregation Layer",
            "test_location": "Paris, France",
            "data_available": bool(test_data.get("hotels") or test_data.get("attractions")),
            "cache_size": len(data_aggregation_service._cache),
            "apis_configured": {
                "google_maps": bool(data_aggregation_service.google_maps.client),
                "yelp": bool(data_aggregation_service.yelp.api_key),
                "llm": bool(data_aggregation_service.llm_service.llm)
            }
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "Data Aggregation Layer",
            "error": str(e)
        }

@router.get("/cache/stats")
async def get_cache_stats():
    """Get cache statistics for the Data Aggregation Layer"""
    try:
        cache_stats = {
            "total_entries": len(data_aggregation_service._cache),
            "cache_ttl_seconds": data_aggregation_service._cache_ttl,
            "entries": []
        }
        
        for key, value in data_aggregation_service._cache.items():
            cache_stats["entries"].append({
                "key": key,
                "expires_at": value["expires_at"].isoformat(),
                "data_keys": list(value["data"].keys()) if isinstance(value["data"], dict) else "non_dict"
            })
        
        return cache_stats
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

@router.delete("/cache/clear")
async def clear_cache():
    """Clear the Data Aggregation Layer cache"""
    try:
        cache_size = len(data_aggregation_service._cache)
        data_aggregation_service._cache.clear()
        
        return {
            "status": "success",
            "message": f"Cleared {cache_size} cache entries",
            "cache_size_after": len(data_aggregation_service._cache)
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }
