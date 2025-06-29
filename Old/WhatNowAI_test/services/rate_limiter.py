"""
Rate Limiter Service
Provides rate limiting for API calls to prevent exceeding quotas
"""
import time
import logging
from typing import Dict, Any, Optional
from collections import defaultdict, deque
from threading import Lock

from config.settings import RATE_LIMIT_CONFIG

logger = logging.getLogger(__name__)


class RateLimiter:
    """Thread-safe rate limiter for API calls"""

    def __init__(self, config: Dict[str, Any] = None):
        """Initialize rate limiter with configuration"""
        self.config = config or RATE_LIMIT_CONFIG
        self.call_history = defaultdict(deque)
        self.lock = Lock()

        logger.info("Rate limiter initialized")

    def can_make_request(self, service: str) -> bool:
        """
        Check if a request can be made for the given service

        Args:
            service: Service name (e.g., 'ticketmaster', 'openai')

        Returns:
            True if request can be made, False otherwise
        """
        with self.lock:
            service_config = self.config.get(service, self.config.get('DEFAULT', {}))

            if not service_config:
                return True  # No rate limiting configured

            calls_limit = service_config.get('calls', 100)
            window_seconds = service_config.get('window', 3600)

            now = time.time()
            cutoff_time = now - window_seconds

            # Clean old entries
            history = self.call_history[service]
            while history and history[0] < cutoff_time:
                history.popleft()

            # Check if we can make another call
            return len(history) < calls_limit

    def record_request(self, service: str):
        """
        Record that a request was made for the given service

        Args:
            service: Service name
        """
        with self.lock:
            self.call_history[service].append(time.time())

    def wait_if_needed(self, service: str) -> float:
        """
        Wait if needed to respect rate limits

        Args:
            service: Service name

        Returns:
            Time waited in seconds
        """
        with self.lock:
            service_config = self.config.get(service, self.config.get('DEFAULT', {}))

            if not service_config:
                return 0.0

            calls_limit = service_config.get('calls', 100)
            window_seconds = service_config.get('window', 3600)

            now = time.time()
            cutoff_time = now - window_seconds

            # Clean old entries
            history = self.call_history[service]
            while history and history[0] < cutoff_time:
                history.popleft()

            if len(history) >= calls_limit:
                # Need to wait until oldest entry expires
                wait_until = history[0] + window_seconds
                wait_time = max(0, wait_until - now)

                if wait_time > 0:
                    logger.info(f"Rate limiting: waiting {wait_time:.2f}s for {service}")
                    time.sleep(wait_time)
                    return wait_time

            return 0.0

    def get_status(self, service: str) -> Dict[str, Any]:
        """
        Get current rate limit status for a service

        Args:
            service: Service name

        Returns:
            Status information
        """
        with self.lock:
            service_config = self.config.get(service, self.config.get('DEFAULT', {}))

            if not service_config:
                return {'rate_limiting': False}

            calls_limit = service_config.get('calls', 100)
            window_seconds = service_config.get('window', 3600)

            now = time.time()
            cutoff_time = now - window_seconds

            # Clean old entries
            history = self.call_history[service]
            while history and history[0] < cutoff_time:
                history.popleft()

            calls_made = len(history)
            remaining_calls = max(0, calls_limit - calls_made)

            # Calculate reset time
            reset_time = None
            if history:
                reset_time = history[0] + window_seconds

            return {
                'rate_limiting': True,
                'calls_limit': calls_limit,
                'window_seconds': window_seconds,
                'calls_made': calls_made,
                'remaining_calls': remaining_calls,
                'reset_time': reset_time,
                'can_make_request': remaining_calls > 0
            }

    def get_all_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status for all configured services"""
        status = {}

        for service in self.config.keys():
            if service != 'DEFAULT':
                status[service] = self.get_status(service)

        return status


# Global rate limiter instance
_rate_limiter = None


def get_rate_limiter() -> RateLimiter:
    """Get global rate limiter instance"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter


def rate_limited(service: str):
    """
    Decorator for rate-limited API calls

    Args:
        service: Service name for rate limiting
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            limiter = get_rate_limiter()

            # Wait if needed
            limiter.wait_if_needed(service)

            # Record the request
            limiter.record_request(service)

            # Make the call
            return func(*args, **kwargs)

        return wrapper
    return decorator
