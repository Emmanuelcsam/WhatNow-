"""
Additional Search Engines for Enhanced Fallback Support

This module provides additional search engines beyond DuckDuckGo, Bing, and Yandex
to ensure robust fallback mechanisms and better performance.
"""

import time
import logging
import requests
import random
from typing import List
from datetime import datetime
from urllib.parse import quote_plus
from services.search_engine_base import OptimizedSearchEngine, SearchResult

logger = logging.getLogger(__name__)


class StartPageOptimized(OptimizedSearchEngine):
    """StartPage search engine (privacy-focused Google proxy)"""

    def __init__(self, config: dict = None):
        super().__init__("StartPage", config)
        self.base_url = "https://www.startpage.com/sp/search"

    def search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        """Optimized StartPage search"""
        results = []
        start_time = time.time()

        try:
            self._rate_limit()

            # StartPage parameters
            params = {
                'query': query,
                'cat': 'web',
                'cmd': 'process_search',
                'language': 'english',
                'engine0': 'v1all',
                'abp': '-1'
            }

            response = self.session.get(self.base_url, params=params, timeout=self.timeout)

            if response.status_code == 200:
                results = self._parse_startpage_response(response, query)
                self._update_performance(True, time.time() - start_time)
            else:
                self._update_performance(False, time.time() - start_time)

        except Exception as e:
            logger.error(f"StartPage search failed: {e}")
            self._update_performance(False, time.time() - start_time)

        return results[:max_results]

    def _parse_startpage_response(self, response, query: str) -> List[SearchResult]:
        """Parse StartPage response"""
        results = []

        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')

            # StartPage result selectors
            result_containers = soup.select('.w-gl__result')

            for container in result_containers[:10]:
                title_elem = container.select_one('.w-gl__result-title a')
                snippet_elem = container.select_one('.w-gl__description')

                if title_elem:
                    title = title_elem.get_text(strip=True)
                    url = title_elem.get('href', '')
                    snippet = snippet_elem.get_text(strip=True) if snippet_elem else ''

                    results.append(SearchResult(
                        title=title,
                        url=url,
                        snippet=snippet,
                        source='startpage',
                        timestamp=datetime.now()
                    ))

        except Exception as e:
            logger.warning(f"Failed to parse StartPage response: {e}")

        return results


class SearxOptimized(OptimizedSearchEngine):
    """SearX search engine (open source metasearch)"""

    def __init__(self, config: dict = None):
        super().__init__("SearX", config)
        # Use public SearX instances
        self.instances = [
            "https://searx.be",
            "https://searx.info",
            "https://search.disroot.org",
            "https://searx.prvcy.eu"
        ]
        self.current_instance = 0

    def search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        """Optimized SearX search with instance rotation"""
        results = []
        start_time = time.time()

        try:
            self._rate_limit()

            # Try different SearX instances
            for attempt in range(min(len(self.instances), 2)):
                instance_url = self.instances[self.current_instance]

                try:
                    params = {
                        'q': query,
                        'format': 'json',
                        'categories': 'general',
                        'engines': 'google,bing,duckduckgo'
                    }

                    response = self.session.get(
                        f"{instance_url}/search",
                        params=params,
                        timeout=self.timeout
                    )

                    if response.status_code == 200:
                        results = self._parse_searx_response(response, query)
                        self._update_performance(True, time.time() - start_time)
                        break
                    else:
                        self.current_instance = (self.current_instance + 1) % len(self.instances)
                        continue

                except requests.RequestException:
                    self.current_instance = (self.current_instance + 1) % len(self.instances)
                    continue

            if not results:
                self._update_performance(False, time.time() - start_time)

        except Exception as e:
            logger.error(f"SearX search failed: {e}")
            self._update_performance(False, time.time() - start_time)

        return results[:max_results]

    def _parse_searx_response(self, response, query: str) -> List[SearchResult]:
        """Parse SearX JSON response"""
        results = []

        try:
            data = response.json()
            
            for item in data.get('results', [])[:10]:
                results.append(SearchResult(
                    title=item.get('title', ''),
                    url=item.get('url', ''),
                    snippet=item.get('content', ''),
                    source='searx',
                    timestamp=datetime.now(),
                    metadata={'engine': item.get('engine', 'unknown')}
                ))

        except Exception as e:
            logger.warning(f"Failed to parse SearX response: {e}")

        return results


class BraveSearchOptimized(OptimizedSearchEngine):
    """Brave Search engine"""

    def __init__(self, config: dict = None):
        super().__init__("BraveSearch", config)
        self.base_url = "https://search.brave.com/search"

    def search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        """Optimized Brave Search"""
        results = []
        start_time = time.time()

        try:
            self._rate_limit()

            params = {
                'q': query,
                'source': 'web'
            }

            # Use a browser-like user agent for Brave
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive'
            }

            response = self.session.get(
                self.base_url,
                params=params,
                headers=headers,
                timeout=self.timeout
            )

            if response.status_code == 200:
                results = self._parse_brave_response(response, query)
                self._update_performance(True, time.time() - start_time)
            else:
                self._update_performance(False, time.time() - start_time)

        except Exception as e:
            logger.error(f"Brave Search failed: {e}")
            self._update_performance(False, time.time() - start_time)

        return results[:max_results]

    def _parse_brave_response(self, response, query: str) -> List[SearchResult]:
        """Parse Brave Search response"""
        results = []

        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')

            # Brave search result selectors
            result_containers = soup.select('[data-type="web"] .snippet')

            for container in result_containers[:10]:
                title_elem = container.select_one('.title a')
                snippet_elem = container.select_one('.snippet-description')

                if title_elem:
                    title = title_elem.get_text(strip=True)
                    url = title_elem.get('href', '')
                    snippet = snippet_elem.get_text(strip=True) if snippet_elem else ''

                    results.append(SearchResult(
                        title=title,
                        url=url,
                        snippet=snippet,
                        source='brave',
                        timestamp=datetime.now()
                    ))

        except Exception as e:
            logger.warning(f"Failed to parse Brave Search response: {e}")

        return results


class GigablastOptimized(OptimizedSearchEngine):
    """Gigablast search engine (independent search engine)"""

    def __init__(self, config: dict = None):
        super().__init__("Gigablast", config)
        self.base_url = "https://www.gigablast.com/search"

    def search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        """Optimized Gigablast search"""
        results = []
        start_time = time.time()

        try:
            self._rate_limit()

            params = {
                'q': query,
                'format': 'json',
                'n': max_results * 2  # Get more for better filtering
            }

            response = self.session.get(self.base_url, params=params, timeout=self.timeout)

            if response.status_code == 200:
                results = self._parse_gigablast_response(response, query)
                self._update_performance(True, time.time() - start_time)
            else:
                self._update_performance(False, time.time() - start_time)

        except Exception as e:
            logger.error(f"Gigablast search failed: {e}")
            self._update_performance(False, time.time() - start_time)

        return results[:max_results]

    def _parse_gigablast_response(self, response, query: str) -> List[SearchResult]:
        """Parse Gigablast JSON response"""
        results = []

        try:
            data = response.json()
            
            for item in data.get('results', [])[:10]:
                results.append(SearchResult(
                    title=item.get('title', ''),
                    url=item.get('url', ''),
                    snippet=item.get('sum', ''),  # Gigablast uses 'sum' for snippet
                    source='gigablast',
                    timestamp=datetime.now()
                ))

        except Exception as e:
            logger.warning(f"Failed to parse Gigablast response: {e}")

        return results


# Registry of additional search engines
ADDITIONAL_SEARCH_ENGINES = {
    'startpage': StartPageOptimized,
    'searx': SearxOptimized,
    'brave': BraveSearchOptimized,
    'gigablast': GigablastOptimized
}
