"""Tests for cache functionality"""

from cloudtruth_mcp.cache import (
    METADATA_TTL,
    PARAMETER_TTL,
    TEMPLATE_TTL,
    CacheManager,
    get_ttl_for_category,
    make_cache_key,
)


class TestCacheManager:
    """Tests for CacheManager"""

    def test_cache_set_get(self):
        """Test basic cache set and get"""
        cache = CacheManager()
        cache.set("key1", "value1", 60)

        result = cache.get("key1")
        assert result == "value1"

    def test_cache_miss(self):
        """Test cache miss"""
        cache = CacheManager()
        result = cache.get("nonexistent")
        assert result is None

    def test_cache_expiration(self):
        """Test cache expiration"""
        cache = CacheManager()
        # Set with very short TTL
        cache.set("key1", "value1", 0)

        # Should be expired immediately
        result = cache.get("key1")
        assert result is None

    def test_cache_invalidate(self):
        """Test cache invalidation"""
        cache = CacheManager()
        cache.set("key1", "value1", 60)

        # Verify it's there
        assert cache.get("key1") == "value1"

        # Invalidate
        result = cache.invalidate("key1")
        assert result is True

        # Should be gone
        assert cache.get("key1") is None

    def test_cache_invalidate_nonexistent(self):
        """Test invalidating nonexistent key"""
        cache = CacheManager()
        result = cache.invalidate("nonexistent")
        assert result is False

    def test_cache_invalidate_pattern(self):
        """Test pattern-based invalidation"""
        cache = CacheManager()
        cache.set("user:1:profile", "data1", 60)
        cache.set("user:1:settings", "data2", 60)
        cache.set("user:2:profile", "data3", 60)

        # Invalidate all user:1 entries
        count = cache.invalidate_pattern("user:1")
        assert count == 2

        # Verify user:1 entries are gone
        assert cache.get("user:1:profile") is None
        assert cache.get("user:1:settings") is None

        # Verify user:2 entry still exists
        assert cache.get("user:2:profile") == "data3"

    def test_cache_clear(self):
        """Test clearing all cache"""
        cache = CacheManager()
        cache.set("key1", "value1", 60)
        cache.set("key2", "value2", 60)
        cache.set("key3", "value3", 60)

        assert len(cache) == 3

        cache.clear()

        assert len(cache) == 0
        assert cache.get("key1") is None

    def test_cache_cleanup_expired(self):
        """Test cleanup of expired entries"""
        cache = CacheManager()
        cache.set("key1", "value1", 0)  # Expired
        cache.set("key2", "value2", 60)  # Not expired

        count = cache.cleanup_expired()
        assert count == 1

        assert cache.get("key1") is None
        assert cache.get("key2") == "value2"

    def test_cache_stats(self):
        """Test cache statistics"""
        cache = CacheManager()

        # Add some entries
        cache.set("key1", "value1", 60)
        cache.set("key2", "value2", 60)

        # Generate some hits and misses
        cache.get("key1")  # Hit
        cache.get("key1")  # Hit
        cache.get("nonexistent")  # Miss

        stats = cache.get_stats()

        assert stats.total_entries == 2
        assert stats.total_hits == 2
        assert stats.total_misses == 1
        assert stats.hit_rate == 2 / 3

    def test_cache_stats_empty(self):
        """Test cache statistics when cache is empty"""
        cache = CacheManager()

        stats = cache.get_stats()

        assert stats.total_entries == 0
        assert stats.total_hits == 0
        assert stats.total_misses == 0
        assert stats.hit_rate == 0.0
        assert stats.oldest_entry_age_seconds == 0.0
        assert stats.newest_entry_age_seconds == 0.0

    def test_cache_contains(self):
        """Test __contains__ operator"""
        cache = CacheManager()
        cache.set("key1", "value1", 60)

        assert "key1" in cache
        assert "nonexistent" not in cache

    def test_cache_contains_expired_entry(self):
        """Test __contains__ returns False for expired entries"""
        cache = CacheManager()

        # Set an entry with 0 TTL (immediately expired)
        cache.set("expired-key", "value", 0)

        # Should not be in cache (expired entries are cleaned up)
        assert "expired-key" not in cache

    def test_cache_len(self):
        """Test __len__ operator"""
        cache = CacheManager()
        assert len(cache) == 0

        cache.set("key1", "value1", 60)
        assert len(cache) == 1

        cache.set("key2", "value2", 60)
        assert len(cache) == 2

        cache.invalidate("key1")
        assert len(cache) == 1


class TestCacheHelpers:
    """Tests for cache helper functions"""

    def test_make_cache_key(self):
        """Test cache key generation"""
        key = make_cache_key("parameter", "proj-123", "DATABASE_URL", "env-456")
        assert key == "parameter:proj-123:DATABASE_URL:env-456"

    def test_make_cache_key_with_none(self):
        """Test cache key with None values"""
        key = make_cache_key("parameter", "proj-123", None, "env-456")
        assert key == "parameter:proj-123:env-456"

    def test_get_ttl_for_category_metadata(self):
        """Test TTL for metadata categories"""
        assert get_ttl_for_category("project") == METADATA_TTL
        assert get_ttl_for_category("projects") == METADATA_TTL
        assert get_ttl_for_category("environment") == METADATA_TTL
        assert get_ttl_for_category("environments") == METADATA_TTL

    def test_get_ttl_for_category_parameter(self):
        """Test TTL for parameter categories"""
        assert get_ttl_for_category("parameter") == PARAMETER_TTL
        assert get_ttl_for_category("parameter_value") == PARAMETER_TTL
        assert get_ttl_for_category("values") == PARAMETER_TTL

    def test_get_ttl_for_category_template(self):
        """Test TTL for template categories"""
        assert get_ttl_for_category("template") == TEMPLATE_TTL
        assert get_ttl_for_category("template_preview") == TEMPLATE_TTL

    def test_get_ttl_for_category_unknown(self):
        """Test TTL for unknown category defaults to parameter TTL"""
        assert get_ttl_for_category("unknown_category") == PARAMETER_TTL


class TestCacheIntegration:
    """Integration tests for cache behavior"""

    def test_cache_with_complex_objects(self):
        """Test caching complex objects"""
        cache = CacheManager()

        data = {
            "id": "proj-123",
            "name": "my-project",
            "parameters": [{"name": "DB_URL", "value": "postgres://..."}],
        }

        cache.set("project:123", data, 60)

        result = cache.get("project:123")
        assert result == data
        assert result["id"] == "proj-123"

    def test_cache_with_lists(self):
        """Test caching lists"""
        cache = CacheManager()

        projects = [{"id": "1", "name": "proj1"}, {"id": "2", "name": "proj2"}]

        cache.set("projects:all", projects, 60)

        result = cache.get("projects:all")
        assert result == projects
        assert len(result) == 2

    def test_multiple_caches_independent(self):
        """Test that multiple cache instances are independent"""
        cache1 = CacheManager()
        cache2 = CacheManager()

        cache1.set("key1", "value1", 60)

        assert cache1.get("key1") == "value1"
        assert cache2.get("key1") is None
