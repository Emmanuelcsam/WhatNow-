#!/usr/bin/env python3
"""
Test script for Norfolk event scraping functionality
"""

import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from osint_utilities import NorfolkEventScraper, LocationIntelligence

def test_norfolk_detection():
    """Test Norfolk area detection"""
    print("🧪 Testing Norfolk area detection...")
    
    # Test with Norfolk coordinates
    norfolk_lat, norfolk_lon = 36.8468, -76.2852
    
    # Get location data
    location_data = {
        'coordinates': (norfolk_lat, norfolk_lon),
        'reverse_geocoding': LocationIntelligence.reverse_geocoding(norfolk_lat, norfolk_lon),
        'nearby_places': LocationIntelligence.nearby_places(norfolk_lat, norfolk_lon)
    }
    
    print(f"📍 Testing coordinates: {norfolk_lat}, {norfolk_lon}")
    reverse_geo = location_data['reverse_geocoding']
    print(f"🔍 Reverse geocoding result: {reverse_geo.get('display_name', 'No address found')}")
    
    # Test Norfolk detection
    is_norfolk = NorfolkEventScraper.is_norfolk_area(location_data)
    print(f"🏛️ Is Norfolk area detected? {is_norfolk}")
    
    # Test with non-Norfolk coordinates (New York City)
    print(f"\n🧪 Testing with non-Norfolk coordinates (NYC)...")
    nyc_lat, nyc_lon = 40.7128, -74.0060
    
    nyc_location_data = {
        'coordinates': (nyc_lat, nyc_lon),
        'reverse_geocoding': LocationIntelligence.reverse_geocoding(nyc_lat, nyc_lon),
        'nearby_places': LocationIntelligence.nearby_places(nyc_lat, nyc_lon)
    }
    
    nyc_reverse_geo = nyc_location_data['reverse_geocoding']
    print(f"📍 NYC coordinates: {nyc_lat}, {nyc_lon}")
    print(f"🔍 NYC reverse geocoding: {nyc_reverse_geo.get('display_name', 'No address found')}")
    
    is_norfolk_nyc = NorfolkEventScraper.is_norfolk_area(nyc_location_data)
    print(f"🏛️ Is NYC detected as Norfolk? {is_norfolk_nyc} (should be False)")
    
    return is_norfolk and not is_norfolk_nyc, location_data

def test_event_scraping():
    """Test NFK Currents event scraping"""
    print("\n🧪 Testing NFK Currents event scraping...")
    
    events_data = NorfolkEventScraper.scrape_nfk_currents()
    
    if 'error' in events_data:
        print(f"❌ Error scraping events: {events_data['error']}")
        return False
    
    print(f"✅ Successfully scraped NFK Currents")
    print(f"📅 Events found: {events_data.get('events_found', 0)}")
    print(f"📰 News items found: {len(events_data.get('news_items', []))}")
    print(f"📊 Total items: {events_data.get('total_items', 0)}")
    
    # Show sample events
    events = events_data.get('events', [])
    if events:
        print(f"\n🎉 Sample events:")
        for i, event in enumerate(events[:3], 1):
            print(f"  {i}. {event.get('title', 'Untitled')}")
            print(f"     Date: {event.get('date', 'TBD')}")
            print(f"     Location: {event.get('location', 'TBD')}")
            print()
    
    # Show sample news
    news_items = events_data.get('news_items', [])
    if news_items:
        print(f"📰 Sample news items:")
        for i, news in enumerate(news_items[:2], 1):
            print(f"  {i}. {news.get('headline', 'No headline')}")
            print()
    
    return True

def test_interest_extraction():
    """Test interest extraction from OSINT data"""
    print("\n🧪 Testing interest extraction from OSINT data...")
    
    # Create mock OSINT investigation results
    mock_investigation = {
        'maigret_results': {
            'johndoe': {
                'GitHub': {'status': 'found', 'url': 'https://github.com/johndoe'},
                'LinkedIn': {'status': 'found', 'url': 'https://linkedin.com/in/johndoe'},
                'Instagram': {'status': 'found', 'url': 'https://instagram.com/johndoe'
                }
            }
        },
        'additional_intel': {
            'domain_analysis': {
                'domain': 'techstartup.com'
            },
            'location_analysis': {
                'nearby_places': [
                    {'type': 'restaurant', 'name': 'Local Cafe'},
                    {'type': 'gym', 'name': 'Fitness Center'},
                    {'type': 'museum', 'name': 'Art Museum'}
                ]
            }
        }
    }
    
    interests = NorfolkEventScraper.extract_interests_from_osint(mock_investigation)
    print(f"🎯 Extracted interests: {interests}")
    
    # Expected interests: technology, programming, professional, networking, photography, art, food, culinary, fitness, health, culture, art, history
    expected_categories = ['technology', 'professional', 'art', 'food', 'fitness']
    found_expected = any(cat in interests for cat in expected_categories)
    
    print(f"✅ Found expected interest categories: {found_expected}")
    
    return found_expected, interests

def test_event_filtering():
    """Test event filtering based on interests"""
    print("\n🧪 Testing event filtering based on interests...")
    
    # Mock events data
    mock_events = {
        'events': [
            {
                'title': 'Tech Meetup: AI and Machine Learning',
                'description': 'Join us for an evening of technology discussions and networking with local developers and programmers.',
                'date': 'Today 7:00 PM',
                'location': 'Downtown Norfolk'
            },
            {
                'title': 'Art Gallery Opening',
                'description': 'New exhibition featuring local artists and their creative works.',
                'date': 'Tomorrow 6:00 PM',
                'location': 'Norfolk Arts Center'
            },
            {
                'title': 'City Council Meeting',
                'description': 'Monthly city council meeting to discuss local government issues.',
                'date': 'Next Tuesday 7:00 PM',
                'location': 'City Hall'
            },
            {
                'title': 'Food Festival',
                'description': 'Annual food festival featuring local restaurants and culinary experiences.',
                'date': 'This Weekend',
                'location': 'Waterfront Park'
            }
        ],
        'news_items': [
            {
                'headline': 'New Tech Hub Opens in Downtown Norfolk',
                'context': 'A new technology incubator has opened, supporting local startups and entrepreneurs.'
            },
            {
                'headline': 'Local Restaurant Wins Award',
                'context': 'A Norfolk restaurant has been recognized for its innovative culinary approach.'
            }
        ],
        'events_found': 4,
        'scrape_date': '2025-06-28'
    }
    
    # Test with tech interests
    tech_interests = ['technology', 'programming', 'professional']
    filtered_events = NorfolkEventScraper.filter_events_by_interests(mock_events, tech_interests)
    
    print(f"📊 Original events: {len(mock_events['events'])}")
    print(f"📊 Filtered events: {len(filtered_events['events'])}")
    print(f"🎯 User interests: {tech_interests}")
    
    # Show filtered events
    if filtered_events['events']:
        print("📅 Filtered events:")
        for event in filtered_events['events']:
            print(f"  • {event['title']} (Score: {event.get('relevance_score', 0)})")
            print(f"    Matched: {', '.join(event.get('matched_interests', []))}")
    
    filtering_worked = len(filtered_events['events']) > 0 and len(filtered_events['events']) <= len(mock_events['events'])
    
    return filtering_worked, filtered_events

def main():
    """Run Norfolk functionality tests"""
    print("🚀 Starting Norfolk Event Scraper Tests")
    print("=" * 50)
    
    # Test 1: Norfolk detection
    is_norfolk, location_data = test_norfolk_detection()
    
    # Test 2: Event scraping
    scraping_success = test_event_scraping()
    
    # Test 3: Interest extraction
    interests_success, interests_data = test_interest_extraction()
    
    # Test 4: Event filtering
    filtering_success, filtered_events_data = test_event_filtering()
    
    print("\n" + "=" * 50)
    print("📋 Test Results Summary:")
    print(f"✅ Norfolk detection: {'PASSED' if is_norfolk else 'FAILED'}")
    print(f"✅ Event scraping: {'PASSED' if scraping_success else 'FAILED'}")
    print(f"✅ Interest extraction: {'PASSED' if interests_success else 'FAILED'}")
    print(f"✅ Event filtering: {'PASSED' if filtering_success else 'FAILED'}")
    
    if is_norfolk and scraping_success and interests_success and filtering_success:
        print("🎉 All tests passed! Norfolk functionality is working.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
    
    print("\n💡 Note: If Norfolk detection failed, try with actual Norfolk coordinates or check the reverse geocoding service.")
    print("💡 Note: If event scraping failed, the website might be down or have changed structure.")

if __name__ == "__main__":
    main()
