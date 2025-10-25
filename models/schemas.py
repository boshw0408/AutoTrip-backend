from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from enum import Enum

class TripType(str, Enum):
    LEISURE = "leisure"
    BUSINESS = "business"
    ADVENTURE = "adventure"
    CULTURAL = "cultural"

class InterestType(str, Enum):
    CULTURE_HISTORY = "Culture & History"
    FOOD_DINING = "Food & Dining"
    NATURE_OUTDOOR = "Nature & Outdoor"
    NIGHTLIFE = "Nightlife"
    SHOPPING = "Shopping"
    ADVENTURE = "Adventure"
    RELAXATION = "Relaxation"
    ART_MUSEUMS = "Art & Museums"

class TripCreate(BaseModel):
    location: str
    start_date: date
    end_date: date
    budget: float
    travelers: int
    interests: List[InterestType]
    trip_type: Optional[TripType] = TripType.LEISURE

class TripResponse(BaseModel):
    id: str
    location: str
    start_date: date
    end_date: date
    duration: int
    budget: float
    travelers: int
    interests: List[str]
    trip_type: str
    itinerary: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

class PlaceSearch(BaseModel):
    location: str
    type: str = "attractions"
    radius: Optional[int] = 5000
    limit: Optional[int] = 20

class PlaceResponse(BaseModel):
    id: str
    name: str
    address: str
    rating: float
    price_level: Optional[int]
    types: List[str]
    location: Dict[str, float]  # lat, lng
    photos: List[str]
    description: Optional[str]

class HotelSearch(BaseModel):
    location: str
    check_in: Optional[date] = None
    check_out: Optional[date] = None
    guests: Optional[int] = 1
    rooms: Optional[int] = 1
    price_min: Optional[float] = None
    price_max: Optional[float] = None

class HotelResponse(BaseModel):
    id: str
    name: str
    address: str
    rating: float
    price_per_night: float
    amenities: List[str]
    photos: List[str]
    location: Dict[str, float]
    distance_from_center: str
    availability: bool

class ItineraryItem(BaseModel):
    id: str
    time: str
    title: str
    description: str
    location: str
    duration: str
    type: str  # hotel, restaurant, attraction, transport
    rating: Optional[float]
    cost: Optional[float]

class ItineraryDay(BaseModel):
    day: int
    date: str
    items: List[ItineraryItem]

class ItineraryGenerate(BaseModel):
    location: str
    start_date: date
    end_date: date
    budget: float
    travelers: int
    interests: List[str]

class ItineraryResponse(BaseModel):
    id: str
    location: str
    duration: int
    days: List[ItineraryDay]
    summary: Optional[str]
    total_estimated_cost: float

class RouteRequest(BaseModel):
    origin: str
    destination: str
    waypoints: Optional[List[str]] = []
    mode: str = "driving"  # driving, walking, transit

class RouteResponse(BaseModel):
    distance: str
    duration: str
    polyline: str
    steps: List[Dict[str, Any]]

class AISummarizeRequest(BaseModel):
    itinerary_data: Dict[str, Any]
    style: Optional[str] = "friendly"  # friendly, professional, casual

class AISummarizeResponse(BaseModel):
    summary: str
    highlights: List[str]
    recommendations: List[str]
