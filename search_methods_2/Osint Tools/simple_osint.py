#!/usr/bin/env python3
"""
Simple OSINT Interface for AI Integration
Direct Python interface - no web dependencies
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from osint_engine_ai import OSINTEngine
except ImportError:
    print("OSINT Engine not found. Please ensure osint_engine_ai.py is in the same directory.")
    sys.exit(1)

class SimpleOSINTInterface:
    """
    Simplified interface for AI systems
    No web dependencies, pure Python
    """
    
    def __init__(self):
        """Initialize the interface"""
        self.engine = OSINTEngine(enable_logging=False)
    
    def investigate_person(self, 
                          name: str = "", 
                          email: str = "", 
                          social_handles: List[str] = None,
                          latitude: float = None,
                          longitude: float = None) -> Dict:
        """
        Simple investigation method for AI systems
        
        Args:
            name: Person's full name
            email: Person's email address  
            social_handles: List of social media usernames
            latitude: Location latitude
            longitude: Location longitude
            
        Returns:
            Dictionary with investigation results
        """
        coords = (latitude, longitude) if latitude and longitude else None
        
        results = self.engine.investigate(
            name=name,
            email=email,
            social_handles=social_handles or [],
            location_coords=coords
        )
        
        return self._simplify_results(results)
    
    def get_interests(self, 
                     name: str = "", 
                     email: str = "", 
                     social_handles: List[str] = None) -> List[str]:
        """
        Get just the interests for a person
        
        Returns:
            List of interest keywords
        """
        results = self.engine.investigate(
            name=name,
            email=email,
            social_handles=social_handles or []
        )
        
        return results.get('extracted_interests', [])
    
    def get_norfolk_events(self, 
                          name: str = "",
                          email: str = "",
                          social_handles: List[str] = None,
                          latitude: float = None,
                          longitude: float = None) -> Dict:
        """
        Get Norfolk events if person is in Norfolk area
        
        Returns:
            Dictionary with events and location info
        """
        coords = (latitude, longitude) if latitude and longitude else None
        
        results = self.engine.investigate(
            name=name,
            email=email,
            social_handles=social_handles or [],
            location_coords=coords
        )
        
        location_intel = results.get('location_intel', {})
        is_norfolk = location_intel.get('is_norfolk_area', False)
        
        if is_norfolk:
            norfolk_events = results.get('norfolk_events', {})
            return {
                'is_norfolk_area': True,
                'events': norfolk_events.get('events', []),
                'news_items': norfolk_events.get('news_items', []),
                'interests_used': results.get('extracted_interests', []),
                'events_filtered': norfolk_events.get('filter_applied', False)
            }
        else:
            return {
                'is_norfolk_area': False,
                'events': [],
                'news_items': [],
                'location': location_intel.get('reverse_geocoding', {}).get('display_name', 'Unknown')
            }
    
    def check_norfolk_area(self, latitude: float, longitude: float) -> bool:
        """
        Check if coordinates are in Norfolk, VA area
        
        Returns:
            True if in Norfolk area, False otherwise
        """
        results = self.engine.investigate(location_coords=(latitude, longitude))
        return results.get('location_intel', {}).get('is_norfolk_area', False)
    
    def _simplify_results(self, results: Dict) -> Dict:
        """Simplify results for AI consumption"""
        return {
            'success': results.get('success', False),
            'target': results.get('target', {}),
            'interests': results.get('extracted_interests', []),
            'social_platforms': self._extract_platforms(results),
            'location_info': {
                'is_norfolk_area': results.get('location_intel', {}).get('is_norfolk_area', False),
                'address': results.get('location_intel', {}).get('reverse_geocoding', {}).get('display_name', ''),
                'nearby_amenities': self._extract_amenities(results)
            },
            'norfolk_events': results.get('norfolk_events', {}),
            'timestamp': results.get('timestamp')
        }
    
    def _extract_platforms(self, results: Dict) -> List[str]:
        """Extract social media platforms found"""
        platforms = []
        for username, data in results.get('social_profiles', {}).items():
            for profile in data.get('verified_profiles', []):
                platforms.append(profile.get('platform', ''))
        return list(set(platforms))
    
    def _extract_amenities(self, results: Dict) -> List[Dict]:
        """Extract nearby amenities summary"""
        location_intel = results.get('location_intel', {})
        nearby_places = location_intel.get('nearby_places', [])
        
        amenity_counts = {}
        for place in nearby_places:
            place_type = place.get('type', 'unknown')
            amenity_counts[place_type] = amenity_counts.get(place_type, 0) + 1
        
        return [{'type': ptype, 'count': count} for ptype, count in amenity_counts.items()]

# Global interface instance for easy access
osint = SimpleOSINTInterface()

# Convenience functions for direct access
def investigate(name="", email="", social_handles=None, latitude=None, longitude=None):
    """Quick investigation function"""
    return osint.investigate_person(name, email, social_handles, latitude, longitude)

def get_interests(name="", email="", social_handles=None):
    """Quick interests function"""
    return osint.get_interests(name, email, social_handles)

def get_norfolk_events(name="", email="", social_handles=None, latitude=None, longitude=None):
    """Quick Norfolk events function"""
    return osint.get_norfolk_events(name, email, social_handles, latitude, longitude)

def is_norfolk_area(latitude, longitude):
    """Quick Norfolk area check"""
    return osint.check_norfolk_area(latitude, longitude)

# CLI interface for testing
def main():
    """Command line interface for testing"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Simple OSINT Interface")
    parser.add_argument("--name", help="Person's name")
    parser.add_argument("--email", help="Person's email")
    parser.add_argument("--social", nargs="*", help="Social handles")
    parser.add_argument("--lat", type=float, help="Latitude")
    parser.add_argument("--lon", type=float, help="Longitude")
    parser.add_argument("--mode", choices=['full', 'interests', 'norfolk', 'location'], 
                       default='full', help="Investigation mode")
    
    args = parser.parse_args()
    
    if args.mode == 'interests':
        result = get_interests(args.name or "", args.email or "", args.social)
        print("Interests:", ', '.join(result))
    
    elif args.mode == 'norfolk':
        result = get_norfolk_events(args.name or "", args.email or "", args.social, args.lat, args.lon)
        print(f"Norfolk Area: {result['is_norfolk_area']}")
        if result['is_norfolk_area']:
            print(f"Events Found: {len(result['events'])}")
            for event in result['events'][:3]:
                print(f"  - {event.get('title', 'Unknown Event')}")
    
    elif args.mode == 'location':
        if args.lat and args.lon:
            result = is_norfolk_area(args.lat, args.lon)
            print(f"Is Norfolk Area: {result}")
        else:
            print("Latitude and longitude required for location check")
    
    else:  # full investigation
        result = investigate(args.name or "", args.email or "", args.social, args.lat, args.lon)
        print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
