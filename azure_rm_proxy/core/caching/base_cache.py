"""Base cache interface for all cache implementations."""

from abc import ABC, abstractmethod
from typing import Any, Optional


class BaseCache(ABC):
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
    def set_with_ttl(self, key: str, value: Any, ttl: int) -> None:
        """
        Set a value in the cache with a specific TTL.

        Args:
            key: The cache key
            value: The value to cache
            ttl: Time to live in seconds
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
