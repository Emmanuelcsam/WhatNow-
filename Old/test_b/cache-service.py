"""
cache_service.py - Caching service for performance optimization
"""
import json
import hashlib
import pickle
import logging
from typing import Any, Optional, Dict, List
from datetime import datetime, timedelta
import redis
import diskcache
from functools import wraps
import threading

logger = logging.getLogger(__name__)

class CacheService:
    """Service for caching data with multiple backends"""
    
    def __init__(self, config):
        self.config = config
        self.cache_dir = config.cache_dir
        
        # Try to initialize Redis
        self.redis_client = None
        try:
            self.redis_client = redis.Redis(
                host='localhost',
                port=6379,
                db=0,
                decode_responses=False
            )
            self.redis_client.ping()
            self.use_redis = True
            logger.info("Redis cache initialized")
        except:
            self.use_redis = False
            logger.info("Redis not available, using disk cache")
        
        # Initialize disk cache as fallback
        self.disk_cache = diskcache.Cache(
            self.cache_dir,
            size_limit=1e9  # 1GB
        )
        
        # Cache statistics
        self.stats = {
            'hits': 0,
            'misses': 0,
            'errors': 0
        }
        self.stats_lock = threading.Lock()
    
    def _generate_key(self, key_parts: List[Any]) -> str:
        """Generate cache key from parts"""
        # Convert all parts to strings and join
        key_str = '|'.join(str(part) for part in key_parts)
        
        # Hash for consistent key length
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache"""
        try:
            # Try Redis first
            if self.use_redis:
                try:
                    value = self.redis_client.get(key)
                    if value is not None:
                        self._record_hit()
                        return pickle.loads(value)
                except Exception as e:
                    logger.debug(f"Redis get error: {e}")
            
            # Fall back to disk cache
            value = self.disk_cache.get(key, default=None)
            if value is not None:
                self._record_hit()
                return value
            
            self._record_miss()
            return default
            
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            self._record_error()
            return default
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with optional TTL (seconds)"""
        try:
            # Default TTL from config
            if ttl is None:
                ttl = self.config.security.cache_expiry_hours * 3600
            
            # Try Redis first
            if self.use_redis:
                try:
                    serialized = pickle.dumps(value)
                    self.redis_client.setex(key, ttl, serialized)
                    return True
                except Exception as e:
                    logger.debug(f"Redis set error: {e}")
            
            # Fall back to disk cache
            self.disk_cache.set(key, value, expire=ttl)
            return True
            
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            self._record_error()
            return False
    
    def delete(self, key: str) -> bool:
        """Delete value from cache"""
        try:
            deleted = False
            
            # Try Redis
            if self.use_redis:
                try:
                    deleted = bool(self.redis_client.delete(key))
                except Exception as e:
                    logger.debug(f"Redis delete error: {e}")
            
            # Also delete from disk cache
            if key in self.disk_cache:
                del self.disk_cache[key]
                deleted = True
            
            return deleted
            
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False
    
    def clear(self) -> bool:
        """Clear all cache"""
        try:
            # Clear Redis
            if self.use_redis:
                try:
                    self.redis_client.flushdb()
                except:
                    pass
            
            # Clear disk cache
            self.disk_cache.clear()
            
            return True
            
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return False
    
    def cache_user_location(self, ip_address: str, location_data: Dict, 
                           ttl: int = 86400) -> bool:
        """Cache user location data"""
        key = self._generate_key(['location', ip_address])
        return self.set(key, location_data, ttl)
    
    def get_user_location(self, ip_address: str) -> Optional[Dict]:
        """Get cached user location"""
        key = self._generate_key(['location', ip_address])
        return self.get(key)
    
    def cache_search_results(self, search_query: Dict, results: List[Dict], 
                           ttl: int = 3600) -> bool:
        """Cache search results"""
        key = self._generate_key([
            'search',
            search_query.get('first_name', ''),
            search_query.get('last_name', ''),
            search_query.get('activity', '')
        ])
        return self.set(key, results, ttl)
    
    def get_search_results(self, search_query: Dict) -> Optional[List[Dict]]:
        """Get cached search results"""
        key = self._generate_key([
            'search',
            search_query.get('first_name', ''),
            search_query.get('last_name', ''),
            search_query.get('activity', '')
        ])
        return self.get(key)
    
    def cache_events(self, cache_key: str, events: List[Dict], 
                    ttl: int = 1800) -> bool:
        """Cache event results"""
        key = self._generate_key(['events', cache_key])
        return self.set(key, events, ttl)
    
    def get_events(self, cache_key: str) -> Optional[List[Dict]]:
        """Get cached events"""
        key = self._generate_key(['events', cache_key])
        return self.get(key)
    
    def cache_processed_data(self, user_id: str, data: Dict, 
                           ttl: int = 7200) -> bool:
        """Cache processed user data"""
        key = self._generate_key(['processed', user_id])
        return self.set(key, data, ttl)
    
    def get_processed_data(self, user_id: str) -> Optional[Dict]:
        """Get cached processed data"""
        key = self._generate_key(['processed', user_id])
        return self.get(key)
    
    def _record_hit(self):
        """Record cache hit"""
        with self.stats_lock:
            self.stats['hits'] += 1
    
    def _record_miss(self):
        """Record cache miss"""
        with self.stats_lock:
            self.stats['misses'] += 1
    
    def _record_error(self):
        """Record cache error"""
        with self.stats_lock:
            self.stats['errors'] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self.stats_lock:
            total = self.stats['hits'] + self.stats['misses']
            hit_rate = (self.stats['hits'] / total * 100) if total > 0 else 0
            
            return {
                'hits': self.stats['hits'],
                'misses': self.stats['misses'],
                'errors': self.stats['errors'],
                'hit_rate': round(hit_rate, 2),
                'backend': 'redis' if self.use_redis else 'disk',
                'disk_cache_size': self.disk_cache.volume()
            }
    
    def cleanup_expired(self) -> int:
        """Clean up expired cache entries"""
        try:
            # Disk cache handles expiration automatically
            # For Redis, we rely on Redis's built-in expiration
            
            # Clean up old disk cache entries
            expired = self.disk_cache.expire()
            return expired
            
        except Exception as e:
            logger.error(f"Cache cleanup error: {e}")
            return 0


def cached(ttl: int = 3600, key_prefix: str = ''):
    """Decorator for caching function results"""
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Generate cache key
            cache_key_parts = [key_prefix or func.__name__]
            cache_key_parts.extend(str(arg) for arg in args)
            cache_key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
            
            cache_key = hashlib.md5(
                '|'.join(cache_key_parts).encode()
            ).hexdigest()
            
            # Try to get from cache
            if hasattr(self, 'cache_service'):
                cached_result = self.cache_service.get(cache_key)
                if cached_result is not None:
                    logger.debug(f"Cache hit for {func.__name__}")
                    return cached_result
            
            # Execute function
            result = func(self, *args, **kwargs)
            
            # Cache result
            if hasattr(self, 'cache_service') and result is not None:
                self.cache_service.set(cache_key, result, ttl)
                logger.debug(f"Cached result for {func.__name__}")
            
            return result
        
        return wrapper
    return decorator


class RateLimiter:
    """Rate limiting implementation"""
    
    def __init__(self, cache_service: CacheService):
        self.cache = cache_service
        self.limits = {}
    
    def add_limit(self, name: str, calls: int, period: int):
        """Add a rate limit rule"""
        self.limits[name] = {'calls': calls, 'period': period}
    
    def check_limit(self, name: str, identifier: str) -> bool:
        """Check if limit is exceeded"""
        if name not in self.limits:
            return True
        
        limit = self.limits[name]
        key = f"ratelimit:{name}:{identifier}"
        
        # Get current count
        current = self.cache.get(key, 0)
        
        if current >= limit['calls']:
            return False
        
        # Increment count
        self.cache.set(key, current + 1, ttl=limit['period'])
        return True
    
    def get_remaining(self, name: str, identifier: str) -> int:
        """Get remaining calls"""
        if name not in self.limits:
            return -1
        
        limit = self.limits[name]
        key = f"ratelimit:{name}:{identifier}"
        current = self.cache.get(key, 0)
        
        return max(0, limit['calls'] - current)


class SessionCache:
    """Session-based caching"""
    
    def __init__(self, cache_service: CacheService):
        self.cache = cache_service
        self.session_ttl = 3600  # 1 hour default
    
    def create_session(self, session_id: str, data: Dict) -> bool:
        """Create new session"""
        key = f"session:{session_id}"
        return self.cache.set(key, data, self.session_ttl)
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session data"""
        key = f"session:{session_id}"
        return self.cache.get(key)
    
    def update_session(self, session_id: str, data: Dict) -> bool:
        """Update session data"""
        key = f"session:{session_id}"
        current = self.get_session(session_id)
        if current:
            current.update(data)
            return self.cache.set(key, current, self.session_ttl)
        return False
    
    def delete_session(self, session_id: str) -> bool:
        """Delete session"""
        key = f"session:{session_id}"
        return self.cache.delete(key)
    
    def extend_session(self, session_id: str) -> bool:
        """Extend session TTL"""
        data = self.get_session(session_id)
        if data:
            return self.create_session(session_id, data)
        return False
