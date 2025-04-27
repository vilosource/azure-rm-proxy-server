"""Unit tests for the VirtualMachineMixin class."""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from azure_rm_proxy.core.mixins.virtual_machine_mixin import VirtualMachineMixin
from azure_rm_proxy.core.models import (
    VirtualMachineModel, 
    VirtualMachineDetail,
    VirtualMachineWithContext,
    NetworkInterfaceModel,
    NsgRuleModel,
    RouteModel,
    AADGroupModel
)


class TestVirtualMachineMixin:
    """Tests for the VirtualMachineMixin class."""

    def setup_method(self):
        """Set up test environment before each test method."""
        self.mixin = VirtualMachineMixin()
        self.mixin.cache = MagicMock()
        self.mixin.limiter = AsyncMock()
        self.mixin.credential = MagicMock()
        self.subscription_id = "test-sub-123"
        self.resource_group = "test-rg"
        self.vm_name = "test-vm"
        
        # Mock the logging methods
        self.mixin._log_debug = MagicMock()
        self.mixin._log_info = MagicMock()
        self.mixin._log_warning = MagicMock()
        self.mixin._log_error = MagicMock()
    
    @pytest.mark.asyncio
    async def test_get_virtual_machines(self):
        """Test get_virtual_machines method."""
        # Mock the compute client and response
        mock_client = AsyncMock()
        mock_vm = MagicMock()
        mock_vm.id = f"/subscriptions/{self.subscription_id}/resourceGroups/{self.resource_group}/providers/Microsoft.Compute/virtualMachines/{self.vm_name}"
        mock_vm.name = self.vm_name
        mock_vm.location = "westus"
        mock_vm.hardware_profile.vm_size = "Standard_D2s_v3"
        mock_vm.storage_profile.os_disk.os_type = "Linux"
        
        # Set up the VMs to be pageable
        mock_client.virtual_machines.list.return_value = AsyncMock()
        mock_client.virtual_machines.list.return_value.__aiter__.return_value = [mock_vm]
        
        # Mock the _get_client method
        self.mixin._get_client = AsyncMock(return_value=mock_client)
        
        # Mock the _convert_to_model method
        self.mixin._convert_to_model = MagicMock(
            return_value=VirtualMachineModel(
                id=mock_vm.id,
                name=mock_vm.name,
                location=mock_vm.location,
                vm_size=mock_vm.hardware_profile.vm_size,
                os_type=mock_vm.storage_profile.os_disk.os_type,
                power_state="running"
            )
        )
        
        # Call the method
        result = await self.mixin.get_virtual_machines(self.subscription_id, self.resource_group, refresh_cache=False)
        
        # Verify results
        assert len(result) == 1
        assert isinstance(result[0], VirtualMachineModel)
        assert result[0].id == mock_vm.id
        assert result[0].name == mock_vm.name
        assert result[0].vm_size == "Standard_D2s_v3"
        assert result[0].os_type == "Linux"
        assert result[0].power_state == "running"
        
        # Verify calls
        self.mixin._get_client.assert_awaited_once_with("compute", self.subscription_id)
        mock_client.virtual_machines.list.assert_called_once_with(self.resource_group)
    
    @pytest.mark.asyncio
    async def test_get_virtual_machines_with_cache(self):
        """Test get_virtual_machines method with cached data."""
        # Mock cached data
        cached_vms = [
            VirtualMachineModel(
                id=f"/subscriptions/{self.subscription_id}/resourceGroups/{self.resource_group}/providers/Microsoft.Compute/virtualMachines/{self.vm_name}",
                name=self.vm_name,
                location="westus",
                vm_size="Standard_D2s_v3",
                os_type="Linux",
                power_state="running"
            )
        ]
        
        self.mixin.cache.get.return_value = cached_vms
        
        # Call the method
        result = await self.mixin.get_virtual_machines(self.subscription_id, self.resource_group)
        
        # Verify results
        assert result == cached_vms
        
        # Verify calls
        self.mixin.cache.get.assert_called_once()
        self.mixin._get_client.assert_not_awaited()
    
    @pytest.mark.asyncio
    async def test_get_vm_details(self):
        """Test get_vm_details method."""
        # Mock the compute client and response
        mock_compute_client = AsyncMock()
        mock_network_client = AsyncMock()
        mock_graph_client = AsyncMock()
        
        # Mock VM
        mock_vm = MagicMock()
        mock_vm.id = f"/subscriptions/{self.subscription_id}/resourceGroups/{self.resource_group}/providers/Microsoft.Compute/virtualMachines/{self.vm_name}"
        mock_vm.name = self.vm_name
        mock_vm.location = "westus"
        mock_vm.hardware_profile.vm_size = "Standard_D2s_v3"
        mock_vm.storage_profile.os_disk.os_type = "Linux"
        mock_vm.network_profile.network_interfaces = [
            MagicMock(id=f"/subscriptions/{self.subscription_id}/resourceGroups/{self.resource_group}/providers/Microsoft.Network/networkInterfaces/nic1")
        ]
        
        # Set up the get operation
        mock_compute_client.virtual_machines.get.return_value = mock_vm
        
        # Mock the _get_client method
        self.mixin._get_client = AsyncMock(side_effect=[
            mock_compute_client,
            mock_network_client,
            mock_graph_client
        ])
        
        # Mock the helper methods
        self.mixin._convert_to_model = MagicMock(
            return_value=VirtualMachineModel(
                id=mock_vm.id,
                name=mock_vm.name,
                location=mock_vm.location,
                vm_size=mock_vm.hardware_profile.vm_size,
                os_type=mock_vm.storage_profile.os_disk.os_type,
                power_state="running"
            )
        )
        
        # Mock the fetch methods
        network_interfaces = [
            NetworkInterfaceModel(
                id="nic1",
                name="nic1",
                private_ip_addresses=["10.0.0.4"],
                public_ip_addresses=["20.30.40.50"]
            )
        ]
        
        nsg_rules = [
            NsgRuleModel(
                name="AllowSSH",
                priority=100,
                direction="Inbound",
                access="Allow",
                protocol="TCP",
                source_port_range="*",
                destination_port_range="22",
                source_address_prefix="*",
                destination_address_prefix="*",
                description="Allow SSH"
            )
        ]
        
        routes = [
            RouteModel(
                name="default",
                address_prefix="0.0.0.0/0",
                next_hop_type="Internet",
                next_hop_ip_address=None
            )
        ]
        
        aad_groups = [
            AADGroupModel(
                id="aad-group-1",
                display_name="Test Group",
                description="Test group description"
            )
        ]
        
        self.mixin._fetch_network_interfaces = AsyncMock(return_value=network_interfaces)
        self.mixin._fetch_nsg_rules = AsyncMock(return_value=nsg_rules)
        self.mixin._fetch_routes = AsyncMock(return_value=routes)
        self.mixin._fetch_aad_groups = AsyncMock(return_value=aad_groups)
        
        # Call the method
        result = await self.mixin.get_vm_details(self.subscription_id, self.resource_group, self.vm_name)
        
        # Verify results
        assert isinstance(result, VirtualMachineDetail)
        assert result.id == mock_vm.id
        assert result.name == mock_vm.name
        assert result.vm_size == "Standard_D2s_v3"
        assert result.os_type == "Linux"
        assert result.network_interfaces == network_interfaces
        assert result.effective_nsg_rules == nsg_rules
        assert result.effective_routes == routes
        assert result.aad_groups == aad_groups
        
        # Verify calls
        assert self.mixin._get_client.call_count == 3
        mock_compute_client.virtual_machines.get.assert_called_once_with(self.resource_group, self.vm_name)
        self.mixin._fetch_network_interfaces.assert_awaited_once()
        self.mixin._fetch_nsg_rules.assert_awaited_once()
        self.mixin._fetch_routes.assert_awaited_once()
        self.mixin._fetch_aad_groups.assert_awaited_once()
    
    @pytest.mark.asyncio
    async def test_get_vm_details_with_cache(self):
        """Test get_vm_details method with cached data."""
        # Mock cached data
        cached_vm_detail = VirtualMachineDetail(
            id=f"/subscriptions/{self.subscription_id}/resourceGroups/{self.resource_group}/providers/Microsoft.Compute/virtualMachines/{self.vm_name}",
            name=self.vm_name,
            location="westus",
            vm_size="Standard_D2s_v3",
            os_type="Linux",
            power_state="running",
            network_interfaces=[
                NetworkInterfaceModel(
                    id="nic1",
                    name="nic1",
                    private_ip_addresses=["10.0.0.4"],
                    public_ip_addresses=["20.30.40.50"]
                )
            ],
            effective_nsg_rules=[
                NsgRuleModel(
                    name="AllowSSH",
                    priority=100,
                    direction="Inbound",
                    access="Allow",
                    protocol="TCP",
                    source_port_range="*",
                    destination_port_range="22",
                    source_address_prefix="*",
                    destination_address_prefix="*",
                    description="Allow SSH"
                )
            ],
            effective_routes=[
                RouteModel(
                    name="default",
                    address_prefix="0.0.0.0/0",
                    next_hop_type="Internet"
                )
            ],
            aad_groups=[
                AADGroupModel(
                    id="aad-group-1",
                    display_name="Test Group",
                    description="Test group description"
                )
            ]
        )
        
        self.mixin.cache.get.return_value = cached_vm_detail
        
        # Call the method
        result = await self.mixin.get_vm_details(self.subscription_id, self.resource_group, self.vm_name)
        
        # Verify results
        assert result == cached_vm_detail
        
        # Verify calls
        self.mixin.cache.get.assert_called_once()
        self.mixin._get_client.assert_not_awaited()
    
    @pytest.mark.asyncio
    async def test_get_all_virtual_machines(self):
        """Test get_all_virtual_machines method."""
        # Mock the subscription mixin
        self.mixin.get_subscriptions = AsyncMock(return_value=[
            MagicMock(subscription_id=self.subscription_id, display_name="Test Subscription")
        ])
        
        # Mock the resource group mixin
        self.mixin.get_resource_groups = AsyncMock(return_value=[
            MagicMock(name=self.resource_group)
        ])
        
        # Mock the get_virtual_machines method
        mock_vm = VirtualMachineModel(
            id=f"/subscriptions/{self.subscription_id}/resourceGroups/{self.resource_group}/providers/Microsoft.Compute/virtualMachines/{self.vm_name}",
            name=self.vm_name,
            location="westus",
            vm_size="Standard_D2s_v3",
            os_type="Linux",
            power_state="running"
        )
        
        self.mixin.get_virtual_machines = AsyncMock(return_value=[mock_vm])
        
        # Call the method
        result = await self.mixin.get_all_virtual_machines()
        
        # Verify results
        assert len(result) == 1
        assert isinstance(result[0], VirtualMachineWithContext)
        assert result[0].id == mock_vm.id
        assert result[0].name == mock_vm.name
        assert result[0].subscription_id == self.subscription_id
        assert result[0].subscription_name == "Test Subscription"
        assert result[0].resource_group_name == self.resource_group
        
        # Verify calls
        self.mixin.get_subscriptions.assert_awaited_once()
        self.mixin.get_resource_groups.assert_awaited_once_with(self.subscription_id)
        self.mixin.get_virtual_machines.assert_awaited_once_with(self.subscription_id, self.resource_group)
    
    @pytest.mark.asyncio
    async def test_get_all_virtual_machines_with_cache(self):
        """Test get_all_virtual_machines method with cached data."""
        # Mock cached data
        cached_vms = [
            VirtualMachineWithContext(
                id=f"/subscriptions/{self.subscription_id}/resourceGroups/{self.resource_group}/providers/Microsoft.Compute/virtualMachines/{self.vm_name}",
                name=self.vm_name,
                location="westus",
                vm_size="Standard_D2s_v3",
                os_type="Linux",
                power_state="running",
                subscription_id=self.subscription_id,
                subscription_name="Test Subscription",
                resource_group_name=self.resource_group,
                detail_url=f"/api/virtual-machines/{self.subscription_id}/{self.resource_group}/{self.vm_name}"
            )
        ]
        
        self.mixin.cache.get.return_value = cached_vms
        
        # Call the method
        result = await self.mixin.get_all_virtual_machines()
        
        # Verify results
        assert result == cached_vms
        
        # Verify calls
        self.mixin.cache.get.assert_called_once()
        self.mixin.get_subscriptions.assert_not_awaited()
        self.mixin.get_resource_groups.assert_not_awaited()
        self.mixin.get_virtual_machines.assert_not_awaited()
    
    @pytest.mark.asyncio
    async def test_find_vm_by_name(self):
        """Test find_vm_by_name method."""
        # Setup test VMs
        test_vms = [
            VirtualMachineWithContext(
                id=f"/subscriptions/{self.subscription_id}/resourceGroups/{self.resource_group}/providers/Microsoft.Compute/virtualMachines/{self.vm_name}",
                name=self.vm_name,
                location="westus",
                vm_size="Standard_D2s_v3",
                os_type="Linux",
                power_state="running",
                subscription_id=self.subscription_id,
                subscription_name="Test Subscription",
                resource_group_name=self.resource_group
            ),
            VirtualMachineWithContext(
                id=f"/subscriptions/{self.subscription_id}/resourceGroups/{self.resource_group}/providers/Microsoft.Compute/virtualMachines/another-vm",
                name="another-vm",
                location="westus",
                vm_size="Standard_D2s_v3",
                os_type="Linux",
                power_state="running",
                subscription_id=self.subscription_id,
                subscription_name="Test Subscription",
                resource_group_name=self.resource_group
            )
        ]
        
        # Mock get_all_virtual_machines
        self.mixin.get_all_virtual_machines = AsyncMock(return_value=test_vms)
        
        # Mock get_vm_details
        vm_detail = VirtualMachineDetail(
            id=f"/subscriptions/{self.subscription_id}/resourceGroups/{self.resource_group}/providers/Microsoft.Compute/virtualMachines/{self.vm_name}",
            name=self.vm_name,
            location="westus",
            vm_size="Standard_D2s_v3",
            os_type="Linux",
            power_state="running",
            network_interfaces=[],
            effective_nsg_rules=[],
            effective_routes=[],
            aad_groups=[]
        )
        
        self.mixin.get_vm_details = AsyncMock(return_value=vm_detail)
        
        # Call the method with exact name
        result = await self.mixin.find_vm_by_name(self.vm_name)
        
        # Verify results
        assert result == vm_detail
        
        # Verify calls
        self.mixin.get_all_virtual_machines.assert_awaited_once()
        self.mixin.get_vm_details.assert_awaited_once_with(
            self.subscription_id, self.resource_group, self.vm_name
        )
        
        # Reset mocks
        self.mixin.get_all_virtual_machines.reset_mock()
        self.mixin.get_vm_details.reset_mock()
        
        # Test with partial name
        result = await self.mixin.find_vm_by_name("test")
        
        # Verify results
        assert result == vm_detail
        
        # Verify calls
        self.mixin.get_all_virtual_machines.assert_awaited_once()
        self.mixin.get_vm_details.assert_awaited_once_with(
            self.subscription_id, self.resource_group, self.vm_name
        )
    
    @pytest.mark.asyncio
    async def test_find_vm_by_name_not_found(self):
        """Test find_vm_by_name method when VM is not found."""
        # Setup test VMs
        test_vms = [
            VirtualMachineWithContext(
                id=f"/subscriptions/{self.subscription_id}/resourceGroups/{self.resource_group}/providers/Microsoft.Compute/virtualMachines/vm1",
                name="vm1",
                location="westus",
                vm_size="Standard_D2s_v3",
                os_type="Linux",
                power_state="running",
                subscription_id=self.subscription_id,
                subscription_name="Test Subscription",
                resource_group_name=self.resource_group
            )
        ]
        
        # Mock get_all_virtual_machines
        self.mixin.get_all_virtual_machines = AsyncMock(return_value=test_vms)
        
        # Call the method with non-existing name
        with pytest.raises(ValueError, match="No VM found with name"):
            await self.mixin.find_vm_by_name("non-existent-vm")
        
        # Verify calls
        self.mixin.get_all_virtual_machines.assert_awaited_once()
        self.mixin.get_vm_details.assert_not_awaited()