from langchain_core.prompts import PromptTemplate
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
                    model_name="gpt-4o-mini",
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
            You are a helpful travel assistant. Summarize this itinerary in exactly ONE sentence:
            
            {itinerary_data}
            
            Provide ONLY one sentence summarizing the trip's main highlights and theme.
            """
        )
        
        # Comprehensive TravelAI prompt for 2-day itinerary generation
        self.travelai_2day_template = PromptTemplate(
            input_variables=["aggregated_data", "start_location", "destination", "interests", "budget", "travelers", "user_preferences"],
            template="""
You are TravelAI — an intelligent trip planner that creates personalized 2-day travel itineraries.
Your goal is to help users plan a short trip including route, attractions, meals, and hotel.

===========================
🎯 OBJECTIVE
===========================
Plan a realistic 2-day itinerary that fits the user's:
- Start location: {start_location}
- Destination: {destination}
- Interests: {interests}
- Budget: ${budget}
- Number of travelers: {travelers}
- Preferences: {user_preferences}

Output must include:
1. Ordered list of attractions for each day (up to 6 total)
2. Restaurant and dessert spots (breakfast, lunch, dinner × 2 days)
3. Hotel recommendation (1 hotel near midpoint)
4. Optimized route between locations
5. Estimated total cost and time per activity

===========================
📊 AVAILABLE DATA
===========================
Here is the aggregated data from multiple sources (Google Maps, Yelp, Instagram):

{aggregated_data}

===========================
🧭 STEP 1: Route Setup
===========================
1. Use the Google Maps Directions API data to find the optimal route from start → destination.
2. Ensure total travel time per day ≤ 6 hours.
3. If total route > 4 hours, reduce number of attractions.
4. Define "midpoint" of route for hotel placement.

===========================
🎡 STEP 2: Attractions Selection
===========================
- Choose up to 6 attractions total across 2 days.
- Select based on user's stated interests ({interests}).
- Prefer attractions along or near the optimal route (within 30 minutes detour).
- Include any must-go landmark if within 2 hours of route.
- For each attraction, include:
  - Name
  - Short "Why Visit" summary
  - Estimated visit time (based on typical durations online)
  - Distance/time from previous stop

===========================
🍽️ STEP 3: Food & Dessert
===========================
- Total of 6 meals (breakfast, lunch, dinner × 2 days).
- Breakfast: near hotel or start location.
- Lunch/dinner: near main attractions of that day.
- Dessert/café: near evening stop or hotel.
- Use trending restaurants if available (via Instagram/Yelp API).
- Filter by: rating ≥ 4.0, price level within budget, and popularity.

===========================
🏨 STEP 4: Hotel Selection
===========================
- CRITICAL: Look for "The user has selected hotel:" in the user preferences section above.
- If a hotel is mentioned in user preferences, you MUST use THAT EXACT HOTEL NAME and address.
- Add a "hotel" type activity for checking in to this specific hotel (usually in the evening of Day 1).
- Add a "hotel" type activity for checking out from this hotel (usually in the morning of Day 2).
- Reference the hotel name, location, and price in your recommendations.
- Do NOT search for other hotels - use ONLY the one specified in user preferences.
- If NO hotel is mentioned in user preferences, skip hotel activities.

===========================
💰 STEP 5: Budget Allocation
===========================
- IMPORTANT: The hotel has already been paid for by the user. Focus allocation on remaining budget.
- Allocate the REMAINING BUDGET provided in user preferences across meals, attractions, and transport.
- If remaining budget is mentioned in user preferences, use that amount. Otherwise, estimate based on typical costs.
- Ensure total spending on meals + attractions + transport stays within the remaining budget.
- Suggest replacements if estimated total exceeds remaining budget by >10%.

===========================
🧩 STEP 6: Final Itinerary Output
===========================
Output a structured plan in JSON + human-readable summary.

JSON Format (STRICTLY FOLLOW THIS STRUCTURE):
{{
  "day1": [
    {{"time": "8:00 AM", "activity": "Breakfast at Joe's Café", "type": "meal", "duration": "1 hour", "cost": 15, "location": "address", "description": "reasoning"}},
    {{"time": "10:00 AM", "activity": "Golden Gate Bridge", "type": "attraction", "duration": "2 hours", "cost": 0, "location": "address", "description": "why visit"}},
    {{"time": "1:00 PM", "activity": "Lunch at Fog Harbor Fish House", "type": "meal", "duration": "1 hour", "cost": 35, "location": "address", "description": "reasoning"}},
    {{"time": "3:00 PM", "activity": "Exploratorium", "type": "attraction", "duration": "3 hours", "cost": 30, "location": "address", "description": "why visit"}},
    {{"time": "7:00 PM", "activity": "Dinner near Fisherman's Wharf", "type": "meal", "duration": "1.5 hours", "cost": 50, "location": "address", "description": "reasoning"}},
    {{"time": "9:00 PM", "activity": "Check into Hotel Zephyr", "type": "hotel", "duration": "overnight", "cost": 150, "location": "address", "description": "reasoning"}}
  ],
  "day2": [
    {{"time": "8:00 AM", "activity": "Breakfast at Hotel", "type": "meal", "duration": "1 hour", "cost": 15, "location": "address", "description": "reasoning"}},
    {{"time": "10:00 AM", "activity": "Alcatraz Island", "type": "attraction", "duration": "3 hours", "cost": 45, "location": "address", "description": "why visit"}},
    {{"time": "2:00 PM", "activity": "Lunch at Scoma's Restaurant", "type": "meal", "duration": "1 hour", "cost": 40, "location": "address", "description": "reasoning"}},
    {{"time": "4:00 PM", "activity": "Chinatown Exploration", "type": "attraction", "duration": "2 hours", "cost": 0, "location": "address", "description": "why visit"}},
    {{"time": "7:00 PM", "activity": "Dinner at The View Lounge", "type": "meal", "duration": "2 hours", "cost": 60, "location": "address", "description": "reasoning"}}
  ],
  "hotel": {{
    "name": "Hotel Name",
    "location": "address",
    "price_per_night": 150,
    "amenities": ["WiFi", "Parking", "Breakfast"],
    "rating": 4.2,
    "reasoning": "why this hotel"
  }},
  "budget_breakdown": {{
    "hotel": 150,
    "meals": 235,
    "attractions": 75,
    "transport": 40,
    "total": 500
  }},
  "route_info": {{
    "total_distance": "XX miles",
    "total_duration": "XX hours",
    "optimization_note": "explanation"
  }},
  "summary": "ONE sentence summarizing the trip highlights and theme - must be exactly one sentence"
}}

Readable summary:
ONE concise sentence covering the trip's main highlights and theme.

===========================
🧠 STEP 7: Reasoning & Personalization
===========================
- Adapt recommendations to user's interests and pace.
- If user prefers relaxing/nature → fewer stops, longer durations.
- If user prefers adventure → denser itinerary.
- Always ensure travel times and order are realistic.
- Prioritize experience quality over quantity.

===========================
CRITICAL INSTRUCTIONS
===========================
1. Use ONLY the data provided in the aggregated_data section. If data is missing, make reasonable estimates based on typical values.
2. Output VALID JSON only - no markdown, no code blocks, no extra text before or after.
3. The JSON must be parseable by Python's json.loads().
4. Each activity must have: time, activity name, type, duration, cost, location, description.
5. Ensure the itinerary is realistic and achievable.
6. Prioritize trending/Instagram restaurants when available.
7. Use the hotel from user preferences - do not select a different hotel.
8. CRITICAL: Do NOT select the same restaurant or attraction more than once across the entire 2-day itinerary. Each place must be unique.
9. Vary restaurants and attractions - no duplicates allowed even if they appear multiple times in the data.

Now generate the itinerary:
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
            response = await self.llm.ainvoke(prompt)
            summary = response.content.strip() if hasattr(response, 'content') else str(response).strip()
            
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
            
            response = await self.llm.ainvoke(prompt)
            highlights_text = response.content.strip() if hasattr(response, 'content') else str(response).strip()
            
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
            
            response = await self.llm.ainvoke(prompt)
            recommendations_text = response.content.strip() if hasattr(response, 'content') else str(response).strip()
            
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
            response = await self.llm.ainvoke("Hello, this is a test.")
            return "AI service is working correctly"
        except Exception as e:
            return f"AI service error: {str(e)}"
    
    async def generate_comprehensive_2day_itinerary(
        self,
        aggregated_data: Dict[str, Any],
        start_location: str,
        destination: str,
        interests: List[str],
        budget: float,
        travelers: int,
        user_preferences: str = ""
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive 2-day itinerary using TravelAI 7-step process
        
        Args:
            aggregated_data: Data from Google Maps, Yelp, Instagram APIs
            start_location: Starting point of the trip
            destination: Final destination
            interests: List of user interests
            budget: Total budget for the trip
            travelers: Number of travelers
            user_preferences: Additional user preferences/requirements
            
        Returns:
            Structured itinerary with day1, day2, hotel, budget breakdown, etc.
        """
        if not self.llm:
            # Fallback to simple mock itinerary
            return self._get_fallback_itinerary(start_location, destination, interests, budget, travelers)
        
        try:
            # Format aggregated data for the prompt
            formatted_data = self._format_aggregated_data(aggregated_data)
            
            # Create the prompt
            prompt = self.travelai_2day_template.format(
                aggregated_data=formatted_data,
                start_location=start_location,
                destination=destination,
                interests=", ".join(interests),
                budget=budget,
                travelers=travelers,
                user_preferences=user_preferences or "No specific preferences"
            )
            
            # Generate itinerary
            print("🤖 Generating comprehensive 2-day itinerary with TravelAI...")
            response = await self.llm.ainvoke(prompt)
            ai_output = response.content.strip() if hasattr(response, 'content') else str(response).strip()
            
            # Parse JSON from the response
            # The AI might wrap the JSON in markdown code blocks or add extra text
            itinerary_json = self._extract_json_from_response(ai_output)
            
            print("✅ Successfully generated comprehensive itinerary")
            return itinerary_json
            
        except Exception as e:
            print(f"❌ Error generating comprehensive itinerary: {e}")
            return self._get_fallback_itinerary(start_location, destination, interests, budget, travelers)
    
    def _format_aggregated_data(self, aggregated_data: Dict[str, Any]) -> str:
        """Format aggregated data into a readable string for the AI prompt"""
        try:
            formatted = []
            
            # Hotels
            hotels = aggregated_data.get("hotels", [])
            if hotels:
                formatted.append(f"\n--- HOTELS ({len(hotels)} found) ---")
                for hotel in hotels[:10]:  # Limit to top 10
                    formatted.append(
                        f"- {hotel.get('name', 'Unknown')}: ${hotel.get('price_per_night', 0)}/night, "
                        f"Rating: {hotel.get('rating', 0)}, Location: {hotel.get('address', 'N/A')}"
                    )
            
            # Attractions
            attractions = aggregated_data.get("attractions", [])
            if attractions:
                formatted.append(f"\n--- ATTRACTIONS ({len(attractions)} found) ---")
                for attraction in attractions[:15]:  # Limit to top 15
                    formatted.append(
                        f"- {attraction.get('name', 'Unknown')}: Rating {attraction.get('rating', 0)}, "
                        f"Types: {', '.join(attraction.get('types', [])[:3])}, "
                        f"Location: {attraction.get('address', 'N/A')}"
                    )
            
            # Restaurants
            restaurants = aggregated_data.get("restaurants", [])
            if restaurants:
                formatted.append(f"\n--- RESTAURANTS ({len(restaurants)} found) ---")
                for restaurant in restaurants[:15]:  # Limit to top 15
                    source = restaurant.get('source', 'unknown')
                    trending_info = ""
                    if source == 'instagram':
                        trending_info = f"🔥 TRENDING (Score: {restaurant.get('trending_score', 0):.2f}, "
                        trending_info += f"Likes: {restaurant.get('likes', 0)})"
                    price_level = restaurant.get('price_level', 2) or 2
                    formatted.append(
                        f"- {restaurant.get('name', 'Unknown')}: Rating {restaurant.get('rating', 0)}, "
                        f"Price: ${'$' * price_level}, "
                        f"Location: {restaurant.get('address', 'N/A')} {trending_info}"
                    )
            
            # Transportation
            transportation = aggregated_data.get("transportation", {})
            if transportation:
                formatted.append(f"\n--- TRANSPORTATION ---")
                formatted.append(f"Location: {transportation.get('location', 'N/A')}")
                formatted.append(f"Options: {', '.join(transportation.get('transportation_options', []))}")
            
            return "\n".join(formatted) if formatted else "No data available"
            
        except Exception as e:
            print(f"Error formatting aggregated data: {e}")
            return "Error formatting data"
    
    def _extract_json_from_response(self, ai_output: str) -> Dict[str, Any]:
        """Extract valid JSON from AI response (handle markdown code blocks)"""
        try:
            # Try to find JSON in code blocks
            import re
            
            # Look for JSON code blocks
            json_match = re.search(r'```(?:json)?\s*(\{.*\})\s*```', ai_output, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
            
            # Look for JSON without code blocks
            json_match = re.search(r'(\{.*\})', ai_output, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
            
            # Try parsing the whole thing
            return json.loads(ai_output)
            
        except Exception as e:
            print(f"Error extracting JSON: {e}")
            print(f"AI Output: {ai_output[:500]}...")
            raise
    
    def _get_fallback_itinerary(
        self,
        start_location: str,
        destination: str,
        interests: List[str],
        budget: float,
        travelers: int
    ) -> Dict[str, Any]:
        """Fallback itinerary when AI is not available"""
        return {
            "day1": [
                {
                    "time": "8:00 AM",
                    "activity": f"Breakfast at {destination} Cafe",
                    "type": "meal",
                    "duration": "1 hour",
                    "cost": 15,
                    "location": destination,
                    "description": "Start your day with a hearty breakfast"
                },
                {
                    "time": "10:00 AM",
                    "activity": f"Explore {destination} City Center",
                    "type": "attraction",
                    "duration": "2 hours",
                    "cost": 0,
                    "location": destination,
                    "description": "Discover the heart of the city"
                },
                {
                    "time": "1:00 PM",
                    "activity": f"Lunch at Local Restaurant",
                    "type": "meal",
                    "duration": "1 hour",
                    "cost": 30,
                    "location": destination,
                    "description": "Enjoy local cuisine"
                },
                {
                    "time": "3:00 PM",
                    "activity": f"Visit Main Attraction",
                    "type": "attraction",
                    "duration": "3 hours",
                    "cost": 25,
                    "location": destination,
                    "description": "See the main attraction"
                },
                {
                    "time": "7:00 PM",
                    "activity": f"Dinner at Local Eatery",
                    "type": "meal",
                    "duration": "1.5 hours",
                    "cost": 50,
                    "location": destination,
                    "description": "Delicious dinner"
                }
            ],
            "day2": [
                {
                    "time": "8:00 AM",
                    "activity": "Breakfast at Hotel",
                    "type": "meal",
                    "duration": "1 hour",
                    "cost": 15,
                    "location": destination,
                    "description": "Hotel breakfast"
                },
                {
                    "time": "10:00 AM",
                    "activity": f"Visit {destination} Museum",
                    "type": "attraction",
                    "duration": "3 hours",
                    "cost": 20,
                    "location": destination,
                    "description": "Cultural experience"
                },
                {
                    "time": "2:00 PM",
                    "activity": "Lunch",
                    "type": "meal",
                    "duration": "1 hour",
                    "cost": 35,
                    "location": destination,
                    "description": "Midday meal"
                },
                {
                    "time": "4:00 PM",
                    "activity": f"Walk in {destination} Park",
                    "type": "attraction",
                    "duration": "2 hours",
                    "cost": 0,
                    "location": destination,
                    "description": "Relaxing stroll"
                },
                {
                    "time": "7:00 PM",
                    "activity": "Dinner",
                    "type": "meal",
                    "duration": "2 hours",
                    "cost": 60,
                    "location": destination,
                    "description": "Final dinner"
                }
            ],
            "hotel": {
                "name": f"Grand Hotel {destination}",
                "location": destination,
                "price_per_night": budget * 0.3,
                "amenities": ["WiFi", "Parking", "Breakfast"],
                "rating": 4.0,
                "reasoning": "Convenient location and good amenities"
            },
            "budget_breakdown": {
                "hotel": budget * 0.3,
                "meals": budget * 0.4,
                "attractions": budget * 0.2,
                "transport": budget * 0.1,
                "total": budget
            },
            "route_info": {
                "total_distance": "Est. XX miles",
                "total_duration": "Est. XX hours",
                "optimization_note": "Fallback itinerary - optimize when full data available"
            },
            "summary": f"A 2-day trip from {start_location} to {destination} focusing on {', '.join(interests[:3])}"
        }
