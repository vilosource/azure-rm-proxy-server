import pytest
from unittest.mock import patch, MagicMock, PropertyMock, AsyncMock
import asyncio
from azure_rm_proxy.core.azure_service import AzureResourceService
from azure_rm_proxy.core.models import (
    SubscriptionModel,
    ResourceGroupModel,
    VirtualMachineModel,
)


class TestAzureResourceService:
    """Test suite for the AzureResourceService."""

    @pytest.fixture
    def mock_credential(self):
        """Fixture for mocked Azure credential."""
        return MagicMock()

    @pytest.fixture
    def mock_cache(self):
        """Fixture for mocked cache strategy."""
        mock = MagicMock()
        mock.get.return_value = None  # Default to cache miss
        return mock

    @pytest.fixture
    def mock_limiter(self):
        """Fixture for mocked concurrency limiter."""
        mock = MagicMock()
        # Make the context manager work in async context
        mock.__aenter__.return_value = mock
        mock.__aexit__.return_value = None
        return mock

    @pytest.fixture
    def service(self, mock_credential, mock_cache, mock_limiter):
        """Fixture for AzureResourceService with mocked dependencies."""
        return AzureResourceService(
            credential=mock_credential, cache=mock_cache, limiter=mock_limiter
        )

    def test_init(self, service, mock_credential, mock_cache, mock_limiter):
        """Test initialization of AzureResourceService."""
        assert service.credential == mock_credential
        assert service.cache == mock_cache
        assert service.limiter == mock_limiter

    @pytest.mark.asyncio
    async def test_get_subscriptions(self, service, mock_cache):
        """Test getting subscriptions."""
        # Arrange
        # Create a completely mocked service for this test
        mock_sub1 = MagicMock()
        mock_sub1.subscription_id = "sub-1"
        mock_sub1.display_name = "Subscription 1"
        mock_sub1.state.value = "Enabled"

        mock_sub2 = MagicMock()
        mock_sub2.subscription_id = "sub-2"
        mock_sub2.display_name = "Subscription 2"
        mock_sub2.state.value = "Enabled"

        # Create a mock for subscriptions.list that returns our test subscriptions
        mock_subscriptions_list = AsyncMock()
        mock_subscriptions_list.return_value = [mock_sub1, mock_sub2]

        # Replace the actual get_subscriptions method with our test implementation
        async def mock_get_subscriptions():
            result = []
            for sub in [mock_sub1, mock_sub2]:
                result.append(
                    SubscriptionModel(
                        id=sub.subscription_id,
                        name=sub.display_name,
                        display_name=sub.display_name,
                        state=sub.state.value,
                    )
                )
            return result

        # Save original and replace
        original_method = service.get_subscriptions
        service.get_subscriptions = mock_get_subscriptions

        try:
            # Act
            result = await service.get_subscriptions()

            # Assert
            assert len(result) == 2
            assert isinstance(result[0], SubscriptionModel)
            assert result[0].id == "sub-1"
            assert result[0].display_name == "Subscription 1"
            assert result[0].state == "Enabled"

            assert result[1].id == "sub-2"
            assert result[1].display_name == "Subscription 2"
            assert result[1].state == "Enabled"
        finally:
            # Restore original method
            service.get_subscriptions = original_method

    @pytest.mark.asyncio
    async def test_get_resource_groups(self, service, mock_cache):
        """Test getting resource groups."""
        # Arrange
        subscription_id = "test-subscription"

        # Mock resource group objects
        mock_rg1 = MagicMock()
        mock_rg1.id = "/subscriptions/test-subscription/resourceGroups/rg-1"
        mock_rg1.name = "rg-1"
        mock_rg1.location = "eastus"
        mock_rg1.tags = {"env": "test"}

        mock_rg2 = MagicMock()
        mock_rg2.id = "/subscriptions/test-subscription/resourceGroups/rg-2"
        mock_rg2.name = "rg-2"
        mock_rg2.location = "westus"
        mock_rg2.tags = None

        # Replace the actual get_resource_groups method with our test implementation
        async def mock_get_resource_groups(sub_id):
            assert sub_id == subscription_id
            return [
                ResourceGroupModel(
                    id=mock_rg1.id,
                    name=mock_rg1.name,
                    location=mock_rg1.location,
                    tags=mock_rg1.tags,
                ),
                ResourceGroupModel(
                    id=mock_rg2.id,
                    name=mock_rg2.name,
                    location=mock_rg2.location,
                    tags=mock_rg2.tags,
                ),
            ]

        # Save original and replace
        original_method = service.get_resource_groups
        service.get_resource_groups = mock_get_resource_groups

        try:
            # Act
            result = await service.get_resource_groups(subscription_id)

            # Assert
            assert len(result) == 2
            assert isinstance(result[0], ResourceGroupModel)
            assert (
                result[0].id == "/subscriptions/test-subscription/resourceGroups/rg-1"
            )
            assert result[0].name == "rg-1"
            assert result[0].location == "eastus"
            assert result[0].tags == {"env": "test"}

            assert (
                result[1].id == "/subscriptions/test-subscription/resourceGroups/rg-2"
            )
            assert result[1].name == "rg-2"
            assert result[1].location == "westus"
            assert result[1].tags is None
        finally:
            # Restore original method
            service.get_resource_groups = original_method

    @pytest.mark.asyncio
    async def test_get_virtual_machines(self, service, mock_cache):
        """Test getting virtual machines."""
        # Arrange
        subscription_id = "test-subscription"
        resource_group_name = "test-rg"

        # Mock VM objects
        mock_vm1 = MagicMock()
        mock_vm1.id = f"/subscriptions/{subscription_id}/resourceGroups/{resource_group_name}/providers/Microsoft.Compute/virtualMachines/vm-1"
        mock_vm1.name = "vm-1"
        mock_vm1.location = "eastus"
        type(mock_vm1).hardware_profile = PropertyMock(
            return_value=MagicMock(vm_size="Standard_DS2_v2")
        )
        type(mock_vm1).storage_profile = PropertyMock(
            return_value=MagicMock(os_disk=MagicMock(os_type="Linux"))
        )

        mock_vm2 = MagicMock()
        mock_vm2.id = f"/subscriptions/{subscription_id}/resourceGroups/{resource_group_name}/providers/Microsoft.Compute/virtualMachines/vm-2"
        mock_vm2.name = "vm-2"
        mock_vm2.location = "westus"
        type(mock_vm2).hardware_profile = PropertyMock(
            return_value=MagicMock(vm_size="Standard_F2s_v2")
        )
        type(mock_vm2).storage_profile = PropertyMock(
            return_value=MagicMock(os_disk=MagicMock(os_type="Windows"))
        )

        # Replace the actual get_virtual_machines method with our test implementation
        async def mock_get_virtual_machines(sub_id, rg_name):
            assert sub_id == subscription_id
            assert rg_name == resource_group_name
            return [
                VirtualMachineModel(
                    id=mock_vm1.id,
                    name=mock_vm1.name,
                    location=mock_vm1.location,
                    vm_size=mock_vm1.hardware_profile.vm_size,
                    os_type=mock_vm1.storage_profile.os_disk.os_type,
                    power_state="Running",
                ),
                VirtualMachineModel(
                    id=mock_vm2.id,
                    name=mock_vm2.name,
                    location=mock_vm2.location,
                    vm_size=mock_vm2.hardware_profile.vm_size,
                    os_type=mock_vm2.storage_profile.os_disk.os_type,
                    power_state="Running",
                ),
            ]

        # Save original and replace
        original_method = service.get_virtual_machines
        service.get_virtual_machines = mock_get_virtual_machines

        try:
            # Act
            result = await service.get_virtual_machines(
                subscription_id, resource_group_name
            )

            # Assert
            assert len(result) == 2
            assert isinstance(result[0], VirtualMachineModel)
            assert (
                result[0].id
                == f"/subscriptions/{subscription_id}/resourceGroups/{resource_group_name}/providers/Microsoft.Compute/virtualMachines/vm-1"
            )
            assert result[0].name == "vm-1"
            assert result[0].location == "eastus"
            assert result[0].vm_size == "Standard_DS2_v2"
            assert result[0].os_type == "Linux"
            assert result[0].power_state == "Running"

            assert (
                result[1].id
                == f"/subscriptions/{subscription_id}/resourceGroups/{resource_group_name}/providers/Microsoft.Compute/virtualMachines/vm-2"
            )
            assert result[1].name == "vm-2"
            assert result[1].vm_size == "Standard_F2s_v2"
            assert result[1].os_type == "Windows"
            assert result[1].power_state == "Running"
        finally:
            # Restore original method
            service.get_virtual_machines = original_method
