from fastapi import APIRouter, HTTPException
from models.schemas import AISummarizeRequest, AISummarizeResponse
from services.llm_service import LLMService

router = APIRouter()
llm_service = LLMService()

@router.post("/summarize", response_model=AISummarizeResponse)
async def summarize_itinerary(request: AISummarizeRequest):
    """Summarize an itinerary using AI"""
    try:
        summary = await llm_service.summarize_itinerary(request.itinerary_data)
        highlights = await llm_service.extract_highlights(request.itinerary_data)
        recommendations = await llm_service.generate_recommendations(request.itinerary_data)
        
        return AISummarizeResponse(
            summary=summary,
            highlights=highlights,
            recommendations=recommendations
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to summarize itinerary: {str(e)}")

@router.post("/personalize")
async def personalize_itinerary(request: dict):
    """Personalize an itinerary based on user preferences"""
    try:
        personalized_itinerary = await llm_service.personalize_itinerary(
            itinerary_data=request.get("itinerary_data"),
            preferences=request.get("preferences", {}),
            style=request.get("style", "friendly")
        )
        
        return {
            "personalized_itinerary": personalized_itinerary,
            "changes_made": request.get("changes_made", []),
            "reasoning": request.get("reasoning", "")
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to personalize itinerary: {str(e)}")

@router.post("/suggest-activities")
async def suggest_activities(request: dict):
    """Suggest additional activities based on location and interests"""
    try:
        suggestions = await llm_service.suggest_activities(
            location=request.get("location"),
            interests=request.get("interests", []),
            budget=request.get("budget", 0),
            duration=request.get("duration", 1)
        )
        
        return {
            "suggestions": suggestions,
            "reasoning": "Based on your interests and location preferences"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to suggest activities: {str(e)}")

@router.get("/health")
async def ai_health_check():
    """Check if AI services are working"""
    try:
        # Test basic AI functionality
        test_response = await llm_service.test_connection()
        
        return {
            "status": "healthy",
            "ai_service": "operational",
            "test_response": test_response
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "ai_service": "error",
            "error": str(e)
        }
