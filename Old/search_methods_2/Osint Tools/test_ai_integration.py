#!/usr/bin/env python3
"""
Test script for AI-ready OSINT Engine
Verifies all components work correctly
"""

import sys
import json
from pathlib import Path

def test_simple_interface():
    """Test the simple Python interface"""
    print("🧪 Testing Simple Python Interface...")
    
    try:
        from simple_osint import investigate, get_interests, get_norfolk_events, is_norfolk_area
        
        # Test interest extraction
        print("  📋 Testing interest extraction...")
        interests = get_interests(name="John Developer", email="john@techcompany.com")
        print(f"     Interests found: {interests}")
        
        # Test Norfolk area detection
        print("  📍 Testing Norfolk area detection...")
        norfolk_coords = (36.8468, -76.2852)  # Norfolk, VA
        nyc_coords = (40.7128, -74.0060)      # New York City
        
        is_norfolk_test = is_norfolk_area(*norfolk_coords)
        is_nyc_test = is_norfolk_area(*nyc_coords)
        
        print(f"     Norfolk coordinates detected as Norfolk: {is_norfolk_test}")
        print(f"     NYC coordinates detected as Norfolk: {is_nyc_test}")
        
        # Test full investigation
        print("  🔍 Testing full investigation...")
        result = investigate(
            name="Jane Smith",
            email="jane@example.com",
            social_handles=["janesmith"],
            latitude=36.8468,
            longitude=-76.2852
        )
        
        print(f"     Investigation success: {result.get('success')}")
        print(f"     Interests found: {len(result.get('interests', []))}")
        print(f"     Norfolk area: {result.get('location_info', {}).get('is_norfolk_area')}")
        
        return True
        
    except Exception as e:
        print(f"     ❌ Simple interface test failed: {e}")
        return False

def test_norfolk_events():
    """Test Norfolk event scraping"""
    print("\n🧪 Testing Norfolk Event Scraping...")
    
    try:
        from simple_osint import get_norfolk_events
        
        # Test with Norfolk coordinates
        result = get_norfolk_events(
            name="Test User",
            email="test@example.com",
            latitude=36.8468,
            longitude=-76.2852
        )
        
        print(f"  📅 Is Norfolk area: {result.get('is_norfolk_area')}")
        
        if result.get('is_norfolk_area'):
            events = result.get('events', [])
            news = result.get('news_items', [])
            
            print(f"     Events found: {len(events)}")
            print(f"     News items found: {len(news)}")
            print(f"     Interest filtering applied: {result.get('events_filtered')}")
            
            # Show sample events
            if events:
                print("     Sample events:")
                for i, event in enumerate(events[:2], 1):
                    title = event.get('title', 'No title')[:50]
                    print(f"       {i}. {title}...")
        else:
            print("     Location not in Norfolk area (as expected for test)")
        
        return True
        
    except Exception as e:
        print(f"     ❌ Norfolk events test failed: {e}")
        return False

def test_engine_direct():
    """Test the engine directly"""
    print("\n🧪 Testing Engine Direct Access...")
    
    try:
        from osint_engine_ai import OSINTEngine
        
        engine = OSINTEngine(enable_logging=False)
        
        # Test basic investigation
        result = engine.investigate(
            name="Test Person",
            email="test@domain.com",
            social_handles=["testuser"],
            location_coords=(36.8468, -76.2852)
        )
        
        print(f"  ⚙️  Engine investigation success: {result.get('success')}")
        print(f"     Target name: {result.get('target', {}).get('name')}")
        print(f"     Interests extracted: {len(result.get('extracted_interests', []))}")
        
        # Test AI export
        ai_export = engine.export_for_ai(result)
        ai_data = json.loads(ai_export)
        
        print(f"     AI export success: {'target_profile' in ai_data}")
        print(f"     AI data keys: {list(ai_data.keys())}")
        
        return True
        
    except Exception as e:
        print(f"     ❌ Engine direct test failed: {e}")
        return False

def test_command_line():
    """Test command line interface"""
    print("\n🧪 Testing Command Line Interface...")
    
    try:
        import subprocess
        
        # Test interests mode
        cmd = [sys.executable, "simple_osint.py", 
               "--name", "Test User", 
               "--mode", "interests"]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print(f"  💻 Command line test success")
            print(f"     Output: {result.stdout.strip()}")
            return True
        else:
            print(f"     ❌ Command line test failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"     ❌ Command line test failed: {e}")
        return False

def test_utilities_import():
    """Test utilities import and basic functionality"""
    print("\n🧪 Testing Utilities Import...")
    
    try:
        from osint_utilities import OSINTUtilities, NorfolkEventScraper
        
        print("  📦 OSINTUtilities imported successfully")
        print("  🏛️  NorfolkEventScraper imported successfully")
        
        # Test basic Norfolk detection
        if NorfolkEventScraper:
            test_location_data = {
                'reverse_geocoding': {
                    'display_name': 'Norfolk, Virginia, United States',
                    'address': {
                        'city': 'Norfolk',
                        'state': 'Virginia',
                        'country': 'United States'
                    }
                }
            }
            
            is_norfolk = NorfolkEventScraper.is_norfolk_area(test_location_data)
            print(f"     Norfolk detection test: {is_norfolk}")
        
        return True
        
    except Exception as e:
        print(f"     ❌ Utilities import test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 OSINT Engine AI Integration Tests")
    print("=" * 50)
    
    tests = [
        ("Utilities Import", test_utilities_import),
        ("Simple Interface", test_simple_interface),
        ("Norfolk Events", test_norfolk_events),
        ("Engine Direct", test_engine_direct),
        ("Command Line", test_command_line)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 Test Results Summary:")
    
    passed = 0
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status} {test_name}")
        if success:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All tests passed! System is ready for AI integration.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
    
    print("\n💡 Next steps:")
    print("   - Use 'simple_osint.py' for AI integration")
    print("   - See 'README_AI.md' for integration examples")
    print("   - Start API server with 'python osint_api.py' if needed")

if __name__ == "__main__":
    main()
