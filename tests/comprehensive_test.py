#!/usr/bin/env python3
"""
Comprehensive test of WhatNowAI functionality
Tests all major components: OSINT, web scraping, personalization, and event correlation
"""

import sys
import json
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

def test_osint_integration():
    """Test OSINT integration functionality"""
    print("=" * 60)
    print("Testing OSINT Integration")
    print("=" * 60)

    try:
        from services.osint_integration import OSINTIntegrator

        integrator = OSINTIntegrator()
        print(f"✅ OSINT Integrator created successfully")
        print(f"   - OSINT Engine available: {integrator.osint_engine is not None}")
        print(f"   - OSINT Utils available: {integrator.osint_utils is not None}")

        # Test a basic OSINT search
        results = integrator.search_person_osint(
            first_name="John",
            last_name="Doe",
            location="Baltimore, MD",
            timeout=5
        )

        total_results = sum(len(category_results) for category_results in results.values())
        print(f"   - OSINT search completed: {total_results} total results")
        print(f"   - Categories searched: {list(results.keys())}")

        return True

    except Exception as e:
        print(f"❌ OSINT Integration failed: {e}")
        return False

def test_enhanced_search():
    """Test enhanced search capabilities"""
    print("=" * 60)
    print("Testing Enhanced Search")
    print("=" * 60)

    try:
        from services.enhanced_search_service import EnhancedSearchService

        search_service = EnhancedSearchService()
        print("✅ Enhanced Search Service created successfully")

        # Test search with sample data
        search_results = search_service.search_comprehensive(
            query="technology events Baltimore",
            location={"latitude": 39.2904, "longitude": -76.6122},
            user_interests=["technology", "networking"],
            max_results=5
        )

        print(f"   - Search completed with {len(search_results)} results")

        return True

    except Exception as e:
        print(f"❌ Enhanced Search failed: {e}")
        return False

def test_background_search():
    """Test background search and personalization"""
    print("=" * 60)
    print("Testing Background Search & Personalization")
    print("=" * 60)

    try:
        from searchmethods.enhanced_background_search import EnhancedBackgroundSearchService

        bg_service = EnhancedBackgroundSearchService()
        print("✅ Background Search Service created successfully")

        # Test background search
        user_data = {
            'name': 'John Doe',
            'location': 'Baltimore, MD',
            'interests': ['technology', 'music'],
            'activity': 'networking events'
        }

        results = bg_service.perform_enhanced_search(user_data, timeout=10)

        print(f"   - Background search completed")
        print(f"   - Results from {len(results.get('sources', []))} sources")
        print(f"   - Total findings: {len(results.get('results', []))}")

        return True

    except Exception as e:
        print(f"❌ Background Search failed: {e}")
        return False

def test_user_profiling():
    """Test user profiling service"""
    print("=" * 60)
    print("Testing User Profiling")
    print("=" * 60)

    try:
        from services.user_profiling_service import UserProfilingService

        profiling_service = UserProfilingService()
        print("✅ User Profiling Service created successfully")

        # Test profile creation
        user_data = {
            'name': 'John Doe',
            'interests': ['technology', 'music', 'sports'],
            'location': 'Baltimore, MD',
            'activity': 'networking events'
        }

        search_results = {
            'social_profiles': [],
            'interests': ['tech', 'concerts'],
            'activities': ['coding', 'attending meetups']
        }

        profile = profiling_service.create_enhanced_profile(user_data, search_results)

        print(f"   - Profile created with {profile['completion_percentage']:.1f}% completion")
        print(f"   - Detected interests: {len(profile.get('interests', []))}")
        print(f"   - Profile categories: {list(profile.keys())}")

        return True

    except Exception as e:
        print(f"❌ User Profiling failed: {e}")
        return False

def test_event_discovery():
    """Test event discovery and correlation"""
    print("=" * 60)
    print("Testing Event Discovery & Correlation")
    print("=" * 60)

    try:
        from services.ticketmaster_service import TicketmasterService
        from config.settings import TICKETMASTER_API_KEY, FLASK_CONFIG

        if not TICKETMASTER_API_KEY:
            print("⚠️ Ticketmaster API key not configured, skipping test")
            return True

        ticketmaster = TicketmasterService(TICKETMASTER_API_KEY, FLASK_CONFIG)
        print("✅ Ticketmaster Service created successfully")

        # Test event search with personalization
        location_data = {"latitude": 39.2904, "longitude": -76.6122}

        events = ticketmaster.search_events_with_ai_ranking(
            location_data=location_data,
            user_interests=['music', 'technology'],
            user_activity='concerts',
            personalization_data={'preferences': 'evening events'},
            max_results=5
        )

        print(f"   - Found {len(events)} events")
        if events:
            print(f"   - Sample event: {events[0].get('name', 'Unknown')}")

        return True

    except Exception as e:
        print(f"❌ Event Discovery failed: {e}")
        return False

def test_geocoding():
    """Test geocoding service"""
    print("=" * 60)
    print("Testing Geocoding Service")
    print("=" * 60)

    try:
        from services.geocoding_service import GeocodingService

        geocoding = GeocodingService()
        print("✅ Geocoding Service created successfully")

        # Test geocoding
        result = geocoding.geocode_address("Baltimore, MD")

        if result:
            print(f"   - Geocoding successful: {result.get('city', 'Unknown')}")
            print(f"   - Coordinates: {result.get('latitude')}, {result.get('longitude')}")
        else:
            print("   - Geocoding returned no results")

        return True

    except Exception as e:
        print(f"❌ Geocoding failed: {e}")
        return False

def test_data_correlation():
    """Test how well the system correlates input data with output recommendations"""
    print("=" * 60)
    print("Testing Data Correlation & Personalization Flow")
    print("=" * 60)

    try:
        # Simulate the full flow from user input to personalized recommendations
        user_input = {
            'name': 'Alice Smith',
            'interests': ['jazz music', 'art galleries', 'wine tasting'],
            'location': 'Baltimore, MD',
            'activity': 'cultural events'
        }

        print(f"📊 Input Analysis:")
        print(f"   - User: {user_input['name']}")
        print(f"   - Interests: {user_input['interests']}")
        print(f"   - Preferred activity: {user_input['activity']}")
        print(f"   - Location: {user_input['location']}")

        # Test how the system processes this data
        from services.enhanced_search_service import EnhancedSearchService
        from services.user_profiling_service import UserProfilingService

        # Step 1: Enhanced search
        search_service = EnhancedSearchService()
        search_results = search_service.search_comprehensive(
            query="jazz music art wine events Baltimore",
            location={"latitude": 39.2904, "longitude": -76.6122},
            user_interests=user_input['interests'],
            max_results=10
        )

        # Step 2: User profiling
        profiling_service = UserProfilingService()
        profile = profiling_service.create_enhanced_profile(user_input, {})

        print(f"📈 Processing Results:")
        print(f"   - Search found {len(search_results)} relevant results")
        print(f"   - User profile completion: {profile.get('completion_percentage', 0):.1f}%")
        print(f"   - Extracted interests: {len(profile.get('interests', []))}")

        # Step 3: Check correlation quality
        input_keywords = set(' '.join(user_input['interests'] + [user_input['activity']]).lower().split())

        correlation_score = 0
        if search_results:
            for result in search_results[:3]:  # Check top 3 results
                result_text = ' '.join([
                    result.get('title', ''),
                    result.get('description', ''),
                    result.get('snippet', '')
                ]).lower()

                matches = sum(1 for keyword in input_keywords if keyword in result_text)
                correlation_score += matches / len(input_keywords)

        correlation_score = correlation_score / min(len(search_results), 3) if search_results else 0

        print(f"🎯 Correlation Analysis:")
        print(f"   - Input-Output correlation score: {correlation_score:.2f}")
        print(f"   - Personalization effectiveness: {'Good' if correlation_score > 0.3 else 'Needs improvement'}")

        return correlation_score > 0.2  # Return True if correlation is reasonable

    except Exception as e:
        print(f"❌ Data Correlation test failed: {e}")
        return False

def main():
    """Run comprehensive functionality test"""
    print("🚀 WhatNowAI Comprehensive Functionality Test")
    print("=" * 60)

    tests = [
        ("OSINT Integration", test_osint_integration),
        ("Enhanced Search", test_enhanced_search),
        ("Background Search", test_background_search),
        ("User Profiling", test_user_profiling),
        ("Event Discovery", test_event_discovery),
        ("Geocoding", test_geocoding),
        ("Data Correlation", test_data_correlation),
    ]

    results = {}

    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results[test_name] = False
        print()

    # Summary
    print("=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for result in results.values() if result)
    total = len(results)

    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name:<30} {status}")

    print(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")

    if passed >= total * 0.8:
        print("🎉 System is functioning well!")
    elif passed >= total * 0.6:
        print("⚠️ System has some issues but core functionality works")
    else:
        print("🚨 System has significant issues requiring attention")

if __name__ == "__main__":
    main()
