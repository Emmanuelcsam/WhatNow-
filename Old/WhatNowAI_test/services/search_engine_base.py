"""
Base Search Engine Classes

This module contains the base classes used by all search engines to avoid circular imports.
"""

import time
import logging
import requests
import random
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Optimized search result with performance metrics"""
    title: str
    url: str
    snippet: str
    source: str
    timestamp: datetime
    relevance_score: float = 0.0
    load_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SearchEnginePerformance:
    """Performance metrics for search engines"""
    name: str
    success_rate: float = 0.0
    avg_response_time: float = 0.0
    rate_limit_hits: int = 0
    total_requests: int = 0
    last_successful: Optional[datetime] = None
    is_available: bool = True


class OptimizedSearchEngine:
    """Base class for optimized search engines"""

    def __init__(self, name: str, config: Dict[str, Any] = None):
        self.name = name
        self.config = config or {}
        self.performance = SearchEnginePerformance(name=name)
        self.last_request_time = 0
        self.min_delay = self.config.get('min_delay', 1.0)
        self.timeout = self.config.get('timeout', 5.0)
        self.max_retries = self.config.get('max_retries', 2)

        # Session with optimized settings
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self._get_random_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })

    def _get_random_user_agent(self) -> str:
        """Get a random user agent for requests"""
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0'
        ]
        return random.choice(user_agents)

    def _rate_limit(self):
        """Implement intelligent rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        # Adaptive delay based on recent performance
        if self.performance.rate_limit_hits > 3:
            delay = self.min_delay * 2  # Double delay if hitting rate limits
        else:
            delay = self.min_delay

        if time_since_last < delay:
            sleep_time = delay - time_since_last + random.uniform(0.1, 0.5)
            time.sleep(sleep_time)

        self.last_request_time = time.time()

    def search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        """Abstract search method to be implemented by subclasses"""
        raise NotImplementedError

    def _update_performance(self, success: bool, response_time: float, rate_limited: bool = False):
        """Update performance metrics"""
        self.performance.total_requests += 1

        if success:
            self.performance.last_successful = datetime.now()
            # Update success rate with exponential moving average
            alpha = 0.1
            self.performance.success_rate = (
                alpha * 1.0 + (1 - alpha) * self.performance.success_rate
            )
        else:
            alpha = 0.1
            self.performance.success_rate = (
                alpha * 0.0 + (1 - alpha) * self.performance.success_rate
            )

        if rate_limited:
            self.performance.rate_limit_hits += 1

        # Update average response time
        alpha = 0.2
        self.performance.avg_response_time = (
            alpha * response_time + (1 - alpha) * self.performance.avg_response_time
        )

        # Mark as unavailable if too many failures
        if self.performance.success_rate < 0.2 and self.performance.total_requests > 5:
            self.performance.is_available = False
            logger.warning(f"Marking {self.name} as unavailable due to poor performance")
