"""
Enhanced Search Service with OSINT Integration
Combines multiple search engines and OSINT tools for comprehensive data gathering
"""
import asyncio
import aiohttp
import logging
import time
import sys
import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from urllib.parse import quote_plus
from pathlib import Path
import json
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Add search_methods_2 to path for imports
sys.path.append(str(Path(__file__).parent.parent / 'search_methods_2'))

try:
    from bs4 import BeautifulSoup
    from duckduckgo_search import DDGS
except ImportError:
    # Will be installed via requirements.txt
    BeautifulSoup = None
    DDGS = None

from config.settings import ENHANCED_SEARCH_CONFIG, SERPER_API_KEY

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Enhanced search result with metadata"""
    title: str
    url: str
    snippet: str
    source: str
    timestamp: datetime
    relevance_score: float = 0.0
    entity_type: str = ""  # person, organization, location, etc.
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'title': self.title,
            'url': self.url,
            'snippet': self.snippet,
            'source': self.source,
            'timestamp': self.timestamp.isoformat(),
            'relevance_score': self.relevance_score,
            'entity_type': self.entity_type,
            'metadata': self.metadata
        }


class EnhancedSearchService:
    """
    Multi-engine search service for comprehensive data gathering
    Integrates OSINT tools and multiple search APIs
    """

    def __init__(self, config: Dict[str, Any] = None):
        """Initialize enhanced search service"""
        self.config = config or ENHANCED_SEARCH_CONFIG
        self.session = self._setup_session()

        # Initialize search engines based on availability
        self.engines = []
        if 'duckduckgo' in self.config.get('SEARCH_ENGINES', []):
            self.engines.append(self._search_duckduckgo)
        if 'serper' in self.config.get('SEARCH_ENGINES', []) and SERPER_API_KEY:
            self.engines.append(self._search_serper)

    def _setup_session(self) -> requests.Session:
        """Setup requests session with retry strategy"""
        session = requests.Session()

        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        # Set headers
        session.headers.update({
            'User-Agent': self.config.get('USER_AGENT', 'WhatNowAI/1.0'),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })

        return session

    def search_person(
        self,
        first_name: str,
        last_name: str,
        location: str = "",
        additional_context: Dict[str, Any] = None,
        max_results: int = 10
    ) -> Dict[str, List[SearchResult]]:
        """
        Comprehensive person search across multiple sources

        Args:
            first_name: Person's first name
            last_name: Person's last name
            location: Location context
            additional_context: Social handles, interests, etc.
            max_results: Maximum results per category

        Returns:
            Categorized search results
        """
        results = {
            'professional': [],
            'social': [],
            'academic': [],
            'general': [],
            'location': []
        }

        # Build search queries
        full_name = f"{first_name} {last_name}"
        queries = self._build_person_queries(full_name, location, additional_context)

        # Execute searches with timeout
        start_time = time.time()
        timeout = self.config.get('TIMEOUT', 15)

        try:
            # Professional search
            if time.time() - start_time < timeout:
                prof_results = self._search_professional_info(full_name, location)
                results['professional'].extend(prof_results[:max_results//2])

            # Social media search
            if time.time() - start_time < timeout and additional_context:
                social_handles = additional_context.get('social_handles', {})
                if social_handles:
                    social_results = self._search_social_platforms(social_handles)
                    results['social'].extend(social_results[:max_results//2])

            # General search (limited to avoid celebrity results)
            if time.time() - start_time < timeout:
                general_results = self._search_general_safe(full_name, location)
                results['general'].extend(general_results[:max_results//3])

        except Exception as e:
            logger.error(f"Error in person search: {e}")

        return results

    def _build_person_queries(
        self,
        full_name: str,
        location: str = "",
        context: Dict[str, Any] = None
    ) -> List[str]:
        """Build targeted search queries for a person"""
        queries = []

        # Basic queries with anti-celebrity filters
        base_query = f'"{full_name}" -wikipedia -celebrity -famous -actor -singer'
        queries.append(base_query)

        if location:
            queries.append(f'"{full_name}" "{location}" -wikipedia -celebrity')

        # Professional context
        if context and context.get('activity'):
            activity = context['activity']
            queries.append(f'"{full_name}" "{activity}" professional')

        return queries[:3]  # Limit to 3 queries for speed

    def _search_professional_info(self, name: str, location: str = "") -> List[SearchResult]:
        """Search for professional information about a person"""
        results = []

        queries = [
            f'"{name}" linkedin profile',
            f'"{name}" professional background',
        ]

        if location:
            queries.append(f'"{name}" "{location}" company work')

        for query in queries[:2]:  # Limit for speed
            try:
                search_results = self._execute_search(query, 'professional')
                results.extend(search_results[:3])  # Limit results per query
                time.sleep(0.5)  # Rate limiting
            except Exception as e:
                logger.warning(f"Professional search failed for query '{query}': {e}")
                continue

        return results

    def _search_social_platforms(self, social_handles: Dict[str, str]) -> List[SearchResult]:
        """Search social media platforms efficiently"""
        results = []

        # Prioritize platforms by reliability and speed
        priority_platforms = ['github', 'linkedin', 'twitter']

        for platform in priority_platforms:
            handle = social_handles.get(platform)
            if not handle:
                continue

            try:
                if platform == 'github':
                    # GitHub API is fastest and most reliable
                    github_results = self._search_github_api(handle)
                    results.extend(github_results)
                else:
                    # Quick search for other platforms
                    platform_results = self._quick_social_search(platform, handle)
                    results.extend(platform_results)

            except Exception as e:
                logger.warning(f"Social search failed for {platform}:{handle}: {e}")
                continue

        return results[:10]  # Limit total social results

    def _search_github_api(self, username: str) -> List[SearchResult]:
        """Search GitHub using their API for reliable data"""
        results = []

        try:
            # GitHub user API
            api_url = f"https://api.github.com/users/{username}"
            response = self.session.get(api_url, timeout=5)

            if response.status_code == 200:
                user_data = response.json()

                result = SearchResult(
                    title=f"GitHub: {user_data.get('name', username)}",
                    url=user_data.get('html_url', ''),
                    snippet=user_data.get('bio', 'GitHub user profile'),
                    source='github',
                    timestamp=datetime.now(),
                    relevance_score=0.9,
                    entity_type='social_profile',
                    metadata={
                        'followers': user_data.get('followers', 0),
                        'public_repos': user_data.get('public_repos', 0),
                        'location': user_data.get('location', ''),
                        'company': user_data.get('company', '')
                    }
                )
                results.append(result)

        except Exception as e:
            logger.warning(f"GitHub API search failed for {username}: {e}")

        return results

    def _quick_social_search(self, platform: str, handle: str) -> List[SearchResult]:
        """Quick search for social media platforms"""
        results = []

        try:
            # Site-specific search
            query = f"site:{platform}.com {handle}"
            search_results = self._execute_search(query, 'social', limit=2)
            results.extend(search_results)

        except Exception as e:
            logger.warning(f"Quick social search failed for {platform}: {e}")

        return results

    def _search_general_safe(self, name: str, location: str = "") -> List[SearchResult]:
        """Safe general search that filters out celebrities"""
        results = []

        # Use specific filters to avoid celebrity results
        base_query = f'"{name}" -wikipedia -celebrity -famous -actor -singer -musician'

        if location:
            query = f'{base_query} "{location}"'
        else:
            query = base_query

        try:
            search_results = self._execute_search(query, 'general', limit=3)
            # Additional filtering
            filtered_results = [r for r in search_results if self._is_not_celebrity(r)]
            results.extend(filtered_results)

        except Exception as e:
            logger.warning(f"General search failed: {e}")

        return results

    def _is_not_celebrity(self, result: SearchResult) -> bool:
        """Check if result is not about a celebrity"""
        celebrity_keywords = [
            'wikipedia', 'celebrity', 'famous', 'actor', 'actress', 'singer',
            'musician', 'politician', 'athlete', 'movie', 'film', 'album',
            'grammy', 'oscar', 'emmy', 'biography', 'filmography', 'discography'
        ]

        text_content = (result.title + ' ' + result.snippet).lower()
        return not any(keyword in text_content for keyword in celebrity_keywords)

    def _execute_search(self, query: str, source_type: str, limit: int = 5) -> List[SearchResult]:
        """Execute search using available engines"""
        results = []

        # Try DuckDuckGo first (no API key required)
        if 'duckduckgo' in self.config.get('SEARCH_ENGINES', []):
            try:
                ddg_results = self._search_duckduckgo(query, source_type, limit)
                results.extend(ddg_results)
            except Exception as e:
                logger.warning(f"DuckDuckGo search failed: {e}")

        # Try Serper if available and we need more results
        if (len(results) < limit and
            'serper' in self.config.get('SEARCH_ENGINES', []) and
            SERPER_API_KEY):
            try:
                serper_results = self._search_serper(query, source_type, limit - len(results))
                results.extend(serper_results)
            except Exception as e:
                logger.warning(f"Serper search failed: {e}")

        return results[:limit]

    def _search_duckduckgo(self, query: str, source_type: str, limit: int = 5) -> List[SearchResult]:
        """Search using DuckDuckGo"""
        results = []

        if not DDGS:
            return results

        try:
            with DDGS() as ddgs:
                search_results = list(ddgs.text(query, max_results=limit))

                for result in search_results:
                    search_result = SearchResult(
                        title=result.get('title', ''),
                        url=result.get('href', ''),
                        snippet=result.get('body', ''),
                        source=f'duckduckgo_{source_type}',
                        timestamp=datetime.now(),
                        relevance_score=0.7
                    )
                    results.append(search_result)

        except Exception as e:
            logger.warning(f"DuckDuckGo search error: {e}")

        return results

    def _search_serper(self, query: str, source_type: str, limit: int = 5) -> List[SearchResult]:
        """Search using Serper API"""
        results = []

        if not SERPER_API_KEY:
            return results

        try:
            url = "https://google.serper.dev/search"
            payload = {
                'q': query,
                'num': limit
            }
            headers = {
                'X-API-KEY': SERPER_API_KEY,
                'Content-Type': 'application/json'
            }

            response = self.session.post(url, json=payload, headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json()

                for result in data.get('organic', [])[:limit]:
                    search_result = SearchResult(
                        title=result.get('title', ''),
                        url=result.get('link', ''),
                        snippet=result.get('snippet', ''),
                        source=f'serper_{source_type}',
                        timestamp=datetime.now(),
                        relevance_score=0.8
                    )
                    results.append(search_result)

        except Exception as e:
            logger.warning(f"Serper search error: {e}")

        return results

    def search_activity_info(self, activity: str, location: str = "") -> List[SearchResult]:
        """Search for activity-related information"""
        results = []

        queries = [
            f"how to get started with {activity}",
            f"{activity} beginner guide"
        ]

        if location:
            queries.append(f"{activity} classes {location}")
            queries.append(f"where to {activity} {location}")

        for query in queries[:3]:  # Limit for speed
            try:
                search_results = self._execute_search(query, 'activity', limit=3)
                results.extend(search_results)
                time.sleep(0.5)  # Rate limiting
            except Exception as e:
                logger.warning(f"Activity search failed for '{query}': {e}")
                continue

        return results[:10]  # Limit total results

    def search_location_events(self, location: str, activity: str = "") -> List[SearchResult]:
        """Search for location-specific events and activities"""
        results = []

        queries = [
            f"events {location} today",
            f"things to do {location}"
        ]

        if activity:
            queries.append(f"{activity} events {location}")

        for query in queries[:3]:  # Limit for speed
            try:
                search_results = self._execute_search(query, 'location', limit=3)
                results.extend(search_results)
                time.sleep(0.5)  # Rate limiting
            except Exception as e:
                logger.warning(f"Location search failed for '{query}': {e}")
                continue

        return results[:10]  # Limit total results

    def search_comprehensive(
        self,
        query: str,
        location: Dict[str, float] = None,
        user_interests: List[str] = None,
        max_results: int = 10
    ) -> List[SearchResult]:
        """
        Comprehensive search combining multiple sources and approaches

        Args:
            query: Main search query
            location: Location data with latitude/longitude
            user_interests: List of user interests
            max_results: Maximum number of results to return

        Returns:
            List of comprehensive search results
        """
        all_results = []

        try:
            # Basic search
            basic_results = self._execute_search(query, "general", limit=max_results // 2)
            all_results.extend(basic_results)

            # Location-based search if location provided
            if location:
                location_str = f"{location.get('latitude', '')},{location.get('longitude', '')}"
                location_query = f"{query} near {location_str}"
                location_results = self._execute_search(location_query, "location", limit=max_results // 4)
                all_results.extend(location_results)

            # Interest-based search if interests provided
            if user_interests:
                for interest in user_interests[:3]:  # Limit to top 3 interests
                    interest_query = f"{query} {interest}"
                    interest_results = self._execute_search(interest_query, "interest", limit=2)
                    all_results.extend(interest_results)

            # Remove duplicates and sort by relevance
            unique_results = []
            seen_urls = set()

            for result in all_results:
                if result.url not in seen_urls:
                    seen_urls.add(result.url)
                    unique_results.append(result)

            # Sort by relevance score (if available) or recency
            unique_results.sort(key=lambda x: (x.relevance_score, x.timestamp), reverse=True)

            return unique_results[:max_results]

        except Exception as e:
            logger.error(f"Comprehensive search failed: {e}")
            return []
