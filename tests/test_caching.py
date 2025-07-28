"""Tests for caching functionality."""

import time
import unittest
from unittest.mock import Mock, patch

from api.caching import (
    SimpleCache,
    cache_result,
    get_cache,
    get_cache_stats,
    invalidate_cache,
)


class TestSimpleCache(unittest.TestCase):
    """Tests for SimpleCache implementation."""

    def test_cache_initialization(self) -> None:
        """Test cache initialization with default TTL."""
        cache = SimpleCache()
        self.assertEqual(cache.default_ttl, 300)
        self.assertEqual(len(cache._cache), 0)
        self.assertEqual(cache._hits, 0)
        self.assertEqual(cache._misses, 0)

    def test_cache_initialization_custom_ttl(self) -> None:
        """Test cache initialization with custom TTL."""
        cache = SimpleCache(default_ttl=600)
        self.assertEqual(cache.default_ttl, 600)

    def test_cache_set_and_get(self) -> None:
        """Test basic cache set and get operations."""
        cache = SimpleCache(default_ttl=100)

        # Set a value
        cache.set("test_key", "test_value")

        # Get the value
        result = cache.get("test_key")
        self.assertEqual(result, "test_value")

    def test_cache_get_nonexistent_key(self) -> None:
        """Test getting a key that doesn't exist."""
        cache = SimpleCache()
        result = cache.get("nonexistent_key")
        self.assertIsNone(result)

    def test_cache_set_with_custom_ttl(self) -> None:
        """Test setting a value with custom TTL."""
        cache = SimpleCache(default_ttl=100)

        # Set with custom TTL
        cache.set("test_key", "test_value", ttl=50)

        # Should still be available
        result = cache.get("test_key")
        self.assertEqual(result, "test_value")

    def test_cache_expiration(self) -> None:
        """Test cache expiration."""
        cache = SimpleCache(default_ttl=0.1)  # Very short TTL

        # Set a value
        cache.set("test_key", "test_value")

        # Should be available immediately
        result = cache.get("test_key")
        self.assertEqual(result, "test_value")

        # Wait for expiration
        time.sleep(0.2)

        # Should be expired
        result = cache.get("test_key")
        self.assertIsNone(result)

    def test_cache_delete(self) -> None:
        """Test cache delete operation."""
        cache = SimpleCache()

        # Set a value
        cache.set("test_key", "test_value")

        # Verify it exists
        result = cache.get("test_key")
        self.assertEqual(result, "test_value")

        # Delete it
        cache.delete("test_key")

        # Should be gone
        result = cache.get("test_key")
        self.assertIsNone(result)

    def test_cache_delete_nonexistent_key(self) -> None:
        """Test deleting a key that doesn't exist."""
        cache = SimpleCache()

        # Should not raise an exception
        cache.delete("nonexistent_key")

    def test_cache_clear(self) -> None:
        """Test cache clear operation."""
        cache = SimpleCache()

        # Set multiple values
        cache.set("key1", "value1")
        cache.set("key2", "value2")

        # Verify they exist
        self.assertEqual(cache.get("key1"), "value1")
        self.assertEqual(cache.get("key2"), "value2")

        # Clear cache
        cache.clear()

        # Should be empty
        self.assertIsNone(cache.get("key1"))
        self.assertIsNone(cache.get("key2"))
        self.assertEqual(cache._hits, 0)
        # Note: clear() resets hits and misses to 0, but the misses from get() calls after clearing are counted
        self.assertEqual(
            cache._misses, 2
        )  # 2 misses from the get() calls after clearing

    def test_cache_stats(self) -> None:
        """Test cache statistics."""
        cache = SimpleCache()

        # Initial stats
        stats = cache.get_stats()
        self.assertEqual(stats["hits"], 0)
        self.assertEqual(stats["misses"], 0)
        self.assertEqual(stats["total_requests"], 0)
        self.assertEqual(stats["hit_rate_percent"], 0)
        self.assertEqual(stats["cache_size"], 0)
        self.assertEqual(stats["default_ttl"], 300)

        # Add some cache activity
        cache.set("key1", "value1")
        cache.get("key1")  # Hit
        cache.get("key2")  # Miss
        cache.get("key1")  # Hit

        stats = cache.get_stats()
        self.assertEqual(stats["hits"], 2)
        self.assertEqual(stats["misses"], 1)
        self.assertEqual(stats["total_requests"], 3)
        self.assertAlmostEqual(stats["hit_rate_percent"], 66.67, places=1)
        self.assertEqual(stats["cache_size"], 1)

    def test_cache_stats_zero_requests(self) -> None:
        """Test cache statistics with zero requests."""
        cache = SimpleCache()
        stats = cache.get_stats()

        self.assertEqual(stats["hits"], 0)
        self.assertEqual(stats["misses"], 0)
        self.assertEqual(stats["total_requests"], 0)
        self.assertEqual(stats["hit_rate_percent"], 0)

    def test_cache_cleanup_expired(self) -> None:
        """Test cleanup of expired entries."""
        cache = SimpleCache(default_ttl=0.1)  # Very short TTL

        # Set multiple values
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")

        # Wait for expiration
        time.sleep(0.2)

        # Cleanup expired entries
        removed_count = cache.cleanup_expired()

        self.assertEqual(removed_count, 3)
        self.assertEqual(len(cache._cache), 0)

    def test_cache_cleanup_no_expired(self) -> None:
        """Test cleanup when no entries are expired."""
        cache = SimpleCache(default_ttl=100)

        # Set a value
        cache.set("key1", "value1")

        # Cleanup (should not remove anything)
        removed_count = cache.cleanup_expired()

        self.assertEqual(removed_count, 0)
        self.assertEqual(len(cache._cache), 1)

    def test_cache_hit_miss_counting(self) -> None:
        """Test that hits and misses are counted correctly."""
        cache = SimpleCache()

        # Initial state
        self.assertEqual(cache._hits, 0)
        self.assertEqual(cache._misses, 0)

        # Miss
        cache.get("nonexistent")
        self.assertEqual(cache._hits, 0)
        self.assertEqual(cache._misses, 1)

        # Set and hit
        cache.set("key1", "value1")
        cache.get("key1")
        self.assertEqual(cache._hits, 1)
        self.assertEqual(cache._misses, 1)

        # Another hit
        cache.get("key1")
        self.assertEqual(cache._hits, 2)
        self.assertEqual(cache._misses, 1)


class TestCacheFunctions(unittest.TestCase):
    """Tests for cache utility functions."""

    @patch("api.caching.get_settings")
    def test_get_cache_initialization(self, mock_get_settings) -> None:
        """Test get_cache function initialization."""
        mock_settings = Mock()
        mock_settings.cache_default_ttl = 600
        mock_get_settings.return_value = mock_settings

        # Clear any existing cache
        import api.caching

        api.caching._cache = None

        cache = get_cache()
        self.assertIsInstance(cache, SimpleCache)
        self.assertEqual(cache.default_ttl, 600)

    @patch("api.caching.get_settings")
    def test_get_cache_singleton(self, mock_get_settings) -> None:
        """Test that get_cache returns the same instance."""
        mock_settings = Mock()
        mock_settings.cache_default_ttl = 300
        mock_get_settings.return_value = mock_settings

        # Clear any existing cache
        import api.caching

        api.caching._cache = None

        cache1 = get_cache()
        cache2 = get_cache()

        self.assertIs(cache1, cache2)

    def test_get_cache_stats(self) -> None:
        """Test get_cache_stats function."""
        # Clear any existing cache
        import api.caching

        api.caching._cache = None

        stats = get_cache_stats()
        self.assertIsInstance(stats, dict)
        self.assertIn("hits", stats)
        self.assertIn("misses", stats)
        self.assertIn("total_requests", stats)
        self.assertIn("hit_rate_percent", stats)
        self.assertIn("cache_size", stats)
        self.assertIn("default_ttl", stats)

    def test_invalidate_cache(self) -> None:
        """Test invalidate_cache function."""
        # Clear any existing cache
        import api.caching

        api.caching._cache = None

        cache = get_cache()

        # Set some test data
        cache.set("test:key1", "value1")
        cache.set("test:key2", "value2")
        cache.set("other:key3", "value3")

        # Invalidate keys with "test:" pattern
        invalidated_count = invalidate_cache("test:")

        self.assertEqual(invalidated_count, 2)
        self.assertIsNone(cache.get("test:key1"))
        self.assertIsNone(cache.get("test:key2"))
        self.assertEqual(cache.get("other:key3"), "value3")

    def test_invalidate_cache_no_matches(self) -> None:
        """Test invalidate_cache with no matching keys."""
        # Clear any existing cache
        import api.caching

        api.caching._cache = None

        cache = get_cache()

        # Set some test data
        cache.set("test:key1", "value1")
        cache.set("test:key2", "value2")

        # Invalidate with non-matching pattern
        invalidated_count = invalidate_cache("nonexistent:")

        self.assertEqual(invalidated_count, 0)
        self.assertEqual(cache.get("test:key1"), "value1")
        self.assertEqual(cache.get("test:key2"), "value2")


class TestCacheDecorator(unittest.TestCase):
    """Tests for cache_result decorator."""

    def test_cache_result_basic(self) -> None:
        """Test basic cache_result decorator functionality."""
        # Clear any existing cache
        import api.caching

        api.caching._cache = None

        call_count = 0

        @cache_result(ttl=100)
        def test_function(x, y):
            nonlocal call_count
            call_count += 1
            return x + y

        # First call
        result1 = test_function(1, 2)
        self.assertEqual(result1, 3)
        self.assertEqual(call_count, 1)

        # Second call with same arguments (should be cached)
        result2 = test_function(1, 2)
        self.assertEqual(result2, 3)
        self.assertEqual(call_count, 1)  # Should not increment

        # Call with different arguments
        result3 = test_function(2, 3)
        self.assertEqual(result3, 5)
        self.assertEqual(call_count, 2)  # Should increment

    def test_cache_result_with_key_prefix(self) -> None:
        """Test cache_result decorator with key prefix."""
        # Clear any existing cache
        import api.caching

        api.caching._cache = None

        call_count = 0

        @cache_result(ttl=100, key_prefix="test_prefix")
        def test_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        # First call
        result1 = test_function(5)
        self.assertEqual(result1, 10)
        self.assertEqual(call_count, 1)

        # Second call (should be cached)
        result2 = test_function(5)
        self.assertEqual(result2, 10)
        self.assertEqual(call_count, 1)

    def test_cache_result_with_kwargs(self) -> None:
        """Test cache_result decorator with keyword arguments."""
        # Clear any existing cache
        import api.caching

        api.caching._cache = None

        call_count = 0

        @cache_result(ttl=100)
        def test_function(x, y=0, z=1):
            nonlocal call_count
            call_count += 1
            return x + y + z

        # First call
        result1 = test_function(1, y=2, z=3)
        self.assertEqual(result1, 6)
        self.assertEqual(call_count, 1)

        # Second call with same arguments (should be cached)
        result2 = test_function(1, y=2, z=3)
        self.assertEqual(result2, 6)
        self.assertEqual(call_count, 1)

        # Call with different keyword arguments
        result3 = test_function(1, y=3, z=3)
        self.assertEqual(result3, 7)
        self.assertEqual(call_count, 2)

    def test_cache_result_expiration(self) -> None:
        """Test cache_result decorator with expiration."""
        # Clear any existing cache
        import api.caching

        api.caching._cache = None

        # Create a cache with very short default TTL
        with patch("api.caching.get_settings") as mock_get_settings:
            mock_settings = Mock()
            mock_settings.cache_default_ttl = 0.1  # Very short TTL
            mock_get_settings.return_value = mock_settings

            call_count = 0

            @cache_result(ttl=0.1)  # Very short TTL
            def test_function(x):
                nonlocal call_count
                call_count += 1
                return x * 2

            # First call
            result1 = test_function(5)
            self.assertEqual(result1, 10)
            self.assertEqual(call_count, 1)

            # Wait for expiration
            time.sleep(0.2)

            # Second call (should not be cached due to expiration)
            result2 = test_function(5)
            self.assertEqual(result2, 10)
            self.assertEqual(call_count, 2)

    def test_cache_result_function_preservation(self) -> None:
        """Test that cache_result preserves function metadata."""

        @cache_result(ttl=100)
        def test_function(x):
            """Test function docstring."""
            return x * 2

        # Check that function metadata is preserved
        self.assertEqual(test_function.__name__, "test_function")
        self.assertEqual(test_function.__doc__, "Test function docstring.")


if __name__ == "__main__":
    unittest.main()
