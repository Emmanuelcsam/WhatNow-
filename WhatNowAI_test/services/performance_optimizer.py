"""
Performance Monitoring and Caching System

This module provides comprehensive performance monitoring and intelligent caching
to optimize the WhatNowAI application for production use.
"""

import time
import logging
import json
import hashlib
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from pathlib import Path
import threading
from collections import defaultdict, deque
import pickle

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """Performance metric data structure"""
    operation: str
    duration: float
    timestamp: datetime
    success: bool
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class CacheEntry:
    """Cache entry with expiration and metadata"""
    key: str
    data: Any
    created_at: datetime
    expires_at: datetime
    access_count: int = 0
    last_accessed: datetime = None

    def __post_init__(self):
        if self.last_accessed is None:
            self.last_accessed = self.created_at

    def is_expired(self) -> bool:
        """Check if cache entry has expired"""
        return datetime.now() > self.expires_at

    def is_fresh(self, max_age_minutes: int = 30) -> bool:
        """Check if cache entry is fresh enough"""
        age = datetime.now() - self.created_at
        return age.total_seconds() < (max_age_minutes * 60)


class PerformanceMonitor:
    """Production performance monitoring system"""

    def __init__(self, max_metrics: int = 1000):
        self.metrics = deque(maxlen=max_metrics)
        self.operation_stats = defaultdict(list)
        self.start_times = {}
        self.lock = threading.Lock()

    def start_operation(self, operation: str, operation_id: str = None) -> str:
        """Start timing an operation"""
        op_id = operation_id or f"{operation}_{int(time.time()*1000)}"
        with self.lock:
            self.start_times[op_id] = {
                'operation': operation,
                'start_time': time.time(),
                'timestamp': datetime.now()
            }
        return op_id

    def end_operation(self, operation_id: str, success: bool = True, metadata: Dict[str, Any] = None):
        """End timing an operation"""
        end_time = time.time()
        
        with self.lock:
            if operation_id not in self.start_times:
                logger.warning(f"Operation ID {operation_id} not found in start times")
                return

            start_info = self.start_times.pop(operation_id)
            duration = end_time - start_info['start_time']

            metric = PerformanceMetric(
                operation=start_info['operation'],
                duration=duration,
                timestamp=start_info['timestamp'],
                success=success,
                metadata=metadata or {}
            )

            self.metrics.append(metric)
            self.operation_stats[start_info['operation']].append(metric)

    def get_operation_stats(self, operation: str) -> Dict[str, Any]:
        """Get statistics for a specific operation"""
        with self.lock:
            metrics = self.operation_stats.get(operation, [])
            
            if not metrics:
                return {'count': 0}

            durations = [m.duration for m in metrics if m.success]
            success_count = sum(1 for m in metrics if m.success)
            total_count = len(metrics)

            return {
                'count': total_count,
                'success_count': success_count,
                'success_rate': success_count / total_count if total_count > 0 else 0,
                'avg_duration': sum(durations) / len(durations) if durations else 0,
                'min_duration': min(durations) if durations else 0,
                'max_duration': max(durations) if durations else 0,
                'recent_failures': sum(1 for m in metrics[-10:] if not m.success)
            }

    def get_performance_report(self) -> str:
        """Generate a human-readable performance report"""
        with self.lock:
            operations = list(self.operation_stats.keys())
            
            if not operations:
                return "No performance data available"

            report_lines = ["=== Performance Report ==="]
            
            for operation in operations:
                stats = self.get_operation_stats(operation)
                
                status = "🟢" if stats['success_rate'] > 0.9 else "🟡" if stats['success_rate'] > 0.7 else "🔴"
                
                report_lines.append(
                    f"{status} {operation}: "
                    f"{stats['success_rate']:.1%} success, "
                    f"{stats['avg_duration']:.2f}s avg, "
                    f"{stats['count']} total"
                )

            return "\n".join(report_lines)


class IntelligentCache:
    """Intelligent caching system with automatic cleanup and performance optimization"""

    def __init__(self, max_size: int = 1000, default_ttl_minutes: int = 30):
        self.max_size = max_size
        self.default_ttl = timedelta(minutes=default_ttl_minutes)
        self.cache = {}
        self.access_order = deque()
        self.lock = threading.Lock()
        self.hit_count = 0
        self.miss_count = 0

    def _generate_key(self, data: Any) -> str:
        """Generate a cache key from data"""
        if isinstance(data, dict):
            # Sort dict for consistent key generation
            sorted_data = json.dumps(data, sort_keys=True)
        else:
            sorted_data = str(data)
        
        return hashlib.md5(sorted_data.encode()).hexdigest()

    def _cleanup_expired(self):
        """Remove expired entries"""
        now = datetime.now()
        expired_keys = [
            key for key, entry in self.cache.items()
            if entry.is_expired()
        ]
        
        for key in expired_keys:
            del self.cache[key]
            try:
                self.access_order.remove(key)
            except ValueError:
                pass

    def _evict_lru(self):
        """Evict least recently used entries if cache is full"""
        while len(self.cache) >= self.max_size and self.access_order:
            lru_key = self.access_order.popleft()
            if lru_key in self.cache:
                del self.cache[lru_key]

    def get(self, key_data: Any, default: Any = None) -> Any:
        """Get item from cache"""
        key = self._generate_key(key_data)
        
        with self.lock:
            if key in self.cache:
                entry = self.cache[key]
                
                if not entry.is_expired():
                    # Update access info
                    entry.access_count += 1
                    entry.last_accessed = datetime.now()
                    
                    # Move to end of access order
                    try:
                        self.access_order.remove(key)
                    except ValueError:
                        pass
                    self.access_order.append(key)
                    
                    self.hit_count += 1
                    return entry.data
                else:
                    # Remove expired entry
                    del self.cache[key]
                    try:
                        self.access_order.remove(key)
                    except ValueError:
                        pass

            self.miss_count += 1
            return default

    def set(self, key_data: Any, value: Any, ttl_minutes: int = None) -> None:
        """Set item in cache"""
        key = self._generate_key(key_data)
        ttl = timedelta(minutes=ttl_minutes) if ttl_minutes else self.default_ttl
        
        with self.lock:
            # Cleanup and eviction
            self._cleanup_expired()
            self._evict_lru()
            
            # Create new entry
            now = datetime.now()
            entry = CacheEntry(
                key=key,
                data=value,
                created_at=now,
                expires_at=now + ttl
            )
            
            self.cache[key] = entry
            self.access_order.append(key)

    def invalidate_pattern(self, pattern: str):
        """Invalidate cache entries matching a pattern"""
        with self.lock:
            keys_to_remove = [
                key for key in self.cache.keys()
                if pattern in str(key)
            ]
            
            for key in keys_to_remove:
                del self.cache[key]
                try:
                    self.access_order.remove(key)
                except ValueError:
                    pass

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self.lock:
            total_requests = self.hit_count + self.miss_count
            hit_rate = self.hit_count / total_requests if total_requests > 0 else 0
            
            return {
                'size': len(self.cache),
                'max_size': self.max_size,
                'hit_count': self.hit_count,
                'miss_count': self.miss_count,
                'hit_rate': hit_rate,
                'expired_entries': sum(1 for entry in self.cache.values() if entry.is_expired())
            }


class ProductionOptimizer:
    """Production optimization system combining monitoring and caching"""

    def __init__(self, cache_size: int = 1000, cache_ttl_minutes: int = 30):
        self.monitor = PerformanceMonitor()
        self.cache = IntelligentCache(cache_size, cache_ttl_minutes)
        
        # Cache categories for different types of data
        self.search_cache = IntelligentCache(500, 15)  # Search results - shorter TTL
        self.api_cache = IntelligentCache(300, 60)     # API responses - longer TTL
        self.user_cache = IntelligentCache(200, 30)    # User profiles - medium TTL

    def time_operation(self, operation: str):
        """Decorator to time operations"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                op_id = self.monitor.start_operation(operation)
                
                try:
                    result = func(*args, **kwargs)
                    self.monitor.end_operation(op_id, success=True)
                    return result
                except Exception as e:
                    self.monitor.end_operation(op_id, success=False, metadata={'error': str(e)})
                    raise
                    
            return wrapper
        return decorator

    def cached_search(self, search_params: Dict[str, Any], search_func, ttl_minutes: int = 15):
        """Cached search execution"""
        # Check cache first
        cached_result = self.search_cache.get(search_params)
        if cached_result is not None:
            logger.debug(f"Cache hit for search: {search_params}")
            return cached_result

        # Execute search and cache result
        op_id = self.monitor.start_operation("cached_search")
        try:
            result = search_func()
            self.search_cache.set(search_params, result, ttl_minutes)
            self.monitor.end_operation(op_id, success=True)
            return result
        except Exception as e:
            self.monitor.end_operation(op_id, success=False, metadata={'error': str(e)})
            raise

    def cached_api_call(self, api_params: Dict[str, Any], api_func, ttl_minutes: int = 60):
        """Cached API call execution"""
        # Check cache first
        cached_result = self.api_cache.get(api_params)
        if cached_result is not None:
            logger.debug(f"Cache hit for API call: {api_params}")
            return cached_result

        # Execute API call and cache result
        op_id = self.monitor.start_operation("cached_api_call")
        try:
            result = api_func()
            self.api_cache.set(api_params, result, ttl_minutes)
            self.monitor.end_operation(op_id, success=True)
            return result
        except Exception as e:
            self.monitor.end_operation(op_id, success=False, metadata={'error': str(e)})
            raise

    def get_comprehensive_report(self) -> Dict[str, Any]:
        """Get comprehensive optimization report"""
        return {
            'performance': self.monitor.get_performance_report(),
            'search_cache_stats': self.search_cache.get_stats(),
            'api_cache_stats': self.api_cache.get_stats(),
            'user_cache_stats': self.user_cache.get_stats(),
            'recommendations': self._get_optimization_recommendations()
        }

    def _get_optimization_recommendations(self) -> List[str]:
        """Generate optimization recommendations"""
        recommendations = []
        
        # Check cache performance
        search_stats = self.search_cache.get_stats()
        if search_stats['hit_rate'] < 0.3:
            recommendations.append("Consider increasing search cache TTL to improve hit rate")
        
        api_stats = self.api_cache.get_stats()
        if api_stats['hit_rate'] < 0.5:
            recommendations.append("Consider increasing API cache TTL to reduce external calls")
        
        # Check for frequent operations
        for operation, metrics in self.monitor.operation_stats.items():
            recent_metrics = metrics[-10:] if len(metrics) > 10 else metrics
            if len(recent_metrics) > 5:
                avg_duration = sum(m.duration for m in recent_metrics) / len(recent_metrics)
                if avg_duration > 5.0:
                    recommendations.append(f"Operation '{operation}' is slow (avg {avg_duration:.2f}s)")
        
        return recommendations


# Global optimizer instance
production_optimizer = ProductionOptimizer()


def get_optimizer() -> ProductionOptimizer:
    """Get the global production optimizer instance"""
    return production_optimizer
