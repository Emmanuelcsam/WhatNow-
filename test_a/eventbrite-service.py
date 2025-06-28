"""
eventbrite_service.py - EventBrite API integration for event discovery
"""
import logging
import requests
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import pytz
from geopy.distance import geodesic
import json

logger = logging.getLogger(__name__)

@dataclass
class Event:
    """Represents an EventBrite event"""
    id: str
    name: str
    description: str
    url: str
    start_time: datetime
    end_time: datetime
    venue_name: str
    venue_address: str
    latitude: float
    longitude: float
    category: str
    subcategory: Optional[str] = None
    organizer: Optional[str] = None
    price: Optional[str] = None
    is_free: bool = False
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
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat(),
            'venue': {
                'name': self.venue_name,
                'address': self.venue_address,
                'latitude': self.latitude,
                'longitude': self.longitude
            },
            'category': self.category,
            'subcategory': self.subcategory,
            'organizer': self.organizer,
            'price': self.price,
            'is_free': self.is_free,
            'image_url': self.image_url,
            'distance_miles': round(self.distance_miles, 1) if self.distance_miles else None,
            'relevance_score': round(self.relevance_score, 2),
            'matching_interests': self.matching_interests
        }
    
    def get_time_until_start(self) -> timedelta:
        """Get time until event starts"""
        now = datetime.now(self.start_time.tzinfo)
        return self.start_time - now
    
    def is_within_time_window(self, hours: int) -> bool:
        """Check if event starts within specified hours"""
        time_until = self.get_time_until_start()
        return timedelta(0) <= time_until <= timedelta(hours=hours)

class EventBriteService:
    """Service for searching and filtering EventBrite events"""
    
    BASE_URL = "https://www.eventbriteapi.com/v3"
    
    def __init__(self, config):
        self.config = config
        self.token = config.api.eventbrite_token
        self.headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
        
        if not self.token:
            logger.error("EventBrite API token not configured")
            self.enabled = False
        else:
            self.enabled = True
    
    def search_events(self, 
                     keywords: List[str],
                     location_data: Dict,
                     interests: List[Dict],
                     radius_miles: Optional[int] = None,
                     time_window_hours: Optional[int] = None) -> List[Event]:
        """
        Search for events based on keywords and location
        
        Args:
            keywords: Search keywords from interest extraction
            location_data: User location data
            interests: User interests for relevance scoring
            radius_miles: Search radius (default from config)
            time_window_hours: Time window (default from config)
            
        Returns:
            List of Event objects
        """
        if not self.enabled:
            logger.error("EventBrite service not enabled")
            return []
        
        # Use defaults from config if not specified
        radius_miles = radius_miles or self.config.events.search_radius_miles
        time_window_hours = time_window_hours or self.config.events.time_window_hours
        
        # Get user coordinates
        user_lat = location_data.get('latitude', 0)
        user_lon = location_data.get('longitude', 0)
        user_location = (user_lat, user_lon)
        
        # Calculate time window
        timezone = pytz.timezone(location_data.get('timezone', 'UTC'))
        start_date = datetime.now(timezone)
        end_date = start_date + timedelta(hours=time_window_hours)
        
        all_events = []
        
        # Search with each keyword
        for keyword in keywords[:10]:  # Limit keywords to avoid rate limiting
            try:
                events = self._search_events_by_keyword(
                    keyword,
                    user_location,
                    start_date,
                    end_date,
                    radius_miles
                )
                all_events.extend(events)
            except Exception as e:
                logger.error(f"Error searching for keyword '{keyword}': {e}")
        
        # Also search by categories based on interests
        categories = self._get_categories_from_interests(interests)
        for category_id in categories[:5]:  # Limit categories
            try:
                events = self._search_events_by_category(
                    category_id,
                    user_location,
                    start_date,
                    end_date,
                    radius_miles
                )
                all_events.extend(events)
            except Exception as e:
                logger.error(f"Error searching category {category_id}: {e}")
        
        # Remove duplicates
        unique_events = self._deduplicate_events(all_events)
        
        # Filter by distance and time
        filtered_events = self._filter_events(
            unique_events,
            user_location,
            radius_miles,
            time_window_hours
        )
        
        # Calculate relevance scores
        scored_events = self._score_events(
            filtered_events,
            keywords,
            interests
        )
        
        # Sort by relevance and distance
        scored_events.sort(
            key=lambda e: (e.relevance_score, -e.distance_miles if e.distance_miles else 0),
            reverse=True
        )
        
        # Limit to max events
        return scored_events[:self.config.events.max_events]
    
    def _search_events_by_keyword(self, 
                                 keyword: str,
                                 user_location: Tuple[float, float],
                                 start_date: datetime,
                                 end_date: datetime,
                                 radius_miles: int) -> List[Event]:
        """Search events by keyword"""
        events = []
        
        params = {
            'q': keyword,
            'location.latitude': user_location[0],
            'location.longitude': user_location[1],
            'location.within': f'{radius_miles}mi',
            'start_date.range_start': start_date.isoformat(),
            'start_date.range_end': end_date.isoformat(),
            'expand': 'venue,organizer,category',
            'sort_by': 'date'
        }
        
        try:
            response = requests.get(
                f'{self.BASE_URL}/events/search/',
                headers=self.headers,
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                for event_data in data.get('events', []):
                    event = self._parse_event(event_data, user_location)
                    if event:
                        events.append(event)
            else:
                logger.error(f"EventBrite API error: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"EventBrite search error: {e}")
        
        return events
    
    def _search_events_by_category(self,
                                  category_id: str,
                                  user_location: Tuple[float, float],
                                  start_date: datetime,
                                  end_date: datetime,
                                  radius_miles: int) -> List[Event]:
        """Search events by category"""
        events = []
        
        params = {
            'categories': category_id,
            'location.latitude': user_location[0],
            'location.longitude': user_location[1],
            'location.within': f'{radius_miles}mi',
            'start_date.range_start': start_date.isoformat(),
            'start_date.range_end': end_date.isoformat(),
            'expand': 'venue,organizer,category',
            'sort_by': 'date'
        }
        
        try:
            response = requests.get(
                f'{self.BASE_URL}/events/search/',
                headers=self.headers,
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                for event_data in data.get('events', []):
                    event = self._parse_event(event_data, user_location)
                    if event:
                        events.append(event)
            else:
                logger.error(f"EventBrite category search error: {response.status_code}")
                
        except Exception as e:
            logger.error(f"EventBrite category search error: {e}")
        
        return events
    
    def _parse_event(self, event_data: Dict, user_location: Tuple[float, float]) -> Optional[Event]:
        """Parse event data from API response"""
        try:
            # Extract basic info
            event_id = event_data.get('id', '')
            name = event_data.get('name', {}).get('text', '')
            description = event_data.get('description', {}).get('text', '')
            url = event_data.get('url', '')
            
            # Parse dates
            start = event_data.get('start', {})
            end = event_data.get('end', {})
            
            start_time = datetime.fromisoformat(start.get('utc', '').replace('Z', '+00:00'))
            end_time = datetime.fromisoformat(end.get('utc', '').replace('Z', '+00:00'))
            
            # Parse venue
            venue = event_data.get('venue', {})
            venue_name = venue.get('name', 'Unknown Venue')
            
            address = venue.get('address', {})
            venue_address = ', '.join([
                address.get('address_1', ''),
                address.get('city', ''),
                address.get('region', ''),
                address.get('postal_code', '')
            ]).strip(', ')
            
            latitude = float(venue.get('latitude', 0) or 0)
            longitude = float(venue.get('longitude', 0) or 0)
            
            # Calculate distance
            if latitude and longitude:
                event_location = (latitude, longitude)
                distance = geodesic(user_location, event_location).miles
            else:
                distance = None
            
            # Parse category
            category = event_data.get('category', {}).get('name', 'General')
            subcategory = event_data.get('subcategory', {}).get('name') if event_data.get('subcategory') else None
            
            # Parse organizer
            organizer = event_data.get('organizer', {}).get('name', '')
            
            # Parse price
            is_free = event_data.get('is_free', False)
            price = 'Free' if is_free else 'Paid'
            
            # Get image
            logo = event_data.get('logo', {})
            image_url = logo.get('url') if logo else None
            
            return Event(
                id=event_id,
                name=name,
                description=description,
                url=url,
                start_time=start_time,
                end_time=end_time,
                venue_name=venue_name,
                venue_address=venue_address,
                latitude=latitude,
                longitude=longitude,
                category=category,
                subcategory=subcategory,
                organizer=organizer,
                price=price,
                is_free=is_free,
                image_url=image_url,
                distance_miles=distance
            )
            
        except Exception as e:
            logger.error(f"Error parsing event: {e}")
            return None
    
    def _get_categories_from_interests(self, interests: List[Dict]) -> List[str]:
        """Map interests to EventBrite category IDs"""
        # EventBrite category mapping
        category_map = {
            'music': '103',  # Music
            'arts': '105',   # Film, Media & Entertainment
            'food': '110',   # Food & Drink
            'sports': '108', # Sports & Fitness
            'technology': '102',  # Science & Technology
            'business': '101',    # Business & Professional
            'education': '115',   # Family & Education
            'health': '107',      # Health & Wellness
            'community': '113',   # Community & Culture
            'entertainment': '104',  # Film & Media
            'travel': '109',         # Travel & Outdoor
            'hobbies': '119'         # Hobbies & Special Interest
        }
        
        categories = set()
        
        for interest in interests:
            interest_category = interest.get('category', '').lower()
            if interest_category in category_map:
                categories.add(category_map[interest_category])
        
        # Add default categories if none found
        if not categories:
            categories.update(['103', '110', '113'])  # Music, Food, Community
        
        return list(categories)
    
    def _deduplicate_events(self, events: List[Event]) -> List[Event]:
        """Remove duplicate events"""
        seen = set()
        unique = []
        
        for event in events:
            if event.id not in seen:
                seen.add(event.id)
                unique.append(event)
        
        return unique
    
    def _filter_events(self, 
                      events: List[Event],
                      user_location: Tuple[float, float],
                      radius_miles: int,
                      time_window_hours: int) -> List[Event]:
        """Filter events by distance and time"""
        filtered = []
        
        for event in events:
            # Check time window
            if not event.is_within_time_window(time_window_hours):
                continue
            
            # Check distance if coordinates available
            if event.latitude and event.longitude:
                if event.distance_miles is not None and event.distance_miles > radius_miles:
                    continue
            
            filtered.append(event)
        
        return filtered
    
    def _score_events(self, 
                     events: List[Event],
                     keywords: List[str],
                     interests: List[Dict]) -> List[Event]:
        """Calculate relevance scores for events"""
        for event in events:
            score = 0.0
            matching_interests = []
            
            # Create searchable text
            event_text = f"{event.name} {event.description} {event.category}".lower()
            
            # Score based on keyword matches
            for keyword in keywords:
                if keyword.lower() in event_text:
                    score += 0.2
                    matching_interests.append(keyword)
            
            # Score based on interest category matches
            for interest in interests:
                interest_keyword = interest.get('keyword', '').lower()
                interest_category = interest.get('category', '').lower()
                confidence = interest.get('confidence', 0.5)
                
                if interest_keyword in event_text:
                    score += 0.3 * confidence
                    matching_interests.append(interest_keyword)
                
                if interest_category in event.category.lower():
                    score += 0.2 * confidence
            
            # Distance scoring (closer is better)
            if event.distance_miles is not None:
                distance_score = 1.0 - (event.distance_miles / self.config.events.search_radius_miles)
                score += 0.2 * max(0, distance_score)
            
            # Time scoring (sooner is better)
            hours_until = event.get_time_until_start().total_seconds() / 3600
            if hours_until > 0:
                time_score = 1.0 - (hours_until / self.config.events.time_window_hours)
                score += 0.1 * max(0, time_score)
            
            # Free event bonus
            if event.is_free:
                score += 0.1
            
            # Cap score at 1.0
            event.relevance_score = min(1.0, score)
            event.matching_interests = list(set(matching_interests))
        
        return events
    
    def get_event_details(self, event_id: str) -> Optional[Dict]:
        """Get detailed information about a specific event"""
        if not self.enabled:
            return None
        
        try:
            response = requests.get(
                f'{self.BASE_URL}/events/{event_id}/',
                headers=self.headers,
                params={'expand': 'venue,organizer,category,ticket_classes'},
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Error fetching event {event_id}: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching event details: {e}")
            return None
    
    def format_events_for_display(self, events: List[Event]) -> List[Dict]:
        """Format events for display in UI"""
        formatted = []
        
        for event in events:
            # Format time
            time_str = event.start_time.strftime('%I:%M %p')
            date_str = event.start_time.strftime('%b %d')
            
            # Get time until event
            time_until = event.get_time_until_start()
            hours = int(time_until.total_seconds() / 3600)
            minutes = int((time_until.total_seconds() % 3600) / 60)
            
            if hours > 0:
                time_until_str = f"{hours}h {minutes}m"
            else:
                time_until_str = f"{minutes}m"
            
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
                'coordinates': {
                    'lat': event.latitude,
                    'lng': event.longitude
                },
                'matching_interests': event.matching_interests
            })
        
        return formatted
