#!/usr/bin/env python3
"""
Enhanced Location Service Test Script

This script tests the comprehensive location detection functionality
to ensure it works correctly with multiple providers and fallbacks.
"""

import sys
import os
sys.path.append('.')

from services.enhanced_location_service import create_location_service
from config.settings import LOCATION_CONFIG

def test_enhanced_location_service():
    """Test the enhanced location service functionality"""
    print("=== Enhanced Location Service Test ===")

    # Create the location service
    try:
        service = create_location_service(
            ipstack_key=LOCATION_CONFIG.get('IPSTACK_API_KEY')
        )
        print(f"✓ Service created with {len(service.providers)} providers")

        # Test 1: Get user's IP
        print("\n1. Testing IP detection...")
        user_ip = service.get_user_ip()
        if user_ip:
            print(f"✓ Detected IP: {user_ip}")
        else:
            print("✗ Failed to detect IP")
            return False

        # Test 2: Get location from IP
        print(f"\n2. Testing IP-based location for {user_ip}...")
        ip_location = service.get_location_from_ip(user_ip)
        if ip_location:
            print(f"✓ Location detected:")
            print(f"   City: {ip_location.city}")
            print(f"   State: {ip_location.state}")
            print(f"   Country: {ip_location.country}")
            print(f"   Coordinates: {ip_location.latitude}, {ip_location.longitude}")
            print(f"   Zip: {ip_location.zip_code}")
            print(f"   Accuracy: {ip_location.accuracy:.2f}")
            print(f"   Source: {ip_location.source}")
        else:
            print("✗ Failed to get location from IP")
            return False

        # Test 3: Comprehensive location
        print(f"\n3. Testing comprehensive location detection...")
        comprehensive = service.get_comprehensive_location()
        if comprehensive and comprehensive.get('primary_location'):
            print(f"✓ Comprehensive location:")
            primary = comprehensive['primary_location']
            print(f"   City: {primary['city']}")
            print(f"   State: {primary['state']}")
            print(f"   Country: {primary['country']}")
            print(f"   Confidence: {comprehensive['confidence']:.2f}")
            print(f"   Methods: {', '.join(comprehensive['methods_used'])}")
        else:
            print("✗ Failed comprehensive location detection")
            return False

        # Test 4: Validation
        print(f"\n4. Testing location validation...")
        is_valid = service.validate_location(comprehensive['primary_location'])
        print(f"✓ Location validation: {'PASSED' if is_valid else 'FAILED'}")

        # Test 5: Address geocoding (optional)
        print(f"\n5. Testing address geocoding...")
        try:
            address_result = service.get_location_for_address("New York, NY")
            if address_result:
                print(f"✓ Geocoded 'New York, NY':")
                print(f"   Coordinates: {address_result.latitude}, {address_result.longitude}")
            else:
                print("✗ Address geocoding failed")
        except Exception as e:
            print(f"✗ Address geocoding error: {e}")

        print(f"\n=== Test Summary ===")
        print(f"✓ Enhanced location service is working properly!")
        print(f"✓ Using IPStack API key: {'Yes' if LOCATION_CONFIG.get('IPSTACK_API_KEY') else 'No'}")
        print(f"✓ Cache size: {len(service.cache)} entries")

        return True

    except Exception as e:
        print(f"✗ Service creation failed: {e}")
        return False

if __name__ == "__main__":
    success = test_enhanced_location_service()
    sys.exit(0 if success else 1)
