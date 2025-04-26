import os
import logging
from ..core.caching import CacheType

logger = logging.getLogger(__name__)


class Settings:
    """Application settings."""

    # Logging settings
    log_level: str = os.getenv("LOG_LEVEL", "INFO").upper()

    # API concurrency settings
    max_concurrency: int = int(os.getenv("MAX_CONCURRENCY", "5"))

    # Mock settings for testing
    use_mock: bool = os.getenv("USE_MOCK", "false").lower() == "true"
    mock_fixtures_dir: str = os.getenv("MOCK_FIXTURES_DIR", "./test_harnesses")

    # Cache settings
    cache_type: str = os.getenv("CACHE_TYPE", CacheType.MEMORY.value)
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    redis_prefix: str = os.getenv("REDIS_PREFIX", "azure_rm_proxy:")
    cache_ttl: int = int(os.getenv("CACHE_TTL", "3600"))  # Default TTL: 1 hour


settings = Settings()

# Apply log level from settings
logging.basicConfig(level=settings.log_level)
logger.setLevel(settings.log_level)

logger.info(
    f"Settings loaded: log_level={settings.log_level}, max_concurrency={settings.max_concurrency}, "
    f"use_mock={settings.use_mock}, mock_fixtures_dir={settings.mock_fixtures_dir}, "
    f"cache_type={settings.cache_type}, redis_url={settings.redis_url.split('@')[-1]}"
)
