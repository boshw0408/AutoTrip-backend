from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from core.config import settings
import json
from typing import Dict, List, Any

class LLMService:
    def __init__(self):
        self.llm = None
        if settings.openai_api_key:
            try:
                self.llm = ChatOpenAI(
                    openai_api_key=settings.openai_api_key,
                    model_name="gpt-3.5-turbo",
                    temperature=0.7
                )
                print("✅ OpenAI API initialized")
            except Exception as e:
                print(f"❌ OpenAI API initialization failed: {e}")
        else:
            print("⚠️ OpenAI API key not provided - using fallback responses")
        
        # Define prompt templates
        self.summarize_template = PromptTemplate(
            input_variables=["itinerary_data"],
            template="""
            You are a helpful travel assistant. Summarize this itinerary in a friendly, concise tone:
            
            {itinerary_data}
            
            Please provide:
            1. A brief overview of the trip
            2. Key highlights and must-see attractions
            3. Any special recommendations or tips
            
            Keep the summary engaging and under 200 words.
            """
        )
        
        self.highlights_template = PromptTemplate(
            input_variables=["itinerary_data"],
            template="""
            Extract the top 5 highlights from this itinerary:
            
            {itinerary_data}
            
            Return as a simple list of highlights.
            """
        )
        
        self.recommendations_template = PromptTemplate(
            input_variables=["itinerary_data"],
            template="""
            Based on this itinerary, provide 3 additional recommendations:
            
            {itinerary_data}
            
            Consider:
            - Local experiences
            - Hidden gems
            - Practical tips
            
            Return as a simple list of recommendations.
            """
        )
    
    async def summarize_itinerary(self, itinerary_data: Dict[str, Any]) -> str:
        """Summarize an itinerary using LangChain + OpenAI"""
        if not self.llm:
            # Fallback to mock summary if AI is not available
            return f"This is a {itinerary_data.get('duration', 3)}-day trip to {itinerary_data.get('location', 'your destination')}. The itinerary includes visits to popular attractions, local restaurants, and cultural sites. Perfect for experiencing the best of what the destination has to offer!"
        
        try:
            # Convert itinerary data to string for the prompt
            itinerary_text = json.dumps(itinerary_data, indent=2)
            
            # Create the prompt
            prompt = self.summarize_template.format(itinerary_data=itinerary_text)
            
            # Generate summary
            response = await self.llm.agenerate([prompt])
            summary = response.generations[0][0].text.strip()
            
            return summary
            
        except Exception as e:
            # Fallback to mock summary if AI fails
            return f"This is a {itinerary_data.get('duration', 3)}-day trip to {itinerary_data.get('location', 'your destination')}. The itinerary includes visits to popular attractions, local restaurants, and cultural sites. Perfect for experiencing the best of what the destination has to offer!"
    
    async def extract_highlights(self, itinerary_data: Dict[str, Any]) -> List[str]:
        """Extract key highlights from an itinerary"""
        if not self.llm:
            # Fallback highlights
            return [
                "Explore local attractions",
                "Try authentic cuisine", 
                "Visit cultural landmarks",
                "Experience local culture",
                "Create lasting memories"
            ]
        
        try:
            itinerary_text = json.dumps(itinerary_data, indent=2)
            prompt = self.highlights_template.format(itinerary_data=itinerary_text)
            
            response = await self.llm.agenerate([prompt])
            highlights_text = response.generations[0][0].text.strip()
            
            # Parse highlights into a list
            highlights = [line.strip('- ').strip() for line in highlights_text.split('\n') if line.strip()]
            return highlights[:5]  # Limit to 5 highlights
            
        except Exception as e:
            # Fallback highlights
            return [
                "Explore local attractions",
                "Try authentic cuisine", 
                "Visit cultural landmarks",
                "Experience local culture",
                "Create lasting memories"
            ]
    
    async def generate_recommendations(self, itinerary_data: Dict[str, Any]) -> List[str]:
        """Generate additional recommendations"""
        if not self.llm:
            # Fallback recommendations
            return [
                "Book restaurants in advance for popular spots",
                "Download offline maps for easy navigation",
                "Check local events happening during your visit"
            ]
        
        try:
            itinerary_text = json.dumps(itinerary_data, indent=2)
            prompt = self.recommendations_template.format(itinerary_data=itinerary_text)
            
            response = await self.llm.agenerate([prompt])
            recommendations_text = response.generations[0][0].text.strip()
            
            # Parse recommendations into a list
            recommendations = [line.strip('- ').strip() for line in recommendations_text.split('\n') if line.strip()]
            return recommendations[:3]  # Limit to 3 recommendations
            
        except Exception as e:
            # Fallback recommendations
            return [
                "Book restaurants in advance for popular spots",
                "Download offline maps for easy navigation",
                "Check local events happening during your visit"
            ]
    
    async def personalize_itinerary(self, itinerary_data: Dict[str, Any], preferences: Dict[str, Any], style: str = "friendly") -> Dict[str, Any]:
        """Personalize an itinerary based on user preferences"""
        try:
            # This would be a more complex prompt for personalization
            personalized_data = itinerary_data.copy()
            
            # Add personalization logic here
            # For now, return the original itinerary with a note
            personalized_data["personalization_note"] = f"Personalized for {style} style preferences"
            
            return personalized_data
            
        except Exception as e:
            return itinerary_data
    
    async def suggest_activities(self, location: str, interests: List[str], budget: float, duration: int) -> List[str]:
        """Suggest activities based on location and interests"""
        try:
            suggestions = [
                f"Explore {location} with a local guide",
                f"Try local cuisine at recommended restaurants",
                f"Visit cultural sites and museums",
                f"Take a walking tour of historic areas",
                f"Experience local nightlife and entertainment"
            ]
            
            return suggestions[:3]  # Return top 3 suggestions
            
        except Exception as e:
            return ["Explore the local area", "Try local food", "Visit popular attractions"]
    
    async def test_connection(self) -> str:
        """Test AI service connection"""
        if not self.llm:
            return "AI service not available - no API key provided"
        
        try:
            response = await self.llm.agenerate(["Hello, this is a test."])
            return "AI service is working correctly"
        except Exception as e:
            return f"AI service error: {str(e)}"
