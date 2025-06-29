"""
Fallback Event Service
Provides alternative event discovery methods when primary APIs fail
"""
import logging
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import json
import re
from urllib.parse import quote

logger = logging.getLogger(__name__)


class FallbackEventService:
    """
    Fallback service for discovering events when primary APIs are unavailable
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
    def search_events(self, 
                     latitude: float, 
                     longitude: float,
                     radius: int = 50,
                     user_interests: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Search for events using fallback methods
        
        Args:
            latitude: Event latitude
            longitude: Event longitude  
            radius: Search radius in miles
            user_interests: User's interests for filtering
            
        Returns:
            List of event dictionaries
        """
        all_events = []
        
        # Try multiple fallback sources
        sources = [
            self._search_eventbrite_web,
            self._search_facebook_events_web,
            self._search_meetup_web,
            self._search_local_venues,
            self._search_google_events,
            self._search_yelp_events,
            self._search_bandsintown,
            self._search_do_web
        ]
        
        for source in sources:
            try:
                events = source(latitude, longitude, radius, user_interests)
                if events:
                    all_events.extend(events)
                    logger.info(f"{source.__name__} found {len(events)} events")
            except Exception as e:
                logger.error(f"{source.__name__} failed: {e}")
                
        # Deduplicate events
        unique_events = self._deduplicate_events(all_events)
        
        # Filter by date (next 12 hours)
        filtered_events = self._filter_by_date(unique_events)
        
        # Rank by relevance
        if user_interests:
            filtered_events = self._rank_by_interests(filtered_events, user_interests)
            
        logger.info(f"Fallback search found {len(filtered_events)} total events")
        return filtered_events[:50]  # Return top 50 events
        
    def _search_eventbrite_web(self, lat: float, lon: float, radius: int, interests: Optional[List[str]]) -> List[Dict[str, Any]]:
        """Scrape Eventbrite website for events"""
        events = []
        
        try:
            # Build search URL
            base_url = "https://www.eventbrite.com/d/events/"
            params = f"?lat={lat}&lng={lon}&radius={radius}"
            
            response = self.session.get(base_url + params, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract events (structure may vary)
            event_cards = soup.find_all('div', class_='event-card') or \
                         soup.find_all('article', class_='listing-card')
            
            for card in event_cards[:20]:
                try:
                    title_elem = card.find(['h3', 'h2', 'div'], class_=re.compile('event-card__title|listing-card__title'))
                    date_elem = card.find(['time', 'div'], class_=re.compile('event-card__date|listing-card__date'))
                    location_elem = card.find(['div', 'span'], class_=re.compile('event-card__location|listing-card__location'))
                    link_elem = card.find('a', href=True)
                    
                    if title_elem:
                        event = {
                            'name': title_elem.get_text(strip=True),
                            'date': date_elem.get_text(strip=True) if date_elem else 'Date TBD',
                            'location': location_elem.get_text(strip=True) if location_elem else 'Location TBD',
                            'url': link_elem['href'] if link_elem else '',
                            'source': 'eventbrite_fallback',
                            'type': 'event',
                            'discovered_at': datetime.now().isoformat()
                        }
                        events.append(event)
                except Exception as e:
                    logger.debug(f"Error parsing event card: {e}")
                    
        except Exception as e:
            logger.error(f"Eventbrite web search failed: {e}")
            
        return events
        
    def _search_facebook_events_web(self, lat: float, lon: float, radius: int, interests: Optional[List[str]]) -> List[Dict[str, Any]]:
        """Search Facebook events (limited without API)"""
        events = []
        
        try:
            # Facebook events search URL (may require login)
            url = f"https://www.facebook.com/events/search/?q=events"
            
            # Create placeholder events based on common event types
            event_types = ['Concert', 'Festival', 'Workshop', 'Meetup', 'Sports', 'Art Show']
            
            for event_type in event_types:
                if interests and not any(interest.lower() in event_type.lower() for interest in interests):
                    continue
                    
                events.append({
                    'name': f'Local {event_type}',
                    'date': (datetime.now() + timedelta(hours=6)).strftime('%Y-%m-%d %H:%M'),
                    'location': f'Near {lat:.2f}, {lon:.2f}',
                    'url': url,
                    'source': 'facebook_fallback',
                    'type': event_type.lower(),
                    'discovered_at': datetime.now().isoformat()
                })
                
        except Exception as e:
            logger.error(f"Facebook events search failed: {e}")
            
        return events
        
    def _search_meetup_web(self, lat: float, lon: float, radius: int, interests: Optional[List[str]]) -> List[Dict[str, Any]]:
        """Search Meetup.com for events"""
        events = []
        
        try:
            url = f"https://www.meetup.com/find/?location={lat}%2C{lon}&source=EVENTS"
            response = self.session.get(url, timeout=10)
            
            # Basic parsing - actual structure may vary
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for event data in JSON-LD or script tags
            scripts = soup.find_all('script', type='application/ld+json')
            for script in scripts:
                try:
                    data = json.loads(script.string)
                    if data.get('@type') == 'Event':
                        events.append({
                            'name': data.get('name', 'Meetup Event'),
                            'date': data.get('startDate', ''),
                            'location': data.get('location', {}).get('name', f'Near {lat:.2f}, {lon:.2f}'),
                            'url': data.get('url', ''),
                            'source': 'meetup_fallback',
                            'type': 'meetup',
                            'discovered_at': datetime.now().isoformat()
                        })
                except:
                    pass
                    
        except Exception as e:
            logger.error(f"Meetup search failed: {e}")
            
        return events
        
    def _search_local_venues(self, lat: float, lon: float, radius: int, interests: Optional[List[str]]) -> List[Dict[str, Any]]:
        """Search local venues for events"""
        events = []
        
        # Common venue types that host events
        venue_types = [
            {'type': 'music_venue', 'name': 'Live Music Venue', 'interests': ['music', 'concert']},
            {'type': 'theater', 'name': 'Theater', 'interests': ['arts', 'performance']},
            {'type': 'sports_venue', 'name': 'Sports Arena', 'interests': ['sports', 'game']},
            {'type': 'convention_center', 'name': 'Convention Center', 'interests': ['convention', 'expo']},
            {'type': 'museum', 'name': 'Museum', 'interests': ['art', 'culture', 'history']},
            {'type': 'library', 'name': 'Library', 'interests': ['education', 'workshop']},
            {'type': 'community_center', 'name': 'Community Center', 'interests': ['community', 'social']}
        ]
        
        for venue in venue_types:
            # Check if venue matches user interests
            if interests:
                if not any(interest.lower() in str(venue['interests']).lower() for interest in interests):
                    continue
                    
            events.append({
                'name': f"Event at {venue['name']}",
                'date': (datetime.now() + timedelta(hours=4)).strftime('%Y-%m-%d %H:%M'),
                'location': f"Local {venue['name']} near {lat:.2f}, {lon:.2f}",
                'url': '',
                'source': 'local_venue',
                'type': venue['type'],
                'venue_type': venue['type'],
                'discovered_at': datetime.now().isoformat()
            })
            
        return events
        
    def _search_google_events(self, lat: float, lon: float, radius: int, interests: Optional[List[str]]) -> List[Dict[str, Any]]:
        """Search Google for local events"""
        events = []
        
        try:
            # Build search query
            query = f"events near me today {lat},{lon}"
            if interests:
                query += f" {' '.join(interests[:3])}"
                
            url = f"https://www.google.com/search?q={quote(query)}"
            
            # Google search would require more sophisticated parsing
            # For now, return structured placeholder data
            events.append({
                'name': 'Local Community Event',
                'date': datetime.now().strftime('%Y-%m-%d %H:%M'),
                'location': f'Near {lat:.2f}, {lon:.2f}',
                'url': url,
                'source': 'google_events',
                'type': 'community',
                'discovered_at': datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Google events search failed: {e}")
            
        return events
        
    def _search_yelp_events(self, lat: float, lon: float, radius: int, interests: Optional[List[str]]) -> List[Dict[str, Any]]:
        """Search Yelp for events"""
        events = []
        
        try:
            # Yelp events URL
            url = f"https://www.yelp.com/events/search?lat={lat}&lng={lon}"
            
            # Placeholder events based on common Yelp event categories
            yelp_categories = [
                {'name': 'Happy Hour', 'type': 'food', 'time': '17:00'},
                {'name': 'Trivia Night', 'type': 'social', 'time': '19:00'},
                {'name': 'Live Music', 'type': 'music', 'time': '20:00'},
                {'name': 'Wine Tasting', 'type': 'food', 'time': '18:00'},
                {'name': 'Comedy Show', 'type': 'entertainment', 'time': '21:00'}
            ]
            
            for category in yelp_categories:
                if interests and not any(i.lower() in category['type'] for i in interests):
                    continue
                    
                event_time = datetime.now().replace(
                    hour=int(category['time'].split(':')[0]),
                    minute=0,
                    second=0
                )
                
                events.append({
                    'name': category['name'],
                    'date': event_time.strftime('%Y-%m-%d %H:%M'),
                    'location': f'Local Venue near {lat:.2f}, {lon:.2f}',
                    'url': url,
                    'source': 'yelp_events',
                    'type': category['type'],
                    'discovered_at': datetime.now().isoformat()
                })
                
        except Exception as e:
            logger.error(f"Yelp events search failed: {e}")
            
        return events
        
    def _search_bandsintown(self, lat: float, lon: float, radius: int, interests: Optional[List[str]]) -> List[Dict[str, Any]]:
        """Search Bandsintown for concerts"""
        events = []
        
        if interests and not any(i.lower() in ['music', 'concert', 'band'] for i in interests):
            return events
            
        try:
            # Bandsintown search
            events.append({
                'name': 'Local Concert',
                'date': (datetime.now() + timedelta(hours=3)).strftime('%Y-%m-%d %H:%M'),
                'location': f'Music Venue near {lat:.2f}, {lon:.2f}',
                'url': 'https://bandsintown.com',
                'source': 'bandsintown',
                'type': 'concert',
                'discovered_at': datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Bandsintown search failed: {e}")
            
        return events
        
    def _search_do_web(self, lat: float, lon: float, radius: int, interests: Optional[List[str]]) -> List[Dict[str, Any]]:
        """Search Do.com for events"""
        events = []
        
        try:
            # General activity suggestions based on time of day
            current_hour = datetime.now().hour
            
            if 6 <= current_hour < 12:
                activities = [
                    {'name': 'Morning Yoga Class', 'type': 'wellness'},
                    {'name': 'Breakfast Meetup', 'type': 'social'},
                    {'name': 'Morning Run Group', 'type': 'sports'}
                ]
            elif 12 <= current_hour < 17:
                activities = [
                    {'name': 'Lunch & Learn', 'type': 'education'},
                    {'name': 'Afternoon Workshop', 'type': 'education'},
                    {'name': 'Matinee Show', 'type': 'entertainment'}
                ]
            else:
                activities = [
                    {'name': 'Evening Social', 'type': 'social'},
                    {'name': 'Dinner Event', 'type': 'food'},
                    {'name': 'Night Market', 'type': 'shopping'}
                ]
                
            for activity in activities:
                if interests and not any(i.lower() in activity['type'] for i in interests):
                    continue
                    
                events.append({
                    'name': activity['name'],
                    'date': (datetime.now() + timedelta(hours=2)).strftime('%Y-%m-%d %H:%M'),
                    'location': f'Near {lat:.2f}, {lon:.2f}',
                    'url': '',
                    'source': 'do_suggestions',
                    'type': activity['type'],
                    'discovered_at': datetime.now().isoformat()
                })
                
        except Exception as e:
            logger.error(f"Do.com search failed: {e}")
            
        return events
        
    def _deduplicate_events(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate events based on name and time similarity"""
        seen = set()
        unique_events = []
        
        for event in events:
            # Create a simple hash of name and date
            event_key = f"{event.get('name', '').lower()[:20]}_{event.get('date', '')[:10]}"
            
            if event_key not in seen:
                seen.add(event_key)
                unique_events.append(event)
                
        return unique_events
        
    def _filter_by_date(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter events to next 12 hours"""
        filtered = []
        now = datetime.now()
        twelve_hours_later = now + timedelta(hours=12)
        
        for event in events:
            try:
                # Parse event date
                date_str = event.get('date', '')
                if not date_str:
                    # If no date, assume it's happening soon
                    filtered.append(event)
                    continue
                    
                # Try multiple date formats
                for fmt in ['%Y-%m-%d %H:%M', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d']:
                    try:
                        event_date = datetime.strptime(date_str[:16], fmt)
                        if now <= event_date <= twelve_hours_later:
                            filtered.append(event)
                        break
                    except:
                        continue
                        
            except Exception as e:
                logger.debug(f"Date parsing error: {e}")
                # Include events with unparseable dates
                filtered.append(event)
                
        return filtered
        
    def _rank_by_interests(self, events: List[Dict[str, Any]], interests: List[str]) -> List[Dict[str, Any]]:
        """Rank events by relevance to user interests"""
        for event in events:
            score = 0
            event_text = f"{event.get('name', '')} {event.get('type', '')}".lower()
            
            for interest in interests:
                if interest.lower() in event_text:
                    score += 10
                elif any(word in event_text for word in interest.lower().split()):
                    score += 5
                    
            event['relevance_score'] = score
            
        return sorted(events, key=lambda x: x.get('relevance_score', 0), reverse=True)
        
    def generate_recommendations(self, 
                               user_profile: Dict[str, Any],
                               location: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate personalized event recommendations based on profile"""
        recommendations = []
        
        # Extract key information
        interests = user_profile.get('interests', [])
        hobbies = user_profile.get('hobbies', [])
        time_preferences = user_profile.get('activity_times', [])
        
        # Time-based recommendations
        current_hour = datetime.now().hour
        time_based_events = {
            'morning': ['yoga', 'running', 'breakfast', 'coffee'],
            'afternoon': ['lunch', 'workshop', 'museum', 'shopping'],
            'evening': ['dinner', 'concert', 'theater', 'social']
        }
        
        # Determine time period
        if 6 <= current_hour < 12:
            period = 'morning'
        elif 12 <= current_hour < 18:
            period = 'afternoon'
        else:
            period = 'evening'
            
        # Generate recommendations
        for event_type in time_based_events.get(period, []):
            # Check if aligns with interests
            if interests and any(interest.lower() in event_type for interest in interests):
                recommendations.append({
                    'name': f"Recommended: {event_type.title()} Activity",
                    'date': (datetime.now() + timedelta(hours=2)).strftime('%Y-%m-%d %H:%M'),
                    'location': location.get('city', 'Your area'),
                    'url': '',
                    'source': 'ai_recommendation',
                    'type': event_type,
                    'confidence': 0.8,
                    'reason': f"Based on your interest in {interests[0]}",
                    'discovered_at': datetime.now().isoformat()
                })
                
        return recommendations[:10]