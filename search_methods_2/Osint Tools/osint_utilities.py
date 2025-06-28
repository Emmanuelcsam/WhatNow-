#!/usr/bin/env python3
"""
OSINT utilities using only FREE APIs and services
No paid API keys required!
"""

import os
import requests
import json
import time
from typing import Dict, List, Optional
import dns.resolver
import whois
from urllib.parse import urlparse
import socket
import ssl
import subprocess
import re
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

class FreeIPLookup:
    """Free IP information lookup using multiple free services"""
    
    @staticmethod
    def get_ip_info(ip: str) -> Dict:
        """Get IP information using free services"""
        results = {'ip': ip, 'services': {}}
        
        # IPInfo.io (free tier)
        try:
            response = requests.get(f"http://ipinfo.io/{ip}/json", timeout=10)
            if response.status_code == 200:
                results['services']['ipinfo'] = response.json()
        except Exception:
            pass
        
        # ip-api.com (free)
        try:
            response = requests.get(f"http://ip-api.com/json/{ip}", timeout=10)
            if response.status_code == 200:
                results['services']['ip-api'] = response.json()
        except Exception:
            pass
        
        return results
    
    @staticmethod
    def get_geolocation(ip: str) -> Dict:
        """Get IP geolocation using free services"""
        try:
            response = requests.get(f"http://ip-api.com/json/{ip}", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    return {
                        'country': data.get('country'),
                        'region': data.get('regionName'),
                        'city': data.get('city'),
                        'lat': data.get('lat'),
                        'lon': data.get('lon'),
                        'isp': data.get('isp'),
                        'org': data.get('org')
                    }
        except Exception:
            pass
        return {}

class FreeEmailValidator:
    """Free email validation and information"""
    
    @staticmethod
    def validate_email_format(email: str) -> Dict:
        """Basic email format validation"""
        import re
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        is_valid = bool(re.match(email_pattern, email))
        
        domain = email.split('@')[1] if '@' in email else ''
        
        return {
            'email': email,
            'format_valid': is_valid,
            'domain': domain,
            'local_part': email.split('@')[0] if '@' in email else '',
        }
    
    @staticmethod
    def check_mx_record(domain: str) -> Dict:
        """Check if domain has MX records"""
        try:
            mx_records = dns.resolver.resolve(domain, 'MX')
            return {
                'has_mx': True,
                'mx_records': [str(mx) for mx in mx_records]
            }
        except Exception:
            return {'has_mx': False, 'mx_records': []}

class FreeBreachChecker:
    """Free alternative to Have I Been Pwned using public breach lists"""
    
    @staticmethod
    def check_common_breaches(email: str) -> Dict:
        """Check against known public breach patterns"""
        # This is a simplified version - in practice, you'd maintain
        # a database of known breach patterns from public sources
        
        domain = email.split('@')[1] if '@' in email else ''
        
        # Common breached domains (public knowledge)
        known_breached_domains = [
            'yahoo.com', 'gmail.com', 'hotmail.com', 'linkedin.com',
            'adobe.com', 'dropbox.com', 'tumblr.com'
        ]
        
        return {
            'email': email,
            'domain_in_known_breaches': domain.lower() in known_breached_domains,
            'note': 'This is a basic check against publicly known breached domains'
        }

class FreeSocialMediaFinder:
    """Free social media profile discovery"""
    
    @staticmethod
    def generate_profile_urls(username: str) -> List[Dict]:
        """Generate common social media URLs for a username"""
        platforms = {
            'Twitter': f'https://twitter.com/{username}',
            'Instagram': f'https://instagram.com/{username}',
            'Facebook': f'https://facebook.com/{username}',
            'LinkedIn': f'https://linkedin.com/in/{username}',
            'GitHub': f'https://github.com/{username}',
            'Reddit': f'https://reddit.com/user/{username}',
            'YouTube': f'https://youtube.com/@{username}',
            'TikTok': f'https://tiktok.com/@{username}',
            'Pinterest': f'https://pinterest.com/{username}',
            'Snapchat': f'https://snapchat.com/add/{username}'
        }
        
        return [{'platform': platform, 'url': url} for platform, url in platforms.items()]
    
    @staticmethod
    def check_profile_exists(url: str, timeout: int = 10) -> bool:
        """Check if a social media profile exists (basic check)"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.head(url, headers=headers, timeout=timeout, allow_redirects=True)
            return response.status_code == 200
        except Exception:
            return False

class DNSRecon:
    """DNS reconnaissance utilities (FREE)"""
    
    @staticmethod
    def get_dns_records(domain: str) -> Dict[str, List[str]]:
        """Get various DNS records for a domain"""
        records = {
            'A': [], 'AAAA': [], 'MX': [], 'NS': [], 'TXT': [], 'CNAME': []
        }
        
        for record_type in records.keys():
            try:
                answers = dns.resolver.resolve(domain, record_type)
                records[record_type] = [str(rdata) for rdata in answers]
            except Exception:
                continue
        
        return records
    
    @staticmethod
    def reverse_dns(ip: str) -> str:
        """Perform reverse DNS lookup"""
        try:
            return str(dns.resolver.resolve_address(ip)[0])
        except Exception:
            return ""
    
    @staticmethod
    def subdomain_enumeration(domain: str, wordlist: List[str] = None) -> List[str]:
        """Basic subdomain enumeration using common subdomains"""
        if not wordlist:
            wordlist = [
                'www', 'mail', 'ftp', 'admin', 'api', 'blog', 'dev', 'test',
                'staging', 'shop', 'store', 'secure', 'vpn', 'remote', 'portal',
                'support', 'help', 'docs', 'cdn', 'static', 'assets', 'images',
                'upload', 'download', 'beta', 'demo', 'sandbox', 'app', 'mobile'
            ]
        
        found_subdomains = []
        
        for sub in wordlist:
            subdomain = f"{sub}.{domain}"
            try:
                dns.resolver.resolve(subdomain, 'A')
                found_subdomains.append(subdomain)
            except Exception:
                continue
            
            # Rate limiting to be respectful
            time.sleep(0.1)
        
        return found_subdomains
    
    @staticmethod
    def get_ssl_info(domain: str) -> Dict:
        """Get SSL certificate information"""
        try:
            context = ssl.create_default_context()
            with socket.create_connection((domain, 443), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=domain) as ssock:
                    cert = ssock.getpeercert()
                    return {
                        'subject': dict(x[0] for x in cert['subject']),
                        'issuer': dict(x[0] for x in cert['issuer']),
                        'version': cert['version'],
                        'serialNumber': cert['serialNumber'],
                        'notBefore': cert['notBefore'],
                        'notAfter': cert['notAfter'],
                        'subjectAltName': cert.get('subjectAltName', [])
                    }
        except Exception as e:
            return {'error': str(e)}

class WhoisLookup:
    """WHOIS lookup utilities (FREE)"""
    
    @staticmethod
    def domain_whois(domain: str) -> Dict:
        """Get WHOIS information for a domain"""
        try:
            w = whois.whois(domain)
            return {
                'domain_name': w.domain_name,
                'registrar': w.registrar,
                'creation_date': str(w.creation_date) if w.creation_date else None,
                'expiration_date': str(w.expiration_date) if w.expiration_date else None,
                'name_servers': w.name_servers,
                'status': w.status,
                'emails': w.emails,
                'org': w.org,
                'address': w.address,
                'city': w.city,
                'state': w.state,
                'country': w.country
            }
        except Exception as e:
            return {'error': f"WHOIS lookup failed: {str(e)}"}

class FreePortScanner:
    """Free port scanning utilities"""
    
    @staticmethod
    def scan_common_ports(host: str, timeout: int = 3) -> Dict:
        """Scan common ports on a host"""
        common_ports = [
            21, 22, 23, 25, 53, 80, 110, 143, 443, 993, 995, 
            1433, 3306, 3389, 5432, 5900, 8080, 8443
        ]
        
        open_ports = []
        closed_ports = []
        
        for port in common_ports:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(timeout)
                result = sock.connect_ex((host, port))
                sock.close()
                
                if result == 0:
                    open_ports.append(port)
                else:
                    closed_ports.append(port)
                    
            except Exception:
                closed_ports.append(port)
        
        return {
            'host': host,
            'open_ports': open_ports,
            'closed_ports': closed_ports,
            'total_scanned': len(common_ports)
        }

class LocationIntelligence:
    """Location-based intelligence gathering (FREE services only)"""
    
    @staticmethod
    def reverse_geocoding(lat: float, lon: float) -> Dict:
        """Convert coordinates to address information using free OpenStreetMap"""
        try:
            # Using OpenStreetMap Nominatim (free, no API key required)
            url = "https://nominatim.openstreetmap.org/reverse"
            params = {
                'lat': lat,
                'lon': lon,
                'format': 'json',
                'addressdetails': 1
            }
            headers = {'User-Agent': 'OSINT-Scraper-Free'}
            
            response = requests.get(url, params=params, headers=headers, timeout=30)
            if response.status_code == 200:
                return response.json()
            
        except Exception as e:
            return {'error': f"Reverse geocoding failed: {str(e)}"}
        
        return {}
    
    @staticmethod
    def nearby_places(lat: float, lon: float, radius: int = 1000) -> List[Dict]:
        """Find nearby places using free OpenStreetMap data"""
        try:
            # Using Overpass API for OpenStreetMap data (free)
            overpass_url = "http://overpass-api.de/api/interpreter"
            overpass_query = f"""
            [out:json][timeout:25];
            (
              node["amenity"](around:{radius},{lat},{lon});
              way["amenity"](around:{radius},{lat},{lon});
              relation["amenity"](around:{radius},{lat},{lon});
            );
            out body;
            """
            
            response = requests.post(overpass_url, data=overpass_query, timeout=30)
            if response.status_code == 200:
                data = response.json()
                places = []
                for element in data.get('elements', []):
                    if 'tags' in element and 'amenity' in element['tags']:
                        places.append({
                            'type': element['tags']['amenity'],
                            'name': element['tags'].get('name', 'Unknown'),
                            'lat': element.get('lat'),
                            'lon': element.get('lon')
                        })
                return places
            
        except Exception as e:
            return [{'error': f"Nearby places lookup failed: {str(e)}"}]
        
        return []

class NorfolkEventScraper:
    """Norfolk, Virginia specific event scraper for NFK Currents"""
    
    @staticmethod
    def is_norfolk_area(location_data: Dict) -> bool:
        """Check if location data indicates SPECIFICALLY Norfolk, Virginia area"""
        if not location_data:
            return False
        
        # Check reverse geocoding data
        geocoding = location_data.get('reverse_geocoding', {})
        if not geocoding:
            return False
        
        display_name = geocoding.get('display_name', '').lower()
        address_parts = geocoding.get('address', {})
        
        # Must be in Virginia first
        state = address_parts.get('state', '').lower()
        if state not in ['virginia', 'va']:
            return False
        
        # Specific Norfolk metropolitan area cities
        norfolk_metro_cities = [
            'norfolk', 'virginia beach', 'chesapeake', 'portsmouth', 
            'suffolk', 'newport news', 'hampton'
        ]
        
        # Check city specifically
        city = address_parts.get('city', '').lower()
        county = address_parts.get('county', '').lower()
        
        # Primary check: City must be in Norfolk metro area
        if any(norfolk_city in city for norfolk_city in norfolk_metro_cities):
            return True
        
        # Secondary check: Display name contains Norfolk area indicators AND Virginia
        if 'virginia' in display_name or 'va' in display_name:
            if any(norfolk_city in display_name for norfolk_city in norfolk_metro_cities):
                return True
            
            # Check for Hampton Roads region
            if 'hampton roads' in display_name:
                return True
        
        # Tertiary check: County-based (Norfolk is independent city, but check surrounding)
        norfolk_counties = ['norfolk', 'virginia beach', 'chesapeake']
        if any(norfolk_county in county for norfolk_county in norfolk_counties):
            return True
        
        return False
    
    @staticmethod
    def scrape_nfk_currents(date_filter: str = None) -> Dict:
        """Scrape events from NFK Currents website"""
        try:
            url = "https://nfk.currents.news/"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            if response.status_code != 200:
                return {'error': f'Failed to fetch NFK Currents: HTTP {response.status_code}'}
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            events = []
            current_date = datetime.now().strftime('%Y-%m-%d')
            
            # Look for event listings - adapt selectors based on site structure
            event_containers = []
            
            # Try multiple selectors to find event content
            selectors_to_try = [
                'article', '.event', '.post', '.entry', '.content-item',
                '[class*="event"]', '[class*="post"]', '[class*="article"]'
            ]
            
            for selector in selectors_to_try:
                containers = soup.select(selector)
                if containers:
                    event_containers = containers
                    break
            
            # If no specific containers found, look for general content
            if not event_containers:
                event_containers = soup.find_all(['div', 'section'], 
                                               class_=re.compile(r'(content|post|article|event)', re.I))
            
            # Extract text content and look for event-like information
            for container in event_containers[:20]:  # Limit to first 20 items
                text_content = container.get_text(strip=True)
                
                # Skip if content is too short or too long
                if len(text_content) < 50 or len(text_content) > 2000:
                    continue
                
                # Look for event indicators
                event_indicators = [
                    'event', 'concert', 'festival', 'show', 'performance',
                    'meeting', 'workshop', 'conference', 'exhibition',
                    'today', 'tonight', 'this week', 'upcoming'
                ]
                
                text_lower = text_content.lower()
                if any(indicator in text_lower for indicator in event_indicators):
                    # Try to extract title
                    title_elem = container.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                    title = title_elem.get_text(strip=True) if title_elem else text_content[:100] + '...'
                    
                    # Try to extract date/time information
                    date_patterns = [
                        r'\b\d{1,2}/\d{1,2}/\d{2,4}\b',
                        r'\b\w+\s+\d{1,2},?\s+\d{4}\b',
                        r'\b\d{1,2}\s+\w+\s+\d{4}\b',
                        r'\btoday\b|\btonight\b|\btomorrow\b',
                        r'\b\w+day\b'  # Monday, Tuesday, etc.
                    ]
                    
                    date_info = "Date not specified"
                    for pattern in date_patterns:
                        matches = re.findall(pattern, text_content, re.IGNORECASE)
                        if matches:
                            date_info = matches[0]
                            break
                    
                    # Try to extract location within Norfolk area
                    location_patterns = [
                        r'\b\d+\s+[A-Za-z\s]+(?:St|Street|Ave|Avenue|Rd|Road|Blvd|Boulevard|Dr|Drive)\b',
                        r'\bat\s+([A-Za-z\s]+)\b',
                        r'\bin\s+([A-Za-z\s]+)\b'
                    ]
                    
                    location_info = "Location not specified"
                    for pattern in location_patterns:
                        matches = re.findall(pattern, text_content, re.IGNORECASE)
                        if matches:
                            location_info = matches[0] if isinstance(matches[0], str) else matches[0][0]
                            break
                    
                    events.append({
                        'title': title,
                        'date': date_info,
                        'location': location_info,
                        'description': text_content[:300] + '...' if len(text_content) > 300 else text_content,
                        'source': 'NFK Currents'
                    })
            
            # Also try to get general news/announcements
            news_items = []
            
            # Look for headline or news elements
            headlines = soup.find_all(['h1', 'h2', 'h3'], limit=10)
            for headline in headlines:
                headline_text = headline.get_text(strip=True)
                if len(headline_text) > 20:  # Filter out very short headlines
                    # Get surrounding context
                    parent = headline.find_parent()
                    context = parent.get_text(strip=True)[:200] + '...' if parent else headline_text
                    
                    news_items.append({
                        'headline': headline_text,
                        'context': context,
                        'source': 'NFK Currents'
                    })
            
            return {
                'url': url,
                'scrape_date': current_date,
                'scrape_time': datetime.now().isoformat(),
                'events_found': len(events),
                'events': events,
                'news_items': news_items,
                'total_items': len(events) + len(news_items)
            }
            
        except requests.RequestException as e:
            return {'error': f'Network error scraping NFK Currents: {str(e)}'}
        except Exception as e:
            return {'error': f'Error scraping NFK Currents: {str(e)}'}

class OSINTUtilities:
    """OSINT utilities using only FREE services - no API keys required!"""
    
    def __init__(self, api_keys: Dict[str, str] = None):
        # Initialize free services (no API keys needed)
        self.ip_lookup = FreeIPLookup()
        self.email_validator = FreeEmailValidator()
        self.breach_checker = FreeBreachChecker()
        self.social_finder = FreeSocialMediaFinder()
        self.port_scanner = FreePortScanner()
        print("✅ Initialized OSINT utilities with FREE services only!")
    
    def comprehensive_domain_analysis(self, domain: str) -> Dict:
        """Perform comprehensive domain analysis using free services"""
        print(f"🔍 Analyzing domain: {domain}")
        
        results = {
            'domain': domain,
            'dns_records': DNSRecon.get_dns_records(domain),
            'whois': WhoisLookup.domain_whois(domain),
            'subdomains': DNSRecon.subdomain_enumeration(domain),
            'ssl_info': DNSRecon.get_ssl_info(domain)
        }
        
        # Get IP information for A records
        if results['dns_records']['A']:
            results['ip_analysis'] = {}
            for ip in results['dns_records']['A'][:3]:  # Limit to first 3 IPs
                results['ip_analysis'][ip] = {
                    'geolocation': self.ip_lookup.get_geolocation(ip),
                    'reverse_dns': DNSRecon.reverse_dns(ip),
                    'port_scan': self.port_scanner.scan_common_ports(ip)
                }
        
        return results
    
    def email_investigation(self, email: str) -> Dict:
        """Comprehensive email investigation using free services"""
        print(f"📧 Investigating email: {email}")
        
        validation = self.email_validator.validate_email_format(email)
        domain = validation['domain']
        
        results = {
            'email': email,
            'format_validation': validation,
            'domain_mx_check': self.email_validator.check_mx_record(domain) if domain else {},
            'breach_check': self.breach_checker.check_common_breaches(email),
            'domain_whois': WhoisLookup.domain_whois(domain) if domain else {}
        }
        
        return results
    
    def social_media_search(self, username: str) -> Dict:
        """Search for social media profiles using free methods"""
        print(f"👤 Searching social media for: {username}")
        
        profile_urls = self.social_finder.generate_profile_urls(username)
        results = {
            'username': username,
            'potential_profiles': profile_urls,
            'verified_profiles': []
        }
        
        # Check which profiles might exist (basic check)
        for profile in profile_urls[:5]:  # Limit to first 5 to avoid rate limiting
            if self.social_finder.check_profile_exists(profile['url']):
                results['verified_profiles'].append(profile)
            time.sleep(1)  # Be respectful with requests
        
        return results
    
    def location_analysis(self, lat: float, lon: float, investigation_results: Dict = None) -> Dict:
        """Analyze location using free services"""
        print(f"📍 Analyzing location: ({lat}, {lon})")
        
        location_data = {
            'coordinates': (lat, lon),
            'reverse_geocoding': LocationIntelligence.reverse_geocoding(lat, lon),
            'nearby_places': LocationIntelligence.nearby_places(lat, lon)
        }
        
        # Check if location is SPECIFICALLY in Norfolk, Virginia area
        if NorfolkEventScraper.is_norfolk_area(location_data):
            print("🏛️ Norfolk, VA area detected - fetching local events...")
            
            # Get raw events first
            raw_events = NorfolkEventScraper.scrape_nfk_currents()
            
            # Extract interests from OSINT investigation if available
            if investigation_results:
                print("🎯 Extracting user interests from OSINT profile...")
                user_interests = NorfolkEventScraper.extract_interests_from_osint(investigation_results)
                print(f"🎯 Detected interests: {', '.join(user_interests[:5])}{'...' if len(user_interests) > 5 else ''}")
                
                # Filter events based on interests
                filtered_events = NorfolkEventScraper.filter_events_by_interests(raw_events, user_interests)
                location_data['norfolk_events'] = filtered_events
            else:
                print("ℹ️ No OSINT data available for interest filtering, showing all events")
                location_data['norfolk_events'] = raw_events
        else:
            print("📍 Location not in Norfolk, VA area - skipping local event scraping")
        
        return location_data
    
    def get_norfolk_events(self, investigation_results: Dict = None) -> Dict:
        """Get current events in Norfolk, Virginia area with interest filtering"""
        raw_events = NorfolkEventScraper.scrape_nfk_currents()
        
        if investigation_results:
            user_interests = NorfolkEventScraper.extract_interests_from_osint(investigation_results)
            return NorfolkEventScraper.filter_events_by_interests(raw_events, user_interests)
        
        return raw_events
    
    @staticmethod
    def extract_interests_from_osint(investigation_results: Dict) -> List[str]:
        """Extract potential interests from OSINT investigation results"""
        interests = set()
        
        # Extract from social media profiles
        maigret_results = investigation_results.get('maigret_results', {})
        for username, results in maigret_results.items():
            if isinstance(results, dict):
                for platform, data in results.items():
                    if isinstance(data, dict) and data.get('status') == 'found':
                        # Add platform as potential interest
                        platform_lower = platform.lower()
                        if platform_lower in ['github', 'stackoverflow']:
                            interests.add('technology')
                            interests.add('programming')
                        elif platform_lower in ['instagram', 'flickr', 'pinterest']:
                            interests.add('photography')
                            interests.add('art')
                        elif platform_lower in ['linkedin']:
                            interests.add('professional')
                            interests.add('networking')
                        elif platform_lower in ['youtube', 'tiktok']:
                            interests.add('media')
                            interests.add('entertainment')
                        elif platform_lower in ['reddit']:
                            interests.add('community')
                            interests.add('discussion')
        
        # Extract from domain analysis (professional interests)
        additional_intel = investigation_results.get('additional_intel', {})
        domain_analysis = additional_intel.get('domain_analysis', {})
        if domain_analysis:
            domain = domain_analysis.get('domain', '').lower()
            
            # Check domain for professional/industry indicators
            if any(term in domain for term in ['tech', 'dev', 'code', 'software']):
                interests.update(['technology', 'programming', 'software'])
            elif any(term in domain for term in ['art', 'design', 'creative']):
                interests.update(['art', 'design', 'creative'])
            elif any(term in domain for term in ['music', 'band', 'sound']):
                interests.update(['music', 'entertainment'])
            elif any(term in domain for term in ['photo', 'image', 'visual']):
                interests.update(['photography', 'visual arts'])
            elif any(term in domain for term in ['biz', 'business', 'corp']):
                interests.update(['business', 'professional'])
            elif any(term in domain for term in ['edu', 'university', 'school']):
                interests.update(['education', 'academic'])
            elif any(term in domain for term in ['health', 'medical', 'wellness']):
                interests.update(['health', 'wellness'])
            elif any(term in domain for term in ['food', 'restaurant', 'culinary']):
                interests.update(['food', 'culinary'])
            elif any(term in domain for term in ['sport', 'fitness', 'gym']):
                interests.update(['sports', 'fitness'])
        
        # Extract from nearby places (location-based interests)
        location_analysis = additional_intel.get('location_analysis', {})
        nearby_places = location_analysis.get('nearby_places', [])
        
        place_type_interests = {
            'restaurant': ['food', 'culinary', 'dining'],
            'bar': ['nightlife', 'social'],
            'gym': ['fitness', 'health'],
            'school': ['education'],
            'hospital': ['health'],
            'library': ['education', 'reading'],
            'museum': ['culture', 'art', 'history'],
            'theatre': ['entertainment', 'performing arts'],
            'cinema': ['entertainment', 'movies'],
            'park': ['outdoors', 'recreation'],
            'church': ['religion', 'community'],
            'bank': ['finance'],
            'shop': ['shopping'],
            'cafe': ['coffee', 'social']
        }
        
        for place in nearby_places:
            place_type = place.get('type', '').lower()
            if place_type in place_type_interests:
                interests.update(place_type_interests[place_type])
        
        # Default interests if none found
        if not interests:
            interests.update(['general', 'community', 'local news'])
        
        return list(interests)
    
    @staticmethod
    def filter_events_by_interests(events_data: Dict, interests: List[str]) -> Dict:
        """Filter events based on user interests"""
        if not events_data or 'error' in events_data:
            return events_data
        
        # Interest keywords mapping
        interest_keywords = {
            'technology': ['tech', 'digital', 'computer', 'software', 'app', 'coding', 'programming', 'innovation', 'startup'],
            'programming': ['coding', 'developer', 'programming', 'hackathon', 'software', 'web development'],
            'art': ['art', 'gallery', 'exhibition', 'painting', 'sculpture', 'artist', 'creative', 'craft'],
            'music': ['concert', 'music', 'band', 'performance', 'jazz', 'rock', 'classical', 'symphony'],
            'entertainment': ['show', 'theater', 'movie', 'film', 'comedy', 'performance', 'festival'],
            'food': ['food', 'restaurant', 'culinary', 'cooking', 'chef', 'dining', 'wine', 'beer', 'festival'],
            'sports': ['sport', 'game', 'football', 'basketball', 'baseball', 'soccer', 'tournament', 'athletic'],
            'fitness': ['fitness', 'gym', 'workout', 'yoga', 'running', 'marathon', 'health', 'wellness'],
            'business': ['business', 'networking', 'professional', 'conference', 'seminar', 'workshop', 'entrepreneur'],
            'education': ['education', 'lecture', 'seminar', 'workshop', 'class', 'learning', 'university', 'school'],
            'community': ['community', 'neighborhood', 'local', 'volunteer', 'charity', 'fundraiser'],
            'outdoors': ['outdoor', 'park', 'nature', 'hiking', 'camping', 'beach', 'recreation'],
            'culture': ['culture', 'museum', 'history', 'heritage', 'cultural', 'tradition'],
            'photography': ['photo', 'photography', 'camera', 'visual', 'exhibition'],
            'nightlife': ['nightlife', 'bar', 'club', 'evening', 'night', 'social'],
            'religion': ['church', 'religious', 'spiritual', 'faith', 'worship', 'prayer'],
            'health': ['health', 'medical', 'wellness', 'mental health', 'support group'],
            'general': ['event', 'meeting', 'gathering', 'announcement', 'news']
        }
        
        # Create comprehensive keyword list based on interests
        relevant_keywords = set()
        for interest in interests:
            interest_lower = interest.lower()
            if interest_lower in interest_keywords:
                relevant_keywords.update(interest_keywords[interest_lower])
        
        # If no specific interests, use general keywords
        if not relevant_keywords:
            relevant_keywords = set(interest_keywords['general'] + interest_keywords['community'])
        
        # Filter events
        filtered_events = []
        original_events = events_data.get('events', [])
        
        for event in original_events:
            event_text = f"{event.get('title', '')} {event.get('description', '')}".lower()
            
            # Check if any relevant keywords are in the event
            if any(keyword in event_text for keyword in relevant_keywords):
                # Add relevance score
                relevance_score = sum(1 for keyword in relevant_keywords if keyword in event_text)
                event['relevance_score'] = relevance_score
                event['matched_interests'] = [keyword for keyword in relevant_keywords if keyword in event_text]
                filtered_events.append(event)
        
        # Sort by relevance score (highest first)
        filtered_events.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        
        # Filter news items too
        filtered_news = []
        original_news = events_data.get('news_items', [])
        
        for news in original_news:
            news_text = f"{news.get('headline', '')} {news.get('context', '')}".lower()
            
            if any(keyword in news_text for keyword in relevant_keywords):
                relevance_score = sum(1 for keyword in relevant_keywords if keyword in news_text)
                news['relevance_score'] = relevance_score
                news['matched_interests'] = [keyword for keyword in relevant_keywords if keyword in news_text]
                filtered_news.append(news)
        
        # Sort news by relevance
        filtered_news.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        
        # Create filtered results
        filtered_data = events_data.copy()
        filtered_data['events'] = filtered_events
        filtered_data['news_items'] = filtered_news
        filtered_data['events_found'] = len(filtered_events)
        filtered_data['original_events_count'] = len(original_events)
        filtered_data['original_news_count'] = len(original_news)
        filtered_data['filter_applied'] = True
        filtered_data['user_interests'] = interests
        filtered_data['matched_keywords'] = list(relevant_keywords)
        
        return filtered_data
