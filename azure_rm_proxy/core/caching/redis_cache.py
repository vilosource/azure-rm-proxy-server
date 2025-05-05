"""Redis cache implementation with TTL support."""

import json
import logging
import urllib.parse
from typing import Any, Optional

import redis

from .base_cache import BaseCache

logger = logging.getLogger(__name__)


class RedisCache(BaseCache):
    """
    Redis cache implementation with TTL support.
    This cache uses Redis to store values and supports time-to-live (TTL) expiration.
    """

    def __init__(self, redis_url="redis://localhost:6379/0", prefix=""):
        """
        Initialize the Redis cache.

        Args:
            redis_url: Redis connection URL (redis://host:port/db)
            prefix: Key prefix for all Redis keys
        """
        self.prefix = prefix

        try:
            self._redis = redis.from_url(redis_url, decode_responses=False)

            # Parse the URL to get components for logging
            parsed_url = urllib.parse.urlparse(redis_url)
            host = parsed_url.hostname or "localhost"
            port = parsed_url.port or 6379
            db = parsed_url.path.lstrip("/") or "0"

            logger.info(
                f"Initialized Redis cache at {host}:{port}/{db} with prefix '{prefix}'"
            )
        except Exception as e:
            logger.error(f"Failed to initialize Redis cache: {e}")
            raise

    def _prefix_key(self, key: str) -> str:
        """
        Add prefix to a key.

        Args:
            key: Original cache key

        Returns:
            Prefixed key for Redis
        """
        if not self.prefix:
            return key
        return f"{self.prefix}{key}"

    def _serialize(self, value: Any) -> bytes:
        """
        Serialize a value to JSON.

        Args:
            value: The value to serialize

        Returns:
            JSON string representation of the value
        """
        try:
            # Process value to handle Pydantic models
            processed_value = self._process_value(value)
            # Serialize to JSON
            return json.dumps(processed_value).encode("utf-8")
        except Exception as e:
            logger.error(f"Serialization error: {e}")
            raise

    def _process_value(self, value: Any) -> Any:
        """
        Process any value to make it JSON serializable.

        Args:
            value: The value to process

        Returns:
            A JSON serializable version of the value
        """
        # Handle None
        if value is None:
            return None

        # Handle Pydantic models
        if hasattr(value, "model_dump"):
            # Pydantic v2
            return value.model_dump()
        elif hasattr(value, "dict") and callable(getattr(value, "dict")):
            # Pydantic v1
            return value.dict()

        # Handle lists (may contain Pydantic models)
        elif isinstance(value, list):
            return [self._process_value(item) for item in value]

        # Handle dictionaries (may contain Pydantic models as values)
        elif isinstance(value, dict):
            return {k: self._process_value(v) for k, v in value.items()}

        # Handle basic types that are directly JSON serializable
        elif isinstance(value, (str, int, float, bool)):
            return value

        # For other types, try to convert to string
        else:
            try:
                return str(value)
            except Exception as e:
                logger.warning(
                    f"Could not serialize object of type {type(value).__name__}, returning string representation: {e}"
                )
                return f"<Non-serializable object of type {type(value).__name__}>"

    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache.

        Args:
            key: The cache key

        Returns:
            The cached value or None if not found
        """
        prefixed_key = self._prefix_key(key)
        value = self._redis.get(prefixed_key)
        if value is None:
            return None

        try:
            return json.loads(value)
        except Exception as e:
            logger.error(
                f"Error deserializing cached value for key {prefixed_key}: {e}"
            )
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set a value in the cache with optional expiration.

        Args:
            key: The cache key
            value: The value to cache
            ttl: Optional time to live in seconds
        """
        prefixed_key = self._prefix_key(key)
        try:
            serialized = self._serialize(value)
            if ttl is not None:
                self._redis.setex(prefixed_key, ttl, serialized)
            else:
                self._redis.set(prefixed_key, serialized)
        except Exception as e:
            logger.error(f"Error serializing value for key {prefixed_key}: {e}")

    def set_with_ttl(self, key: str, value: Any, ttl: int) -> None:
        """
        Set a value in the cache with a specific TTL.

        Args:
            key: The cache key
            value: The value to cache
            ttl: Time to live in seconds
        """
        prefixed_key = self._prefix_key(key)
        try:
            serialized = self._serialize(value)
            self._redis.setex(prefixed_key, ttl, serialized)
        except Exception as e:
            logger.error(f"Error serializing value for key {prefixed_key}: {e}")

    def delete(self, key: str) -> None:
        """
        Delete a value from the cache.

        Args:
            key: The cache key
        """
        prefixed_key = self._prefix_key(key)
        self._redis.delete(prefixed_key)

    def clear(self) -> None:
        """Clear all values from the cache."""
        if self.prefix:
            # Delete only keys with our prefix
            cursor = 0
            while True:
                cursor, keys = self._redis.scan(cursor, f"{self.prefix}*", 100)
                if keys:
                    self._redis.delete(*keys)
                if cursor == 0:
                    break
        else:
            # Without a prefix, we can't safely delete only our keys
            # Log a warning instead of flushdb
            logger.warning(
                "Clear() called without a prefix. For safety, no keys were deleted. "
                "Set a prefix to enable selective clearing."
            )
