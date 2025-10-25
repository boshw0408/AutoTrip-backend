"""
Quick Test Script for Google Maps Service
Run this in your actual project environment to test if Google Maps API is working
"""
import asyncio
import sys
import os
# Add your project path if needed
# sys.path.append('/path/to/your/project')
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.google_maps import GoogleMapsService

async def quick_test():
    print("="*60)
    print("QUICK GOOGLE MAPS API TEST")
    print("="*60)
    
    service = GoogleMapsService()
    
    # Test 1: Geocoding
    print("\n1. Testing Geocoding...")
    coords = await service.geocode_address("Golden Gate Bridge, San Francisco")
    if coords:
        print(f"   ✅ Geocoding works! Coords: {coords}")
    else:
        print("   ❌ Geocoding failed")
    
    # Test 2: Basic Directions
    print("\n2. Testing Directions...")
    directions = await service.get_directions(
        "San Francisco Airport",
        "Golden Gate Bridge"
    )
    if directions:
        print(f"   ✅ Directions work!")
        print(f"      Distance: {directions.get('distance')}")
        print(f"      Duration: {directions.get('duration')}")
    else:
        print("   ❌ Directions failed")
    
    # Test 3: Trip Planning
    print("\n3. Testing Trip Planning...")
    trip = await service.plan_trip(
        origin="Los Angeles, CA",
        destination="San Francisco, CA",
        waypoints=["Santa Barbara, CA"]
    )
    if trip:
        print(f"   ✅ Trip planning works!")
        print(f"      Total Distance: {trip.total_distance}")
        print(f"      Total Duration: {trip.total_duration}")
        print(f"      Stops: {len(trip.optimized_order)}")
    else:
        print("   ❌ Trip planning failed")
    
    print("\n" + "="*60)
    print("Test complete!")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(quick_test())
