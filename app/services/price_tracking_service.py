"""
Price Tracking Service for Flight Search App
Handles storage and analysis of flight price data over time
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class PriceTrackingService:
    """Service for tracking and analyzing flight prices over time"""
    
    def __init__(self, data_dir: str = "data/price_tracking"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
    def store_search_results(self, search_params: Dict[str, Any], flights: List[Dict[str, Any]]) -> None:
        """Store search results with timestamp for price tracking"""
        try:
            # Create unique identifier for this search
            route = f"{search_params['origin']}-{search_params['destination']}"
            date_key = datetime.now().strftime("%Y-%m-%d")
            
            # Load existing data
            data_file = self.data_dir / f"{route}_{date_key}.json"
            existing_data = self._load_data(data_file)
            
            # Convert FlightOffer objects to dictionaries for JSON serialization
            flights_data = []
            for flight in flights:
                if hasattr(flight, 'dict'):
                    flights_data.append(flight.dict())
                else:
                    flights_data.append(flight)
            
            # Add new search result
            search_entry = {
                "timestamp": datetime.now().isoformat(),
                "search_params": search_params,
                "flights": flights_data,
                "flight_count": len(flights_data),
                "price_range": self._calculate_price_range(flights_data) if flights_data else None
            }
            
            existing_data.append(search_entry)
            
            # Save updated data
            self._save_data(data_file, existing_data)
            
            logger.info(f"Stored {len(flights)} flights for route {route}")
            
        except Exception as e:
            logger.error(f"Error storing search results: {e}")
    
    def get_price_history(self, origin: str, destination: str, days: int = 30) -> Dict[str, Any]:
        """Get price history for a specific route over the last N days"""
        try:
            route = f"{origin}-{destination}"
            history_data = []
            
            # Get data for the last N days
            for i in range(days):
                date = datetime.now() - timedelta(days=i)
                date_key = date.strftime("%Y-%m-%d")
                data_file = self.data_dir / f"{route}_{date_key}.json"
                
                if data_file.exists():
                    daily_data = self._load_data(data_file)
                    history_data.extend(daily_data)
            
            # Analyze price trends
            analysis = self._analyze_price_trends(history_data)
            
            return {
                "route": route,
                "total_searches": len(history_data),
                "date_range": {
                    "from": (datetime.now() - timedelta(days=days)).isoformat(),
                    "to": datetime.now().isoformat()
                },
                "price_analysis": analysis,
                "historical_data": history_data
            }
            
        except Exception as e:
            logger.error(f"Error getting price history: {e}")
            return {"error": str(e)}
    
    def get_price_alerts(self, origin: str, destination: str, target_price: float) -> Dict[str, Any]:
        """Check if current prices are below target price for alerts"""
        try:
            route = f"{origin}-{destination}"
            date_key = datetime.now().strftime("%Y-%m-%d")
            data_file = self.data_dir / f"{route}_{date_key}.json"
            
            if not data_file.exists():
                return {"alert": False, "message": "No recent data available"}
            
            recent_data = self._load_data(data_file)
            if not recent_data:
                return {"alert": False, "message": "No recent searches found"}
            
            # Get the most recent search
            latest_search = max(recent_data, key=lambda x: x["timestamp"])
            flights = latest_search["flights"]
            
            if not flights:
                return {"alert": False, "message": "No flights found in recent search"}
            
            # Check if any flight is below target price
            lowest_price = min(float(flight["price_total"]) for flight in flights)
            
            if lowest_price <= target_price:
                return {
                    "alert": True,
                    "lowest_price": lowest_price,
                    "target_price": target_price,
                    "savings": target_price - lowest_price,
                    "message": f"Price alert! Found flights at ${lowest_price:.2f}"
                }
            else:
                return {
                    "alert": False,
                    "lowest_price": lowest_price,
                    "target_price": target_price,
                    "message": f"Current lowest price is ${lowest_price:.2f}"
                }
                
        except Exception as e:
            logger.error(f"Error checking price alerts: {e}")
            return {"error": str(e)}
    
    def get_route_statistics(self, origin: str, destination: str) -> Dict[str, Any]:
        """Get comprehensive statistics for a route"""
        try:
            route = f"{origin}-{destination}"
            history = self.get_price_history(origin, destination, 30)
            
            if "error" in history:
                return history
            
            historical_data = history["historical_data"]
            
            if not historical_data:
                return {"message": "No historical data available for this route"}
            
            # Calculate comprehensive statistics
            all_prices = []
            all_durations = []
            airline_frequency = {}
            
            for search in historical_data:
                for flight in search["flights"]:
                    all_prices.append(float(flight["price_total"]))
                    if "total_duration_minutes" in flight:
                        all_durations.append(flight["total_duration_minutes"])
                    
                    airline = flight.get("airline_code", "Unknown")
                    airline_frequency[airline] = airline_frequency.get(airline, 0) + 1
            
            if not all_prices:
                return {"message": "No price data available"}
            
            # Calculate statistics
            stats = {
                "route": route,
                "total_searches": len(historical_data),
                "total_flights_analyzed": len(all_prices),
                "price_statistics": {
                    "min_price": min(all_prices),
                    "max_price": max(all_prices),
                    "avg_price": sum(all_prices) / len(all_prices),
                    "median_price": sorted(all_prices)[len(all_prices) // 2]
                },
                "airline_distribution": airline_frequency,
                "most_common_airline": max(airline_frequency, key=airline_frequency.get) if airline_frequency else None,
                "data_quality": {
                    "has_price_data": len(all_prices) > 0,
                    "has_duration_data": len(all_durations) > 0,
                    "coverage_days": len(set(search["timestamp"][:10] for search in historical_data))
                }
            }
            
            if all_durations:
                stats["duration_statistics"] = {
                    "min_duration": min(all_durations),
                    "max_duration": max(all_durations),
                    "avg_duration": sum(all_durations) / len(all_durations)
                }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting route statistics: {e}")
            return {"error": str(e)}
    
    def _load_data(self, file_path: Path) -> List[Dict[str, Any]]:
        """Load data from JSON file"""
        try:
            if file_path.exists():
                with open(file_path, 'r') as f:
                    return json.load(f)
            return []
        except Exception as e:
            logger.error(f"Error loading data from {file_path}: {e}")
            return []
    
    def _save_data(self, file_path: Path, data: List[Dict[str, Any]]) -> None:
        """Save data to JSON file"""
        try:
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving data to {file_path}: {e}")
    
    def _calculate_price_range(self, flights: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate price range from flight list"""
        if not flights:
            return {"min": 0, "max": 0, "avg": 0}
        
        prices = []
        for flight in flights:
            if isinstance(flight, dict) and "price_total" in flight:
                prices.append(float(flight["price_total"]))
            elif hasattr(flight, "price_total"):
                prices.append(float(flight.price_total))
        
        if not prices:
            return {"min": 0, "max": 0, "avg": 0}
            
        return {
            "min": min(prices),
            "max": max(prices),
            "avg": sum(prices) / len(prices)
        }
    
    def _analyze_price_trends(self, historical_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze price trends from historical data"""
        if not historical_data:
            return {"trend": "no_data", "message": "No historical data available"}
        
        # Sort by timestamp
        sorted_data = sorted(historical_data, key=lambda x: x["timestamp"])
        
        # Get price ranges for each search
        price_ranges = []
        for search in sorted_data:
            if search["price_range"]:
                price_ranges.append(search["price_range"]["min"])
        
        if len(price_ranges) < 2:
            return {"trend": "insufficient_data", "message": "Need at least 2 data points for trend analysis"}
        
        # Calculate trend
        recent_avg = sum(price_ranges[-3:]) / min(3, len(price_ranges))  # Last 3 searches
        older_avg = sum(price_ranges[:3]) / min(3, len(price_ranges))    # First 3 searches
        
        trend_percentage = ((recent_avg - older_avg) / older_avg) * 100
        
        if trend_percentage > 5:
            trend = "increasing"
        elif trend_percentage < -5:
            trend = "decreasing"
        else:
            trend = "stable"
        
        return {
            "trend": trend,
            "trend_percentage": round(trend_percentage, 2),
            "recent_avg_price": round(recent_avg, 2),
            "historical_avg_price": round(older_avg, 2),
            "data_points": len(price_ranges)
        }
    
    def cleanup_old_data(self, days_to_keep: int = 90) -> None:
        """Clean up data older than specified days"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            deleted_files = 0
            
            for file_path in self.data_dir.glob("*.json"):
                # Extract date from filename
                filename = file_path.stem
                if "_" in filename:
                    date_part = filename.split("_")[-1]
                    try:
                        file_date = datetime.strptime(date_part, "%Y-%m-%d")
                        if file_date < cutoff_date:
                            file_path.unlink()
                            deleted_files += 1
                    except ValueError:
                        # Skip files with invalid date format
                        continue
            
            logger.info(f"Cleaned up {deleted_files} old data files")
            
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
