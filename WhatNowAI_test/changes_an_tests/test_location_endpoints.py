#!/usr/bin/env python3
"""Test script to verify location endpoints are working"""

import requests
import json
import time

# Base URL for the application
BASE_URL = "http://localhost:5002"

# Test IP address (Google DNS)
TEST_IP = "8.8.8.8"

# Williamsburg, VA coordinates
WILLIAMSBURG_LAT = 37.2707
WILLIAMSBURG_LON = -76.7075

def test_comprehensive_location():
    """Test the comprehensive location endpoint"""
    print("\n=== Testing Comprehensive Location Endpoint ===")
    
    # Test with IP only
    print("\n1. Testing with IP only:")
    response = requests.post(f"{BASE_URL}/api/location/comprehensive", 
                           json={"ip": TEST_IP})
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
    else:
        print(f"Error: {response.text}")
    
    time.sleep(1)  # Rate limiting
    
    # Test with coordinates (Williamsburg, VA)
    print("\n2. Testing with Williamsburg, VA coordinates:")
    response = requests.post(f"{BASE_URL}/api/location/comprehensive", 
                           json={"latitude": WILLIAMSBURG_LAT, "longitude": WILLIAMSBURG_LON})
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
    else:
        print(f"Error: {response.text}")

def test_reverse_geocode():
    """Test the reverse geocode endpoint"""
    print("\n\n=== Testing Reverse Geocode Endpoint ===")
    
    print("Testing with Williamsburg, VA coordinates:")
    response = requests.post(f"{BASE_URL}/api/location/reverse-geocode", 
                           json={"latitude": WILLIAMSBURG_LAT, "longitude": WILLIAMSBURG_LON})
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
    else:
        print(f"Error: {response.text}")

def test_ip_location():
    """Test the IP location endpoint"""
    print("\n\n=== Testing IP Location Endpoint ===")
    
    print(f"Testing with IP: {TEST_IP}")
    response = requests.post(f"{BASE_URL}/api/location/from-ip", 
                           json={"ip": TEST_IP})
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
    else:
        print(f"Error: {response.text}")

def test_detect_location():
    """Test the detect location endpoint (used by frontend)"""
    print("\n\n=== Testing Detect Location Endpoint ===")
    
    # Test without coordinates
    print("\n1. Testing without coordinates:")
    response = requests.post(f"{BASE_URL}/detect-location", json={})
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
    else:
        print(f"Error: {response.text}")
    
    time.sleep(1)
    
    # Test with coordinates
    print("\n2. Testing with Williamsburg, VA coordinates:")
    response = requests.post(f"{BASE_URL}/detect-location", 
                           json={"latitude": WILLIAMSBURG_LAT, "longitude": WILLIAMSBURG_LON})
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
    else:
        print(f"Error: {response.text}")

if __name__ == "__main__":
    print("Starting location endpoint tests...")
    print(f"Make sure the application is running on {BASE_URL}")
    print("-" * 50)
    
    try:
        # Quick connectivity test
        response = requests.get(f"{BASE_URL}/", timeout=5)
        print("✓ Application is running")
    except Exception as e:
        print(f"✗ Cannot connect to application: {e}")
        print("Please make sure the application is running with: python app.py")
        exit(1)
    
    # Run tests
    test_comprehensive_location()
    test_reverse_geocode()
    test_ip_location()
    test_detect_location()
    
    print("\n" + "=" * 50)
    print("All tests completed!")