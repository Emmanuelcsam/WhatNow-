"""
Production-Optimized OSINT Web Scraping Service

This module provides optimized web scraping for production use with:
- Multiple search engine backends with fallback support
- Intelligent rate limiting and request optimization
- Fast minimal crawling with targeted data extraction
- Robust error handling and retry mechanisms
- Performance monitoring and optimization
"""

import asyncio
import aiohttp
import requests
import time
import logging
import random
import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from urllib.parse import quote_plus, urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed
import re
from pathlib import Path
import sys

# Add search methods to path
sys.path.append(str(Path(__file__).parent.parent / 'search_methods_2'))

from services.search_engine_base import (
    SearchResult, SearchEnginePerformance, OptimizedSearchEngine
)
from services.additional_search_engines import (
    StartPageOptimized, SearxOptimized, BraveSearchOptimized, GigablastOptimized
)

logger = logging.getLogger(__name__)


# Base classes imported from search_engine_base


class DuckDuckGoOptimized(OptimizedSearchEngine):
    """Optimized DuckDuckGo search with fallback strategies and improved timeout handling"""

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("DuckDuckGo", config)
        self.base_urls = [
            "https://lite.duckduckgo.com/lite/",
            "https://duckduckgo.com/html/",
            "https://start.duckduckgo.com/"
        ]
        self.current_url_index = 0

    def search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        """Optimized DuckDuckGo search with multiple backends"""
        results = []
        start_time = time.time()

        try:
            self._rate_limit()

            # Try different DuckDuckGo backends
            for attempt in range(min(len(self.base_urls), self.max_retries)):
                url = self.base_urls[self.current_url_index]

                try:
                    params = {
                        'q': query,
                        'kl': 'us-en',
                        'o': 'json' if 'lite' in url else 'html'
                    }

                    response = self.session.get(url, params=params, timeout=5)

                    if response.status_code == 200:
                        results = self._parse_duckduckgo_response(response, query)
                        self._update_performance(True, time.time() - start_time)
                        break
                    elif response.status_code == 202:  # Rate limited
                        self._update_performance(False, time.time() - start_time, rate_limited=True)
                        self.current_url_index = (self.current_url_index + 1) % len(self.base_urls)
                        time.sleep(2)  # Wait before trying next backend
                        continue
                    else:
                        logger.warning(f"DuckDuckGo returned status {response.status_code}")

                except requests.exceptions.Timeout as e:
                    logger.warning(f"DuckDuckGo timeout on {url}: {e}")
                    self.current_url_index = (self.current_url_index + 1) % len(self.base_urls)
                    continue
                except requests.RequestException as e:
                    logger.warning(f"DuckDuckGo request failed on {url}: {e}")
                    self.current_url_index = (self.current_url_index + 1) % len(self.base_urls)
                    continue

            if not results:
                self._update_performance(False, time.time() - start_time)

        except Exception as e:
            logger.error(f"DuckDuckGo search failed: {e}")
            self._update_performance(False, time.time() - start_time)

        return results[:max_results]

    def _parse_duckduckgo_response(self, response, query: str) -> List[SearchResult]:
        """Parse DuckDuckGo response"""
        results = []

        try:
            if 'json' in response.headers.get('content-type', ''):
                # JSON response
                data = response.json()
                for item in data.get('results', [])[:10]:
                    results.append(SearchResult(
                        title=item.get('title', ''),
                        url=item.get('url', ''),
                        snippet=item.get('snippet', ''),
                        source='duckduckgo',
                        timestamp=datetime.now(),
                        metadata={'backend': 'json'}
                    ))
            else:
                # HTML response - quick parsing
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.text, 'html.parser')

                # Find result links (different selectors for different backends)
                selectors = [
                    'a[class*="result"]',
                    '.result__a',
                    '.web-result a',
                    'h2 a'
                ]

                for selector in selectors:
                    links = soup.select(selector)
                    if links:
                        for link in links[:10]:
                            title = link.get_text(strip=True)
                            url = link.get('href', '')

                            # Find snippet
                            snippet = ""
                            parent = link.find_parent()
                            if parent:
                                snippet_elem = parent.find(class_=re.compile(r'snippet|description'))
                                if snippet_elem:
                                    snippet = snippet_elem.get_text(strip=True)

                            if title and url:
                                results.append(SearchResult(
                                    title=title,
                                    url=url,
                                    snippet=snippet,
                                    source='duckduckgo',
                                    timestamp=datetime.now(),
                                    metadata={'backend': 'html'}
                                ))
                        break

        except Exception as e:
            logger.warning(f"Failed to parse DuckDuckGo response: {e}")

        return results


class BingOptimized(OptimizedSearchEngine):
    """Optimized Bing search"""

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("Bing", config)
        self.base_url = "https://www.bing.com/search"

    def search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        """Optimized Bing search"""
        results = []
        start_time = time.time()

        try:
            self._rate_limit()

            params = {
                'q': query,
                'count': max_results * 2,  # Get more for better filtering
                'mkt': 'en-US'
            }

            response = self.session.get(self.base_url, params=params, timeout=self.timeout)

            if response.status_code == 200:
                results = self._parse_bing_response(response, query)
                self._update_performance(True, time.time() - start_time)
            else:
                self._update_performance(False, time.time() - start_time)

        except Exception as e:
            logger.error(f"Bing search failed: {e}")
            self._update_performance(False, time.time() - start_time)

        return results[:max_results]

    def _parse_bing_response(self, response, query: str) -> List[SearchResult]:
        """Parse Bing response"""
        results = []

        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')

            # Bing result selectors
            result_containers = soup.select('.b_algo')

            for container in result_containers[:10]:
                title_elem = container.select_one('h2 a')
                snippet_elem = container.select_one('.b_caption p')

                if title_elem:
                    title = title_elem.get_text(strip=True)
                    url = title_elem.get('href', '')
                    snippet = snippet_elem.get_text(strip=True) if snippet_elem else ''

                    results.append(SearchResult(
                        title=title,
                        url=url,
                        snippet=snippet,
                        source='bing',
                        timestamp=datetime.now()
                    ))

        except Exception as e:
            logger.warning(f"Failed to parse Bing response: {e}")

        return results


class YandexOptimized(OptimizedSearchEngine):
    """Optimized Yandex search as fallback"""

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("Yandex", config)
        self.base_url = "https://yandex.com/search/"

    def search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        """Optimized Yandex search"""
        results = []
        start_time = time.time()

        try:
            self._rate_limit()

            params = {
                'text': query,
                'lr': 213,  # Region ID for international
                'numdoc': max_results * 2
            }

            response = self.session.get(self.base_url, params=params, timeout=self.timeout)

            if response.status_code == 200:
                results = self._parse_yandex_response(response, query)
                self._update_performance(True, time.time() - start_time)
            else:
                self._update_performance(False, time.time() - start_time)

        except Exception as e:
            logger.error(f"Yandex search failed: {e}")
            self._update_performance(False, time.time() - start_time)

        return results[:max_results]

    def _parse_yandex_response(self, response, query: str) -> List[SearchResult]:
        """Parse Yandex response"""
        results = []

        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')

            # Yandex result selectors
            result_containers = soup.select('.serp-item')

            for container in result_containers[:10]:
                title_elem = container.select_one('.organic__url-text, .organic__title-wrapper a')
                snippet_elem = container.select_one('.organic__text')

                if title_elem:
                    title = title_elem.get_text(strip=True)
                    url = title_elem.get('href', '')
                    snippet = snippet_elem.get_text(strip=True) if snippet_elem else ''

                    results.append(SearchResult(
                        title=title,
                        url=url,
                        snippet=snippet,
                        source='yandex',
                        timestamp=datetime.now()
                    ))

        except Exception as e:
            logger.warning(f"Failed to parse Yandex response: {e}")

        return results


class ProductionOSINTService:
    """Production-optimized OSINT service with multiple search backends"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.search_engines = []
        self.performance_monitor = {}

        # Initialize search engines
        self._initialize_search_engines()

        # Fast crawl settings
        self.max_concurrent = self.config.get('max_concurrent', 3)
        self.fast_timeout = self.config.get('fast_timeout', 3.0)
        self.minimal_crawl_mode = self.config.get('minimal_crawl_mode', True)

        logger.info("Production OSINT service initialized with optimized settings")

    def _initialize_search_engines(self):
        """Initialize available search engines"""
        engine_configs = {
            'duckduckgo': {'min_delay': 0.5, 'timeout': 3.0},
            'bing': {'min_delay': 1.0, 'timeout': 4.0},
            'yandex': {'min_delay': 1.5, 'timeout': 5.0},
            'startpage': {'min_delay': 1.0, 'timeout': 4.0},
            'searx': {'min_delay': 0.8, 'timeout': 3.5},
            'brave': {'min_delay': 1.2, 'timeout': 4.5},
            'gigablast': {'min_delay': 2.0, 'timeout': 6.0}
        }

        engines = [
            # Primary engines (fast and reliable)
            DuckDuckGoOptimized(engine_configs['duckduckgo']),
            BingOptimized(engine_configs['bing']),
            StartPageOptimized(engine_configs['startpage']),
            SearxOptimized(engine_configs['searx']),
            
            # Fallback engines  
            YandexOptimized(engine_configs['yandex']),
            BraveSearchOptimized(engine_configs['brave']),
            GigablastOptimized(engine_configs['gigablast'])
        ]

        # Test engine availability
        for engine in engines:
            try:
                # Quick test search
                test_results = engine.search("test", max_results=1)
                if len(test_results) > 0 or engine.performance.success_rate > 0:
                    self.search_engines.append(engine)
                    logger.info(f"Search engine {engine.name} is available")
                else:
                    logger.warning(f"Search engine {engine.name} failed initial test")
            except Exception as e:
                logger.warning(f"Search engine {engine.name} initialization failed: {e}")

    def get_best_performing_engines(self, count: int = 2) -> List[OptimizedSearchEngine]:
        """Get the best performing search engines"""
        available_engines = [e for e in self.search_engines if e.performance.is_available]

        # Sort by performance score
        scored_engines = []
        for engine in available_engines:
            # Performance score combines success rate, response time, and recency
            score = engine.performance.success_rate * 0.6
            if engine.performance.avg_response_time > 0:
                score += (1.0 / engine.performance.avg_response_time) * 0.3
            if engine.performance.last_successful:
                time_since = (datetime.now() - engine.performance.last_successful).total_seconds()
                recency_score = max(0, 1.0 - (time_since / 3600))  # Decay over hour
                score += recency_score * 0.1
            scored_engines.append((engine, score))

        # Sort by score and return top performers
        scored_engines.sort(key=lambda x: x[1], reverse=True)
        return [engine for engine, score in scored_engines[:count]]

    def fast_multi_engine_search(
        self,
        query: str,
        max_results_per_engine: int = 3,
        timeout: float = 8.0
    ) -> List[SearchResult]:
        """Fast multi-engine search with concurrent execution"""
        best_engines = self.get_best_performing_engines(count=2)

        if not best_engines:
            logger.warning("No available search engines for fast search")
            return []

        all_results = []

        # Use ThreadPoolExecutor for concurrent searches
        with ThreadPoolExecutor(max_workers=len(best_engines)) as executor:
            future_to_engine = {
                executor.submit(engine.search, query, max_results_per_engine): engine
                for engine in best_engines
            }

            for future in as_completed(future_to_engine, timeout=timeout):
                engine = future_to_engine[future]
                try:
                    results = future.result(timeout=2.0)
                    all_results.extend(results)
                    logger.debug(f"Engine {engine.name} returned {len(results)} results")
                except Exception as e:
                    logger.warning(f"Engine {engine.name} search failed: {e}")

        # Remove duplicates and sort by relevance
        unique_results = self._deduplicate_results(all_results)
        return unique_results

    def _deduplicate_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """Remove duplicate results based on URL similarity"""
        seen_urls = set()
        unique_results = []

        for result in results:
            # Normalize URL for comparison
            normalized_url = result.url.lower().strip('/')

            if normalized_url not in seen_urls and normalized_url:
                seen_urls.add(normalized_url)
                unique_results.append(result)

        return unique_results

    def perform_fast_osint_search(
        self,
        user_profile: Dict[str, Any],
        timeout: float = 10.0
    ) -> Dict[str, Any]:
        """
        Perform fast OSINT search optimized for production

        Args:
            user_profile: User profile data
            timeout: Maximum search time

        Returns:
            Dictionary with search results and metadata
        """
        start_time = time.time()

        # Build targeted search queries
        queries = self._build_targeted_queries(user_profile)

        all_results = []
        sources_used = []

        # Perform searches with time limit
        for query in queries:
            if time.time() - start_time > timeout:
                break

            remaining_time = timeout - (time.time() - start_time)
            if remaining_time < 2.0:
                break

            try:
                results = self.fast_multi_engine_search(
                    query,
                    max_results_per_engine=2,
                    timeout=min(remaining_time, 5.0)
                )
                all_results.extend(results)

                # Track which engines were used
                for result in results:
                    if result.source not in sources_used:
                        sources_used.append(result.source)

            except Exception as e:
                logger.warning(f"Fast search for query '{query}' failed: {e}")

        # Process and filter results
        filtered_results = self._filter_results_for_interests(all_results, user_profile)

        search_time = time.time() - start_time

        return {
            'results': filtered_results,
            'total_found': len(all_results),
            'filtered_count': len(filtered_results),
            'sources_used': sources_used,
            'search_time': search_time,
            'queries_executed': len(queries),
            'performance_summary': self._get_performance_summary()
        }

    def _build_targeted_queries(self, user_profile: Dict[str, Any]) -> List[str]:
        """Build targeted search queries based on user profile"""
        name = user_profile.get('name', '')
        location = user_profile.get('location', '')
        activity = user_profile.get('activity', '')
        interests = user_profile.get('interests', [])

        queries = []

        # Basic identity queries (minimal for privacy)
        if name and len(name.split()) >= 2:
            first_name, last_name = name.split()[0], name.split()[-1]
            if location:
                queries.append(f'"{first_name} {last_name}" {location}')

        # Activity-based queries
        if activity and location:
            queries.extend([
                f"{activity} {location}",
                f"{activity} events {location}",
                f"upcoming {activity} {location}"
            ])

        # Interest-based queries (limited to protect privacy)
        for interest in interests[:2]:  # Only top 2 interests
            if location:
                queries.append(f"{interest} {location} events")

        return queries[:5]  # Limit total queries for fast execution

    def _filter_results_for_interests(
        self,
        results: List[SearchResult],
        user_profile: Dict[str, Any]
    ) -> List[SearchResult]:
        """Filter results based on user interests and activity"""
        activity = user_profile.get('activity', '').lower()
        interests = [i.lower() for i in user_profile.get('interests', [])]

        filtered_results = []

        for result in results:
            text = f"{result.title} {result.snippet}".lower()

            # Calculate relevance score
            relevance_score = 0.0

            # Activity matching
            if activity and activity in text:
                relevance_score += 0.4

            # Interest matching
            for interest in interests:
                if interest in text:
                    relevance_score += 0.2

            # Event-related keywords
            event_keywords = ['event', 'festival', 'concert', 'gathering', 'meetup', 'workshop']
            for keyword in event_keywords:
                if keyword in text:
                    relevance_score += 0.1
                    break

            result.relevance_score = relevance_score

            # Only include results with some relevance
            if relevance_score > 0.1:
                filtered_results.append(result)

        # Sort by relevance
        filtered_results.sort(key=lambda x: x.relevance_score, reverse=True)

        return filtered_results[:10]  # Return top 10 most relevant

    def _get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary of all search engines"""
        summary = {}

        for engine in self.search_engines:
            summary[engine.name] = {
                'success_rate': engine.performance.success_rate,
                'avg_response_time': engine.performance.avg_response_time,
                'total_requests': engine.performance.total_requests,
                'rate_limit_hits': engine.performance.rate_limit_hits,
                'is_available': engine.performance.is_available
            }

        return summary

    def get_performance_report(self) -> str:
        """Get a human-readable performance report"""
        report_lines = ["=== OSINT Performance Report ==="]

        for engine in self.search_engines:
            perf = engine.performance
            status = "🟢 Available" if perf.is_available else "🔴 Unavailable"

            report_lines.append(
                f"{engine.name}: {status} | "
                f"Success: {perf.success_rate:.1%} | "
                f"Avg Time: {perf.avg_response_time:.2f}s | "
                f"Requests: {perf.total_requests} | "
                f"Rate Limits: {perf.rate_limit_hits}"
            )

        return "\n".join(report_lines)
