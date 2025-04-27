"""Unit tests for the RouteMixin class."""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from azure_rm_proxy.core.mixins.route_mixin import RouteMixin
from azure_rm_proxy.core.models import RouteTableModel, RouteTableSummaryModel, RouteEntryModel


class TestRouteMixin:
    """Tests for the RouteMixin class."""

    def setup_method(self):
        """Set up test environment before each test method."""
        self.mixin = RouteMixin()
        self.mixin.cache = MagicMock()
        self.mixin.limiter = AsyncMock()
        self.mixin.credential = MagicMock()
        self.subscription_id = "test-sub-123"
        self.resource_group = "test-rg"
        self.route_table_name = "test-rt"
        
        # Mock the logging methods
        self.mixin._log_debug = MagicMock()
        self.mixin._log_info = MagicMock()
        self.mixin._log_warning = MagicMock()
        self.mixin._log_error = MagicMock()
    
    @pytest.mark.asyncio
    async def test_get_route_tables(self):
        """Test get_route_tables method."""
        # Mock the network client and response
        mock_client = AsyncMock()
        mock_route_table = MagicMock()
        mock_route_table.id = f"/subscriptions/{self.subscription_id}/resourceGroups/{self.resource_group}/providers/Microsoft.Network/routeTables/{self.route_table_name}"
        mock_route_table.name = self.route_table_name
        mock_route_table.location = "westus"
        mock_route_table.tags = {"environment": "test"}
        mock_route_table.provisioning_state = "Succeeded"
        mock_route_table.subnets = [MagicMock(), MagicMock()]
        mock_route_table.routes = [MagicMock(), MagicMock(), MagicMock()]
        
        # Set up the routes to be pageable
        mock_client.route_tables.list.return_value = AsyncMock()
        mock_client.route_tables.list.return_value.__aiter__.return_value = [mock_route_table]
        
        # Mock the _get_client method
        self.mixin._get_client = AsyncMock(return_value=mock_client)
        
        # Call the method
        result = await self.mixin.get_route_tables(self.subscription_id, refresh_cache=False)
        
        # Verify results
        assert len(result) == 1
        assert isinstance(result[0], RouteTableSummaryModel)
        assert result[0].id == mock_route_table.id
        assert result[0].name == mock_route_table.name
        assert result[0].route_count == 3
        assert result[0].subnet_count == 2
        
        # Verify calls
        self.mixin._get_client.assert_awaited_once_with("network", self.subscription_id)
        mock_client.route_tables.list.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_route_tables_with_cache(self):
        """Test get_route_tables method with cached data."""
        # Mock cached data
        cached_routes = [
            RouteTableSummaryModel(
                id=f"/subscriptions/{self.subscription_id}/resourceGroups/{self.resource_group}/providers/Microsoft.Network/routeTables/{self.route_table_name}",
                name=self.route_table_name,
                location="westus",
                resource_group=self.resource_group,
                route_count=3,
                subnet_count=2,
                provisioning_state="Succeeded",
                subscription_id=self.subscription_id
            )
        ]
        
        self.mixin.cache.get.return_value = cached_routes
        
        # Mock _get_client to ensure it's not called
        with patch.object(self.mixin, "_get_client", new_callable=AsyncMock) as mock_get_client:
            # Call the method
            result = await self.mixin.get_route_tables(self.subscription_id)

            # Verify results
            assert result == cached_routes

            # Verify calls
            self.mixin.cache.get.assert_called_once()
            mock_get_client.assert_not_called() # Check the mock
    
    @pytest.mark.asyncio
    async def test_get_route_table(self):
        """Test get_route_table method."""
        # Mock the network client and response
        mock_client = AsyncMock()
        mock_route_table = MagicMock()
        mock_route_table.id = f"/subscriptions/{self.subscription_id}/resourceGroups/{self.resource_group}/providers/Microsoft.Network/routeTables/{self.route_table_name}"
        mock_route_table.name = self.route_table_name
        mock_route_table.location = "westus"
        mock_route_table.resource_group = self.resource_group
        mock_route_table.provisioning_state = "Succeeded"
        mock_route_table.disable_bgp_route_propagation = False
        mock_route_table.tags = {"environment": "test"}
        
        # Set up routes
        mock_route1 = MagicMock()
        mock_route1.name = "route1"
        mock_route1.address_prefix = "10.0.0.0/16"
        mock_route1.next_hop_type = "VirtualAppliance"
        mock_route1.next_hop_ip_address = "10.0.0.4"
        
        mock_route2 = MagicMock()
        mock_route2.name = "route2"
        mock_route2.address_prefix = "0.0.0.0/0"
        mock_route2.next_hop_type = "Internet"
        mock_route2.next_hop_ip_address = None
        
        mock_route_table.routes = [mock_route1, mock_route2]
        
        # Set up subnets
        mock_subnet1 = MagicMock()
        mock_subnet1.id = f"/subscriptions/{self.subscription_id}/resourceGroups/{self.resource_group}/providers/Microsoft.Network/virtualNetworks/vnet1/subnets/subnet1"
        mock_subnet2 = MagicMock()
        mock_subnet2.id = f"/subscriptions/{self.subscription_id}/resourceGroups/{self.resource_group}/providers/Microsoft.Network/virtualNetworks/vnet1/subnets/subnet2"
        
        mock_route_table.subnets = [mock_subnet1, mock_subnet2]
        
        # Mock the get operation
        mock_client.route_tables.get.return_value = mock_route_table
        
        # Mock the _get_client method
        self.mixin._get_client = AsyncMock(return_value=mock_client)
        
        # Call the method
        result = await self.mixin.get_route_table(self.subscription_id, self.resource_group, self.route_table_name)
        
        # Verify results
        assert isinstance(result, RouteTableModel)
        assert result.id == mock_route_table.id
        assert result.name == mock_route_table.name
        assert len(result.routes) == 2
        assert result.routes[0].name == "route1"
        assert result.routes[0].address_prefix == "10.0.0.0/16"
        assert result.routes[0].next_hop_type == "VirtualAppliance"
        assert result.routes[0].next_hop_ip_address == "10.0.0.4"
        assert len(result.subnets) == 2
        
        # Verify calls
        self.mixin._get_client.assert_awaited_once_with("network", self.subscription_id)
        mock_client.route_tables.get.assert_called_once_with(self.resource_group, self.route_table_name)
    
    @pytest.mark.asyncio
    async def test_get_route_table_with_cache(self):
        """Test get_route_table method with cached data."""
        # Mock cached data
        cached_route_table = RouteTableModel(
            id=f"/subscriptions/{self.subscription_id}/resourceGroups/{self.resource_group}/providers/Microsoft.Network/routeTables/{self.route_table_name}",
            name=self.route_table_name,
            location="westus",
            resource_group=self.resource_group,
            routes=[
                RouteEntryModel(
                    name="route1",
                    address_prefix="10.0.0.0/16",
                    next_hop_type="VirtualAppliance",
                    next_hop_ip_address="10.0.0.4"
                ),
                RouteEntryModel(
                    name="route2",
                    address_prefix="0.0.0.0/0",
                    next_hop_type="Internet"
                )
            ],
            subnets=[
                f"/subscriptions/{self.subscription_id}/resourceGroups/{self.resource_group}/providers/Microsoft.Network/virtualNetworks/vnet1/subnets/subnet1",
                f"/subscriptions/{self.subscription_id}/resourceGroups/{self.resource_group}/providers/Microsoft.Network/virtualNetworks/vnet1/subnets/subnet2"
            ],
            provisioning_state="Succeeded",
            disable_bgp_route_propagation=False,
            subscription_id=self.subscription_id
        )
        
        self.mixin.cache.get.return_value = cached_route_table
        
        # Mock _get_client to ensure it's not called
        with patch.object(self.mixin, "_get_client", new_callable=AsyncMock) as mock_get_client:
            # Call the method
            result = await self.mixin.get_route_table(self.subscription_id, self.resource_group, self.route_table_name)

            # Verify results
            assert result == cached_route_table

            # Verify calls
            self.mixin.cache.get.assert_called_once()
            mock_get_client.assert_not_called() # Check the mock