"""In-memory cache implementation with TTL support."""

import logging
import threading
import time
from typing import Any, Dict, Optional, Tuple

from .base_cache import BaseCache

logger = logging.getLogger(__name__)


class MemoryCache(BaseCache):
    """
    In-memory cache implementation with TTL support.
    This cache uses a dictionary to store values in memory and supports
    time-to-live (TTL) expiration.
    """

    def __init__(self):
        """Initialize the memory cache."""
        self._cache: Dict[str, Tuple[Any, Optional[float]]] = {}
        self._lock = threading.RLock()
        logger.info("Initialized in-memory cache")

    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache, respecting TTL.

        Args:
            key: The cache key

        Returns:
            The cached value or None if not found or expired
        """
        with self._lock:
            if key not in self._cache:
                return None

            value, expiry = self._cache[key]

            # Check if the value has expired
            if expiry and time.time() > expiry:
                # Remove the expired value
                del self._cache[key]
                return None

            return value

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set a value in the cache with optional TTL.

        Args:
            key: The cache key
            value: The value to cache
            ttl: Time to live in seconds (optional)
        """
        if ttl is not None:
            self.set_with_ttl(key, value, ttl)
        else:
            with self._lock:
                self._cache[key] = (value, None)

    def set_with_ttl(self, key: str, value: Any, ttl: int) -> None:
        """
        Set a value in the cache with a specific TTL.

        Args:
            key: The cache key
            value: The value to cache
            ttl: Time to live in seconds
        """
        expiry = time.time() + ttl
        with self._lock:
            self._cache[key] = (value, expiry)

    def delete(self, key: str) -> None:
        """
        Delete a value from the cache.

        Args:
            key: The cache key
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]

    def clear(self) -> None:
        """Clear all values from the cache."""
        with self._lock:
            self._cache.clear()
