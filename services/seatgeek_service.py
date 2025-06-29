"""
SeatGeek Events Service
Integrates with SeatGeek API for additional event discovery
"""
import logging
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import time

from config.settings import (
    SEATGEEK_CLIENT_ID, SEATGEEK_CLIENT_SECRET, SEATGEEK_CONFIG,
    RATE_LIMIT_CONFIG
)

logger = logging.getLogger(__name__)


class SeatGeekService:
    """Service for discovering events via SeatGeek API"""

    def __init__(self, client_id: str = None, client_secret: str = None, config: Dict[str, Any] = None):
        """Initialize SeatGeek service"""
        self.client_id = client_id or SEATGEEK_CLIENT_ID
        self.client_secret = client_secret or SEATGEEK_CLIENT_SECRET
        self.config = config or SEATGEEK_CONFIG

        self.base_url = self.config['BASE_URL']
        self.timeout = self.config.get('TIMEOUT', 10)

        # Rate limiting
        self.rate_limit = RATE_LIMIT_CONFIG.get('seatgeek', {})
        self.last_request_time = 0

        # Setup session
        self.session = requests.Session()
        if self.client_id:
            self.session.auth = (self.client_id, self.client_secret)

    def search_events(
        self,
        location: Dict[str, Any],
        user_interests: List[str] = None,
        user_activity: str = "",
        personalization_data: Dict[str, Any] = None,
        user_profile: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for events using SeatGeek API

        Args:
            location: Location data with lat/lng
            user_interests: List of user interests
            user_activity: User's stated activity
            personalization_data: Enhanced personalization data
            user_profile: Enhanced user profile for AI ranking

        Returns:
            List of formatted event data
        """
        if not self.client_id:
            logger.warning("SeatGeek API credentials not configured")
            return []

        try:
            # Rate limiting
            self._check_rate_limit()

            # Build search parameters
            params = self._build_search_params(location, user_interests, user_activity)

            # Make API request
            response = self._make_api_request('/events', params)

            if response and 'events' in response:
                events = response['events']
                logger.info(f"SeatGeek returned {len(events)} events")

                # Format events
                formatted_events = self._format_events(events)

                # Apply AI ranking if available
                if user_profile and formatted_events:
                    formatted_events = self._rank_events_with_ai(formatted_events, user_profile)

                return formatted_events[:self.config.get('MAX_EVENTS', 30)]

        except Exception as e:
            logger.error(f"SeatGeek search failed: {e}")

        return []

    def _build_search_params(
        self,
        location: Dict[str, Any],
        user_interests: List[str] = None,
        user_activity: str = ""
    ) -> Dict[str, Any]:
        """Build search parameters for SeatGeek API"""
        params = {
            'per_page': self.config.get('MAX_EVENTS', 30),
            'range': f"{self.config.get('SEARCH_RADIUS', 50)}mi",
            'sort': 'datetime_utc.asc'
        }

        # Location
        if location.get('latitude') and location.get('longitude'):
            params['lat'] = location['latitude']
            params['lon'] = location['longitude']
        elif location.get('city'):
            params['venue.city'] = location['city']

        # Date range
        now = datetime.now()
        end_date = now + timedelta(days=self.config.get('DEFAULT_TIME_RANGE', 12) * 30)
        params['datetime_utc.gte'] = now.strftime('%Y-%m-%dT%H:%M:%S')
        params['datetime_utc.lte'] = end_date.strftime('%Y-%m-%dT%H:%M:%S')

        # Category filtering based on interests
        if user_interests or user_activity:
            categories = self._map_interests_to_categories(user_interests, user_activity)
            if categories:
                params['taxonomies.name'] = ','.join(categories)

        return params

    def _map_interests_to_categories(
        self,
        user_interests: List[str] = None,
        user_activity: str = ""
    ) -> List[str]:
        """Map user interests to SeatGeek categories"""
        categories = []

        # SeatGeek taxonomy mapping
        category_mapping = {
            'music': ['concert'],
            'sports': ['sports'],
            'theater': ['theater'],
            'comedy': ['comedy'],
            'dance': ['dance_performance_tour'],
            'family': ['family'],
            'festival': ['festival'],
            'conference': ['conference']
        }

        # Map from interests
        if user_interests:
            for interest in user_interests:
                interest_lower = interest.lower()
                for key, seatgeek_cats in category_mapping.items():
                    if key in interest_lower:
                        categories.extend(seatgeek_cats)

        # Map from activity
        if user_activity:
            activity_lower = user_activity.lower()
            for key, seatgeek_cats in category_mapping.items():
                if key in activity_lower:
                    categories.extend(seatgeek_cats)

        return list(set(categories))  # Remove duplicates

    def _make_api_request(self, endpoint: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Make authenticated request to SeatGeek API"""
        try:
            url = f"{self.base_url}{endpoint}"

            response = self.session.get(
                url,
                params=params,
                timeout=self.timeout
            )

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                logger.error("SeatGeek authentication failed")
            elif response.status_code == 429:
                logger.warning("SeatGeek rate limit exceeded")
            else:
                logger.warning(f"SeatGeek API error: {response.status_code}")

        except requests.exceptions.Timeout:
            logger.warning("SeatGeek API timeout")
        except requests.exceptions.RequestException as e:
            logger.error(f"SeatGeek API request failed: {e}")

        return None

    def _format_events(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format SeatGeek events to standard format"""
        formatted_events = []

        for event in events:
            try:
                # Extract venue information
                venue = event.get('venue', {})

                # Format datetime
                datetime_str = event.get('datetime_utc', '')
                event_datetime = None
                if datetime_str:
                    try:
                        event_datetime = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
                    except:
                        pass

                # Build formatted event
                formatted_event = {
                    'id': f"seatgeek_{event.get('id')}",
                    'name': event.get('title', 'Unknown Event'),
                    'description': self._build_description(event),
                    'date': event_datetime.isoformat() if event_datetime else '',
                    'time': event_datetime.strftime('%H:%M') if event_datetime else '',
                    'venue': {
                        'name': venue.get('name', 'Unknown Venue'),
                        'address': venue.get('address', ''),
                        'city': venue.get('city', ''),
                        'state': venue.get('state', ''),
                        'coordinates': {
                            'latitude': venue.get('location', {}).get('lat'),
                            'longitude': venue.get('location', {}).get('lon')
                        }
                    },
                    'category': self._get_event_category(event),
                    'price_range': self._get_price_range(event),
                    'url': event.get('url', ''),
                    'source': 'seatgeek',
                    'popularity_score': event.get('popularity', 0),
                    'ai_relevance_score': 0.7  # Default score, will be updated by AI ranking
                }

                formatted_events.append(formatted_event)

            except Exception as e:
                logger.warning(f"Failed to format SeatGeek event: {e}")
                continue

        return formatted_events

    def _build_description(self, event: Dict[str, Any]) -> str:
        """Build event description from SeatGeek data"""
        description_parts = []

        # Primary taxonomy
        taxonomies = event.get('taxonomies', [])
        if taxonomies:
            primary_category = taxonomies[0].get('name', '')
            if primary_category:
                description_parts.append(f"Category: {primary_category}")

        # Performers
        performers = event.get('performers', [])
        if performers:
            performer_names = [p.get('name', '') for p in performers[:3]]
            performer_names = [name for name in performer_names if name]
            if performer_names:
                description_parts.append(f"Featuring: {', '.join(performer_names)}")

        return ' | '.join(description_parts) if description_parts else 'Live event'

    def _get_event_category(self, event: Dict[str, Any]) -> str:
        """Extract event category"""
        taxonomies = event.get('taxonomies', [])
        if taxonomies:
            return taxonomies[0].get('name', 'General')
        return 'General'

    def _get_price_range(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Extract price range information"""
        stats = event.get('stats', {})
        return {
            'min': stats.get('lowest_price'),
            'max': stats.get('highest_price'),
            'average': stats.get('average_price'),
            'currency': 'USD'
        }

    def _rank_events_with_ai(
        self,
        events: List[Dict[str, Any]],
        user_profile: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Apply AI-based ranking to events"""
        try:
            # Simple scoring based on user profile
            for event in events:
                score = 0.7  # Base score

                # Category matching
                event_category = event.get('category', '').lower()
                user_interests = user_profile.get('interests', [])

                for interest in user_interests:
                    if interest.lower() in event_category:
                        score += 0.2
                        break

                # Popularity boost
                popularity = event.get('popularity_score', 0)
                if popularity > 0.7:
                    score += 0.1

                # Price preference (prefer reasonable prices)
                price_range = event.get('price_range', {})
                min_price = price_range.get('min')
                if min_price and min_price < 100:  # Under $100
                    score += 0.1

                event['ai_relevance_score'] = min(1.0, score)

            # Sort by AI relevance score
            events.sort(key=lambda x: x.get('ai_relevance_score', 0), reverse=True)

        except Exception as e:
            logger.warning(f"AI ranking failed: {e}")

        return events

    def _check_rate_limit(self):
        """Check and enforce rate limiting"""
        if self.rate_limit:
            calls_per_window = self.rate_limit.get('calls', 1000)
            window_seconds = self.rate_limit.get('window', 3600)

            current_time = time.time()
            time_since_last = current_time - self.last_request_time

            if time_since_last < (window_seconds / calls_per_window):
                sleep_time = (window_seconds / calls_per_window) - time_since_last
                time.sleep(sleep_time)

            self.last_request_time = time.time()

    def is_configured(self) -> bool:
        """Check if service is properly configured"""
        return bool(self.client_id and self.client_secret)
