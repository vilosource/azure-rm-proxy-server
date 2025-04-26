"""Virtual machine functionality mixin for Azure Resource Service."""

import logging
import asyncio
from typing import List, Optional

from azure.core.exceptions import ResourceNotFoundError, ClientAuthenticationError

from ..azure_clients import AzureClientFactory
from ..models import (
    VirtualMachineModel,
    VirtualMachineDetail,
    VirtualMachineWithContext,
    VirtualMachineHostname,
    SubscriptionModel,
)
from .base_mixin import BaseAzureResourceMixin
from ...app.config import settings

logger = logging.getLogger(__name__)


class VirtualMachineMixin(BaseAzureResourceMixin):
    """Mixin for virtual machine-related operations."""

    async def get_virtual_machines(
        self,
        subscription_id: str,
        resource_group_name: str,
        refresh_cache: bool = False,
    ) -> List[VirtualMachineModel]:
        """
        Get all virtual machines for a resource group.

        Args:
            subscription_id: Azure subscription ID
            resource_group_name: Resource group name
            refresh_cache: Whether to refresh the cache

        Returns:
            List of virtual machine models
        """
        cache_key = self._get_cache_key(["vms", subscription_id, resource_group_name])
        self._log_debug(
            f"Attempting to get VMs for RG {resource_group_name} in subscription {subscription_id} with refresh_cache={refresh_cache}"
        )

        if not refresh_cache:
            cached_data = self.cache.get(cache_key)
            if cached_data:
                self._log_debug(
                    f"Cache hit for VMs in resource group {resource_group_name} in subscription {subscription_id}"
                )
                return cached_data

        self._log_info(
            f"Fetching VMs for resource group {resource_group_name} in subscription {subscription_id} from Azure"
        )
        try:
            compute_client = AzureClientFactory.create_compute_client(
                subscription_id, self.credential
            )

            async with self.limiter:
                self._log_debug(
                    f"Acquired concurrency limiter for VMs in RG {resource_group_name} in subscription {subscription_id}"
                )

                virtual_machines = []
                for vm in compute_client.virtual_machines.list(resource_group_name):
                    vm_dict = {
                        "id": vm.id,
                        "name": vm.name,
                        "location": vm.location,
                        "vm_size": (
                            vm.hardware_profile.vm_size
                            if vm.hardware_profile
                            else "Unknown"
                        ),
                        "os_type": (
                            vm.storage_profile.os_disk.os_type
                            if vm.storage_profile and vm.storage_profile.os_disk
                            else None
                        ),
                        "power_state": None,
                    }
                    virtual_machines.append(VirtualMachineModel.model_validate(vm_dict))

                self._log_debug(
                    f"Released concurrency limiter for VMs in RG {resource_group_name} in subscription {subscription_id}"
                )

            self._set_cache_with_ttl(cache_key, virtual_machines, settings.cache_ttl)
            self._log_info(
                f"Fetched {len(virtual_machines)} VMs for resource group {resource_group_name} in subscription {subscription_id}"
            )
            return virtual_machines

        except ResourceNotFoundError as e:
            self._log_warning(
                f"Resource group {resource_group_name} not found in subscription {subscription_id}: {e}"
            )
            raise
        except ClientAuthenticationError as e:
            self._log_error(f"Authentication error fetching VMs: {e}")
            raise
        except Exception as e:
            self._log_error(
                f"Error fetching VMs for resource group {resource_group_name} in subscription {subscription_id}: {e}"
            )
            raise

    def _create_vm_model_from_azure_vm(self, vm):
        """
        Create a VM model from an Azure VM object.

        Args:
            vm: Azure VM object

        Returns:
            VirtualMachineModel object
        """
        vm_dict = {
            "id": vm.id,
            "name": vm.name,
            "location": vm.location,
            "vm_size": (
                vm.hardware_profile.vm_size
                if hasattr(vm, "hardware_profile") and vm.hardware_profile
                else "Unknown"
            ),
            "os_type": (
                vm.storage_profile.os_disk.os_type
                if hasattr(vm, "storage_profile")
                and vm.storage_profile
                and hasattr(vm.storage_profile, "os_disk")
                and vm.storage_profile.os_disk
                else None
            ),
            "power_state": None,
        }
        return VirtualMachineModel.model_validate(vm_dict)

    async def get_vm_details(
        self,
        subscription_id: str,
        resource_group_name: str,
        vm_name: str,
        refresh_cache: bool = False,
    ) -> VirtualMachineDetail:
        """
        Get detailed information about a virtual machine.

        Args:
            subscription_id: Azure subscription ID
            resource_group_name: Resource group name
            vm_name: Virtual machine name
            refresh_cache: Whether to refresh the cache

        Returns:
            Virtual machine detail object
        """
        cache_key = self._get_cache_key(
            ["vm_details", subscription_id, resource_group_name, vm_name]
        )
        self._log_debug(
            f"Attempting to get VM details for {vm_name} with refresh_cache={refresh_cache}"
        )

        if not refresh_cache:
            cached_data = self.cache.get(cache_key)
            if cached_data:
                self._log_debug(f"Cache hit for VM details of {vm_name}")
                return cached_data

        self._log_info(
            f"Fetching VM details for {vm_name} in RG {resource_group_name} in subscription {subscription_id} from Azure"
        )

        try:
            async with self.limiter:
                self._log_debug(
                    f"Acquired concurrency limiter for VM details of {vm_name}"
                )

                compute_client = AzureClientFactory.create_compute_client(
                    subscription_id, self.credential
                )
                network_client = AzureClientFactory.create_network_client(
                    subscription_id, self.credential
                )

                vm = compute_client.virtual_machines.get(resource_group_name, vm_name)
                vm_model = self._create_vm_model_from_azure_vm(vm)
                self._log_debug(f"Fetched base VM data for {vm_name}")

                network_interfaces = await self._fetch_network_interfaces(
                    vm, network_client, vm_name
                )

                effective_nsg_rules, effective_routes, aad_groups = (
                    await asyncio.gather(
                        self._fetch_nsg_rules(
                            network_client, resource_group_name, network_interfaces
                        ),
                        self._fetch_routes(
                            network_client, resource_group_name, network_interfaces
                        ),
                        self._fetch_aad_groups(subscription_id, vm),
                    )
                )

                vm_detail = VirtualMachineDetail(
                    network_interfaces=network_interfaces,
                    effective_nsg_rules=effective_nsg_rules,
                    effective_routes=effective_routes,
                    aad_groups=aad_groups,
                    **vm_model.model_dump(),
                )

                self._set_cache_with_ttl(cache_key, vm_detail, settings.cache_ttl)
                self._log_info(
                    f"Successfully fetched and cached VM details for {vm_name}"
                )
                self._log_debug(
                    f"Released concurrency limiter for VM details of {vm_name}"
                )
                return vm_detail

        except ResourceNotFoundError as e:
            self._log_warning(
                f"VM {vm_name} not found in RG {resource_group_name} in subscription {subscription_id}: {e}"
            )
            raise
        except ClientAuthenticationError as e:
            self._log_error(f"Authentication error fetching VM details: {e}")
            raise
        except Exception as e:
            self._log_error(f"Error fetching VM details for {vm_name}: {e}")
            raise

    async def get_all_virtual_machines(
        self, refresh_cache: bool = False
    ) -> List[VirtualMachineWithContext]:
        """
        Get all virtual machines across all subscriptions and resource groups.

        Args:
            refresh_cache: Whether to refresh the cache

        Returns:
            List of virtual machines with subscription and resource group context
        """
        cache_key = self._get_cache_key(["all_vms"])
        self._log_debug(f"Attempting to get all VMs with refresh_cache={refresh_cache}")

        if not refresh_cache:
            cached_data = self.cache.get(cache_key)
            if cached_data:
                self._log_debug("Cache hit for all VMs")
                return cached_data

        self._log_info("Fetching all VMs across all subscriptions")
        try:
            subscriptions = await self.get_subscriptions(refresh_cache=refresh_cache)

            all_vms = []

            for sub in subscriptions:
                try:
                    resource_groups = await self.get_resource_groups(
                        sub.id, refresh_cache=refresh_cache
                    )

                    for rg in resource_groups:
                        try:
                            vms = await self.get_virtual_machines(
                                sub.id, rg.name, refresh_cache=refresh_cache
                            )
                            for vm in vms:
                                vm_dict = vm.model_dump()
                                vm_dict["subscription_id"] = sub.id
                                vm_dict["subscription_name"] = sub.name
                                vm_dict["resource_group_name"] = rg.name
                                all_vms.append(
                                    VirtualMachineWithContext.model_validate(vm_dict)
                                )
                        except Exception as e:
                            self._log_warning(
                                f"Error fetching VMs for resource group {rg.name} in subscription {sub.id}: {e}"
                            )
                            continue
                except Exception as e:
                    self._log_warning(
                        f"Error fetching resource groups for subscription {sub.id}: {e}"
                    )
                    continue

            self._set_cache_with_ttl(cache_key, all_vms, settings.cache_ttl)
            self._log_info(f"Fetched {len(all_vms)} VMs across all subscriptions")
            return all_vms
        except Exception as e:
            self._log_error(f"Error fetching all VMs: {e}")
            raise

    async def find_vm_by_name(
        self, vm_name: str, refresh_cache: bool = False
    ) -> VirtualMachineDetail:
        """
        Find a virtual machine by name across all subscriptions and resource groups.

        Args:
            vm_name: Virtual machine name
            refresh_cache: Whether to refresh the cache

        Returns:
            Virtual machine detail object

        Raises:
            ResourceNotFoundError: If VM is not found
        """
        cache_key = self._get_cache_key(["vm_by_name", vm_name])
        self._log_debug(
            f"Attempting to find VM {vm_name} with refresh_cache={refresh_cache}"
        )

        if not refresh_cache:
            cached_data = self.cache.get(cache_key)
            if cached_data:
                self._log_debug(f"Cache hit for VM {vm_name}")
                return cached_data

        self._log_info(f"Finding VM {vm_name} across all subscriptions")
        try:
            subscriptions = await self.get_subscriptions(refresh_cache=refresh_cache)

            for sub in subscriptions:
                try:
                    resource_groups = await self.get_resource_groups(
                        sub.id, refresh_cache=refresh_cache
                    )

                    for rg in resource_groups:
                        try:
                            vms = await self.get_virtual_machines(
                                sub.id, rg.name, refresh_cache=refresh_cache
                            )

                            for vm in vms:
                                if vm.name.lower() == vm_name.lower():
                                    vm_details = await self.get_vm_details(
                                        sub.id,
                                        rg.name,
                                        vm.name,
                                        refresh_cache=refresh_cache,
                                    )
                                    self._set_cache_with_ttl(
                                        cache_key, vm_details, settings.cache_ttl
                                    )
                                    return vm_details
                        except Exception as e:
                            self._log_warning(
                                f"Error fetching VMs for resource group {rg.name} in subscription {sub.id}: {e}"
                            )
                            continue
                except Exception as e:
                    self._log_warning(
                        f"Error fetching resource groups for subscription {sub.id}: {e}"
                    )
                    continue

            self._log_warning(
                f"VM {vm_name} not found in any subscription or resource group"
            )
            raise ResourceNotFoundError(f"VM {vm_name} not found")
        except ResourceNotFoundError:
            raise
        except Exception as e:
            self._log_error(f"Error finding VM {vm_name}: {e}")
            raise

    async def get_vm_hostnames(
        self, subscription_id: str = None, refresh_cache: bool = False
    ) -> List[VirtualMachineHostname]:
        """
        Get a list of VM names and their hostnames from tags.

        Args:
            subscription_id: Optional subscription ID to filter by. If None, gets VMs from all subscriptions.
            refresh_cache: Whether to refresh the cache

        Returns:
            List of VirtualMachineHostname objects
        """
        cache_key = self._get_cache_key(["vm_hostnames", subscription_id or "all"])
        self._log_debug(
            f"Attempting to get VM hostnames with refresh_cache={refresh_cache}"
        )

        if not refresh_cache:
            cached_data = self.cache.get(cache_key)
            if cached_data:
                self._log_debug("Cache hit for VM hostnames")
                return cached_data

        self._log_info(
            f"Fetching VM hostnames for subscription {'all' if subscription_id is None else subscription_id}"
        )

        try:
            if subscription_id:
                subscriptions = [await self._get_subscription_by_id(subscription_id)]
                self._log_info(f"Processing single subscription: {subscription_id}")
            else:
                subscriptions = await self.get_subscriptions(
                    refresh_cache=refresh_cache
                )
                self._log_info(f"Processing all {len(subscriptions)} subscriptions")

            vm_hostnames = []

            for sub in subscriptions:
                self._log_info(f"Processing subscription: {sub.id} ({sub.name})")

                try:
                    resource_groups = await self.get_resource_groups(
                        sub.id, refresh_cache=refresh_cache
                    )
                    self._log_info(
                        f"Found {len(resource_groups)} resource groups in subscription {sub.id}"
                    )

                    for rg in resource_groups:
                        try:
                            self._log_debug(
                                f"Processing resource group: {rg.name} in subscription {sub.id}"
                            )
                            compute_client = AzureClientFactory.create_compute_client(
                                sub.id, self.credential
                            )

                            async with self.limiter:
                                vms_in_rg = []
                                for vm in compute_client.virtual_machines.list(rg.name):
                                    hostname = None
                                    if hasattr(vm, "tags") and vm.tags:
                                        hostname = vm.tags.get("hostname")

                                    vm_hostname = VirtualMachineHostname(
                                        vm_name=vm.name, hostname=hostname
                                    )
                                    vms_in_rg.append(vm_hostname)
                                    vm_hostnames.append(vm_hostname)

                                self._log_debug(
                                    f"Found {len(vms_in_rg)} VMs in resource group {rg.name}"
                                )
                        except Exception as e:
                            self._log_warning(
                                f"Error fetching VMs for resource group {rg.name} in subscription {sub.id}: {str(e)}"
                            )
                            continue
                except Exception as e:
                    self._log_warning(
                        f"Error fetching resource groups for subscription {sub.id}: {str(e)}"
                    )
                    continue

            if not vm_hostnames and subscription_id is None:
                self._log_warning(
                    "No VM hostnames found across any subscriptions. This might indicate an issue with permissions or connectivity."
                )

            self._set_cache_with_ttl(cache_key, vm_hostnames, settings.cache_ttl)
            self._log_info(
                f"Fetched hostnames for {len(vm_hostnames)} VMs across {'all subscriptions' if subscription_id is None else 'subscription ' + subscription_id}"
            )
            return vm_hostnames
        except Exception as e:
            self._log_error(f"Error fetching VM hostnames: {str(e)}")
            raise

    async def _get_subscription_by_id(self, subscription_id: str) -> SubscriptionModel:
        """
        Get subscription by ID.

        Args:
            subscription_id: Subscription ID

        Returns:
            SubscriptionModel

        Raises:
            ResourceNotFoundError: If subscription is not found
        """
        subscriptions = await self.get_subscriptions()

        for sub in subscriptions:
            if sub.id == subscription_id:
                return sub

        raise ResourceNotFoundError(f"Subscription {subscription_id} not found")
