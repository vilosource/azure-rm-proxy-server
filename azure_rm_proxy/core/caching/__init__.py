"""Caching package for Azure RM Proxy."""

from enum import Enum, auto
from abc import ABC, abstractmethod
from typing import Any, Optional
from .memory_cache import MemoryCache as InMemoryCache


class CacheType(Enum):
    """Enum for cache types."""

    MEMORY = "memory"
    REDIS = "redis"
    NO_CACHE = "no_cache"


class CacheStrategy(ABC):
    """Abstract base class defining the interface for all cache implementations."""

    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache.

        Args:
            key: The cache key

        Returns:
            The cached value or None if not found
        """
        pass

    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set a value in the cache with optional TTL.

        Args:
            key: The cache key
            value: The value to cache
            ttl: Time to live in seconds (optional)
        """
        pass

    @abstractmethod
    def delete(self, key: str) -> None:
        """
        Delete a value from the cache.

        Args:
            key: The cache key
        """
        pass

    @abstractmethod
    def clear(self) -> None:
        """Clear all values from the cache."""
        pass


class CacheFactory:
    """Factory for creating cache implementations based on type."""

    @staticmethod
    def create_cache(cache_type: CacheType, **kwargs) -> CacheStrategy:
        """
        Create a cache implementation based on the specified type.

        Args:
            cache_type: The type of cache to create
            **kwargs: Additional arguments to pass to the cache constructor

        Returns:
            A cache implementation
        """
        from .memory_cache import MemoryCache
        from .no_cache import NoCache

        if cache_type == CacheType.MEMORY:
            return MemoryCache(**kwargs)
        elif cache_type == CacheType.NO_CACHE:
            return NoCache(**kwargs)
        elif cache_type == CacheType.REDIS:
            try:
                from .redis_cache import RedisCache

                return RedisCache(**kwargs)
            except ImportError:
                print("Redis dependencies not installed. Falling back to memory cache.")
                return MemoryCache(**kwargs)
        else:
            raise ValueError(f"Unknown cache type: {cache_type}")
