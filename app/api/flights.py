from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
import logging

from app.models.flight import (
    FlightSearchRequest, 
    FlightSearchResponse,
    AirportInfo,
    HealthCheck
)
from app.services.flight_service import FlightService
from app.services.price_tracking_service import PriceTrackingService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/flights", tags=["flights"])

# Dependency to get flight service
def get_flight_service() -> FlightService:
    try:
        return FlightService()
    except ValueError as e:
        raise HTTPException(status_code=500, detail=f"Flight service configuration error: {str(e)}")

# Dependency to get price tracking service
def get_price_tracking_service() -> PriceTrackingService:
    try:
        return PriceTrackingService()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Price tracking service error: {str(e)}")

@router.post("/search", response_model=FlightSearchResponse)
async def search_flights(
    request: FlightSearchRequest,
    flight_service: FlightService = Depends(get_flight_service),
    price_service: PriceTrackingService = Depends(get_price_tracking_service)
):
    """Search for flights"""
    try:
        logger.info(f"Flight search request: {request}")
        
        result = await flight_service.search_flights(request)
        
        # Store search results for price tracking
        search_params = request.dict()
        price_service.store_search_results(search_params, result.offers)
        
        logger.info(f"Found {result.total_offers} flight offers")
        return result
        
    except Exception as e:
        logger.error(f"Flight search error: {e}")
        raise HTTPException(status_code=500, detail="Flight search failed")

@router.get("/search-oneway")
async def search_oneway_flights(
    origin: str = Query(..., description="Origin airport code"),
    destination: str = Query(..., description="Destination airport code"),
    departure_date: str = Query(..., description="Departure date (YYYY-MM-DD)"),
    adults: int = Query(1, ge=1, le=9, description="Number of adult passengers"),
    children: int = Query(0, ge=0, le=9, description="Number of child passengers"),
    infants: int = Query(0, ge=0, le=9, description="Number of infant passengers"),
    cabin_class: str = Query("ECONOMY", description="Cabin class"),
    max_stops: Optional[int] = Query(None, ge=0, le=5, description="Maximum number of stops"),
    flight_service: FlightService = Depends(get_flight_service)
):
    """Search for one-way flights only"""
    try:
        logger.info(f"One-way flight search: {origin} -> {destination} on {departure_date}")
        
        # Create one-way search request
        request = FlightSearchRequest(
            origin=origin,
            destination=destination,
            departure_date=departure_date,
            return_date=None,  # One-way only
            adults=adults,
            children=children,
            infants=infants,
            cabin_class=cabin_class,
            max_stops=max_stops
        )
        
        result = await flight_service.search_flights(request)
        
        logger.info(f"Found {result.total_offers} one-way flight offers")
        return result
        
    except Exception as e:
        logger.error(f"One-way flight search error: {e}")
        raise HTTPException(status_code=500, detail="One-way flight search failed")

@router.get("/airports", response_model=List[AirportInfo])
async def search_airports(
    q: str = Query(..., description="Search query for airports"),
    flight_service: FlightService = Depends(get_flight_service)
):
    """Search for airports by city or code"""
    try:
        if len(q) < 2:
            raise HTTPException(status_code=400, detail="Search query must be at least 2 characters")
        
        airports = await flight_service.get_airports(q)
        return airports
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Airport search error: {e}")
        raise HTTPException(status_code=500, detail="Airport search failed")

@router.get("/health", response_model=HealthCheck)
async def health_check(flight_service: FlightService = Depends(get_flight_service)):
    """Health check endpoint"""
    try:
        from app.core.config import settings
        from datetime import datetime
        
        amadeus_connected = await flight_service.health_check()
        
        return HealthCheck(
            status="healthy" if amadeus_connected else "degraded",
            timestamp=datetime.utcnow(),
            version=settings.app_version,
            amadeus_connected=amadeus_connected
        )
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return HealthCheck(
            status="unhealthy",
            timestamp=datetime.utcnow(),
            version=settings.app_version,
            amadeus_connected=False
        )

@router.get("/price-history/{origin}/{destination}")
async def get_price_history(
    origin: str,
    destination: str,
    days: int = Query(30, description="Number of days to look back"),
    price_service: PriceTrackingService = Depends(get_price_tracking_service)
):
    """Get price history for a specific route"""
    try:
        history = price_service.get_price_history(origin, destination, days)
        return history
    except Exception as e:
        logger.error(f"Price history error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get price history")

@router.get("/price-alert/{origin}/{destination}")
async def check_price_alert(
    origin: str,
    destination: str,
    target_price: float = Query(..., description="Target price to check against"),
    price_service: PriceTrackingService = Depends(get_price_tracking_service)
):
    """Check if current prices are below target price"""
    try:
        alert = price_service.get_price_alerts(origin, destination, target_price)
        return alert
    except Exception as e:
        logger.error(f"Price alert error: {e}")
        raise HTTPException(status_code=500, detail="Failed to check price alert")

@router.get("/route-stats/{origin}/{destination}")
async def get_route_statistics(
    origin: str,
    destination: str,
    price_service: PriceTrackingService = Depends(get_price_tracking_service)
):
    """Get comprehensive statistics for a route"""
    try:
        stats = price_service.get_route_statistics(origin, destination)
        return stats
    except Exception as e:
        logger.error(f"Route statistics error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get route statistics")

@router.post("/cleanup-data")
async def cleanup_old_data(
    days_to_keep: int = Query(90, description="Number of days of data to keep"),
    price_service: PriceTrackingService = Depends(get_price_tracking_service)
):
    """Clean up old price tracking data"""
    try:
        price_service.cleanup_old_data(days_to_keep)
        return {"message": f"Cleaned up data older than {days_to_keep} days"}
    except Exception as e:
        logger.error(f"Data cleanup error: {e}")
        raise HTTPException(status_code=500, detail="Failed to cleanup data")
