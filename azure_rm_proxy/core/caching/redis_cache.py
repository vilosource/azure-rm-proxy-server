"""Redis cache implementation with TTL support."""

import json
import logging
from typing import Any, Optional

import redis

from .base_cache import BaseCache

logger = logging.getLogger(__name__)


class RedisCache(BaseCache):
    """
    Redis cache implementation with TTL support.
    This cache uses Redis to store values and supports time-to-live (TTL) expiration.
    """

    def __init__(self, host="localhost", port=6379, db=0, password=None):
        """
        Initialize the Redis cache.

        Args:
            host: Redis host
            port: Redis port
            db: Redis DB number
            password: Redis password
        """
        self._redis = redis.Redis(
            host=host, port=port, db=db, password=password, decode_responses=False
        )
        logger.info(f"Initialized Redis cache at {host}:{port}")

    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache.

        Args:
            key: The cache key

        Returns:
            The cached value or None if not found
        """
        value = self._redis.get(key)
        if value is None:
            return None

        try:
            return json.loads(value)
        except Exception as e:
            logger.error(f"Error deserializing cached value for key {key}: {e}")
            return None

    def set(self, key: str, value: Any) -> None:
        """
        Set a value in the cache without expiration.

        Args:
            key: The cache key
            value: The value to cache
        """
        try:
            serialized = json.dumps(value)
            self._redis.set(key, serialized)
        except Exception as e:
            logger.error(f"Error serializing value for key {key}: {e}")

    def set_with_ttl(self, key: str, value: Any, ttl: int) -> None:
        """
        Set a value in the cache with a specific TTL.

        Args:
            key: The cache key
            value: The value to cache
            ttl: Time to live in seconds
        """
        try:
            serialized = json.dumps(value)
            self._redis.setex(key, ttl, serialized)
        except Exception as e:
            logger.error(f"Error serializing value for key {key}: {e}")

    def delete(self, key: str) -> None:
        """
        Delete a value from the cache.

        Args:
            key: The cache key
        """
        self._redis.delete(key)

    def clear(self) -> None:
        """Clear all values from the cache."""
        self._redis.flushdb()
