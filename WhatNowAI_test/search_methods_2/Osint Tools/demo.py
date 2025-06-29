#!/usr/bin/env python3
"""
Demo script for OSINT Scraper
Demonstrates functionality using only FREE services - no API keys required!
"""

import sys
from pathlib import Path
from osint_scraper import OSINTTarget, OSINTScraper
from osint_utilities import OSINTUtilities

def demo_target_analysis():
    """Demonstrate target analysis with sample data using FREE services"""
    print("🎉 OSINT Scraper Demo - 100% FREE Services!")
    print("=" * 60)
    print("✅ No API keys required - all services are completely free!")
    print()
    
    # Create a sample target
    target = OSINTTarget(
        full_name="John Doe",
        email="john.doe@example.com",
        social_handles=["johndoe", "john_doe"],
        address="123 Main St, Anytown, USA",
        coordinates=(40.7128, -74.0060)  # NYC coordinates
    )
    
    print("🎯 Target Information:")
    print(f"  Name: {target.full_name}")
    print(f"  Email: {target.email}")
    print(f"  Domain: {target.domain}")
    print(f"  Social Handles: {', '.join(target.social_handles)}")
    print(f"  Username Variants: {', '.join(target.username_variants)}")
    print(f"  Coordinates: {target.coordinates}")
    print()
    
    # Initialize utilities (all FREE - no API keys needed!)
    print("🔧 Initializing FREE OSINT utilities...")
    utilities = OSINTUtilities()
    print()
    
    # Demonstrate DNS reconnaissance
    if target.domain:
        print("🌐 DNS Reconnaissance Demo:")
        print("-" * 40)
        
        from osint_utilities import DNSRecon
        dns_records = DNSRecon.get_dns_records(target.domain)
        
        for record_type, records in dns_records.items():
            if records:
                print(f"  {record_type}: {', '.join(records)}")
        print()
    
    # Demonstrate email investigation
    if target.email:
        print("📧 Email Investigation Demo:")
        print("-" * 40)
        
        email_results = utilities.email_investigation(target.email)
        validation = email_results.get('format_validation', {})
        
        print(f"  Email Format: {'Valid' if validation.get('format_valid') else 'Invalid'}")
        print(f"  Domain: {validation.get('domain', 'N/A')}")
        
        mx_check = email_results.get('domain_mx_check', {})
        print(f"  Has MX Records: {'Yes' if mx_check.get('has_mx') else 'No'}")
        
        breach_check = email_results.get('breach_check', {})
        if breach_check.get('domain_in_known_breaches'):
            print("  ⚠️  Domain appears in known breach databases")
        else:
            print("  ✅ Domain not in common breach lists")
        print()
    
    # Demonstrate social media search
    if target.username_variants:
        print("👤 Social Media Search Demo:")
        print("-" * 40)
        
        username = target.username_variants[0]
        social_results = utilities.social_media_search(username)
        
        print(f"  Username: {username}")
        potential_profiles = social_results.get('potential_profiles', [])
        print(f"  Generated {len(potential_profiles)} potential profile URLs:")
        
        for profile in potential_profiles[:5]:  # Show first 5
            print(f"    - {profile['platform']}: {profile['url']}")
        
        verified = social_results.get('verified_profiles', [])
        if verified:
            print(f"  ✅ Found {len(verified)} potentially active profiles!")
        print()
    
    # Demonstrate location analysis (using free APIs)
    if target.coordinates:
        print("📍 Location Analysis Demo:")
        print("-" * 40)
        
        lat, lon = target.coordinates
        location_data = utilities.location_analysis(lat, lon)
        
        reverse_geo = location_data.get('reverse_geocoding', {})
        if reverse_geo and 'display_name' in reverse_geo:
            print(f"  Address: {reverse_geo['display_name']}")
        
        nearby_places = location_data.get('nearby_places', [])
        if nearby_places:
            print(f"  Nearby places found: {len(nearby_places)}")
            for place in nearby_places[:5]:  # Show first 5
                name = place.get('name', 'Unknown')
                place_type = place.get('type', 'Unknown')
                print(f"    - {name}: {place_type}")
        print()
    
    print("✅ Demo completed successfully!")
    print()
    print("🚀 What you can do next:")
    print("1. Run a full investigation: python osint_scraper.py --interactive")
    print("2. Setup OSINT tools: python osint_scraper.py --setup")
    print("3. Use the Windows launcher: run.bat")
    print()
    print("💡 Features available (100% FREE):")
    print("  ✅ DNS reconnaissance and subdomain enumeration")
    print("  ✅ WHOIS lookups and SSL certificate analysis")
    print("  ✅ Email format validation and MX record checks")
    print("  ✅ Social media profile URL generation")
    print("  ✅ IP geolocation and port scanning")
    print("  ✅ Location analysis with nearby places")
    print("  ✅ Basic breach domain checking")
    print("  ✅ Integration with Maigret, Recon-ng, and SpiderFoot")

if __name__ == "__main__":
    try:
        demo_target_analysis()
    except ImportError as e:
        print(f"Import error: {e}")
        print("Please install required dependencies first:")
        print("python install_deps.py")
    except Exception as e:
        print(f"Demo error: {e}")
        print("Some functionality may require network access.")
