"""
free_events_service.py - Free event discovery service to replace EventBrite
Aggregates events from multiple free sources without requiring API keys
"""
import logging
import requests
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
import re
from bs4 import BeautifulSoup
from urllib.parse import quote_plus, urlencode
import time
from geopy.distance import geodesic
import pytz
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

@dataclass
class Event:
    """Represents an event from any source"""
    id: str
    name: str
    description: str
    url: str
    start_time: datetime
    end_time: Optional[datetime]
    venue_name: str
    venue_address: str
    latitude: Optional[float]
    longitude: Optional[float]
    category: str
    source: str  # google, meetup, facebook, etc.
    price: Optional[str] = None
    is_free: bool = True
    image_url: Optional[str] = None
    distance_miles: Optional[float] = None
    relevance_score: float = 0.0
    matching_interests: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description[:200] + '...' if len(self.description) > 200 else self.description,
            'url': self.url,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'venue': {
                'name': self.venue_name,
                'address': self.venue_address,
                'latitude': self.latitude,
                'longitude': self.longitude
            },
            'category': self.category,
            'source': self.source,
            'price': self.price,
            'is_free': self.is_free,
            'image_url': self.image_url,
            'distance_miles': round(self.distance_miles, 1) if self.distance_miles else None,
            'relevance_score': round(self.relevance_score, 2),
            'matching_interests': self.matching_interests
        }

class GoogleEventsService:
    """Scrape Google Events without API key"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9'
        }
    
    def search_events(self, keywords: List[str], location: str, 
                     date_range: Optional[Tuple[datetime, datetime]] = None) -> List[Event]:
        """Search Google Events for local events"""
        events = []
        
        # Build search queries
        for keyword in keywords[:5]:  # Limit to avoid rate limiting
            query = f"{keyword} events near {location}"
            
            try:
                # Search Google Events
                events_url = f"https://www.google.com/search?q={quote_plus(query)}&tbm=evts"
                
                response = requests.get(events_url, headers=self.headers, timeout=10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Parse event cards - Google's structure may vary
                    event_cards = soup.find_all('div', {'class': re.compile(r'event|listing', re.I)})
                    
                    for card in event_cards[:10]:  # Limit per search
                        event = self._parse_event_card(card, keyword)
                        if event:
                            events.append(event)
                
                time.sleep(1)  # Rate limiting
                
            except Exception as e:
                logger.error(f"Google Events search error for '{keyword}': {e}")
        
        return events
    
    def _parse_event_card(self, card, keyword: str) -> Optional[Event]:
        """Parse a Google Events card"""
        try:
            # Extract event details (structure may vary)
            title = card.find(['h3', 'h4', 'a'])
            if not title:
                return None
            
            event_name = title.get_text(strip=True)
            
            # Extract date/time
            date_elem = card.find(text=re.compile(r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\b'))
            start_time = datetime.now()  # Default
            
            if date_elem:
                try:
                    # Parse date string
                    date_str = date_elem.strip()
                    # Simple parsing - would need more robust solution
                    start_time = datetime.now() + timedelta(days=7)  # Placeholder
                except:
                    pass
            
            # Extract venue
            venue_elem = card.find(text=re.compile(r'at |@'))
            venue_name = "Venue TBD"
            if venue_elem:
                venue_name = venue_elem.split('at')[-1].strip()
            
            # Extract URL
            link = card.find('a', href=True)
            event_url = link['href'] if link else "#"
            if event_url.startswith('/'):
                event_url = f"https://www.google.com{event_url}"
            
            # Create event
            return Event(
                id=f"google_{hash(event_name)}",
                name=event_name,
                description=f"Event found for: {keyword}",
                url=event_url,
                start_time=start_time,
                end_time=None,
                venue_name=venue_name,
                venue_address="",
                latitude=None,
                longitude=None,
                category=self._categorize_event(event_name, keyword),
                source="google_events",
                is_free=True
            )
            
        except Exception as e:
            logger.debug(f"Error parsing Google event card: {e}")
            return None
    
    def _categorize_event(self, event_name: str, keyword: str) -> str:
        """Categorize event based on name and keyword"""
        categories = {
            'music': ['concert', 'music', 'band', 'dj', 'festival'],
            'sports': ['game', 'match', 'race', 'sports', 'fitness'],
            'arts': ['art', 'gallery', 'exhibition', 'museum', 'theater'],
            'food': ['food', 'taste', 'restaurant', 'culinary', 'wine'],
            'technology': ['tech', 'hackathon', 'coding', 'startup'],
            'community': ['meetup', 'networking', 'social', 'volunteer'],
            'education': ['workshop', 'class', 'seminar', 'lecture']
        }
        
        event_lower = event_name.lower()
        keyword_lower = keyword.lower()
        
        for category, terms in categories.items():
            for term in terms:
                if term in event_lower or term in keyword_lower:
                    return category
        
        return 'general'

class MeetupService:
    """Meetup API integration (optional - requires API key)"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.enabled = bool(api_key)
        self.base_url = "https://api.meetup.com"
        self.headers = {
            'Authorization': f'Bearer {api_key}' if api_key else '',
            'Content-Type': 'application/json'
        }
    
    def search_events(self, keywords: List[str], location: Dict,
                     radius_miles: int = 25) -> List[Event]:
        """Search Meetup events using GraphQL API"""
        if not self.enabled:
            return []
        
        events = []
        
        for keyword in keywords[:3]:
            try:
                # GraphQL query for event search
                query = """
                query($filter: SearchConnectionFilter!) {
                    keywordSearch(filter: $filter) {
                        edges {
                            node {
                                ... on Event {
                                    id
                                    title
                                    eventUrl
                                    description
                                    dateTime
                                    endTime
                                    venue {
                                        name
                                        address
                                        lat
                                        lng
                                    }
                                    group {
                                        name
                                    }
                                }
                            }
                        }
                    }
                }
                """
                
                variables = {
                    "filter": {
                        "query": keyword,
                        "lat": location.get('latitude', 0),
                        "lon": location.get('longitude', 0),
                        "radius": radius_miles,
                        "source": "EVENTS"
                    }
                }
                
                response = requests.post(
                    f"{self.base_url}/gql",
                    headers=self.headers,
                    json={"query": query, "variables": variables},
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    for edge in data.get('data', {}).get('keywordSearch', {}).get('edges', []):
                        node = edge.get('node', {})
                        if node:
                            event = self._parse_meetup_event(node, location)
                            if event:
                                events.append(event)
                
            except Exception as e:
                logger.error(f"Meetup search error: {e}")
        
        return events
    
    def _parse_meetup_event(self, event_data: Dict, user_location: Dict) -> Optional[Event]:
        """Parse Meetup event data"""
        try:
            venue = event_data.get('venue', {})
            
            # Calculate distance if coordinates available
            distance = None
            lat = venue.get('lat')
            lng = venue.get('lng')
            
            if lat and lng and user_location:
                event_loc = (lat, lng)
                user_loc = (user_location['latitude'], user_location['longitude'])
                distance = geodesic(user_loc, event_loc).miles
            
            return Event(
                id=f"meetup_{event_data['id']}",
                name=event_data['title'],
                description=event_data.get('description', ''),
                url=event_data['eventUrl'],
                start_time=datetime.fromisoformat(event_data['dateTime'].replace('Z', '+00:00')),
                end_time=datetime.fromisoformat(event_data['endTime'].replace('Z', '+00:00')) if event_data.get('endTime') else None,
                venue_name=venue.get('name', 'TBD'),
                venue_address=venue.get('address', ''),
                latitude=lat,
                longitude=lng,
                category='community',
                source='meetup',
                distance_miles=distance
            )
            
        except Exception as e:
            logger.error(f"Error parsing Meetup event: {e}")
            return None

class FacebookEventsService:
    """Scrape public Facebook events (limited functionality)"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    def search_events(self, keywords: List[str], location: str) -> List[Event]:
        """Search Facebook events (limited without API)"""
        events = []
        
        # Facebook search is limited without API
        # This is a basic implementation that may need updates
        for keyword in keywords[:2]:
            try:
                # Try mobile Facebook which sometimes has simpler structure
                search_url = f"https://m.facebook.com/events/search/?q={quote_plus(f'{keyword} {location}')}"
                
                response = requests.get(search_url, headers=self.headers, timeout=10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Parse event listings (structure varies)
                    event_links = soup.find_all('a', href=re.compile(r'/events/\d+'))
                    
                    for link in event_links[:5]:
                        event = self._parse_facebook_event(link)
                        if event:
                            events.append(event)
                
                time.sleep(2)  # Be respectful
                
            except Exception as e:
                logger.debug(f"Facebook events search error: {e}")
        
        return events
    
    def _parse_facebook_event(self, link_elem) -> Optional[Event]:
        """Parse Facebook event from link element"""
        try:
            event_url = f"https://facebook.com{link_elem['href']}"
            event_name = link_elem.get_text(strip=True)
            
            if not event_name:
                return None
            
            return Event(
                id=f"facebook_{hash(event_url)}",
                name=event_name,
                description="Facebook event",
                url=event_url,
                start_time=datetime.now() + timedelta(days=7),  # Placeholder
                end_time=None,
                venue_name="See event page",
                venue_address="",
                latitude=None,
                longitude=None,
                category='general',
                source='facebook'
            )
            
        except Exception as e:
            logger.debug(f"Error parsing Facebook event: {e}")
            return None

class LocalEventAggregator:
    """Aggregate events from local event websites"""
    
    def __init__(self):
        self.local_sources = {
            'eventful': self._scrape_eventful,
            'allevents': self._scrape_allevents,
            'yelp': self._scrape_yelp_events
        }
    
    def search_events(self, keywords: List[str], location: str) -> List[Event]:
        """Search multiple local event sources"""
        events = []
        
        for source_name, scraper_func in self.local_sources.items():
            try:
                source_events = scraper_func(keywords, location)
                events.extend(source_events)
            except Exception as e:
                logger.debug(f"Error scraping {source_name}: {e}")
        
        return events
    
    def _scrape_eventful(self, keywords: List[str], location: str) -> List[Event]:
        """Scrape Eventful.com"""
        events = []
        
        for keyword in keywords[:2]:
            try:
                search_url = f"https://www.eventful.com/events?q={quote_plus(keyword)}&l={quote_plus(location)}"
                
                response = requests.get(search_url, timeout=10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Parse event listings
                    event_items = soup.find_all('li', class_='event-item')
                    
                    for item in event_items[:5]:
                        title_elem = item.find('h3', class_='event-title')
                        if title_elem:
                            events.append(Event(
                                id=f"eventful_{hash(title_elem.text)}",
                                name=title_elem.get_text(strip=True),
                                description="",
                                url=title_elem.find('a')['href'] if title_elem.find('a') else "#",
                                start_time=datetime.now() + timedelta(days=7),
                                end_time=None,
                                venue_name="TBD",
                                venue_address=location,
                                latitude=None,
                                longitude=None,
                                category='general',
                                source='eventful'
                            ))
                
            except Exception as e:
                logger.debug(f"Eventful scraping error: {e}")
        
        return events
    
    def _scrape_allevents(self, keywords: List[str], location: str) -> List[Event]:
        """Scrape AllEvents.in"""
        events = []
        
        try:
            # AllEvents uses a different URL structure
            location_slug = location.lower().replace(' ', '-').replace(',', '')
            
            for keyword in keywords[:2]:
                search_url = f"https://allevents.in/{location_slug}/{keyword}"
                
                response = requests.get(search_url, timeout=10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Parse event cards
                    event_cards = soup.find_all('div', class_='event-card')
                    
                    for card in event_cards[:5]:
                        title = card.find(['h3', 'h4', 'a'])
                        if title:
                            events.append(Event(
                                id=f"allevents_{hash(title.text)}",
                                name=title.get_text(strip=True),
                                description="",
                                url="#",
                                start_time=datetime.now() + timedelta(days=7),
                                end_time=None,
                                venue_name="TBD",
                                venue_address=location,
                                latitude=None,
                                longitude=None,
                                category='general',
                                source='allevents'
                            ))
        
        except Exception as e:
            logger.debug(f"AllEvents scraping error: {e}")
        
        return events
    
    def _scrape_yelp_events(self, keywords: List[str], location: str) -> List[Event]:
        """Scrape Yelp Events"""
        events = []
        
        try:
            base_url = "https://www.yelp.com/events"
            params = {
                'find_desc': ' '.join(keywords[:2]),
                'find_loc': location
            }
            
            response = requests.get(base_url, params=params, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Parse Yelp event structure
                event_items = soup.find_all('div', {'class': re.compile(r'event-item|listing', re.I)})
                
                for item in event_items[:5]:
                    title = item.find(['h3', 'h4', 'a'])
                    if title:
                        events.append(Event(
                            id=f"yelp_{hash(title.text)}",
                            name=title.get_text(strip=True),
                            description="",
                            url="#",
                            start_time=datetime.now() + timedelta(days=7),
                            end_time=None,
                            venue_name="TBD",
                            venue_address=location,
                            latitude=None,
                            longitude=None,
                            category='general',
                            source='yelp'
                        ))
        
        except Exception as e:
            logger.debug(f"Yelp events scraping error: {e}")
        
        return events


class FreeEventDiscoveryService:
    """Main service that aggregates events from all free sources"""
    
    def __init__(self, config):
        self.config = config
        
        # Initialize services
        self.google_events = GoogleEventsService()
        self.meetup = MeetupService(config.api.meetup_api_key if hasattr(config.api, 'meetup_api_key') else None)
        self.facebook_events = FacebookEventsService()
        self.local_aggregator = LocalEventAggregator()
        
        # Service weights for relevance scoring
        self.source_weights = {
            'google_events': 1.0,
            'meetup': 0.9,
            'facebook': 0.7,
            'eventful': 0.6,
            'allevents': 0.5,
            'yelp': 0.5
        }
    
    async def search_events_async(self, 
                                 keywords: List[str],
                                 location_data: Dict,
                                 interests: List[Dict],
                                 radius_miles: int = 25,
                                 time_window_hours: int = 168) -> List[Event]:
        """Asynchronously search all event sources"""
        
        # Prepare location string
        location_str = f"{location_data.get('city', '')}, {location_data.get('region', '')}"
        
        # Create tasks for each service
        tasks = []
        
        # Google Events
        tasks.append(asyncio.create_task(
            asyncio.to_thread(self.google_events.search_events, keywords, location_str)
        ))
        
        # Meetup (if enabled)
        if self.meetup.enabled:
            tasks.append(asyncio.create_task(
                asyncio.to_thread(self.meetup.search_events, keywords, location_data, radius_miles)
            ))
        
        # Facebook Events
        tasks.append(asyncio.create_task(
            asyncio.to_thread(self.facebook_events.search_events, keywords[:3], location_str)
        ))
        
        # Local aggregator
        tasks.append(asyncio.create_task(
            asyncio.to_thread(self.local_aggregator.search_events, keywords[:3], location_str)
        ))
        
        # Wait for all tasks
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine results
        all_events = []
        for result in results:
            if isinstance(result, list):
                all_events.extend(result)
            elif isinstance(result, Exception):
                logger.error(f"Event search error: {result}")
        
        # Process and filter events
        unique_events = self._deduplicate_events(all_events)
        filtered_events = self._filter_events(unique_events, location_data, radius_miles, time_window_hours)
        scored_events = self._score_events(filtered_events, keywords, interests)
        
        # Sort by relevance
        scored_events.sort(key=lambda e: (e.relevance_score, -e.distance_miles if e.distance_miles else 0), reverse=True)
        
        return scored_events[:self.config.events.max_events]
    
    def search_events(self, 
                     keywords: List[str],
                     location_data: Dict,
                     interests: List[Dict],
                     radius_miles: int = 25,
                     time_window_hours: int = 168) -> List[Event]:
        """Synchronous version of event search"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            return loop.run_until_complete(
                self.search_events_async(keywords, location_data, interests, radius_miles, time_window_hours)
            )
        finally:
            loop.close()
    
    def _deduplicate_events(self, events: List[Event]) -> List[Event]:
        """Remove duplicate events based on name and venue"""
        seen = set()
        unique = []
        
        for event in events:
            # Create signature based on name and venue
            sig = f"{event.name.lower()[:30]}_{event.venue_name.lower()[:20]}"
            
            if sig not in seen:
                seen.add(sig)
                unique.append(event)
        
        return unique
    
    def _filter_events(self, events: List[Event], location_data: Dict, 
                      radius_miles: int, time_window_hours: int) -> List[Event]:
        """Filter events by distance and time"""
        filtered = []
        user_location = (location_data['latitude'], location_data['longitude'])
        timezone = pytz.timezone(location_data.get('timezone', 'UTC'))
        
        now = datetime.now(timezone)
        window_end = now + timedelta(hours=time_window_hours)
        
        for event in events:
            # Check time window
            if event.start_time:
                # Make timezone aware if needed
                if event.start_time.tzinfo is None:
                    event.start_time = timezone.localize(event.start_time)
                
                if event.start_time < now or event.start_time > window_end:
                    continue
            
            # Calculate distance if not already done
            if event.latitude and event.longitude and event.distance_miles is None:
                event_location = (event.latitude, event.longitude)
                event.distance_miles = geodesic(user_location, event_location).miles
            
            # Check distance if available
            if event.distance_miles and event.distance_miles > radius_miles:
                continue
            
            filtered.append(event)
        
        return filtered
    
    def _score_events(self, events: List[Event], keywords: List[str], interests: List[Dict]) -> List[Event]:
        """Calculate relevance scores for events"""
        for event in events:
            score = 0.0
            matching_interests = []
            
            # Base score from source reliability
            source_weight = self.source_weights.get(event.source, 0.5)
            score += 0.2 * source_weight
            
            # Create searchable text
            event_text = f"{event.name} {event.description} {event.category}".lower()
            
            # Score based on keyword matches
            for keyword in keywords:
                if keyword.lower() in event_text:
                    score += 0.15
                    matching_interests.append(keyword)
            
            # Score based on interest matches
            for interest in interests:
                interest_keyword = interest.get('keyword', '').lower()
                interest_category = interest.get('category', '').lower()
                confidence = interest.get('confidence', 0.5)
                
                if interest_keyword in event_text:
                    score += 0.2 * confidence
                    matching_interests.append(interest_keyword)
                
                if interest_category == event.category:
                    score += 0.15 * confidence
            
            # Distance scoring (if available)
            if event.distance_miles is not None:
                distance_score = 1.0 - (event.distance_miles / 50)  # Normalize to 50 miles
                score += 0.15 * max(0, distance_score)
            
            # Time scoring (sooner is better)
            if event.start_time:
                hours_until = (event.start_time - datetime.now(event.start_time.tzinfo)).total_seconds() / 3600
                if hours_until > 0:
                    time_score = 1.0 - (hours_until / 168)  # Normalize to 1 week
                    score += 0.1 * max(0, time_score)
            
            # Free event bonus
            if event.is_free:
                score += 0.1
            
            # Cap score at 1.0
            event.relevance_score = min(1.0, score)
            event.matching_interests = list(set(matching_interests))
        
        return events
    
    def format_events_for_display(self, events: List[Event]) -> List[Dict]:
        """Format events for display in UI"""
        formatted = []
        
        for event in events:
            # Format time
            if event.start_time:
                time_str = event.start_time.strftime('%I:%M %p')
                date_str = event.start_time.strftime('%b %d')
                
                # Get time until event
                if event.start_time.tzinfo:
                    time_until = event.start_time - datetime.now(event.start_time.tzinfo)
                else:
                    time_until = event.start_time - datetime.now()
                
                hours = int(time_until.total_seconds() / 3600)
                minutes = int((time_until.total_seconds() % 3600) / 60)
                
                if hours > 0:
                    time_until_str = f"{hours}h {minutes}m"
                else:
                    time_until_str = f"{minutes}m"
            else:
                time_str = "TBD"
                date_str = "TBD"
                time_until_str = "TBD"
            
            formatted.append({
                'id': event.id,
                'name': event.name,
                'time': time_str,
                'date': date_str,
                'time_until': time_until_str,
                'venue': event.venue_name,
                'distance': f"{event.distance_miles:.1f} mi" if event.distance_miles else "Unknown",
                'category': event.category,
                'is_free': event.is_free,
                'relevance': f"{int(event.relevance_score * 100)}%",
                'url': event.url,
                'source': event.source,
                'coordinates': {
                    'lat': event.latitude,
                    'lng': event.longitude
                } if event.latitude and event.longitude else None,
                'matching_interests': event.matching_interests
            })
        
        return formatted
