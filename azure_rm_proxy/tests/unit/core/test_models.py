import pytest
from pydantic import ValidationError
from azure_rm_proxy.core.models import (
    SubscriptionModel,
    ResourceGroupModel,
    NetworkInterfaceModel,
    NsgRuleModel,
    RouteModel,
    RouteEntryModel,
    RouteTableSummaryModel,
    RouteTableModel,
    AADGroupModel,
    VirtualMachineModel,
    VirtualMachineDetail,
    VirtualMachineWithContext,
    VirtualMachineHostname,
    VirtualMachineReport,
)


class TestModels:
    """Test suite for data models."""

    def test_subscription_model(self):
        """Test SubscriptionModel validation."""
        # Valid data
        data = {"id": "sub-123", "name": "Test Subscription", "state": "Enabled"}

        # Create model
        subscription = SubscriptionModel(**data)

        # Assertions
        assert subscription.id == "sub-123"
        assert subscription.name == "Test Subscription"
        assert subscription.display_name is None
        assert subscription.state == "Enabled"

        # Test with all fields
        data_with_all = {
            "id": "sub-123",
            "name": "Test Subscription",
            "display_name": "Displayed Subscription Name",
            "state": "Enabled",
        }

        subscription_full = SubscriptionModel(**data_with_all)
        assert subscription_full.display_name == "Displayed Subscription Name"

        # Missing required field
        with pytest.raises(ValidationError):
            SubscriptionModel(id="sub-123", name="Test Subscription")  # Missing state

    def test_resource_group_model(self):
        """Test ResourceGroupModel validation."""
        # Valid data
        data = {"id": "rg-123", "name": "test-resource-group", "location": "eastus"}

        # Create model
        resource_group = ResourceGroupModel(**data)

        # Assertions
        assert resource_group.id == "rg-123"
        assert resource_group.name == "test-resource-group"
        assert resource_group.location == "eastus"
        assert resource_group.tags is None

        # Test with tags
        data_with_tags = {
            "id": "rg-123",
            "name": "test-resource-group",
            "location": "eastus",
            "tags": {"env": "test", "owner": "test-user"},
        }

        resource_group_with_tags = ResourceGroupModel(**data_with_tags)
        assert resource_group_with_tags.tags == {"env": "test", "owner": "test-user"}

    def test_network_interface_model(self):
        """Test NetworkInterfaceModel validation."""
        # Valid data
        data = {
            "id": "nic-123",
            "name": "test-nic",
            "private_ip_addresses": ["10.0.0.4"],
            "public_ip_addresses": [],
        }

        # Create model
        nic = NetworkInterfaceModel(**data)

        # Assertions
        assert nic.id == "nic-123"
        assert nic.name == "test-nic"
        assert nic.private_ip_addresses == ["10.0.0.4"]
        assert nic.public_ip_addresses == []

        # Test with multiple IPs
        data_multiple_ips = {
            "id": "nic-123",
            "name": "test-nic",
            "private_ip_addresses": ["10.0.0.4", "10.0.0.5"],
            "public_ip_addresses": ["20.30.40.50", "20.30.40.51"],
        }

        nic_multiple_ips = NetworkInterfaceModel(**data_multiple_ips)
        assert len(nic_multiple_ips.private_ip_addresses) == 2
        assert len(nic_multiple_ips.public_ip_addresses) == 2

    def test_virtual_machine_model(self):
        """Test VirtualMachineModel validation."""
        # Valid data
        data = {
            "id": "vm-123",
            "name": "test-vm",
            "location": "eastus",
            "vm_size": "Standard_DS2_v2",
        }

        # Create model
        vm = VirtualMachineModel(**data)

        # Assertions
        assert vm.id == "vm-123"
        assert vm.name == "test-vm"
        assert vm.location == "eastus"
        assert vm.vm_size == "Standard_DS2_v2"
        assert vm.os_type is None
        assert vm.power_state is None

        # Test with optional fields
        data_with_optional = {
            "id": "vm-123",
            "name": "test-vm",
            "location": "eastus",
            "vm_size": "Standard_DS2_v2",
            "os_type": "Linux",
            "power_state": "Running",
        }

        vm_with_optional = VirtualMachineModel(**data_with_optional)
        assert vm_with_optional.os_type == "Linux"
        assert vm_with_optional.power_state == "Running"

    def test_virtual_machine_detail(self):
        """Test VirtualMachineDetail validation."""
        # Create test data
        nic = NetworkInterfaceModel(
            id="nic-123",
            name="test-nic",
            private_ip_addresses=["10.0.0.4"],
            public_ip_addresses=[],
        )

        nsg_rule = NsgRuleModel(
            name="test-rule",
            direction="Inbound",
            protocol="TCP",
            port_range="80",
            access="Allow",
        )

        route = RouteModel(
            address_prefix="0.0.0.0/0",
            next_hop_type="Internet",
            next_hop_ip=None,
            route_origin="Default",
        )

        aad_group = AADGroupModel(id="group-123", display_name="Test Group")

        # Valid VM detail data
        data = {
            "id": "vm-123",
            "name": "test-vm",
            "location": "eastus",
            "vm_size": "Standard_DS2_v2",
            "os_type": "Linux",
            "power_state": "Running",
            "network_interfaces": [nic.model_dump()],
            "effective_nsg_rules": [nsg_rule.model_dump()],
            "effective_routes": [route.model_dump()],
            "aad_groups": [aad_group.model_dump()],
        }

        # Create model
        vm_detail = VirtualMachineDetail(**data)

        # Assertions
        assert vm_detail.id == "vm-123"
        assert vm_detail.name == "test-vm"
        assert len(vm_detail.network_interfaces) == 1
        assert vm_detail.network_interfaces[0].id == "nic-123"
        assert len(vm_detail.effective_nsg_rules) == 1
        assert vm_detail.effective_nsg_rules[0].name == "test-rule"
        assert len(vm_detail.effective_routes) == 1
        assert vm_detail.effective_routes[0].next_hop_type == "Internet"
        assert len(vm_detail.aad_groups) == 1
        assert vm_detail.aad_groups[0].display_name == "Test Group"

    def test_virtual_machine_report(self):
        """Test VirtualMachineReport validation."""
        # Valid data
        data = {
            "vm_name": "test-vm",
            "vm_size": "Standard_DS2_v2",
            "resource_group": "test-rg",
            "location": "eastus",
            "subscription_id": "sub-123",
        }

        # Create model
        vm_report = VirtualMachineReport(**data)

        # Assertions
        assert vm_report.vm_name == "test-vm"
        assert vm_report.vm_size == "Standard_DS2_v2"
        assert vm_report.resource_group == "test-rg"
        assert vm_report.location == "eastus"
        assert vm_report.subscription_id == "sub-123"
        assert vm_report.hostname is None
        assert vm_report.os is None
        assert vm_report.environment is None
        assert vm_report.purpose is None
        assert vm_report.ip_addresses == []
        assert vm_report.public_ip_addresses == []
        assert vm_report.os_disk_size_gb is None
        assert vm_report.subscription_name is None

        # Test with all fields
        data_with_all = {
            "vm_name": "test-vm",
            "vm_size": "Standard_DS2_v2",
            "resource_group": "test-rg",
            "location": "eastus",
            "subscription_id": "sub-123",
            "subscription_name": "Test Subscription",
            "hostname": "test-vm.example.com",
            "os": "Linux",
            "environment": "Production",
            "purpose": "Web Server",
            "ip_addresses": ["10.0.0.4"],
            "public_ip_addresses": ["20.30.40.50"],
            "os_disk_size_gb": 128.0,
        }

        vm_report_full = VirtualMachineReport(**data_with_all)
        assert vm_report_full.hostname == "test-vm.example.com"
        assert vm_report_full.os == "Linux"
        assert vm_report_full.environment == "Production"
        assert vm_report_full.purpose == "Web Server"
        assert vm_report_full.ip_addresses == ["10.0.0.4"]
        assert vm_report_full.public_ip_addresses == ["20.30.40.50"]
        # Use approximate comparison for floating point values
        assert abs(vm_report_full.os_disk_size_gb - 128.0) < 0.0001
        assert vm_report_full.subscription_name == "Test Subscription"
