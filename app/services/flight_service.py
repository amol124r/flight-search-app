from amadeus import Client, ResponseError
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

from app.models.flight import (
    FlightSearchRequest, 
    FlightSearchResponse, 
    FlightOffer, 
    FlightSegment,
    AirportInfo
)
from app.core.config import settings

logger = logging.getLogger(__name__)

class FlightService:
    """Service for flight search operations using Amadeus API"""
    
    def __init__(self):
        if not settings.amadeus_api_key or not settings.amadeus_api_secret:
            raise ValueError("Amadeus API credentials not configured")
        
        self.client = Client(
            client_id=settings.amadeus_api_key,
            client_secret=settings.amadeus_api_secret,
            hostname=settings.amadeus_environment
        )
    
    async def search_flights(self, request: FlightSearchRequest) -> FlightSearchResponse:
        """Search for flights using Amadeus API"""
        try:
            # Prepare search parameters according to Amadeus API documentation
            # Use maximum API limit to get comprehensive dataset for proper filtering
            params = {
                'originLocationCode': request.origin,
                'destinationLocationCode': request.destination,
                'departureDate': request.departure_date,
                'adults': request.adults,
                'max': 250  # Maximum allowed by Amadeus API for comprehensive dataset
            }
            
            # Add return date if provided (for round-trip flights)
            if request.return_date:
                params['returnDate'] = request.return_date
            
            # Add children count if provided
            if request.children > 0:
                params['children'] = request.children
            
            # Add infants count if provided  
            if request.infants > 0:
                params['infants'] = request.infants
            
            # Add travel class if not economy
            if request.cabin_class != "ECONOMY":
                params['travelClass'] = request.cabin_class
            
            # Add currency (default to USD)
            params['currencyCode'] = 'USD'
            
            logger.info(f"Making Amadeus API request with params: {params}")
            
            # Make API request
            response = self.client.shopping.flight_offers_search.get(**params)
            
            # Parse and format response
            offers = self._parse_flight_offers(response.data)
            
            # Enhanced filtering by max stops if specified
            if request.max_stops is not None:
                original_count = len(offers)
                filtered_offers = []
                
                for offer in offers:
                    # Calculate stops for outbound and return segments
                    outbound_stops = max(0, len(offer.outbound_segments) - 1)
                    return_stops = max(0, len(offer.return_segments) - 1) if offer.return_segments else 0
                    max_flight_stops = max(outbound_stops, return_stops)
                    
                    # Include flight if it meets the stops criteria
                    if max_flight_stops <= request.max_stops:
                        filtered_offers.append(offer)
                
                offers = filtered_offers
                logger.info(f"Filtered {len(offers)} flights out of {original_count} original results for max_stops={request.max_stops}")
                
                # If no results match the strict criteria, provide a fallback with slightly relaxed criteria
                if len(offers) == 0 and request.max_stops > 0:
                    logger.info(f"No flights found with max_stops={request.max_stops}, trying with relaxed criteria")
                    # Re-parse original offers for fallback
                    original_offers = self._parse_flight_offers(response.data)
                    relaxed_offers = []
                    
                    for offer in original_offers:
                        outbound_stops = max(0, len(offer.outbound_segments) - 1)
                        return_stops = max(0, len(offer.return_segments) - 1) if offer.return_segments else 0
                        max_flight_stops = max(outbound_stops, return_stops)
                        
                        # Allow one extra stop as fallback
                        if max_flight_stops <= request.max_stops + 1:
                            relaxed_offers.append(offer)
                    
                    if len(relaxed_offers) > 0:
                        offers = relaxed_offers[:20]  # Limit fallback results
                        logger.info(f"Found {len(offers)} flights with relaxed stops criteria")
            
            # Limit final results to top 50 for performance (can be adjusted)
            if len(offers) > 50:
                # Sort by price and take top 50 for better user experience
                offers = sorted(offers, key=lambda x: x.price_total)[:50]
                logger.info(f"Limited results to top 50 flights by price for performance")
            
            return FlightSearchResponse(
                search_params=request,
                offers=offers,
                total_offers=len(offers),
                search_timestamp=datetime.utcnow(),
                source="amadeus_api"
            )
            
        except ResponseError as e:
            logger.error(f"Amadeus API error: {e}")
            logger.error(f"Error details: {e.response.body if hasattr(e, 'response') else 'No response body'}")
            return FlightSearchResponse(
                search_params=request,
                offers=[],
                total_offers=0,
                search_timestamp=datetime.utcnow(),
                source=f"amadeus_api_error: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Unexpected error in flight search: {e}")
            raise
    
    def _parse_flight_offers(self, data: List[Dict]) -> List[FlightOffer]:
        """Parse Amadeus API response into FlightOffer objects"""
        offers = []
        
        for offer_data in data:
            try:
                if 'itineraries' not in offer_data or 'price' not in offer_data:
                    continue
                
                # Extract price information
                price_info = offer_data['price']
                
                # Parse itineraries
                itineraries = offer_data['itineraries']
                outbound_segments = self._parse_segments(itineraries[0]['segments'])
                
                return_segments = None
                if len(itineraries) > 1:
                    return_segments = self._parse_segments(itineraries[1]['segments'])
                
                # Create flight offer
                offer = FlightOffer(
                    id=offer_data.get('id', ''),
                    price_total=float(price_info['total']),
                    currency=price_info['currency'],
                    outbound_segments=outbound_segments,
                    return_segments=return_segments,
                    cabin_class=offer_data.get('travelerPricings', [{}])[0].get('fareDetailsBySegment', [{}])[0].get('cabin', 'ECONOMY'),
                    airline=outbound_segments[0].airline_code if outbound_segments else 'Unknown',
                    booking_url=f"https://www.amadeus.com/booking/{offer_data.get('id', '')}"
                )
                
                offers.append(offer)
                
            except Exception as e:
                logger.warning(f"Failed to parse flight offer: {e}")
                continue
        
        return offers
    
    def _parse_segments(self, segments_data: List[Dict]) -> List[FlightSegment]:
        """Parse flight segments from Amadeus response"""
        segments = []
        
        for segment_data in segments_data:
            departure = segment_data['departure']
            arrival = segment_data['arrival']
            
            segment = FlightSegment(
                departure_time=departure['at'],
                arrival_time=arrival['at'],
                departure_airport=departure['iataCode'],
                arrival_airport=arrival['iataCode'],
                airline_code=segment_data['carrierCode'],
                flight_number=segment_data['number'],
                aircraft=segment_data.get('aircraft', {}).get('code'),
                duration=segment_data.get('duration')
            )
            
            segments.append(segment)
        
        return segments
    
    async def get_airports(self, query: str) -> List[AirportInfo]:
        """Search for airports by city or airport code"""
        try:
            response = self.client.reference_data.locations.get(
                keyword=query,
                subType='AIRPORT'
            )
            
            airports = []
            for location in response.data:
                airport = AirportInfo(
                    code=location['iataCode'],
                    name=location['name'],
                    city=location.get('address', {}).get('cityName', ''),
                    country=location.get('address', {}).get('countryName', ''),
                    timezone=location.get('timeZoneOffset')
                )
                airports.append(airport)
            
            return airports
            
        except ResponseError as e:
            logger.error(f"Error searching airports: {e}")
            return []
    
    async def health_check(self) -> bool:
        """Check if Amadeus API is accessible"""
        try:
            # Try a simple airport search API call without max parameter
            response = self.client.reference_data.locations.get(
                keyword='JFK', 
                subType='AIRPORT'
            )
            # If we get a response without error, API is working
            return response.data is not None and len(response.data) > 0
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
