"""Unit tests for the NetworkMixin class."""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from azure_rm_proxy.core.mixins.network_mixin import NetworkMixin
from azure_rm_proxy.core.models import NetworkInterfaceModel, NsgRuleModel, RouteModel
from azure.core.exceptions import ResourceNotFoundError


class TestNetworkMixin:
    """Tests for the NetworkMixin class."""

    def setup_method(self):
        """Set up test environment before each test method."""
        self.mixin = NetworkMixin()
        self.mixin.cache = MagicMock()
        self.mixin.limiter = AsyncMock()
        self.mixin.credential = MagicMock()
        
    def test_get_private_ips(self):
        """Test the _get_private_ips method."""
        # Create a mock NIC with IP configurations
        nic = MagicMock()
        ip_config1 = MagicMock()
        ip_config1.private_ip_address = "10.0.0.1"
        ip_config2 = MagicMock()
        ip_config2.private_ip_address = "10.0.0.2"
        nic.ip_configurations = [ip_config1, ip_config2]
        
        # Call the method
        result = self.mixin._get_private_ips(nic)
        
        # Verify results
        assert len(result) == 2
        assert "10.0.0.1" in result
        assert "10.0.0.2" in result
        
    def test_get_private_ips_empty(self):
        """Test the _get_private_ips method with no IP configurations."""
        # Create a mock NIC with no IP configurations
        nic = MagicMock()
        nic.ip_configurations = []
        
        # Call the method
        result = self.mixin._get_private_ips(nic)
        
        # Verify results
        assert len(result) == 0
        
    def test_get_port_range(self):
        """Test the _get_port_range method."""
        # Test with destination_port_range
        rule1 = MagicMock()
        rule1.destination_port_range = "80"
        result1 = self.mixin._get_port_range(rule1)
        assert result1 == "80"
        
        # Test with destination_port_ranges
        rule2 = MagicMock()
        rule2.destination_port_range = None
        rule2.destination_port_ranges = ["80", "443"]
        result2 = self.mixin._get_port_range(rule2)
        assert result2 == "80,443"
        
        # Test with neither
        rule3 = MagicMock()
        rule3.destination_port_range = None
        result3 = self.mixin._get_port_range(rule3)
        assert result3 == "Any"
        
    @pytest.mark.asyncio
    async def test_get_public_ips(self):
        """Test the _get_public_ips method."""
        # Create a mock NIC with public IP configuration
        nic = MagicMock()
        ip_config = MagicMock()
        ip_config.public_ip_address = MagicMock()
        ip_config.public_ip_address.name = "test-pip"
        nic.ip_configurations = [ip_config]
        
        # Create a mock network client
        network_client = MagicMock()
        public_ip = MagicMock()
        public_ip.ip_address = "1.2.3.4"
        network_client.public_ip_addresses.get.return_value = public_ip
        
        # Call the method
        result = await self.mixin._get_public_ips(nic, network_client, "test-rg", "test-vm")
        
        # Verify results
        assert len(result) == 1
        assert result[0] == "1.2.3.4"
        network_client.public_ip_addresses.get.assert_called_once_with("test-rg", "test-pip")
        
    @pytest.mark.asyncio
    async def test_get_public_ips_not_found(self):
        """Test the _get_public_ips method with ResourceNotFoundError."""
        # Create a mock NIC with public IP configuration
        nic = MagicMock()
        ip_config = MagicMock()
        ip_config.public_ip_address = MagicMock()
        ip_config.public_ip_address.name = "test-pip"
        nic.ip_configurations = [ip_config]
        
        # Create a mock network client that raises ResourceNotFoundError
        network_client = MagicMock()
        network_client.public_ip_addresses.get.side_effect = ResourceNotFoundError("Public IP not found")
        
        # Call the method
        result = await self.mixin._get_public_ips(nic, network_client, "test-rg", "test-vm")
        
        # Verify results
        assert len(result) == 0  # No public IPs should be returned
        network_client.public_ip_addresses.get.assert_called_once_with("test-rg", "test-pip")
        
    @pytest.mark.asyncio
    async def test_fetch_network_interfaces(self):
        """Test the _fetch_network_interfaces method."""
        # Create a mock VM with network interfaces
        vm = MagicMock()
        nic_ref = MagicMock()
        nic_ref.id = "/subscriptions/sub123/resourceGroups/rg1/providers/Microsoft.Network/networkInterfaces/nic1"
        vm.network_profile.network_interfaces = [nic_ref]
        
        # Create a mock network client
        network_client = MagicMock()
        nic = MagicMock()
        nic.id = nic_ref.id
        nic.name = "nic1"
        nic.ip_configurations = []
        network_client.network_interfaces.get.return_value = nic
        
        # Mock the helper methods
        with patch.object(self.mixin, "_get_private_ips") as mock_get_private_ips:
            mock_get_private_ips.return_value = ["10.0.0.1"]
            
            with patch.object(self.mixin, "_get_public_ips") as mock_get_public_ips:
                mock_get_public_ips.return_value = ["1.2.3.4"]
                
                # Call the method
                result = await self.mixin._fetch_network_interfaces(vm, network_client, "test-vm")
                
                # Verify results
                assert len(result) == 1
                assert isinstance(result[0], NetworkInterfaceModel)
                assert result[0].id == nic_ref.id
                assert result[0].name == "nic1"
                assert result[0].private_ip_addresses == ["10.0.0.1"]
                assert result[0].public_ip_addresses == ["1.2.3.4"]
                network_client.network_interfaces.get.assert_called_once_with("rg1", "nic1")
                
    @pytest.mark.asyncio
    async def test_fetch_nsg_rules_direct_method(self):
        """Test the _fetch_nsg_rules method using the direct method."""
        # Create mock network interfaces
        nic = MagicMock()
        nic.id = "/subscriptions/sub123/resourceGroups/rg1/providers/Microsoft.Network/networkInterfaces/nic1"
        nic.name = "nic1"
        network_interfaces = [NetworkInterfaceModel(
            id=nic.id,
            name=nic.name,
            private_ip_addresses=["10.0.0.1"],
            public_ip_addresses=["1.2.3.4"]
        )]
        
        # Create a mock network client
        network_client = MagicMock()
        
        # Mock the NIC with NSG
        detailed_nic = MagicMock()
        detailed_nic.network_security_group = MagicMock()
        detailed_nic.network_security_group.id = "/subscriptions/sub123/resourceGroups/rg1/providers/Microsoft.Network/networkSecurityGroups/nsg1"
        network_client.network_interfaces.get.return_value = detailed_nic
        
        # Mock the NSG with security rules
        nsg = MagicMock()
        rule = MagicMock()
        rule.name = "allow-ssh"
        rule.direction = "Inbound"
        rule.protocol = "Tcp"
        rule.destination_port_range = "22"
        rule.access = "Allow"
        nsg.security_rules = [rule]
        network_client.network_security_groups.get.return_value = nsg
        
        # Call the method
        result = await self.mixin._fetch_nsg_rules(network_client, "rg1", network_interfaces)
        
        # Verify results
        assert len(result) == 1
        assert isinstance(result[0], NsgRuleModel)
        assert result[0].name == "allow-ssh"
        assert result[0].direction == "Inbound"
        assert result[0].protocol == "Tcp"
        assert result[0].port_range == "22"
        assert result[0].access == "Allow"
        
    @pytest.mark.asyncio
    async def test_fetch_routes_direct_method(self):
        """Test _fetch_routes using the direct subnet/route table method."""
        # Create mock network interfaces
        nic = MagicMock()
        nic.id = "/subscriptions/sub123/resourceGroups/rg1/providers/Microsoft.Network/networkInterfaces/nic1"
        nic.name = "nic1"
        network_interfaces = [NetworkInterfaceModel(
            id=nic.id,
            name=nic.name,
            private_ip_addresses=["10.0.0.1"],
            public_ip_addresses=["1.2.3.4"]
        )]
        
        # Create a mock network client
        network_client = MagicMock()
        
        # Mock the NIC with subnet
        detailed_nic = MagicMock()
        ip_config = MagicMock()
        ip_config.subnet = MagicMock()
        ip_config.subnet.id = "/subscriptions/sub123/resourceGroups/rg1/providers/Microsoft.Network/virtualNetworks/vnet1/subnets/subnet1"
        detailed_nic.ip_configurations = [ip_config]
        network_client.network_interfaces.get.return_value = detailed_nic
        
        # Mock the subnet with route table
        subnet = MagicMock()
        subnet.route_table = MagicMock()
        subnet.route_table.id = "/subscriptions/sub123/resourceGroups/rg1/providers/Microsoft.Network/routeTables/rt1"
        network_client.subnets.get.return_value = subnet
        
        # Mock the route table with routes
        rt = MagicMock()
        route = MagicMock()
        route.name = "my-route"
        route.address_prefix = "10.0.0.0/8"
        route.next_hop_type = "VirtualAppliance"
        route.next_hop_ip_address = "10.10.10.10"
        rt.routes = [route]
        network_client.route_tables.get.return_value = rt
        
        # Call the method
        result = await self.mixin._fetch_routes(network_client, "rg1", network_interfaces)
        
        # Verify results
        assert len(result) == 1
        assert isinstance(result[0], RouteEntryModel)  # Check for RouteEntryModel
        assert result[0].name == "my-route"
        assert result[0].address_prefix == "10.0.0.0/8"
        assert result[0].next_hop_type == "VirtualAppliance"
        # Assert using the correct attribute name
        assert result[0].next_hop_ip_address == "10.10.10.10"