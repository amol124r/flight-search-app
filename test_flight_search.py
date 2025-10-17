#!/usr/bin/env python3
"""
Test script for Flight Search App
Run this to verify your Amadeus API setup works correctly
"""

import asyncio
import os
from dotenv import load_dotenv
from app.services.flight_service import FlightService
from app.models.flight import FlightSearchRequest

# Load environment variables
load_dotenv()

async def test_flight_search():
    """Test the flight search functionality"""
    
    print("🚀 Testing Flight Search App")
    print("=" * 50)
    
    # Check if API credentials are configured
    api_key = os.getenv("AMADEUS_API_KEY")
    api_secret = os.getenv("AMADEUS_API_SECRET")
    
    if not api_key or not api_secret:
        print("❌ ERROR: Amadeus API credentials not found!")
        print("\n📋 Setup Instructions:")
        print("1. Go to: https://developers.amadeus.com/")
        print("2. Sign up for a free account")
        print("3. Create a new app and get your API Key & Secret")
        print("4. Copy env.example to .env")
        print("5. Add your credentials to .env file:")
        print("   AMADEUS_API_KEY=your_api_key_here")
        print("   AMADEUS_API_SECRET=your_api_secret_here")
        return False
    
    print(f"✅ API Key configured: {api_key[:8]}...")
    print(f"✅ API Secret configured: {'*' * len(api_secret)}")
    
    try:
        # Initialize flight service
        print("\n🔧 Initializing Flight Service...")
        flight_service = FlightService()
        
        # Test health check
        print("🏥 Testing API connection...")
        is_healthy = await flight_service.health_check()
        
        if not is_healthy:
            print("❌ API health check failed!")
            return False
        
        print("✅ API connection successful!")
        
        # Test flight search
        print("\n✈️ Testing flight search...")
        from datetime import datetime, timedelta
        
        # Use dates 30 days from now for better results
        departure = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
        return_date = (datetime.now() + timedelta(days=37)).strftime('%Y-%m-%d')
        
        search_request = FlightSearchRequest(
            origin="JFK",
            destination="LAX",
            departure_date=departure,
            return_date=return_date,
            adults=2,
            children=0
        )
        
        print(f"   Searching: {search_request.origin} → {search_request.destination}")
        print(f"   Dates: {search_request.departure_date} to {search_request.return_date}")
        
        result = await flight_service.search_flights(search_request)
        
        print(f"✅ Search completed!")
        print(f"📊 Found {result.total_offers} flight offers")
        
        if result.offers:
            print("\n🎯 Sample Results:")
            for i, offer in enumerate(result.offers[:3], 1):
                print(f"\n{i}. {offer.airline}")
                print(f"   💰 Price: ${offer.price_total:.0f} {offer.currency}")
                print(f"   🛫 Departure: {offer.outbound_segments[0].departure_time}")
                print(f"   🛬 Arrival: {offer.outbound_segments[0].arrival_time}")
        
        print("\n🎉 All tests passed! Your Flight Search App is ready to use.")
        print("\n🚀 Next steps:")
        print("1. Run: python main.py")
        print("2. Open: http://localhost:8030")
        print("3. Start searching for flights!")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        print("\n🔧 Troubleshooting:")
        print("- Verify your API credentials are correct")
        print("- Check your internet connection")
        print("- Ensure you're using the test environment (not production)")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_flight_search())
    exit(0 if success else 1)
