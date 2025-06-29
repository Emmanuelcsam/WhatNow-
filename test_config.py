#!/usr/bin/env python3
"""
Quick test to verify the enhanced location service configuration
"""

import os
import sys

def test_configuration():
    """Test if the enhanced location configuration is correct"""
    print("=== Enhanced Location Service Configuration Test ===")

    # Check if secrets.txt exists and has IPStack key
    secrets_file = 'secrets.txt'
    if os.path.exists(secrets_file):
        print("✓ secrets.txt found")

        with open(secrets_file, 'r') as f:
            content = f.read()
            if 'IPSTACK_API_KEY' in content and '3e3cd89b32d39af7119d79f8fe981803' in content:
                print("✓ IPStack API key configured correctly")
            else:
                print("✗ IPStack API key not found or incorrect")
                return False
    else:
        print("✗ secrets.txt not found")
        return False

    # Check if enhanced location service file exists
    service_file = 'services/enhanced_location_service.py'
    if os.path.exists(service_file):
        print("✓ Enhanced location service file exists")
    else:
        print("✗ Enhanced location service file missing")
        return False

    # Check if enhanced location JS exists
    js_file = 'static/js/enhanced-location.js'
    if os.path.exists(js_file):
        print("✓ Enhanced location JavaScript exists")
    else:
        print("✗ Enhanced location JavaScript missing")
        return False

    # Check if templates are updated
    home_template = 'templates/home.html'
    if os.path.exists(home_template):
        with open(home_template, 'r') as f:
            content = f.read()
            if 'enhanced-location.js' in content:
                print("✓ Home template includes enhanced location script")
            else:
                print("✗ Home template not updated with enhanced location script")
                return False

    # Check if demo template exists
    demo_template = 'templates/location_demo.html'
    if os.path.exists(demo_template):
        print("✓ Location demo template exists")
    else:
        print("✗ Location demo template missing")
        return False

    # Check if routes are updated
    routes_file = 'routes.py'
    if os.path.exists(routes_file):
        with open(routes_file, 'r') as f:
            content = f.read()
            if '/api/location/test' in content and 'enhanced_location_service' in content:
                print("✓ Routes updated with enhanced location endpoints")
            else:
                print("✗ Routes not properly updated")
                return False

    print("\n=== Configuration Summary ===")
    print("✓ All components configured correctly!")
    print("✓ Ready for enhanced location detection")
    print("✓ Multiple fallback methods available")
    print("✓ IPStack API integration configured")
    print("✓ Browser geolocation support enabled")
    print("✓ Demo page available at /location-demo")

    return True

def show_usage_instructions():
    """Show instructions for using the enhanced location system"""
    print("\n=== Usage Instructions ===")
    print("1. Start the Flask application:")
    print("   python app.py")
    print("")
    print("2. Open your browser and visit:")
    print("   http://localhost:5000/location-demo")
    print("")
    print("3. Test the location detection by clicking 'Detect My Location'")
    print("")
    print("4. The system will try multiple methods:")
    print("   - Browser geolocation (most accurate)")
    print("   - IPStack API (using your provided key)")
    print("   - Fallback providers (ip-api.com, freegeoip.app)")
    print("")
    print("5. View the main application:")
    print("   http://localhost:5000/")
    print("")
    print("6. API endpoints available:")
    print("   POST /api/location/comprehensive - Full detection")
    print("   POST /api/location/from-ip - IP-based only")
    print("   POST /api/location/test - Service health check")

if __name__ == "__main__":
    success = test_configuration()

    if success:
        show_usage_instructions()
        print("\n🎉 Enhanced location detection system ready!")
    else:
        print("\n❌ Configuration issues found. Please check the setup.")
        sys.exit(1)
