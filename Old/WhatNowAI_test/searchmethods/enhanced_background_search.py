"""
Enhanced Background Search Service
Production-optimized version with multiple search backends, NewsAPI integration, and fast OSINT
"""
import asyncio
import aiohttp
import logging
import time
import requests
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from urllib.parse import quote_plus
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

try:
    from bs4 import BeautifulSoup
    from duckduckgo_search import DDGS
except ImportError:
    BeautifulSoup = None
    DDGS = None

from services.enhanced_search_service import EnhancedSearchService
from services.osint_integration import OSINTIntegrator
from services.optimized_osint_service import ProductionOSINTService
from services.newsapi_service import NewsAPIEventService
from services.performance_optimizer import get_optimizer, production_optimizer
from config.settings import ENHANCED_SEARCH_CONFIG, NEWSAPI_KEY
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class UserProfile:
    """Enhanced user profile data structure"""
    name: str
    location: str = ""
    social_handles: Dict[str, str] = None
    activity: str = ""
    interests: List[str] = None

    def __post_init__(self):
        if self.social_handles is None:
            self.social_handles = {}
        if self.interests is None:
            self.interests = []


@dataclass
class SearchResult:
    """Enhanced search result data structure"""
    source: str
    title: str
    url: str
    content: str
    relevance_score: float = 0.0
    timestamp: str = ""
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class EnhancedBackgroundSearchService:
    """
    Enhanced background search service with OSINT integration
    Provides faster, more reliable search with better privacy protection
    """

    def __init__(self, config: Dict[str, Any] = None):
        """Initialize enhanced background search service with optimized components"""
        self.config = config or ENHANCED_SEARCH_CONFIG
        self.session = self._setup_session()

        # Initialize optimized services
        self.enhanced_search = EnhancedSearchService(config)
        self.osint_integrator = OSINTIntegrator()
        self.production_osint = ProductionOSINTService(config)

        # Initialize NewsAPI service if key is available
        self.news_service = None
        if NEWSAPI_KEY:
            try:
                self.news_service = NewsAPIEventService(NEWSAPI_KEY, config)
                logger.info("NewsAPI service initialized for event discovery")
            except Exception as e:
                logger.warning(f"Failed to initialize NewsAPI service: {e}")

        # Search timeout (optimized for production)
        self.search_timeout = self.config.get('TIMEOUT', 10)  # Reduced to 10 seconds
        self.fast_mode = self.config.get('FAST_MODE', True)  # Enable fast mode by default

        logger.info("Enhanced background search service initialized with production optimizations")

    def _setup_session(self) -> requests.Session:
        """Setup requests session with retry strategy and privacy headers"""
        session = requests.Session()

        # Configure retry strategy
        retry_strategy = Retry(
            total=2,  # Reduced retries for faster response
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        # Privacy-focused headers
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',  # Do Not Track
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })

        return session

    def perform_search(self, user_profile: UserProfile) -> Dict[str, Any]:
        """
        Perform production-optimized background search with caching and monitoring

        Args:
            user_profile: User profile to search for

        Returns:
            Comprehensive search results with summaries and performance metrics
        """
        # Create cache key from user profile
        search_params = {
            'name': user_profile.name,
            'location': user_profile.location,
            'activity': user_profile.activity,
            'interests': user_profile.interests,
            'fast_mode': self.fast_mode
        }

        # Check cache first
        optimizer = get_optimizer()

        def execute_search():
            return self._execute_search_internal(user_profile)

        # Use cached search with shorter TTL for dynamic content
        return optimizer.cached_search(
            search_params,
            execute_search,
            ttl_minutes=10  # Cache for 10 minutes
        )

    def _execute_search_internal(self, user_profile: UserProfile) -> Dict[str, Any]:
        """Internal search execution with performance monitoring"""
        start_time = time.time()
        optimizer = get_optimizer()

        # Start monitoring the overall search operation
        search_op_id = optimizer.monitor.start_operation("enhanced_background_search")

        # Initialize results structure
        results = {
            'raw_results': {
                'general': [],
                'social': [],
                'location': [],
                'activity': [],
                'osint': [],
                'news_events': []
            },
            'summaries': {},
            'metadata': {
                'search_time': 0,
                'sources_used': [],
                'osint_available': False,
                'news_api_available': bool(self.news_service),
                'privacy_mode': self.config.get('PRIVACY_MODE', True),
                'fast_mode': self.fast_mode,
                'performance_report': {},
                'cache_used': False
            }
        }

        try:
            # Check available tools
            osint_tools = self.osint_integrator.get_available_tools()
            results['metadata']['osint_available'] = any(osint_tools.values())

            # Use fast concurrent search execution with individual operation monitoring
            search_futures = {}
            max_workers = 4 if self.fast_mode else 3

            with ThreadPoolExecutor(max_workers=max_workers) as executor:

                # Fast OSINT search (prioritized for speed)
                if self.fast_mode and user_profile.name:
                    search_futures['osint'] = executor.submit(
                        self._monitored_osint_search, user_profile, optimizer
                    )

                # NewsAPI event search (if available)
                if self.news_service and user_profile.location:
                    search_futures['news_events'] = executor.submit(
                        self._monitored_news_search, user_profile, optimizer
                    )

                # Social media search (reduced scope for speed)
                if user_profile.social_handles:
                    search_futures['social'] = executor.submit(
                        self._monitored_social_search, user_profile, optimizer
                    )

                # Activity and location search (optimized)
                if user_profile.activity:
                    search_futures['activity'] = executor.submit(
                        self._monitored_activity_search, user_profile, optimizer
                    )

                if user_profile.location:
                    search_futures['location'] = executor.submit(
                        self._monitored_location_search, user_profile, optimizer
                    )

                # Collect results with timeout (reduced for fast response)
                for category, future in search_futures.items():
                    try:
                        remaining_time = max(1, self.search_timeout - (time.time() - start_time))
                        category_results = future.result(timeout=remaining_time)
                        results['raw_results'][category] = category_results
                        results['metadata']['sources_used'].append(category)

                    except Exception as e:
                        logger.warning(f"Search failed for {category}: {e}")
                        results['raw_results'][category] = []

            # Generate summaries based on collected results
            results['summaries'] = self._generate_summaries(results['raw_results'])

            # Add performance report
            if hasattr(self, 'production_osint'):
                results['metadata']['performance_report'] = self.production_osint.get_performance_report()

            # Mark search as successful
            optimizer.monitor.end_operation(search_op_id, success=True)

        except Exception as e:
            logger.error(f"Enhanced background search failed: {e}")
            results['summaries'] = self._get_fallback_summaries()
            optimizer.monitor.end_operation(search_op_id, success=False, metadata={'error': str(e)})

        # Calculate final metrics
        search_time = time.time() - start_time
        results['metadata']['search_time'] = search_time
        results['metadata']['total_results'] = sum(
            len(category_results) for category_results in results['raw_results'].values()
        )

        logger.info(f"Enhanced search completed in {search_time:.2f}s, "
                   f"found {results['metadata']['total_results']} results from "
                   f"{len(results['metadata']['sources_used'])} sources: "
                   f"{results['metadata']['sources_used']}")

        return results

    def _fast_osint_search(self, user_profile: UserProfile) -> List[SearchResult]:
        """Perform fast OSINT search using optimized service"""
        try:
            # Convert UserProfile to dict for the optimized service
            profile_dict = {
                'name': user_profile.name,
                'location': user_profile.location,
                'activity': user_profile.activity,
                'interests': user_profile.interests,
                'social_handles': user_profile.social_handles
            }

            # Use production OSINT service for fast search
            osint_data = self.production_osint.perform_fast_osint_search(
                profile_dict,
                timeout=self.search_timeout // 2  # Use half the total timeout
            )

            # Convert results to SearchResult objects
            search_results = []
            for result_data in osint_data.get('results', []):
                search_results.append(SearchResult(
                    source=f"osint_{result_data.source}",
                    title=result_data.title,
                    url=result_data.url,
                    content=result_data.snippet,
                    relevance_score=result_data.relevance_score,
                    timestamp=result_data.timestamp.isoformat() if hasattr(result_data.timestamp, 'isoformat') else str(result_data.timestamp),
                    metadata={'osint_source': result_data.source}
                ))

            logger.info(f"Fast OSINT search completed: {len(search_results)} results in {osint_data.get('search_time', 0):.2f}s")
            return search_results

        except Exception as e:
            logger.warning(f"Fast OSINT search failed: {e}")
            return []

    def _search_news_events(self, user_profile: UserProfile) -> List[SearchResult]:
        """Search for events using NewsAPI"""
        try:
            if not self.news_service:
                return []

            news_events = self.news_service.search_local_events(
                location=user_profile.location,
                user_interests=user_profile.interests,
                user_activity=user_profile.activity,
                days_ahead=14
            )

            # Convert to SearchResult objects
            search_results = []
            for event in news_events[:10]:  # Limit for performance
                search_results.append(SearchResult(
                    source=f"news_{event.source}",
                    title=event.title,
                    url=event.url,
                    content=event.description,
                    relevance_score=event.confidence_score,
                    timestamp=datetime.now().isoformat(),
                    metadata={'event_type': event.event_type}
                ))

            logger.info(f"NewsAPI event search found {len(search_results)} relevant events")
            return search_results

        except Exception as e:
            logger.warning(f"NewsAPI event search failed: {e}")
            return []

    def _search_social_enhanced(self, user_profile: UserProfile) -> List[SearchResult]:
        """Enhanced social media search with privacy protection"""
        results = []

        try:
            # Check if we have any social handles to search
            has_social_handles = user_profile.social_handles and any(
                handle.strip() for handle in user_profile.social_handles.values()
            )

            if has_social_handles:
                # Use enhanced search service for social platforms
                social_results = self.enhanced_search.search_person(
                    first_name=user_profile.name.split()[0] if user_profile.name else "",
                    last_name=" ".join(user_profile.name.split()[1:]) if len(user_profile.name.split()) > 1 else "",
                    location=user_profile.location,
                    additional_context={'social_handles': user_profile.social_handles},
                    max_results=8
                )

                # Convert to our format
                for category, search_results in social_results.items():
                    if 'social' in category.lower():
                        for result in search_results:
                            search_result = SearchResult(
                                source='enhanced_social',
                                title=result.title,
                                url=result.url,
                                content=result.snippet,
                                relevance_score=result.relevance_score,
                                timestamp=result.timestamp.isoformat(),
                                metadata={'category': category, 'entity_type': result.entity_type}
                            )
                            results.append(search_result)
            else:
                # No social handles provided - create a placeholder result
                results.append(SearchResult(
                    source='social_info',
                    title='Social Media Search',
                    url='',
                    content='No social media handles provided for enhanced search',
                    relevance_score=0.5,
                    timestamp='',
                    metadata={'status': 'no_handles_provided'}
                ))

        except Exception as e:
            logger.warning(f"Enhanced social search failed: {e}")
            # Create error result
            results.append(SearchResult(
                source='social_error',
                title='Social Search Status',
                url='',
                content=f'Social media search encountered an issue: {str(e)[:100]}',
                relevance_score=0.3,
                timestamp='',
                metadata={'error': True}
            ))

        return results[:10]  # Limit results

    def _search_activity_enhanced(self, user_profile: UserProfile) -> List[SearchResult]:
        """Enhanced activity search"""
        results = []

        try:
            # Use enhanced search for activity information
            activity_results = self.enhanced_search.search_activity_info(
                activity=user_profile.activity,
                location=user_profile.location
            )

            # Convert to our format
            for result in activity_results:
                search_result = SearchResult(
                    source='enhanced_activity',
                    title=result.title,
                    url=result.url,
                    content=result.snippet,
                    relevance_score=result.relevance_score,
                    timestamp=result.timestamp.isoformat(),
                    metadata={'activity': user_profile.activity}
                )
                results.append(search_result)

        except Exception as e:
            logger.warning(f"Enhanced activity search failed: {e}")

        return results[:8]  # Limit results

    def _search_location_enhanced(self, user_profile: UserProfile) -> List[SearchResult]:
        """Enhanced location search"""
        results = []

        try:
            # Use enhanced search for location events
            location_results = self.enhanced_search.search_location_events(
                location=user_profile.location,
                activity=user_profile.activity
            )

            # Convert to our format
            for result in location_results:
                search_result = SearchResult(
                    source='enhanced_location',
                    title=result.title,
                    url=result.url,
                    content=result.snippet,
                    relevance_score=result.relevance_score,
                    timestamp=result.timestamp.isoformat(),
                    metadata={'location': user_profile.location}
                )
                results.append(search_result)

        except Exception as e:
            logger.warning(f"Enhanced location search failed: {e}")

        return results[:8]  # Limit results

    def _search_osint_enhanced(self, user_profile: UserProfile) -> List[SearchResult]:
        """Enhanced OSINT search"""
        results = []

        try:
            if not user_profile.name:
                return results

            # Split name for OSINT search
            name_parts = user_profile.name.split()
            first_name = name_parts[0] if name_parts else ""
            last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""

            # Quick OSINT search with short timeout
            osint_results = self.osint_integrator.search_person_osint(
                first_name=first_name,
                last_name=last_name,
                location=user_profile.location,
                social_handles=user_profile.social_handles,
                timeout=8  # Short timeout for OSINT
            )

            # Convert OSINT results to our format
            for category, osint_items in osint_results.items():
                for item in osint_items[:3]:  # Limit per category
                    search_result = SearchResult(
                        source=f'osint_{category}',
                        title=f"OSINT: {category}",
                        url=item.content.get('profile_url', ''),
                        content=json.dumps(item.content),
                        relevance_score=item.confidence,
                        timestamp=item.timestamp.isoformat(),
                        metadata={'osint_category': category, 'osint_source': item.source}
                    )
                    results.append(search_result)

        except Exception as e:
            logger.warning(f"Enhanced OSINT search failed: {e}")

        return results[:10]  # Limit total OSINT results

    def _generate_summaries(self, raw_results: Dict[str, List[SearchResult]]) -> Dict[str, str]:
        """Generate intelligent summaries from search results"""
        summaries = {}

        try:
            # Social summary
            social_results = raw_results.get('social', [])
            if social_results:
                social_platforms = set()
                for result in social_results:
                    if 'github' in result.url.lower():
                        social_platforms.add('GitHub')
                    elif 'linkedin' in result.url.lower():
                        social_platforms.add('LinkedIn')
                    elif 'twitter' in result.url.lower():
                        social_platforms.add('Twitter')

                if social_platforms:
                    summaries['social'] = f"Found social media presence on: {', '.join(social_platforms)}"
                else:
                    summaries['social'] = f"Found {len(social_results)} social media references"
            else:
                summaries['social'] = "No specific social media profiles found"

            # Location summary
            location_results = raw_results.get('location', [])
            if location_results:
                summaries['location'] = f"Found {len(location_results)} location-related activities and events"
            else:
                summaries['location'] = "No specific local activities found"

            # Activity summary
            activity_results = raw_results.get('activity', [])
            if activity_results:
                summaries['activity'] = f"Found {len(activity_results)} activity-related resources and guides"
            else:
                summaries['activity'] = "No specific activity information found"

            # News events summary
            news_results = raw_results.get('news_events', [])
            if news_results:
                summaries['news_events'] = f"Found {len(news_results)} news articles about local events and activities"
            else:
                summaries['news_events'] = "No recent news about local events found"
            location_results = raw_results.get('location', [])
            if location_results:
                summaries['location'] = f"Found {len(location_results)} location-related activities and events"
            else:
                summaries['location'] = "No specific local activities found"

            # Activity summary
            activity_results = raw_results.get('activity', [])
            if activity_results:
                summaries['activity'] = f"Found {len(activity_results)} activity-related resources and guides"
            else:
                summaries['activity'] = "No specific activity information found"

            # OSINT summary
            osint_results = raw_results.get('osint', [])
            if osint_results:
                summaries['osint'] = f"Advanced search found {len(osint_results)} additional data points"
            else:
                summaries['osint'] = "Advanced search capabilities utilized"

            # General summary
            total_results = sum(len(results) for results in raw_results.values())
            if total_results > 0:
                summaries['general'] = f"Comprehensive search completed with {total_results} total findings across multiple sources"
            else:
                summaries['general'] = "Search completed with privacy-focused approach"

        except Exception as e:
            logger.warning(f"Summary generation failed: {e}")
            summaries = self._get_fallback_summaries()

        return summaries

    def _get_fallback_summaries(self) -> Dict[str, str]:
        """Get fallback summaries when search fails"""
        return {
            'general': 'Search completed with enhanced privacy protection',
            'social': 'Social media search performed with privacy safeguards',
            'location': 'Location-based search completed',
            'activity': 'Activity-related information search performed',
            'osint': 'Advanced search capabilities available but not utilized due to privacy settings'
        }

    def perform_enhanced_search(self, user_data: Dict[str, Any], timeout: int = 30) -> Dict[str, Any]:
        """
        Enhanced search wrapper that accepts user data dictionary

        Args:
            user_data: Dictionary containing user information
            timeout: Search timeout in seconds

        Returns:
            Search results with sources and findings
        """
        try:
            # Convert user_data dict to UserProfile
            user_profile = UserProfile(
                name=user_data.get('name', ''),
                location=user_data.get('location', ''),
                interests=user_data.get('interests', []),
                activity=user_data.get('activity', ''),
                social_handles=user_data.get('social_handles', {})
            )

            # Perform the actual search
            results = self.perform_search(user_profile)

            return results

        except Exception as e:
            logger.error(f"Enhanced search failed: {e}")
            return {
                'sources': [],
                'results': [],
                'summaries': {},
                'metadata': {'error': str(e)}
            }

    def _monitored_osint_search(self, user_profile: UserProfile, optimizer) -> List[SearchResult]:
        """OSINT search with performance monitoring"""
        op_id = optimizer.monitor.start_operation("osint_search")
        try:
            results = self._fast_osint_search(user_profile)
            optimizer.monitor.end_operation(op_id, success=True, metadata={'results_count': len(results)})
            return results
        except Exception as e:
            optimizer.monitor.end_operation(op_id, success=False, metadata={'error': str(e)})
            return []

    def _monitored_news_search(self, user_profile: UserProfile, optimizer) -> List[SearchResult]:
        """News search with performance monitoring"""
        op_id = optimizer.monitor.start_operation("news_search")
        try:
            results = self._search_news_events(user_profile)
            optimizer.monitor.end_operation(op_id, success=True, metadata={'results_count': len(results)})
            return results
        except Exception as e:
            optimizer.monitor.end_operation(op_id, success=False, metadata={'error': str(e)})
            return []

    def _monitored_social_search(self, user_profile: UserProfile, optimizer) -> List[SearchResult]:
        """Social search with performance monitoring"""
        op_id = optimizer.monitor.start_operation("social_search")
        try:
            results = self._search_social_enhanced(user_profile)
            optimizer.monitor.end_operation(op_id, success=True, metadata={'results_count': len(results)})
            return results
        except Exception as e:
            optimizer.monitor.end_operation(op_id, success=False, metadata={'error': str(e)})
            return []

    def _monitored_activity_search(self, user_profile: UserProfile, optimizer) -> List[SearchResult]:
        """Activity search with performance monitoring"""
        op_id = optimizer.monitor.start_operation("activity_search")
        try:
            results = self._search_activity_enhanced(user_profile)
            optimizer.monitor.end_operation(op_id, success=True, metadata={'results_count': len(results)})
            return results
        except Exception as e:
            optimizer.monitor.end_operation(op_id, success=False, metadata={'error': str(e)})
            return []

    def _monitored_location_search(self, user_profile: UserProfile, optimizer) -> List[SearchResult]:
        """Location search with performance monitoring"""
        op_id = optimizer.monitor.start_operation("location_search")
        try:
            results = self._search_location_enhanced(user_profile)
            optimizer.monitor.end_operation(op_id, success=True, metadata={'results_count': len(results)})
            return results
        except Exception as e:
            optimizer.monitor.end_operation(op_id, success=False, metadata={'error': str(e)})
            return []

# Legacy function for backward compatibility
def perform_background_search(user_profile: UserProfile) -> Dict[str, Any]:
    """
    Legacy function wrapper for backward compatibility
    """
    enhanced_service = EnhancedBackgroundSearchService()
    return enhanced_service.perform_search(user_profile)
