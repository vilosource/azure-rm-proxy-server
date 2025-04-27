"""Unit tests for the BaseAzureResourceMixin class."""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock, call

from azure_rm_proxy.core.mixins.base_mixin import BaseAzureResourceMixin, cached_azure_operation
from azure.core.exceptions import ResourceNotFoundError, ClientAuthenticationError


class TestBaseAzureResourceMixin:
    """Tests for the BaseAzureResourceMixin class."""

    def setup_method(self):
        """Set up test environment before each test method."""
        self.mixin = BaseAzureResourceMixin()
        self.mixin.cache = MagicMock()
        self.mixin.limiter = AsyncMock()
        self.mixin.credential = MagicMock()
    
    @pytest.mark.asyncio
    async def test_get_client(self):
        """Test _get_client method."""
        # Test with compute client
        subscription_id = "test-sub-123"
        
        with patch("azure_rm_proxy.core.azure_clients.AzureClientFactory") as mock_factory:
            mock_compute_client = MagicMock()
            mock_factory.create_compute_client.return_value = mock_compute_client
            
            result = await self.mixin._get_client("compute", subscription_id)
            
            assert result == mock_compute_client
            mock_factory.create_compute_client.assert_called_once_with(subscription_id, self.mixin.credential)
        
        # Test with network client
        with patch("azure_rm_proxy.core.azure_clients.AzureClientFactory") as mock_factory:
            mock_network_client = MagicMock()
            mock_factory.create_network_client.return_value = mock_network_client
            
            result = await self.mixin._get_client("network", subscription_id)
            
            assert result == mock_network_client
            mock_factory.create_network_client.assert_called_once_with(subscription_id, self.mixin.credential)
        
        # Test with resource client
        with patch("azure_rm_proxy.core.azure_clients.AzureClientFactory") as mock_factory:
            mock_resource_client = MagicMock()
            mock_factory.create_resource_client.return_value = mock_resource_client
            
            result = await self.mixin._get_client("resource", subscription_id)
            
            assert result == mock_resource_client
            mock_factory.create_resource_client.assert_called_once_with(subscription_id, self.mixin.credential)
    
    @pytest.mark.asyncio
    async def test_get_client_error(self):
        """Test _get_client method with invalid client type."""
        subscription_id = "test-sub-123"
        
        with pytest.raises(ValueError) as exc_info:
            await self.mixin._get_client("invalid_client_type", subscription_id)
        
        assert "Unsupported client type" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_get_client_with_rate_limiting(self):
        """Test _get_client method with rate limiting."""
        subscription_id = "test-sub-123"
        
        with patch("azure_rm_proxy.core.azure_clients.AzureClientFactory") as mock_factory:
            mock_compute_client = MagicMock()
            mock_factory.create_compute_client.return_value = mock_compute_client
            
            # Call the method
            result = await self.mixin._get_client("compute", subscription_id)
            
            # Verify result and rate limiter interaction
            assert result == mock_compute_client
            self.mixin.limiter.acquire.assert_awaited_once()
            mock_factory.create_compute_client.assert_called_once_with(subscription_id, self.mixin.credential)
    
    def test_extract_resource_group_from_id(self):
        """Test _extract_resource_group_from_id method."""
        # Valid resource ID
        resource_id = "/subscriptions/test-sub-123/resourceGroups/test-rg/providers/Microsoft.Compute/virtualMachines/test-vm"
        result = self.mixin._extract_resource_group_from_id(resource_id)
        assert result == "test-rg"
        
        # Invalid resource ID
        resource_id = "/subscriptions/test-sub-123/invalid/test-rg/providers/Microsoft.Compute/virtualMachines/test-vm"
        result = self.mixin._extract_resource_group_from_id(resource_id, default_rg="default-rg")
        assert result == "default-rg"
    
    def test_get_cache_key(self):
        """Test _get_cache_key method."""
        # Test with string components
        key_components = ["test", "key", "components"]
        result = self.mixin._get_cache_key(key_components)
        assert result == "test:key:components"
        
        # Test with mixed type components
        key_components = ["test", 123, True, None]
        result = self.mixin._get_cache_key(key_components)
        assert result == "test:123:True"
    
    def test_set_cache_with_ttl(self):
        """Test _set_cache_with_ttl method."""
        # Test with TTL and set_with_ttl method available
        self.mixin.cache.set_with_ttl = MagicMock()
        self.mixin._set_cache_with_ttl("test-key", "test-value", 300)
        self.mixin.cache.set_with_ttl.assert_called_once_with("test-key", "test-value", 300)
        
        # Test with TTL but no set_with_ttl method
        self.mixin.cache = MagicMock()
        self.mixin._set_cache_with_ttl("test-key", "test-value", 300)
        self.mixin.cache.set.assert_called_once_with("test-key", "test-value")
        
        # Test with no TTL
        self.mixin.cache = MagicMock()
        self.mixin._set_cache_with_ttl("test-key", "test-value")
        self.mixin.cache.set.assert_called_once_with("test-key", "test-value")
        
        # Test with no cache
        self.mixin.cache = None
        # This should not raise an exception
        self.mixin._set_cache_with_ttl("test-key", "test-value", 300)


# Test the cached_azure_operation decorator separately
class TestCachedAzureOperationDecorator:
    """Tests for the cached_azure_operation decorator."""
    
    def setup_method(self):
        """Set up test environment before each test method."""
        # Create a test model class
        from pydantic import BaseModel
        
        class TestModel(BaseModel):
            id: str
            name: str
        
        self.TestModel = TestModel
        
        # Create a class with a decorated method for testing
        class TestClass(BaseAzureResourceMixin):
            def __init__(self):
                self.cache = MagicMock()
                self.limiter = AsyncMock()
                self.credential = MagicMock()
                self.call_count = 0
            
            @cached_azure_operation(model_class=TestModel, cache_key_prefix="test")
            async def cached_method(self, param1, param2=None, refresh_cache=False):
                self.call_count += 1
                return {"id": f"id-{param1}", "name": f"name-{param2}"}
        
        self.test_instance = TestClass()
    
    @pytest.mark.asyncio
    async def test_cache_hit(self):
        """Test cached_azure_operation decorator with a cache hit."""
        # Set up cache hit
        cached_value = {"id": "cached-id", "name": "cached-name"}
        self.test_instance.cache.get.return_value = cached_value
        
        # Call the decorated method
        result = await self.test_instance.cached_method("value1", "value2")
        
        # Verify result and cache interaction
        assert result.id == "cached-id"
        assert result.name == "cached-name"
        assert isinstance(result, self.TestModel)
        self.test_instance.cache.get.assert_called_once()
        self.test_instance.cache.set.assert_not_called()
        assert self.test_instance.call_count == 0  # Original method not called
    
    @pytest.mark.asyncio
    async def test_cache_miss(self):
        """Test cached_azure_operation decorator with a cache miss."""
        # Set up cache miss
        self.test_instance.cache.get.return_value = None
        
        # Call the decorated method
        result = await self.test_instance.cached_method("value1", "value2")
        
        # Verify result and cache interaction
        assert result.id == "id-value1"
        assert result.name == "name-value2"
        assert isinstance(result, self.TestModel)
        self.test_instance.cache.get.assert_called_once()
        self.test_instance.cache.set.assert_called_once()  # Cache was updated
        assert self.test_instance.call_count == 1  # Original method was called
    
    @pytest.mark.asyncio
    async def test_refresh_cache(self):
        """Test cached_azure_operation decorator with refresh_cache=True."""
        # Set up cache (should be ignored)
        cached_value = {"id": "cached-id", "name": "cached-name"}
        self.test_instance.cache.get.return_value = cached_value
        
        # Call the decorated method with refresh_cache=True
        result = await self.test_instance.cached_method("value1", "value2", refresh_cache=True)
        
        # Verify result and cache interaction
        assert result.id == "id-value1"
        assert result.name == "name-value2"
        assert isinstance(result, self.TestModel)
        self.test_instance.cache.get.assert_not_called()  # Cache not checked
        self.test_instance.cache.set.assert_called_once()  # Cache was updated
        assert self.test_instance.call_count == 1  # Original method was called
    
    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test cached_azure_operation decorator error handling."""
        # Create a class with a method that raises an exception
        class ErrorTestClass(BaseAzureResourceMixin):
            def __init__(self):
                self.cache = MagicMock()
                self.limiter = AsyncMock()
                self.credential = MagicMock()
            
            @cached_azure_operation(model_class=self.TestModel, cache_key_prefix="test")
            async def error_method(self, param1, param2=None, refresh_cache=False):
                raise ResourceNotFoundError("Resource not found")
        
        test_instance = ErrorTestClass()
        test_instance.cache.get.return_value = None
        test_instance._log_warning = MagicMock()
        
        # Call the method and expect an exception
        with pytest.raises(ResourceNotFoundError):
            await test_instance.error_method("value1", "value2")
        
        # Verify cache interaction and logging
        test_instance.cache.get.assert_called_once()
        test_instance.cache.set.assert_not_called()  # Cache not updated due to error
        test_instance._log_warning.assert_called_once()