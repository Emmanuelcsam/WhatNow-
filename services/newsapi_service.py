"""
NewsAPI Service for Event Discovery

This module integrates with the NewsAPI to find news about upcoming events,
gatherings, festivals, and local activities in specific locations.
"""

import requests
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
import re
from urllib.parse import quote_plus

logger = logging.getLogger(__name__)


@dataclass
class NewsEvent:
    """News-based event data structure"""
    title: str
    description: str
    url: str
    source: str
    published_at: str
    image_url: str = ""
    location_mentioned: str = ""
    event_type: str = ""
    confidence_score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            'title': self.title,
            'description': self.description,
            'url': self.url,
            'source': self.source,
            'published_at': self.published_at,
            'image_url': self.image_url,
            'location_mentioned': self.location_mentioned,
            'event_type': self.event_type,
            'confidence_score': self.confidence_score
        }


class NewsAPIEventService:
    """Service for discovering events through news articles"""

    def __init__(self, api_key: str, config: Dict[str, Any] = None):
        """
        Initialize the NewsAPI service

        Args:
            api_key: NewsAPI key
            config: Configuration dictionary
        """
        self.api_key = api_key
        self.config = config or {}
        self.base_url = "https://newsapi.org/v2"
        self.timeout = self.config.get('timeout', 10)

        # Event-related keywords for filtering
        self.event_keywords = [
            'festival', 'concert', 'event', 'gathering', 'meetup', 'conference',
            'workshop', 'seminar', 'exhibition', 'show', 'performance', 'fair',
            'market', 'competition', 'tournament', 'celebration', 'party',
            'networking', 'summit', 'convention', 'expo', 'gala', 'fundraiser',
            'screening', 'premiere', 'launch', 'opening', 'closing'
        ]

        # Session for connection pooling
        self.session = requests.Session()
        self.session.headers.update({
            'X-API-Key': self.api_key,
            'User-Agent': 'WhatNowAI/1.0'
        })

        logger.info("NewsAPI event service initialized")

    def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Optional[Dict]:
        """Make a request to the NewsAPI"""
        if not self.api_key:
            logger.warning("NewsAPI key not provided")
            return None

        url = f"{self.base_url}/{endpoint}"

        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"NewsAPI request failed: {e}")
            return None

    def search_local_events(
        self,
        location: str,
        user_interests: List[str] = None,
        user_activity: str = "",
        days_ahead: int = 30
    ) -> List[NewsEvent]:
        """
        Search for local events and activities in news

        Args:
            location: Location name (city, state, country)
            user_interests: List of user interests
            user_activity: User's desired activity
            days_ahead: Number of days to look ahead

        Returns:
            List of news-based events
        """
        all_events = []

        # Build search queries
        search_queries = self._build_event_queries(location, user_interests, user_activity)

        # Search for each query
        for query in search_queries:
            events = self._search_events_by_query(query, days_ahead)
            all_events.extend(events)

        # Remove duplicates and sort by relevance
        unique_events = self._deduplicate_events(all_events)
        sorted_events = sorted(unique_events, key=lambda x: x.confidence_score, reverse=True)

        return sorted_events[:20]  # Return top 20 most relevant

    def _build_event_queries(
        self,
        location: str,
        user_interests: List[str] = None,
        user_activity: str = ""
    ) -> List[str]:
        """Build search queries for event discovery"""
        queries = []

        # Base event queries for the location
        base_queries = [
            f"{location} events upcoming",
            f"{location} festivals concerts",
            f"{location} activities weekend",
            f"{location} things to do",
            f"upcoming {location} gatherings"
        ]
        queries.extend(base_queries)

        # Add user activity specific queries
        if user_activity:
            activity_queries = [
                f"{location} {user_activity}",
                f"{location} {user_activity} events",
                f"upcoming {user_activity} {location}"
            ]
            queries.extend(activity_queries)

        # Add interest-based queries
        if user_interests:
            for interest in user_interests[:3]:  # Limit to top 3 interests
                interest_queries = [
                    f"{location} {interest} events",
                    f"{location} {interest} activities",
                    f"{interest} {location} upcoming"
                ]
                queries.extend(interest_queries)

        return queries

    def _search_events_by_query(self, query: str, days_ahead: int) -> List[NewsEvent]:
        """Search for events using a specific query"""
        # Calculate date range
        from_date = datetime.now().strftime('%Y-%m-%d')
        to_date = (datetime.now() + timedelta(days=days_ahead)).strftime('%Y-%m-%d')

        params = {
            'q': query,
            'from': from_date,
            'to': to_date,
            'sortBy': 'relevancy',
            'language': 'en',
            'pageSize': 20
        }

        result = self._make_request('everything', params)

        if not result or 'articles' not in result:
            return []

        events = []
        for article in result['articles']:
            event = self._parse_article_for_event(article, query)
            if event and event.confidence_score > 0.3:  # Only include relevant events
                events.append(event)

        return events

    def _parse_article_for_event(self, article: Dict[str, Any], query: str) -> Optional[NewsEvent]:
        """Parse a news article to extract event information"""
        title = article.get('title', '')
        description = article.get('description', '') or article.get('content', '')

        # Check if this is likely an event
        confidence_score = self._calculate_event_confidence(title, description)

        if confidence_score < 0.3:
            return None

        # Extract event type
        event_type = self._extract_event_type(title, description)

        # Extract location mentions
        location_mentioned = self._extract_location_mentions(title, description)

        return NewsEvent(
            title=title[:200],  # Truncate long titles
            description=description[:500] if description else '',  # Truncate long descriptions
            url=article.get('url', ''),
            source=article.get('source', {}).get('name', 'Unknown'),
            published_at=article.get('publishedAt', ''),
            image_url=article.get('urlToImage', ''),
            location_mentioned=location_mentioned,
            event_type=event_type,
            confidence_score=confidence_score
        )

    def _calculate_event_confidence(self, title: str, description: str) -> float:
        """Calculate confidence that this article is about an event"""
        text = f"{title} {description}".lower()

        # Count event-related keywords
        keyword_matches = sum(1 for keyword in self.event_keywords if keyword in text)

        # Check for date/time indicators
        date_patterns = [
            r'\b(january|february|march|april|may|june|july|august|september|october|november|december)\b',
            r'\b\d{1,2}(st|nd|rd|th)?\s+(january|february|march|april|may|june|july|august|september|october|november|december)\b',
            r'\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b',
            r'\b(this|next|upcoming)\s+(week|weekend|month)\b',
            r'\b\d{1,2}:\d{2}\s*(am|pm)?\b',
            r'\b(tonight|today|tomorrow)\b'
        ]

        date_matches = sum(1 for pattern in date_patterns if re.search(pattern, text))

        # Check for location indicators
        location_patterns = [
            r'\bat\s+[A-Z][a-z]+',  # "at Location"
            r'\bin\s+[A-Z][a-z]+',  # "in City"
            r'\bdowntown\b',
            r'\bcenter\b',
            r'\bhall\b',
            r'\btheater\b',
            r'\bpark\b'
        ]

        location_matches = sum(1 for pattern in location_patterns if re.search(pattern, text))

        # Calculate confidence score
        base_score = min(keyword_matches * 0.2, 1.0)
        date_bonus = min(date_matches * 0.15, 0.3)
        location_bonus = min(location_matches * 0.1, 0.2)

        return min(base_score + date_bonus + location_bonus, 1.0)

    def _extract_event_type(self, title: str, description: str) -> str:
        """Extract the type of event from the text"""
        text = f"{title} {description}".lower()

        event_types = {
            'music': ['concert', 'festival', 'music', 'band', 'singer', 'performance'],
            'food': ['food', 'restaurant', 'dining', 'taste', 'culinary', 'chef'],
            'sports': ['sports', 'game', 'match', 'tournament', 'competition', 'team'],
            'arts': ['art', 'gallery', 'exhibition', 'museum', 'theater', 'play'],
            'business': ['conference', 'networking', 'business', 'workshop', 'seminar'],
            'community': ['community', 'local', 'neighborhood', 'residents', 'public'],
            'education': ['workshop', 'class', 'seminar', 'training', 'course'],
            'entertainment': ['show', 'comedy', 'entertainment', 'performance', 'movie']
        }

        for event_type, keywords in event_types.items():
            if any(keyword in text for keyword in keywords):
                return event_type

        return 'general'

    def _extract_location_mentions(self, title: str, description: str) -> str:
        """Extract location mentions from the text"""
        text = f"{title} {description}"

        # Look for location patterns
        location_patterns = [
            r'\bat\s+([A-Z][a-zA-Z\s]+?)(?:\s|,|\.)',
            r'\bin\s+([A-Z][a-zA-Z\s]+?)(?:\s|,|\.)',
            r'([A-Z][a-zA-Z\s]+?)\s+(?:Center|Hall|Theater|Park|Stadium)'
        ]

        for pattern in location_patterns:
            matches = re.findall(pattern, text)
            if matches:
                return matches[0].strip()

        return ""

    def _deduplicate_events(self, events: List[NewsEvent]) -> List[NewsEvent]:
        """Remove duplicate events based on title similarity"""
        unique_events = []
        seen_titles = set()

        for event in events:
            # Create a normalized title for comparison
            normalized_title = re.sub(r'[^\w\s]', '', event.title.lower()).strip()

            if normalized_title not in seen_titles:
                seen_titles.add(normalized_title)
                unique_events.append(event)

        return unique_events

    def search_trending_events(self, location: str, category: str = None) -> List[NewsEvent]:
        """
        Search for trending events in a location

        Args:
            location: Location name
            category: Optional category filter

        Returns:
            List of trending events
        """
        query = f"{location} trending events"
        if category:
            query += f" {category}"

        return self._search_events_by_query(query, days_ahead=14)

    def get_weekend_activities(self, location: str) -> List[NewsEvent]:
        """
        Get weekend activities and events

        Args:
            location: Location name

        Returns:
            List of weekend events
        """
        queries = [
            f"{location} weekend events",
            f"{location} saturday sunday activities",
            f"this weekend {location} things to do"
        ]

        all_events = []
        for query in queries:
            events = self._search_events_by_query(query, days_ahead=7)
            all_events.extend(events)

        return self._deduplicate_events(all_events)[:10]
