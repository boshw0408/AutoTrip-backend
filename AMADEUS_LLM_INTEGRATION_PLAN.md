# Amadeus Hotel API Integration - LLM-Driven Approach
## AutoTrip - Simple API Wrapper for LLM

---

## 🎯 New Philosophy

**OLD Approach (Scrapped):**
- Backend does all the filtering, ranking, and logic ❌
- Complex scoring algorithms ❌
- Hard-coded interest-to-amenity mapping ❌

**NEW Approach (LLM-Driven):**
- Amadeus service is just a **thin API wrapper** ✅
- Raw hotel data goes to **LLM (GPT/Claude)** ✅
- **LLM makes all decisions** about filtering, ranking, recommendations ✅
- Backend just **passes data through** ✅

---

## 🏗️ Simplified Architecture

```
User Input
    ↓
Trip Planning Request
    ↓
┌─────────────────────────────────────┐
│  Amadeus Service (Thin Wrapper)     │
│  - Get access token                 │
│  - Call search APIs                 │
│  - Return RAW data                  │
└─────────────────────────────────────┘
    ↓
Raw Hotel Data (JSON)
    ↓
┌─────────────────────────────────────┐
│  LLM Service (GPT-4/Claude)         │
│  - Receives user preferences        │
│  - Receives raw hotel data          │
│  - Analyzes and filters             │
│  - Ranks by relevance               │
│  - Generates recommendations        │
└─────────────────────────────────────┘
    ↓
Personalized Hotel Recommendations
    ↓
User
```

---

## 📝 What We Actually Need

### 1. Simple Amadeus Service
**Purpose:** Just fetch data from Amadeus API, no logic

**Methods:**
```python
class AmadeusService:
    # Authentication
    def get_access_token() -> str
    
    # Search hotels by location (returns RAW data)
    async def search_hotels(
        latitude: float,
        longitude: float,
        radius: int = 20
    ) -> dict  # Raw Amadeus response
    
    # Get hotel offers/pricing (returns RAW data)
    async def get_hotel_offers(
        hotel_ids: List[str],
        check_in: str,
        check_out: str,
        adults: int
    ) -> dict  # Raw Amadeus response
```

### 2. LLM Prompt with Hotel Data
**Purpose:** Let LLM analyze and recommend

**Prompt Structure:**
```
You are a travel planning assistant. Help find the best hotels.

USER PREFERENCES:
- Destination: Half Moon Bay, CA
- Dates: Oct 25-26, 2025 (1 night)
- Budget: $1000 total
- Travelers: 2
- Interests: Culture & History, Food & Dining, Nature & Outdoor

AVAILABLE HOTELS (from Amadeus API):
[Raw JSON data with 20-50 hotels]

INSTRUCTIONS:
1. Analyze the hotels based on user preferences
2. Consider budget (allocate ~50% to accommodation = $500)
3. Match hotels to user interests (e.g., look for restaurants, outdoor activities)
4. Rank hotels by best fit
5. Return top 5 recommendations with explanations

OUTPUT FORMAT:
{
  "recommendations": [
    {
      "hotel_id": "...",
      "hotel_name": "...",
      "price_per_night": 450,
      "why_recommended": "Perfect for your interests because...",
      "pros": [...],
      "cons": [...]
    }
  ],
  "budget_analysis": "...",
  "alternative_suggestions": "..."
}
```

---

## 🔧 Minimal Implementation

### File Structure
```
services/
├── amadeus_api.py          # Simple API wrapper (100 lines)
└── llm_service.py          # Existing (add hotel recommendation method)

routes/
└── trips.py                # Add hotel search endpoint
```

---

## 📄 Code Implementation

### 1. amadeus_api.py (Simple Wrapper)

```python
"""
Simple Amadeus API wrapper - NO LOGIC
Just fetches data and returns it
"""
import requests
from typing import List, Dict, Any
from datetime import datetime, timedelta
from core.config import settings

class AmadeusAPI:
    """Thin wrapper around Amadeus API"""
    
    def __init__(self):
        self.api_key = settings.amadeus_api_key
        self.api_secret = settings.amadeus_api_secret
        self.base_url = settings.amadeus_base_url
        self.access_token = None
        self.token_expiry = None
    
    def _get_token(self) -> str:
        """Get OAuth2 access token"""
        if self.access_token and datetime.now() < self.token_expiry:
            return self.access_token
        
        response = requests.post(
            f"{self.base_url}/v1/security/oauth2/token",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "grant_type": "client_credentials",
                "client_id": self.api_key,
                "client_secret": self.api_secret
            }
        )
        response.raise_for_status()
        
        data = response.json()
        self.access_token = data["access_token"]
        self.token_expiry = datetime.now() + timedelta(seconds=data["expires_in"] - 60)
        return self.access_token
    
    async def search_hotels(
        self,
        latitude: float,
        longitude: float,
        radius: int = 20
    ) -> Dict[str, Any]:
        """Search hotels by coordinates - returns RAW Amadeus data"""
        token = self._get_token()
        
        response = requests.get(
            f"{self.base_url}/v1/reference-data/locations/hotels/by-geocode",
            headers={"Authorization": f"Bearer {token}"},
            params={
                "latitude": latitude,
                "longitude": longitude,
                "radius": radius,
                "radiusUnit": "MILE"
            }
        )
        response.raise_for_status()
        return response.json()  # Return RAW data
    
    async def get_hotel_offers(
        self,
        hotel_ids: List[str],
        check_in_date: str,
        check_out_date: str,
        adults: int = 2,
        currency: str = "USD"
    ) -> Dict[str, Any]:
        """Get hotel offers - returns RAW Amadeus data"""
        token = self._get_token()
        
        response = requests.get(
            f"{self.base_url}/v3/shopping/hotel-offers",
            headers={"Authorization": f"Bearer {token}"},
            params={
                "hotelIds": ",".join(hotel_ids[:100]),
                "checkInDate": check_in_date,
                "checkOutDate": check_out_date,
                "adults": adults,
                "currency": currency,
                "bestRateOnly": "true"
            }
        )
        response.raise_for_status()
        return response.json()  # Return RAW data

# Singleton
amadeus_api = AmadeusAPI()
```

### 2. Add to llm_service.py

```python
async def recommend_hotels(
    self,
    user_preferences: dict,
    available_hotels: dict
) -> dict:
    """
    Let LLM analyze hotels and make recommendations
    
    Args:
        user_preferences: {
            "destination": "Half Moon Bay",
            "dates": "Oct 25-26, 2025",
            "budget": 1000,
            "travelers": 2,
            "interests": ["Culture", "Food", "Nature"]
        }
        available_hotels: Raw Amadeus API response
    
    Returns:
        LLM recommendations
    """
    prompt = f"""
You are a travel planning expert. Recommend the best hotels for this trip.

USER PREFERENCES:
{json.dumps(user_preferences, indent=2)}

AVAILABLE HOTELS:
{json.dumps(available_hotels, indent=2)}

TASK:
1. Analyze hotels based on user preferences and budget
2. Allocate approximately 50% of budget to accommodation
3. Match hotels to user interests
4. Consider price, location, amenities, and ratings
5. Recommend top 5 hotels with detailed explanations

Respond in JSON format:
{{
  "recommendations": [
    {{
      "hotel_id": "string",
      "hotel_name": "string",
      "price_per_night": number,
      "total_price": number,
      "rating": number,
      "why_recommended": "string",
      "matches_interests": ["list"],
      "pros": ["list"],
      "cons": ["list"]
    }}
  ],
  "budget_breakdown": {{
    "accommodation_budget": number,
    "remaining_budget": number,
    "explanation": "string"
  }}
}}
"""
    
    response = await self.llm.agenerate([prompt])
    result = response.generations[0][0].text.strip()
    
    # Parse JSON response
    return json.loads(result)
```

### 3. Add endpoint to trips.py

```python
@router.post("/hotels/search")
async def search_hotels(
    request: dict,
    google_maps: GoogleMapsService = Depends(get_google_maps_service),
    llm: LLMService = Depends(get_llm_service)
):
    """
    Search hotels using Amadeus + LLM recommendations
    
    Request body:
    {
        "destination": "Half Moon Bay, CA",
        "check_in": "2025-10-25",
        "check_out": "2025-10-26",
        "budget": 1000,
        "travelers": 2,
        "interests": ["Culture & History", "Food & Dining"]
    }
    """
    try:
        # 1. Geocode destination
        coords = await google_maps.geocode_address(request["destination"])
        
        # 2. Search hotels (RAW data)
        hotels = await amadeus_api.search_hotels(
            latitude=coords["lat"],
            longitude=coords["lng"],
            radius=20
        )
        
        # 3. Get pricing (RAW data)
        hotel_ids = [h["hotelId"] for h in hotels.get("data", [])[:50]]
        offers = await amadeus_api.get_hotel_offers(
            hotel_ids=hotel_ids,
            check_in_date=request["check_in"],
            check_out_date=request["check_out"],
            adults=min(request["travelers"], 2)
        )
        
        # 4. Let LLM analyze and recommend
        recommendations = await llm.recommend_hotels(
            user_preferences={
                "destination": request["destination"],
                "dates": f"{request['check_in']} to {request['check_out']}",
                "budget": request["budget"],
                "travelers": request["travelers"],
                "interests": request["interests"]
            },
            available_hotels=offers
        )
        
        return recommendations
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

---

## 🔄 Data Flow

### Step-by-Step Process

1. **User submits trip details**
   ```json
   {
     "destination": "Half Moon Bay",
     "check_in": "2025-10-25",
     "check_out": "2025-10-26",
     "budget": 1000,
     "travelers": 2,
     "interests": ["Culture", "Food", "Nature"]
   }
   ```

2. **Backend geocodes destination**
   ```python
   coords = {"lat": 37.46, "lng": -122.43}
   ```

3. **Fetch raw hotel data from Amadeus**
   ```python
   # Get 50 hotels near location
   hotels = await amadeus_api.search_hotels(37.46, -122.43, 20)
   
   # Get pricing for those hotels
   offers = await amadeus_api.get_hotel_offers(hotel_ids, "2025-10-25", "2025-10-26", 2)
   ```

4. **Pass everything to LLM**
   ```python
   # LLM receives:
   # - User preferences
   # - Raw hotel data (50 hotels with all details)
   # LLM analyzes and returns top 5 recommendations
   ```

5. **Return LLM recommendations to user**
   ```json
   {
     "recommendations": [
       {
         "hotel_name": "Oceano Hotel & Spa",
         "price_per_night": 450,
         "why_recommended": "Perfect match! Ocean views, great restaurant...",
         "matches_interests": ["Nature & Outdoor", "Food & Dining"]
       }
     ]
   }
   ```

---

## 📊 Comparison: Old vs New

| Aspect | Old Approach (Scrapped) | New Approach (LLM) |
|--------|-------------------------|-------------------|
| **Code Complexity** | 500+ lines | ~100 lines |
| **Logic Location** | Backend Python code | LLM prompt |
| **Filtering** | Hard-coded rules | LLM understands context |
| **Ranking** | Scoring algorithm | LLM reasoning |
| **Customization** | Change Python code | Change prompt |
| **Flexibility** | Rigid rules | Adapts to any request |
| **Maintenance** | Update code constantly | Update prompt |
| **Interest Matching** | Manual mapping dict | LLM infers |

---

## 🎯 Implementation Checklist

### Phase 1: Basic Integration (This Week)
- [ ] Create `services/amadeus_api.py` (thin wrapper)
- [ ] Add Amadeus credentials to `.env`
- [ ] Test authentication
- [ ] Test hotel search API
- [ ] Test hotel offers API

### Phase 2: LLM Integration (This Week)
- [ ] Add `recommend_hotels()` to `llm_service.py`
- [ ] Create LLM prompt for hotel recommendations
- [ ] Test with sample data
- [ ] Refine prompt based on results

### Phase 3: Endpoint Integration (Next Week)
- [ ] Add `/hotels/search` endpoint to `trips.py`
- [ ] Connect: User Input → Amadeus → LLM → Response
- [ ] Test end-to-end flow
- [ ] Add error handling

### Phase 4: Trip Planning Integration (Next Week)
- [ ] Integrate hotel search into `/trips/plan`
- [ ] Return hotels alongside itinerary
- [ ] LLM generates complete trip with hotels

---

## 💡 Why This Approach is Better

### 1. **Simplicity**
```python
# Old way: 300 lines of filtering logic ❌
def filter_hotels(hotels, budget, interests):
    # Complex scoring algorithm
    # Hard-coded rules
    # Manual mappings
    ...

# New way: 5 lines ✅
offers = await amadeus_api.get_hotel_offers(...)
recommendations = await llm.recommend_hotels(preferences, offers)
return recommendations
```

### 2. **Flexibility**
```
User: "Find me a quirky boutique hotel with vintage vibes"

Old approach: ❌ No "quirky" or "vintage" in our rules
New approach: ✅ LLM understands and finds it
```

### 3. **Natural Language Understanding**
```
LLM can handle:
- "Something romantic for our anniversary" ✅
- "Pet-friendly with a backyard" ✅
- "Close to vegetarian restaurants" ✅
- "Accessible for wheelchair users" ✅

Hard-coded rules: ❌ Would need hundreds of if-statements
```

### 4. **Easy Updates**
```
Change requirements?

Old: Rewrite Python code, deploy
New: Update prompt, done
```

---

## 🚀 Next Steps

1. **Get Amadeus API Secret** (you only gave me the key)
2. **Copy `amadeus_api.py`** to `services/` folder
3. **Update `.env`** with credentials
4. **Test authentication** first
5. **Add LLM method** for hotel recommendations
6. **Create endpoint** and test

**Want me to create the actual implementation files now?** I'll make:
- Clean `amadeus_api.py` (thin wrapper, ~100 lines)
- Updated `llm_service.py` (add hotel method)
- Updated `trips.py` (add hotel endpoint)

Ready to implement! 🎯

---

**End of Simplified Plan**
