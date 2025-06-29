#!/usr/bin/env python3
"""
OSINT Intelligence Engine - AI Integration Ready
Streamlined for external AI system integration
"""

import os
import sys
import json
import subprocess
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
import warnings

# Suppress warnings for cleaner output
warnings.filterwarnings("ignore")

# Third-party imports with fallback
try:
    import requests
    from colorama import init, Fore, Style
    init(autoreset=True)
except ImportError:
    print("Installing required packages...")
    subprocess.run([sys.executable, "-m", "pip", "install", "requests", "colorama"], check=True)
    import requests
    from colorama import init, Fore, Style
    init(autoreset=True)

# Local imports with fallback
try:
    from osint_utilities import OSINTUtilities, NorfolkEventScraper
except ImportError:
    OSINTUtilities = None
    NorfolkEventScraper = None

class OSINTEngine:
    """
    Streamlined OSINT Engine for AI Integration
    Designed to be called by larger AI systems
    """
    
    def __init__(self, enable_logging: bool = False):
        """Initialize the OSINT Engine"""
        self.base_dir = Path(__file__).parent
        self.output_dir = self.base_dir / "output"
        self.output_dir.mkdir(exist_ok=True)
        
        # Simple logging setup
        self.enable_logging = enable_logging
        if enable_logging:
            logging.basicConfig(level=logging.INFO, format='%(message)s')
            self.logger = logging.getLogger(__name__)
        else:
            self.logger = None
        
        # Initialize utilities
        if OSINTUtilities:
            self.utilities = OSINTUtilities({})
        else:
            self.utilities = None
    
    def _log(self, message: str, level: str = "info"):
        """Internal logging method"""
        if self.logger:
            getattr(self.logger, level)(message)
    
    def investigate(self, 
                   name: str = "", 
                   email: str = "", 
                   social_handles: List[str] = None, 
                   location_coords: Tuple[float, float] = None,
                   browser_location: Dict = None) -> Dict:
        """
        Main investigation method - AI entry point
        
        Args:
            name: Target's full name
            email: Target's email address
            social_handles: List of social media handles
            location_coords: (latitude, longitude) tuple
            browser_location: Browser geolocation data
            
        Returns:
            Dict containing investigation results and extracted intelligence
        """
        self._log(f"Starting OSINT investigation for: {name or email}")
        
        # Use browser location if provided, otherwise use coordinates
        if browser_location and not location_coords:
            location_coords = (
                browser_location.get('latitude'),
                browser_location.get('longitude')
            )
        
        # Initialize results structure
        results = {
            'target': {
                'name': name,
                'email': email,
                'social_handles': social_handles or [],
                'location': location_coords
            },
            'extracted_interests': [],
            'social_profiles': {},
            'domain_intel': {},
            'location_intel': {},
            'norfolk_events': None,
            'success': False,
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            if not self.utilities:
                self._log("OSINT utilities not available", "warning")
                return results
            
            # Generate username variants
            username_variants = self._generate_usernames(name, social_handles or [])
            
            # Social media investigation
            if username_variants:
                self._log("Investigating social media profiles...")
                results['social_profiles'] = self._investigate_social_media(username_variants)
            
            # Domain/Email investigation
            if email:
                self._log("Investigating email and domain...")
                results['domain_intel'] = self._investigate_domain(email)
            
            # Location investigation
            if location_coords:
                self._log("Analyzing location...")
                results['location_intel'] = self._investigate_location(location_coords, results)
            
            # Extract interests from all gathered intelligence
            results['extracted_interests'] = self._extract_interests(results)
            
            # Norfolk-specific event scraping if applicable
            if results['location_intel'].get('is_norfolk_area'):
                self._log("Norfolk, VA detected - fetching relevant local events...")
                results['norfolk_events'] = self._get_norfolk_events(results['extracted_interests'])
            
            results['success'] = True
            self._log("Investigation completed successfully")
            
        except Exception as e:
            self._log(f"Investigation failed: {str(e)}", "error")
            results['error'] = str(e)
        
        return results
    
    def _generate_usernames(self, name: str, social_handles: List[str]) -> List[str]:
        """Generate possible username variants"""
        if not name:
            return social_handles
        
        variants = set(social_handles)
        name_parts = name.lower().split()
        
        if len(name_parts) >= 2:
            first, last = name_parts[0], name_parts[-1]
            variants.update([
                first + last, first + '.' + last, first + '_' + last,
                first + last[0], first[0] + last, last + first
            ])
        elif len(name_parts) == 1:
            variants.add(name_parts[0])
        
        return list(variants)
    
    def _investigate_social_media(self, usernames: List[str]) -> Dict:
        """Investigate social media profiles"""
        if not self.utilities:
            return {}
        
        profiles = {}
        for username in usernames[:3]:  # Limit to avoid rate limiting
            try:
                result = self.utilities.social_media_search(username)
                if result.get('verified_profiles'):
                    profiles[username] = result
            except Exception as e:
                self._log(f"Social media search failed for {username}: {e}", "warning")
        
        return profiles
    
    def _investigate_domain(self, email: str) -> Dict:
        """Investigate email domain"""
        if not self.utilities or '@' not in email:
            return {}
        
        domain = email.split('@')[1]
        try:
            return self.utilities.comprehensive_domain_analysis(domain)
        except Exception as e:
            self._log(f"Domain analysis failed: {e}", "warning")
            return {}
    
    def _investigate_location(self, coords: Tuple[float, float], context: Dict) -> Dict:
        """Investigate location with context"""
        if not self.utilities:
            return {}
        
        try:
            lat, lon = coords
            location_data = self.utilities.location_analysis(lat, lon, context)
            
            # Check if Norfolk area
            if NorfolkEventScraper and NorfolkEventScraper.is_norfolk_area(location_data):
                location_data['is_norfolk_area'] = True
            else:
                location_data['is_norfolk_area'] = False
            
            return location_data
        except Exception as e:
            self._log(f"Location analysis failed: {e}", "warning")
            return {}
    
    def _extract_interests(self, investigation_data: Dict) -> List[str]:
        """Extract interests from investigation data"""
        if not NorfolkEventScraper:
            return []
        
        try:
            # Create mock investigation results for the utility function
            mock_results = {
                'maigret_results': {},
                'additional_intel': {
                    'domain_analysis': investigation_data.get('domain_intel', {}),
                    'location_analysis': investigation_data.get('location_intel', {}),
                    'social_media_search': investigation_data.get('social_profiles', {})
                }
            }
            
            # Convert social profiles to expected format
            if investigation_data.get('social_profiles'):
                mock_results['maigret_results'] = {}
                for username, data in investigation_data['social_profiles'].items():
                    mock_results['maigret_results'][username] = {}
                    for profile in data.get('verified_profiles', []):
                        platform = profile.get('platform', 'unknown')
                        mock_results['maigret_results'][username][platform] = {
                            'status': 'found',
                            'url': profile.get('url', '')
                        }
            
            return NorfolkEventScraper.extract_interests_from_osint(mock_results)
        except Exception as e:
            self._log(f"Interest extraction failed: {e}", "warning")
            return ['general', 'community']
    
    def _get_norfolk_events(self, interests: List[str]) -> Dict:
        """Get Norfolk events filtered by interests"""
        if not NorfolkEventScraper:
            return {}
        
        try:
            raw_events = NorfolkEventScraper.scrape_nfk_currents()
            if interests:
                return NorfolkEventScraper.filter_events_by_interests(raw_events, interests)
            return raw_events
        except Exception as e:
            self._log(f"Norfolk events scraping failed: {e}", "warning")
            return {}
    
    def get_interests_keywords(self, investigation_results: Dict) -> List[str]:
        """
        Extract keywords for use by other AI systems
        
        Args:
            investigation_results: Results from investigate() method
            
        Returns:
            List of interest keywords for external use
        """
        interests = investigation_results.get('extracted_interests', [])
        
        # Expand interests to include related keywords
        keyword_mapping = {
            'technology': ['tech', 'software', 'coding', 'programming', 'digital'],
            'art': ['art', 'creative', 'design', 'visual', 'gallery'],
            'music': ['music', 'concert', 'band', 'performance', 'audio'],
            'food': ['food', 'restaurant', 'culinary', 'dining', 'cooking'],
            'sports': ['sports', 'fitness', 'athletic', 'game', 'competition'],
            'business': ['business', 'professional', 'networking', 'corporate'],
            'education': ['education', 'learning', 'academic', 'university'],
            'health': ['health', 'wellness', 'medical', 'fitness'],
            'community': ['community', 'local', 'neighborhood', 'social'],
            'entertainment': ['entertainment', 'show', 'performance', 'event']
        }
        
        keywords = set()
        for interest in interests:
            interest_lower = interest.lower()
            if interest_lower in keyword_mapping:
                keywords.update(keyword_mapping[interest_lower])
            else:
                keywords.add(interest_lower)
        
        return list(keywords)
    
    def export_for_ai(self, investigation_results: Dict, export_path: str = None) -> str:
        """
        Export results in AI-friendly format
        
        Args:
            investigation_results: Results from investigate() method
            export_path: Optional path to save the export
            
        Returns:
            JSON string of AI-friendly data
        """
        ai_data = {
            'target_profile': {
                'name': investigation_results['target']['name'],
                'email': investigation_results['target']['email'],
                'social_handles': investigation_results['target']['social_handles'],
                'location': investigation_results['target']['location']
            },
            'interests': investigation_results.get('extracted_interests', []),
            'interest_keywords': self.get_interests_keywords(investigation_results),
            'social_presence': {
                'platforms_found': [],
                'verified_profiles': []
            },
            'location_context': {
                'is_norfolk_va': investigation_results.get('location_intel', {}).get('is_norfolk_area', False),
                'nearby_amenities': []
            },
            'norfolk_events': investigation_results.get('norfolk_events'),
            'metadata': {
                'timestamp': investigation_results.get('timestamp'),
                'success': investigation_results.get('success', False)
            }
        }
        
        # Process social profiles
        for username, data in investigation_results.get('social_profiles', {}).items():
            for profile in data.get('verified_profiles', []):
                ai_data['social_presence']['platforms_found'].append(profile['platform'])
                ai_data['social_presence']['verified_profiles'].append({
                    'platform': profile['platform'],
                    'username': username,
                    'url': profile['url']
                })
        
        # Process location amenities
        location_intel = investigation_results.get('location_intel', {})
        nearby_places = location_intel.get('nearby_places', [])
        place_summary = {}
        for place in nearby_places:
            place_type = place.get('type', 'unknown')
            place_summary[place_type] = place_summary.get(place_type, 0) + 1
        
        ai_data['location_context']['nearby_amenities'] = [
            {'type': ptype, 'count': count} 
            for ptype, count in place_summary.items()
        ]
        
        # Export to file if path provided
        if export_path:
            export_file = Path(export_path)
            export_file.parent.mkdir(parents=True, exist_ok=True)
            with open(export_file, 'w', encoding='utf-8') as f:
                json.dump(ai_data, f, indent=2, ensure_ascii=False)
        
        return json.dumps(ai_data, indent=2, ensure_ascii=False)

def main():
    """Command-line interface for AI integration"""
    import argparse
    
    parser = argparse.ArgumentParser(description="OSINT Engine for AI Integration")
    parser.add_argument("--name", help="Target's full name")
    parser.add_argument("--email", help="Target's email address")
    parser.add_argument("--social", nargs="*", help="Social media handles")
    parser.add_argument("--lat", type=float, help="Latitude")
    parser.add_argument("--lon", type=float, help="Longitude")
    parser.add_argument("--output", help="Output file path")
    parser.add_argument("--interests-only", action="store_true", help="Only output interests")
    parser.add_argument("--norfolk-events-only", action="store_true", help="Only output Norfolk events")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--quiet", action="store_true", help="Suppress logging")
    
    args = parser.parse_args()
    
    if not any([args.name, args.email]):
        print("Error: Must provide at least name or email")
        return 1
    
    # Initialize engine
    engine = OSINTEngine(enable_logging=not args.quiet)
    
    # Prepare coordinates
    coords = (args.lat, args.lon) if args.lat and args.lon else None
    
    # Run investigation
    results = engine.investigate(
        name=args.name or "",
        email=args.email or "",
        social_handles=args.social or [],
        location_coords=coords
    )
    
    # Handle specific output requests
    if args.interests_only:
        interests = results.get('extracted_interests', [])
        if args.json:
            print(json.dumps(interests))
        else:
            print(' '.join(interests))
        return 0
    
    if args.norfolk_events_only:
        events = results.get('norfolk_events', {})
        if args.json:
            print(json.dumps(events, indent=2))
        else:
            if events and events.get('events'):
                for event in events['events']:
                    print(f"- {event.get('title', 'Unknown Event')}")
        return 0
    
    # Generate AI-friendly export
    ai_export = engine.export_for_ai(results, args.output)
    
    if args.json:
        print(ai_export)
    else:
        # Human-readable summary
        print(f"Investigation Results for: {args.name or args.email}")
        print(f"Success: {results.get('success', False)}")
        print(f"Interests: {', '.join(results.get('extracted_interests', []))}")
        print(f"Norfolk Area: {results.get('location_intel', {}).get('is_norfolk_area', False)}")
        
        if results.get('norfolk_events'):
            events = results['norfolk_events'].get('events', [])
            print(f"Norfolk Events Found: {len(events)}")
    
    return 0

if __name__ == "__main__":
    exit(main())
