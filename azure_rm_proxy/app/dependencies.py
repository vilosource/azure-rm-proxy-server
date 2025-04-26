import logging
from functools import lru_cache

from ..core.azure_service import AzureResourceService
from ..core.auth import get_credentials
from ..core.azure_clients import AzureClientFactory
from ..core.caching import CacheStrategy, CacheFactory, CacheType
from ..core.concurrency import ConcurrencyLimiter
from ..tools.mock_azure_service import MockAzureResourceService
from .config import settings

logger = logging.getLogger(__name__)


@lru_cache()
def get_azure_service() -> AzureResourceService:
    """
    Returns an instance of AzureResourceService or MockAzureResourceService based on configuration.

    If settings.use_mock is True, returns a MockAzureResourceService that uses test harnesses.
    Otherwise, returns the real AzureResourceService that connects to Azure.
    """
    # Create cache implementation based on configuration
    cache_config = {"redis_url": settings.redis_url, "prefix": settings.redis_prefix}

    try:
        # Convert string cache type to enum
        cache_type = CacheType(settings.cache_type)
        cache: CacheStrategy = CacheFactory.create_cache(cache_type, **cache_config)
        logger.info(f"Using cache implementation: {settings.cache_type}")
    except Exception as e:
        logger.error(
            f"Failed to initialize {settings.cache_type} cache, falling back to in-memory cache: {e}"
        )
        cache = CacheFactory.create_cache(CacheType.MEMORY)

    limiter = ConcurrencyLimiter(max_concurrent=settings.max_concurrency)

    if settings.use_mock:
        logger.info(
            f"Creating MockAzureResourceService instance with fixtures from {settings.mock_fixtures_dir}"
        )
        return MockAzureResourceService(
            cache=cache, limiter=limiter, fixtures_dir=settings.mock_fixtures_dir
        )
    else:
        logger.info("Creating AzureResourceService instance")
        credential = get_credentials()
        return AzureResourceService(credential, cache, limiter)
