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
            redis_url = getattr(settings, "redis_url", "redis://localhost:6379/0")
            redis_prefix = getattr(settings, "redis_prefix", "azure_rm_proxy:")

            try:
                logger.info(
                    f"Creating Redis cache with URL: {redis_url} and prefix: {redis_prefix}"
                )
                return RedisCache(redis_url=redis_url, prefix=redis_prefix)
            except Exception as e:
                logger.error(
                    f"Failed to create Redis cache: {e}. Falling back to memory cache."
                )
                return MemoryCache()
        elif cache_type == CacheType.NO_CACHE.value:
            logger.info("Creating no-cache implementation (caching disabled)")
            return NoCache()
        else:  # Default to memory cache
            logger.info("Creating in-memory cache")
            return MemoryCache()
