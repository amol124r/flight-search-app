from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class FlightSearchRequest(BaseModel):
    """Request model for flight search"""
    origin: str = Field(..., description="Origin airport code (e.g., JFK)")
    destination: str = Field(..., description="Destination airport code (e.g., LAX)")
    departure_date: str = Field(..., description="Departure date (YYYY-MM-DD)")
    return_date: Optional[str] = Field(None, description="Return date (YYYY-MM-DD)")
    adults: int = Field(1, ge=1, le=9, description="Number of adult passengers")
    children: int = Field(0, ge=0, le=9, description="Number of child passengers")
    infants: int = Field(0, ge=0, le=9, description="Number of infant passengers")
    cabin_class: str = Field("ECONOMY", description="Cabin class")
    max_stops: Optional[int] = Field(None, ge=0, le=5, description="Maximum number of stops (0 for non-stop)")

class FlightSegment(BaseModel):
    """Flight segment information"""
    departure_time: str
    arrival_time: str
    departure_airport: str
    arrival_airport: str
    airline_code: str
    flight_number: str
    aircraft: Optional[str] = None
    duration: Optional[str] = None

class FlightOffer(BaseModel):
    """Flight offer with pricing and details"""
    id: str
    price_total: float
    currency: str
    outbound_segments: List[FlightSegment]
    return_segments: Optional[List[FlightSegment]] = None
    cabin_class: str
    airline: str
    booking_url: Optional[str] = None

class FlightSearchResponse(BaseModel):
    """Response model for flight search"""
    search_params: FlightSearchRequest
    offers: List[FlightOffer]
    total_offers: int
    search_timestamp: datetime
    source: str = "amadeus_api"

class AirportInfo(BaseModel):
    """Airport information"""
    code: str
    name: str
    city: str
    country: str
    timezone: Optional[str] = None

class HealthCheck(BaseModel):
    """Health check response"""
    status: str
    timestamp: datetime
    version: str
    amadeus_connected: bool
