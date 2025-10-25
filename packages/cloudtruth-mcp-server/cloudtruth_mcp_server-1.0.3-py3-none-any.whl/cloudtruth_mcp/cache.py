"""Caching layer for CloudTruth MCP Server"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional, TypeVar

from .models import CacheEntry, CacheStats

logger = logging.getLogger(__name__)

T = TypeVar("T")

# Cache TTL constants (in seconds)
METADATA_TTL = 300  # 5 minutes - for projects, environments
PARAMETER_TTL = 60  # 1 minute - for parameter values
TEMPLATE_TTL = 30  # 30 seconds - for rendered templates


class CacheManager:
    """
    In-memory cache manager with TTL support.

    Implements a simple LRU-style cache with time-based expiration.
    Thread-safe for single-threaded async applications.
    """

    def __init__(self) -> None:
        self._cache: Dict[str, CacheEntry[Any]] = {}
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value if found and not expired, None otherwise
        """
        if key not in self._cache:
            self._misses += 1
            logger.debug(f"Cache miss: {key}")
            return None

        entry = self._cache[key]

        if entry.is_expired:
            # Remove expired entry
            del self._cache[key]
            self._misses += 1
            logger.debug(f"Cache expired: {key}")
            return None

        self._hits += 1
        logger.debug(f"Cache hit: {key} (age: {entry.age_seconds:.1f}s)")
        return entry.value

    def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        """
        Store value in cache with TTL.

        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Time to live in seconds
        """
        entry = CacheEntry(
            key=key, value=value, created_at=datetime.utcnow(), ttl_seconds=ttl_seconds
        )
        self._cache[key] = entry
        logger.debug(f"Cache set: {key} (TTL: {ttl_seconds}s)")

    def invalidate(self, key: str) -> bool:
        """
        Invalidate a specific cache entry.

        Args:
            key: Cache key to invalidate

        Returns:
            True if entry was found and removed, False otherwise
        """
        if key in self._cache:
            del self._cache[key]
            logger.debug(f"Cache invalidated: {key}")
            return True
        return False

    def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate all cache entries matching a pattern.

        Args:
            pattern: String pattern to match (substring match)

        Returns:
            Number of entries invalidated
        """
        keys_to_remove = [key for key in self._cache.keys() if pattern in key]
        count = len(keys_to_remove)

        for key in keys_to_remove:
            del self._cache[key]

        if count > 0:
            logger.debug(f"Cache invalidated {count} entries matching: {pattern}")

        return count

    def clear(self) -> None:
        """Clear all cache entries."""
        count = len(self._cache)
        self._cache.clear()
        self._hits = 0
        self._misses = 0
        logger.info(f"Cache cleared: {count} entries removed")

    def cleanup_expired(self) -> int:
        """
        Remove all expired entries from cache.

        Returns:
            Number of entries removed
        """
        expired_keys = [key for key, entry in self._cache.items() if entry.is_expired]
        count = len(expired_keys)

        for key in expired_keys:
            del self._cache[key]

        if count > 0:
            logger.debug(f"Cache cleanup: {count} expired entries removed")

        return count

    def get_stats(self) -> CacheStats:
        """
        Get cache statistics.

        Returns:
            CacheStats object with current statistics
        """
        total_requests = self._hits + self._misses
        hit_rate = self._hits / total_requests if total_requests > 0 else 0.0

        # Calculate size estimate (rough)
        import sys

        total_size = sum(sys.getsizeof(entry.value) for entry in self._cache.values())

        # Get age of oldest and newest entries
        if self._cache:
            ages = [entry.age_seconds for entry in self._cache.values()]
            oldest_age = max(ages)
            newest_age = min(ages)
        else:
            oldest_age = 0.0
            newest_age = 0.0

        return CacheStats(
            total_entries=len(self._cache),
            total_hits=self._hits,
            total_misses=self._misses,
            hit_rate=hit_rate,
            total_size_bytes=total_size,
            oldest_entry_age_seconds=oldest_age,
            newest_entry_age_seconds=newest_age,
        )

    def __len__(self) -> int:
        """Return number of entries in cache."""
        return len(self._cache)

    def __contains__(self, key: str) -> bool:
        """Check if key exists in cache (and is not expired)."""
        if key not in self._cache:
            return False
        entry = self._cache[key]
        if entry.is_expired:
            del self._cache[key]
            return False
        return True


def make_cache_key(category: str, *args: str) -> str:
    """
    Create a cache key from category and arguments.

    Args:
        category: Cache category (e.g., 'project', 'parameter', 'environment')
        *args: Additional components for the key

    Returns:
        Cache key string

    Example:
        >>> make_cache_key('parameter', 'proj-123', 'DATABASE_URL', 'env-456')
        'parameter:proj-123:DATABASE_URL:env-456'
    """
    components = [category] + list(args)
    return ":".join(str(c) for c in components if c is not None)


def get_ttl_for_category(category: str) -> int:
    """
    Get appropriate TTL for a cache category.

    Args:
        category: Cache category

    Returns:
        TTL in seconds

    Categories:
        - metadata: projects, environments (300s)
        - parameter: parameter values (60s)
        - template: rendered templates (30s)
    """
    if category in ["project", "environment", "projects", "environments"]:
        return METADATA_TTL
    elif category in ["parameter", "parameter_value", "values"]:
        return PARAMETER_TTL
    elif category in ["template", "template_preview"]:
        return TEMPLATE_TTL
    else:
        # Default to parameter TTL for unknown categories
        logger.warning(
            f"Unknown cache category '{category}', using default TTL of {PARAMETER_TTL}s"
        )
        return PARAMETER_TTL
