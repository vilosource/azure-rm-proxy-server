"""Unit tests for the SubscriptionMixin class."""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from azure_rm_proxy.core.mixins.subscription_mixin import SubscriptionMixin
from azure_rm_proxy.core.models import SubscriptionModel


class TestSubscriptionMixin:
    """Tests for the SubscriptionMixin class."""

    def setup_method(self):
        """Set up test environment before each test method."""
        self.mixin = SubscriptionMixin()
        self.mixin.cache = MagicMock()
        self.mixin.limiter = AsyncMock()
        self.mixin.credential = MagicMock()
    
    @pytest.mark.asyncio
    async def test_get_subscriptions(self):
        """Test get_subscriptions method with cache miss."""
        # Mock subscription_client
        mock_subscription = MagicMock()
        mock_subscription.subscription_id = "test-sub-123"
        mock_subscription.display_name = "Test Subscription"
        mock_subscription.state = "Enabled"
        
        mock_subscription_client = MagicMock()
        mock_subscription_client.subscriptions = MagicMock()
        mock_subscription_client.subscriptions.list = AsyncMock(
            return_value=[mock_subscription]
        )
        
        with patch("azure_rm_proxy.core.azure_clients.AzureClientFactory") as mock_factory:
            mock_factory.create_subscription_client.return_value = mock_subscription_client
            
            # Test method with cache miss
            self.mixin.cache.get.return_value = None
            
            result = await self.mixin.get_subscriptions()
            
            # Verify result
            assert len(result) == 1
            assert isinstance(result[0], SubscriptionModel)
            assert result[0].id == "test-sub-123"
            assert result[0].name == "test-sub-123"  # Name defaults to ID
            assert result[0].display_name == "Test Subscription"
            assert result[0].state == "Enabled"
            
            # Verify cache interaction
            self.mixin.cache.get.assert_called_once()
            self.mixin.cache.set.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_subscriptions_cache_hit(self):
        """Test get_subscriptions method with cache hit."""
        # Mock cached data
        cached_data = [
            SubscriptionModel(
                id="cached-sub-123",
                name="cached-sub-123",
                display_name="Cached Subscription",
                state="Enabled"
            )
        ]
        
        self.mixin.cache.get.return_value = cached_data
        
        # Test method with cache hit
        result = await self.mixin.get_subscriptions()
        
        # Verify result from cache
        assert result == cached_data
        assert len(result) == 1
        assert result[0].id == "cached-sub-123"
        assert result[0].display_name == "Cached Subscription"
        
        # Verify cache interaction
        self.mixin.cache.get.assert_called_once()
        self.mixin.cache.set.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_get_subscriptions_refresh_cache(self):
        """Test get_subscriptions method with refresh_cache=True."""
        # Mock subscription_client
        mock_subscription = MagicMock()
        mock_subscription.subscription_id = "test-sub-123"
        mock_subscription.display_name = "Test Subscription"
        mock_subscription.state = "Enabled"
        
        mock_subscription_client = MagicMock()
        mock_subscription_client.subscriptions = MagicMock()
        mock_subscription_client.subscriptions.list = AsyncMock(
            return_value=[mock_subscription]
        )
        
        with patch("azure_rm_proxy.core.azure_clients.AzureClientFactory") as mock_factory:
            mock_factory.create_subscription_client.return_value = mock_subscription_client
            
            # Test method with refresh_cache=True
            result = await self.mixin.get_subscriptions(refresh_cache=True)
            
            # Verify result
            assert len(result) == 1
            assert isinstance(result[0], SubscriptionModel)
            assert result[0].id == "test-sub-123"
            
            # Verify cache interaction
            self.mixin.cache.get.assert_not_called()  # Cache not checked
            self.mixin.cache.set.assert_called_once()  # Cache updated
    
    @pytest.mark.asyncio
    async def test_get_subscriptions_empty_list(self):
        """Test get_subscriptions method with empty subscription list."""
        # Mock subscription_client with empty list
        mock_subscription_client = MagicMock()
        mock_subscription_client.subscriptions = MagicMock()
        mock_subscription_client.subscriptions.list = AsyncMock(return_value=[])
        
        with patch("azure_rm_proxy.core.azure_clients.AzureClientFactory") as mock_factory:
            mock_factory.create_subscription_client.return_value = mock_subscription_client
            
            # Test method with empty list
            self.mixin.cache.get.return_value = None
            result = await self.mixin.get_subscriptions()
            
            # Verify result
            assert len(result) == 0
            
            # Verify cache interaction
            self.mixin.cache.get.assert_called_once()
            self.mixin.cache.set.assert_called_once()  # Empty list still cached
    
    @pytest.mark.asyncio
    async def test_get_subscription_by_id(self):
        """Test get_subscription_by_id method."""
        subscription_id = "test-sub-123"
        
        # Mock get_subscriptions to return test data
        mock_subscriptions = [
            SubscriptionModel(
                id="test-sub-123",
                name="test-sub-123",
                display_name="Test Subscription 1",
                state="Enabled"
            ),
            SubscriptionModel(
                id="test-sub-456",
                name="test-sub-456",
                display_name="Test Subscription 2",
                state="Enabled"
            )
        ]
        
        with patch.object(self.mixin, "get_subscriptions", AsyncMock(return_value=mock_subscriptions)):
            # Test method with existing subscription
            result = await self.mixin.get_subscription_by_id(subscription_id)
            
            # Verify result
            assert result is not None
            assert result.id == subscription_id
            assert result.display_name == "Test Subscription 1"
            
            # Test method with non-existent subscription
            result = await self.mixin.get_subscription_by_id("non-existent-id")
            
            # Verify result
            assert result is None
    
    @pytest.mark.asyncio
    async def test_get_subscription_by_id_refresh_cache(self):
        """Test get_subscription_by_id method with refresh_cache=True."""
        subscription_id = "test-sub-123"
        
        # Mock get_subscriptions to return test data
        mock_subscriptions = [
            SubscriptionModel(
                id="test-sub-123",
                name="test-sub-123",
                display_name="Test Subscription 1",
                state="Enabled"
            )
        ]
        
        with patch.object(self.mixin, "get_subscriptions", AsyncMock(return_value=mock_subscriptions)) as mock_get_subs:
            # Test method with refresh_cache=True
            result = await self.mixin.get_subscription_by_id(subscription_id, refresh_cache=True)
            
            # Verify result
            assert result is not None
            assert result.id == subscription_id
            
            # Verify get_subscriptions was called with refresh_cache=True
            mock_get_subs.assert_called_once_with(refresh_cache=True)