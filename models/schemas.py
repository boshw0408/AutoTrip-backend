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
    origin: Optional[str] = None
    location: str
    start_date: date
    end_date: date
    budget: float
    travelers: int
    interests: List[InterestType]
    trip_type: Optional[TripType] = TripType.LEISURE

class TripResponse(BaseModel):
    id: str
    origin: Optional[str] = None
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

# Hotel Search Models
class HotelSearchRequest(BaseModel):
    destination: str
    check_in: date
    check_out: date
    travelers: int
    budget: float
    interests: List[str] = []
    starting_location: Optional[str] = None  # Optional starting location for midpoint calculation

class HotelSearchResponse(BaseModel):
    id: str
    name: str
    address: str
    coordinates: Dict[str, float]
    rating: float
    amenities: List[str]
    price_per_night: float
    total_price: float
    currency: str
    available: bool
    distance_from_center: str
    photos: List[str]
    description: str
    check_in_time: str
    check_out_time: str
    cancellation_policy: str
    source: str

class HotelComparisonRequest(BaseModel):
    hotel_ids: List[str]
    check_in: date
    check_out: date
    travelers: int

class HotelComparisonResponse(BaseModel):
    hotels: List[HotelSearchResponse]
    comparison_metrics: Dict[str, Any]

class BudgetBreakdownResponse(BaseModel):
    total_budget: float
    accommodation_budget: float
    per_night_budget: float
    per_person_budget: float
    budget_tiers: Dict[str, float]

# Legacy models (keeping for backward compatibility)
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
    origin: Optional[str] = None
    location: str
    start_date: date
    end_date: date
    budget: float
    travelers: int
    interests: List[str]
    selected_hotel: Optional[Dict[str, Any]] = None  # Selected hotel information

class ItineraryResponse(BaseModel):
    id: str
    location: str
    origin: Optional[str] = None
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

# Hotel Booking Models
class GuestName(BaseModel):
    title: str  # MR, MRS, MS, etc.
    first_name: str
    last_name: str

class GuestContact(BaseModel):
    email: str
    phone: str

class Guest(BaseModel):
    name: GuestName
    contact: GuestContact

class PaymentCard(BaseModel):
    vendor_code: str  # VI (Visa), CA (MasterCard), AX (American Express)
    card_number: str
    expiry_date: str  # YYYY-MM format
    cvv: str

class HotelBookingRequest(BaseModel):
    offer_id: str
    guests: List[Guest]
    payment: PaymentCard

class HotelBookingResponse(BaseModel):
    booking_id: str
    status: str
    hotel_name: str
    check_in: str
    check_out: str
    guests: List[Guest]
    total_price: float
    currency: str
    confirmation_number: Optional[str] = None
    booking_details: Dict[str, Any]