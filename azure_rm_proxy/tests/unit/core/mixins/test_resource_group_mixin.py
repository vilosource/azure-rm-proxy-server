"""Unit tests for the ResourceGroupMixin class."""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from azure_rm_proxy.core.mixins.resource_group_mixin import ResourceGroupMixin
from azure_rm_proxy.core.models import ResourceGroupModel


class TestResourceGroupMixin:
    """Tests for the ResourceGroupMixin class."""

    def setup_method(self):
        """Set up test environment before each test method."""
        self.mixin = ResourceGroupMixin()
        self.mixin.cache = MagicMock()
        self.mixin.limiter = AsyncMock()
        self.mixin.credential = MagicMock()
    
    @pytest.mark.asyncio
    async def test_get_resource_groups(self):
        """Test get_resource_groups method with cache miss."""
        subscription_id = "test-sub-123"
        
        # Mock resource group
        mock_resource_group = MagicMock()
        mock_resource_group.id = "/subscriptions/test-sub-123/resourceGroups/test-rg-1"
        mock_resource_group.name = "test-rg-1"
        mock_resource_group.location = "westus"
        mock_resource_group.tags = {"env": "test"}
        
        # Mock resource client
        mock_resource_client = MagicMock()
        mock_resource_client.resource_groups = MagicMock()
        mock_resource_client.resource_groups.list = AsyncMock(
            return_value=[mock_resource_group]
        )
        
        # Mock _get_client method
        with patch.object(self.mixin, "_get_client", AsyncMock(return_value=mock_resource_client)):
            # Test method with cache miss
            self.mixin.cache.get.return_value = None
            
            result = await self.mixin.get_resource_groups(subscription_id)
            
            # Verify result
            assert len(result) == 1
            assert isinstance(result[0], ResourceGroupModel)
            assert result[0].id == "/subscriptions/test-sub-123/resourceGroups/test-rg-1"
            assert result[0].name == "test-rg-1"
            assert result[0].location == "westus"
            assert result[0].tags == {"env": "test"}
            
            # Verify cache interaction
            self.mixin.cache.get.assert_called_once()
            self.mixin.cache.set.assert_called_once()
            
            # Verify _get_client call
            self.mixin._get_client.assert_called_once_with("resource", subscription_id)
    
    @pytest.mark.asyncio
    async def test_get_resource_groups_cache_hit(self):
        """Test get_resource_groups method with cache hit."""
        subscription_id = "test-sub-123"
        
        # Mock cached data
        cached_data = [
            ResourceGroupModel(
                id="/subscriptions/test-sub-123/resourceGroups/cached-rg",
                name="cached-rg",
                location="eastus",
                tags={"cached": "true"}
            )
        ]
        
        self.mixin.cache.get.return_value = cached_data
        
        # Mock _get_client to ensure it's not called
        with patch.object(self.mixin, "_get_client", new_callable=AsyncMock) as mock_get_client:
            # Test method with cache hit
            result = await self.mixin.get_resource_groups(subscription_id)
            
            # Verify result from cache
            assert result == cached_data
            assert len(result) == 1
            assert result[0].id == "/subscriptions/test-sub-123/resourceGroups/cached-rg"
            assert result[0].name == "cached-rg"
            
            # Verify cache interaction
            self.mixin.cache.get.assert_called_once()
            self.mixin.cache.set.assert_not_called()
            
            # Verify _get_client was not called
            mock_get_client.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_get_resource_groups_refresh_cache(self):
        """Test get_resource_groups method with refresh_cache=True."""
        subscription_id = "test-sub-123"
        
        # Mock resource group
        mock_resource_group = MagicMock()
        mock_resource_group.id = "/subscriptions/test-sub-123/resourceGroups/test-rg-1"
        mock_resource_group.name = "test-rg-1"
        mock_resource_group.location = "westus"
        mock_resource_group.tags = {"env": "test"}
        
        # Mock resource client
        mock_resource_client = MagicMock()
        mock_resource_client.resource_groups = MagicMock()
        mock_resource_client.resource_groups.list = AsyncMock(
            return_value=[mock_resource_group]
        )
        
        # Mock _get_client method
        with patch.object(self.mixin, "_get_client", AsyncMock(return_value=mock_resource_client)):
            # Test method with refresh_cache=True
            result = await self.mixin.get_resource_groups(subscription_id, refresh_cache=True)
            
            # Verify result
            assert len(result) == 1
            assert isinstance(result[0], ResourceGroupModel)
            assert result[0].id == "/subscriptions/test-sub-123/resourceGroups/test-rg-1"
            
            # Verify cache interaction
            self.mixin.cache.get.assert_not_called()  # Cache not checked
            self.mixin.cache.set.assert_called_once()  # Cache updated
            
            # Verify _get_client call
            self.mixin._get_client.assert_called_once_with("resource", subscription_id)
    
    @pytest.mark.asyncio
    async def test_get_resource_groups_empty_list(self):
        """Test get_resource_groups method with empty resource group list."""
        subscription_id = "test-sub-123"
        
        # Mock resource client with empty list
        mock_resource_client = MagicMock()
        mock_resource_client.resource_groups = MagicMock()
        mock_resource_client.resource_groups.list = AsyncMock(return_value=[])
        
        # Mock _get_client method
        with patch.object(self.mixin, "_get_client", AsyncMock(return_value=mock_resource_client)):
            # Test method with empty list
            self.mixin.cache.get.return_value = None
            result = await self.mixin.get_resource_groups(subscription_id)
            
            # Verify result
            assert len(result) == 0
            
            # Verify cache interaction
            self.mixin.cache.get.assert_called_once()
            self.mixin.cache.set.assert_called_once()  # Empty list still cached
    
    @pytest.mark.asyncio
    async def test_get_resource_group_by_name(self):
        """Test get_resource_group_by_name method."""
        subscription_id = "test-sub-123"
        resource_group_name = "test-rg-1"
        
        # Mock get_resource_groups to return test data
        mock_resource_groups = [
            ResourceGroupModel(
                id="/subscriptions/test-sub-123/resourceGroups/test-rg-1",
                name="test-rg-1",
                location="westus",
                tags={"env": "test1"}
            ),
            ResourceGroupModel(
                id="/subscriptions/test-sub-123/resourceGroups/test-rg-2",
                name="test-rg-2",
                location="eastus",
                tags={"env": "test2"}
            )
        ]
        
        with patch.object(self.mixin, "get_resource_groups", AsyncMock(return_value=mock_resource_groups)):
            # Test method with existing resource group
            result = await self.mixin.get_resource_group_by_name(subscription_id, resource_group_name)
            
            # Verify result
            assert result is not None
            assert result.name == resource_group_name
            assert result.location == "westus"
            assert result.tags == {"env": "test1"}
            
            # Test method with non-existent resource group
            result = await self.mixin.get_resource_group_by_name(subscription_id, "non-existent-rg")
            
            # Verify result
            assert result is None
    
    @pytest.mark.asyncio
    async def test_get_resource_group_by_name_refresh_cache(self):
        """Test get_resource_group_by_name method with refresh_cache=True."""
        subscription_id = "test-sub-123"
        resource_group_name = "test-rg-1"
        
        # Mock get_resource_groups to return test data
        mock_resource_groups = [
            ResourceGroupModel(
                id="/subscriptions/test-sub-123/resourceGroups/test-rg-1",
                name="test-rg-1",
                location="westus",
                tags={"env": "test1"}
            )
        ]
        
        with patch.object(self.mixin, "get_resource_groups", AsyncMock(return_value=mock_resource_groups)) as mock_get_rgs:
            # Test method with refresh_cache=True
            result = await self.mixin.get_resource_group_by_name(
                subscription_id, resource_group_name, refresh_cache=True
            )
            
            # Verify result
            assert result is not None
            assert result.name == resource_group_name
            
            # Verify get_resource_groups was called with refresh_cache=True
            mock_get_rgs.assert_called_once_with(subscription_id, refresh_cache=True)