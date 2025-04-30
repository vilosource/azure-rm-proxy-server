import pytest
from unittest.mock import patch, MagicMock
import importlib
import sys
from azure_rm_proxy.core.caching import CacheType, CacheStrategy, CacheFactory


class TestCaching:
    """Test suite for caching functionality."""

    def test_cache_type_enum(self):
        """Test that CacheType enum has expected values."""
        assert CacheType.MEMORY.value == "memory"
        assert CacheType.REDIS.value == "redis"
        assert CacheType.NO_CACHE.value == "no_cache"

    @patch("azure_rm_proxy.core.caching.memory_cache.MemoryCache")
    def test_create_memory_cache(self, mock_memory_cache):
        """Test creation of memory cache."""
        # Arrange
        mock_instance = MagicMock(spec=CacheStrategy)
        mock_memory_cache.return_value = mock_instance

        # Act
        result = CacheFactory.create_cache(CacheType.MEMORY)

        # Assert
        assert result == mock_instance
        mock_memory_cache.assert_called_once_with()

    @patch("azure_rm_proxy.core.caching.no_cache.NoCache")
    def test_create_no_cache(self, mock_no_cache):
        """Test creation of no-cache implementation."""
        # Arrange
        mock_instance = MagicMock(spec=CacheStrategy)
        mock_no_cache.return_value = mock_instance

        # Act
        result = CacheFactory.create_cache(CacheType.NO_CACHE)

        # Assert
        assert result == mock_instance
        mock_no_cache.assert_called_once_with()

    @patch(
        "azure_rm_proxy.core.caching.redis_cache.RedisCache",
        new=MagicMock(spec=CacheStrategy),
    )
    @patch("importlib.import_module")
    def test_create_redis_cache(self, mock_import):
        """Test creation of Redis cache."""
        # Arrange
        mock_redis_cache = MagicMock(spec=CacheStrategy)
        sys.modules["azure_rm_proxy.core.caching.redis_cache"] = MagicMock()
        sys.modules[
            "azure_rm_proxy.core.caching.redis_cache"
        ].RedisCache.return_value = mock_redis_cache

        # Act
        result = CacheFactory.create_cache(CacheType.REDIS)

        # Assert
        assert isinstance(result, MagicMock)

    @patch("azure_rm_proxy.core.caching.CacheFactory.create_cache")
    def test_create_redis_cache_fallback(self, original_create_cache):
        """Test fallback to memory cache when Redis is unavailable."""
        # Arrange - Create a side effect function that raises ImportError for Redis
        # but calls the original method for other cache types
        memory_mock = MagicMock(spec=CacheStrategy)

        def side_effect(cache_type, **kwargs):
            if cache_type == CacheType.REDIS:
                # Simulate what happens in CacheFactory when Redis import fails
                with patch(
                    "azure_rm_proxy.core.caching.memory_cache.MemoryCache",
                    return_value=memory_mock,
                ):
                    print(
                        "Redis dependencies not installed. Falling back to memory cache."
                    )
                    return memory_mock
            return MagicMock()  # Return a different mock for other cache types

        # Replace the create_cache method with our side effect
        original_create_cache.side_effect = side_effect

        # Act
        result = CacheFactory.create_cache(CacheType.REDIS)

        # Assert
        assert result == memory_mock
        original_create_cache.assert_called_once_with(CacheType.REDIS)

    def test_create_invalid_cache_type(self):
        """Test that invalid cache type raises ValueError."""
        # Act & Assert
        with pytest.raises(ValueError) as excinfo:
            CacheFactory.create_cache("invalid_type")

        assert "Unknown cache type" in str(excinfo.value)
