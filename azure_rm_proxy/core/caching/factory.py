"""Cache factory to create the appropriate cache implementation."""

import logging
from typing import Any, Dict, Optional, Type

from ..settings import Settings
from .base_cache import BaseCache
from .memory_cache import MemoryCache
from .redis_cache import RedisCache
from .no_cache import NoCache
from . import CacheType

logger = logging.getLogger(__name__)


class CacheFactory:
    """Factory class for creating cache instances."""

    @staticmethod
    def create_cache(settings: Settings) -> BaseCache:
        """
        Create a cache instance based on settings.

        Args:
            settings: Application settings

        Returns:
            A cache instance
        """
        cache_type = getattr(settings, "cache_type", CacheType.MEMORY.value)

        if cache_type == CacheType.REDIS.value:
            redis_url = getattr(settings, "redis_url", None)
            if not redis_url:
                logger.warning(
                    "Redis cache type specified but no Redis URL provided. Falling back to memory cache."
                )
                return MemoryCache()
            return RedisCache(redis_url=redis_url)
        elif cache_type == CacheType.NO_CACHE.value:
            return NoCache()
        else:  # Default to memory cache
            return MemoryCache()
