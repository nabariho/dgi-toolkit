"""Caching functionality for DGI Toolkit API."""

import functools
import time
from collections.abc import Callable
from typing import Any

from .logging_config import get_logger

logger = get_logger(__name__)


class SimpleCache:
    """Simple in-memory cache implementation."""

    def __init__(self, default_ttl: int = 300):
        """Initialize cache with default TTL.

        Args:
            default_ttl: Default time-to-live in seconds (default: 5 minutes)
        """
        self._cache: dict[str, tuple[Any, float]] = {}
        self.default_ttl = default_ttl
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Any | None:
        """Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        if key in self._cache:
            value, timestamp = self._cache[key]
            if time.time() - timestamp < self.default_ttl:
                self._hits += 1
                logger.debug(f"Cache hit for key: {key}")
                return value
            else:
                # Expired, remove from cache
                del self._cache[key]
                logger.debug(f"Cache expired for key: {key}")

        self._misses += 1
        logger.debug(f"Cache miss for key: {key}")
        return None

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if None)
        """
        ttl = ttl or self.default_ttl
        self._cache[key] = (value, time.time())
        logger.debug(f"Cached value for key: {key} with TTL: {ttl}s")

    def delete(self, key: str) -> None:
        """Delete value from cache.

        Args:
            key: Cache key to delete
        """
        if key in self._cache:
            del self._cache[key]
            logger.debug(f"Deleted cache key: {key}")

    def clear(self) -> None:
        """Clear all cached values."""
        self._cache.clear()
        self._hits = 0
        self._misses = 0
        logger.info("Cache cleared")

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        total_requests = self._hits + self._misses
        hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0

        return {
            "hits": self._hits,
            "misses": self._misses,
            "total_requests": total_requests,
            "hit_rate_percent": round(hit_rate, 2),
            "cache_size": len(self._cache),
            "default_ttl": self.default_ttl,
        }

    def cleanup_expired(self) -> int:
        """Remove expired entries from cache.

        Returns:
            Number of expired entries removed
        """
        current_time = time.time()
        expired_keys = [
            key
            for key, (_, timestamp) in self._cache.items()
            if current_time - timestamp >= self.default_ttl
        ]

        for key in expired_keys:
            del self._cache[key]

        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")

        return len(expired_keys)


# Global cache instance
_cache = SimpleCache()


def get_cache() -> SimpleCache:
    """Get the global cache instance.

    Returns:
        SimpleCache instance
    """
    return _cache


def cache_result(ttl: int | None = None, key_prefix: str = ""):
    """Decorator to cache function results.

    Args:
        ttl: Time-to-live in seconds (uses cache default if None)
        key_prefix: Prefix for cache keys

    Returns:
        Decorated function
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from function name, args, and kwargs
            cache_key = f"{key_prefix}:{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"

            # Try to get from cache
            cached_result = _cache.get(cache_key)
            if cached_result is not None:
                return cached_result

            # Execute function and cache result
            result = func(*args, **kwargs)
            _cache.set(cache_key, result, ttl)

            return result

        return wrapper

    return decorator


def invalidate_cache(pattern: str) -> int:
    """Invalidate cache entries matching a pattern.

    Args:
        pattern: Pattern to match cache keys (simple string matching)

    Returns:
        Number of cache entries invalidated
    """
    cache = get_cache()
    keys_to_delete = [key for key in cache._cache if pattern in key]

    for key in keys_to_delete:
        cache.delete(key)

    logger.info(
        f"Invalidated {len(keys_to_delete)} cache entries matching pattern: {pattern}"
    )
    return len(keys_to_delete)


def get_cache_stats() -> dict[str, Any]:
    """Get cache statistics.

    Returns:
        Dictionary with cache statistics
    """
    return get_cache().get_stats()
