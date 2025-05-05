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
    VirtualMachineReport,  # Add the import here
)
from .base_mixin import BaseAzureResourceMixin, cached_azure_operation
from ...app.config import settings

logger = logging.getLogger(__name__)


class VirtualMachineMixin(BaseAzureResourceMixin):
    """Mixin for virtual machine-related operations."""

    @cached_azure_operation(model_class=VirtualMachineModel)
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
        # Get compute client with concurrency control
        compute_client = await self._get_client("compute", subscription_id)

        virtual_machines = []
        for vm in compute_client.virtual_machines.list(resource_group_name):
            vm_model = self._create_vm_model_from_azure_vm(vm)
            virtual_machines.append(vm_model)

        self._log_info(
            f"Fetched {len(virtual_machines)} VMs for resource group {resource_group_name} in subscription {subscription_id}"
        )
        return virtual_machines

    def _create_vm_model_from_azure_vm(self, vm):
        """
        Create a VM model from an Azure VM object.

        Args:
            vm: Azure VM object

        Returns:
            VirtualMachineModel object
        """
        # Use the helper method to convert Azure object to Pydantic model
        return self._convert_to_model(
            vm,
            VirtualMachineModel,
            vm_size=(
                vm.hardware_profile.vm_size
                if hasattr(vm, "hardware_profile") and vm.hardware_profile
                else "Unknown"
            ),
            os_type=(
                vm.storage_profile.os_disk.os_type
                if hasattr(vm, "storage_profile")
                and vm.storage_profile
                and hasattr(vm.storage_profile, "os_disk")
                and vm.storage_profile.os_disk
                else None
            ),
            power_state=None,
        )

    @cached_azure_operation(model_class=VirtualMachineDetail)
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
        # Get compute and network clients
        compute_client = await self._get_client("compute", subscription_id)
        network_client = await self._get_client("network", subscription_id)

        vm = compute_client.virtual_machines.get(resource_group_name, vm_name)
        vm_model = self._create_vm_model_from_azure_vm(vm)
        self._log_debug(f"Fetched base VM data for {vm_name}")

        network_interfaces = await self._fetch_network_interfaces(
            vm, network_client, vm_name
        )

        effective_nsg_rules, effective_routes, aad_groups = await asyncio.gather(
            self._fetch_nsg_rules(
                network_client, resource_group_name, network_interfaces
            ),
            self._fetch_routes(network_client, resource_group_name, network_interfaces),
            self._fetch_aad_groups(subscription_id, vm),
        )

        # Fetch hostnames for the subscription
        hostnames = await self.get_vm_hostnames(
            subscription_id, refresh_cache=refresh_cache
        )
        hostname_map = {vm.vm_name: vm.hostname for vm in hostnames}

        # Add hostname to the VM detail
        vm_detail = VirtualMachineDetail(
            network_interfaces=network_interfaces,
            effective_nsg_rules=effective_nsg_rules,
            effective_routes=effective_routes,
            aad_groups=aad_groups,
            hostname=hostname_map.get(vm_name),  # Add hostname here
            **vm_model.model_dump(),
        )

        self._log_info(f"Successfully fetched VM details for {vm_name}")
        return vm_detail

    @cached_azure_operation(model_class=VirtualMachineWithContext)
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
        # Get all subscriptions
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

        self._log_info(f"Fetched {len(all_vms)} VMs across all subscriptions")
        return all_vms

    @cached_azure_operation(model_class=VirtualMachineDetail)
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
        # Get all subscriptions
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

    @cached_azure_operation(model_class=VirtualMachineHostname)
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
        # Determine which subscriptions to process
        if subscription_id:
            subscriptions = [await self._get_subscription_by_id(subscription_id)]
            self._log_info(f"Processing single subscription: {subscription_id}")
        else:
            subscriptions = await self.get_subscriptions(refresh_cache=refresh_cache)
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
                        compute_client = await self._get_client("compute", sub.id)

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

        self._log_info(
            f"Fetched hostnames for {len(vm_hostnames)} VMs across {'all subscriptions' if subscription_id is None else 'subscription ' + subscription_id}"
        )
        return vm_hostnames

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
            # Handle if sub is a dictionary (from cache) instead of a SubscriptionModel
            if isinstance(sub, dict):
                if sub.get("id") == subscription_id:
                    return SubscriptionModel.model_validate(sub)
            else:
                if sub.id == subscription_id:
                    return sub

        raise ResourceNotFoundError(f"Subscription {subscription_id} not found")

    @cached_azure_operation(model_class=VirtualMachineReport)
    async def get_vm_report(
        self,
        refresh_cache: bool = False,
    ) -> List["VirtualMachineReport"]:
        """
        Generate a report of all virtual machines with detailed information.

        Args:
            refresh_cache: Whether to refresh the cache

        Returns:
            List of virtual machine report objects with detailed information
        """
        # Import here to avoid circular import
        from ..models import VirtualMachineReport

        # Get all VMs with basic context
        all_vms = await self.get_all_virtual_machines(refresh_cache=refresh_cache)
        self._log_info(f"Found {len(all_vms)} VMs across all subscriptions for report")

        report_entries = []

        # Get hostnames to reuse across all VMs
        self._log_debug("Fetching VM hostnames for all subscriptions")
        all_hostnames = await self.get_vm_hostnames(refresh_cache=refresh_cache)
        hostname_map = {vm.vm_name: vm.hostname for vm in all_hostnames}

        for vm in all_vms:
            try:
                # Get detailed VM information
                vm_detail = await self.get_vm_details(
                    vm.subscription_id,
                    vm.resource_group_name,
                    vm.name,
                    refresh_cache=refresh_cache,
                )

                # Get VM properties for report
                private_ips = []
                public_ips = []

                # Extract IP addresses from network interfaces
                for nic in vm_detail.network_interfaces:
                    private_ips.extend(nic.private_ip_addresses)
                    public_ips.extend(nic.public_ip_addresses)

                # Get VM OS disk size and tags
                os_disk_size = None
                environment = None
                purpose = None

                try:
                    compute_client = await self._get_client(
                        "compute", vm.subscription_id
                    )

                    azure_vm = compute_client.virtual_machines.get(
                        vm.resource_group_name, vm.name
                    )

                    # Get OS disk size
                    if (
                        hasattr(azure_vm, "storage_profile")
                        and azure_vm.storage_profile
                        and hasattr(azure_vm.storage_profile, "os_disk")
                        and azure_vm.storage_profile.os_disk
                        and hasattr(azure_vm.storage_profile.os_disk, "disk_size_gb")
                    ):
                        os_disk_size = azure_vm.storage_profile.os_disk.disk_size_gb

                    # Get tags
                    if hasattr(azure_vm, "tags") and azure_vm.tags:
                        environment = azure_vm.tags.get("environment")
                        purpose = azure_vm.tags.get("purpose")
                except Exception as e:
                    self._log_warning(
                        f"Error fetching OS disk size and tags for VM {vm.name}: {e}"
                    )

                # Create report entry
                report_entry = VirtualMachineReport(
                    hostname=hostname_map.get(vm.name),
                    os=vm_detail.os_type,
                    environment=environment,
                    purpose=purpose,
                    ip_addresses=private_ips,
                    public_ip_addresses=public_ips,
                    vm_name=vm.name,
                    vm_size=vm.vm_size,
                    os_disk_size_gb=os_disk_size,
                    resource_group=vm.resource_group_name,
                    location=vm.location,
                    subscription_id=vm.subscription_id,
                    subscription_name=vm.subscription_name,
                )
                report_entries.append(report_entry)

            except Exception as e:
                self._log_warning(f"Error processing VM {vm.name} for report: {e}")
                continue

        self._log_info(f"Generated report for {len(report_entries)} VMs")
        return report_entries

    async def _fetch_network_interfaces(self, vm, network_client, vm_name):
        """
        Fetch network interfaces for a VM.

        Args:
            vm: Azure VM object
            network_client: Azure Network Management client
            vm_name: Name of the VM

        Returns:
            List of NetworkInterfaceModel objects
        """
        from ..models import NetworkInterfaceModel

        network_interfaces = []
        if (
            not hasattr(vm, "network_profile")
            or not vm.network_profile
            or not vm.network_profile.network_interfaces
        ):
            self._log_warning(f"VM {vm_name} has no network interfaces")
            return network_interfaces

        for nic_ref in vm.network_profile.network_interfaces:
            try:
                # Extract resource group and NIC name from the ID
                nic_id = nic_ref.id
                nic_name = nic_id.split("/")[-1]
                nic_resource_group = self._extract_resource_group_from_id(nic_id)

                if not nic_resource_group:
                    self._log_warning(
                        f"Could not extract resource group from NIC ID: {nic_id}"
                    )
                    continue

                self._log_debug(
                    f"Fetching details for NIC {nic_name} in resource group {nic_resource_group}"
                )

                nic = network_client.network_interfaces.get(
                    nic_resource_group, nic_name
                )

                private_ips = []
                public_ips = []

                if nic.ip_configurations:
                    for ip_config in nic.ip_configurations:
                        # Get private IP
                        if ip_config.private_ip_address:
                            private_ips.append(ip_config.private_ip_address)

                        # Get public IP if available
                        if ip_config.public_ip_address:
                            public_ip_id = ip_config.public_ip_address.id
                            public_ip_name = public_ip_id.split("/")[-1]
                            public_ip_rg = self._extract_resource_group_from_id(
                                public_ip_id
                            )

                            try:
                                public_ip = network_client.public_ip_addresses.get(
                                    public_ip_rg, public_ip_name
                                )
                                if public_ip.ip_address:
                                    public_ips.append(public_ip.ip_address)
                            except Exception as e:
                                self._log_warning(
                                    f"Error fetching public IP {public_ip_name}: {e}"
                                )

                nic_model = NetworkInterfaceModel(
                    id=nic.id,
                    name=nic.name,
                    private_ip_addresses=private_ips,
                    public_ip_addresses=public_ips,
                )
                network_interfaces.append(nic_model)

            except Exception as e:
                self._log_warning(
                    f"Error processing network interface for VM {vm_name}: {e}"
                )

        return network_interfaces

    async def _fetch_nsg_rules(
        self, network_client, resource_group_name, network_interfaces
    ):
        """
        Fetch effective NSG rules for network interfaces.

        Args:
            network_client: Azure Network Management client
            resource_group_name: Resource group name
            network_interfaces: List of NetworkInterfaceModel objects

        Returns:
            List of NsgRuleModel objects
        """
        from ..models import NsgRuleModel

        nsg_rules = []

        # For each NIC, get effective security rules
        for nic in network_interfaces:
            try:
                nic_name = nic.name
                nic_resource_group = self._extract_resource_group_from_id(nic.id)

                self._log_debug(f"Fetching NSG rules for NIC {nic_name}")

                # Azure SDK expects a specific format for these calls
                poller = network_client.network_interfaces.begin_get_effective_network_security_group(
                    nic_resource_group, nic_name
                )
                result = poller.result()

                if result and hasattr(result, "effective_security_rules"):
                    for rule in result.effective_security_rules:
                        rule_name = rule.name if hasattr(rule, "name") else "Unknown"

                        # Extract protocol
                        protocol = rule.protocol if hasattr(rule, "protocol") else "*"

                        # Extract direction
                        direction = (
                            rule.direction if hasattr(rule, "direction") else "Unknown"
                        )

                        # Extract port range
                        port_range = "*"
                        if (
                            hasattr(rule, "destination_port_range")
                            and rule.destination_port_range
                        ):
                            port_range = rule.destination_port_range

                        # Extract access
                        access = rule.access if hasattr(rule, "access") else "Unknown"

                        nsg_rule = NsgRuleModel(
                            name=rule_name,
                            protocol=protocol,
                            direction=direction,
                            port_range=port_range,
                            access=access,
                        )
                        nsg_rules.append(nsg_rule)

            except Exception as e:
                self._log_warning(f"Error fetching NSG rules for NIC {nic.name}: {e}")

        return nsg_rules

    async def _fetch_routes(
        self, network_client, resource_group_name, network_interfaces
    ):
        """
        Fetch effective routes for network interfaces.

        Args:
            network_client: Azure Network Management client
            resource_group_name: Resource group name
            network_interfaces: List of NetworkInterfaceModel objects

        Returns:
            List of RouteModel objects
        """
        from ..models import RouteModel

        all_routes = []

        # For each NIC, get effective routes
        for nic in network_interfaces:
            try:
                nic_name = nic.name
                nic_resource_group = self._extract_resource_group_from_id(nic.id)

                self._log_debug(f"Fetching routes for NIC {nic_name}")

                # Azure SDK expects a specific format for these calls
                poller = (
                    network_client.network_interfaces.begin_get_effective_route_table(
                        nic_resource_group, nic_name
                    )
                )
                result = poller.result()

                if result and hasattr(result, "value"):
                    for route in result.value:
                        # Handle address_prefix which might be a list or a string
                        address_prefix = route.address_prefix
                        if isinstance(address_prefix, list):
                            address_prefix = address_prefix[0] if address_prefix else ""

                        # Handle next_hop_ip_address which might be a list or a string
                        next_hop_ip = None
                        if hasattr(route, "next_hop_ip_address"):
                            next_hop_ip = route.next_hop_ip_address
                            if isinstance(next_hop_ip, list):
                                next_hop_ip = next_hop_ip[0] if next_hop_ip else None

                        route_model = RouteModel(
                            address_prefix=address_prefix,
                            next_hop_type=route.next_hop_type,
                            next_hop_ip=next_hop_ip,
                            route_origin=(
                                route.source if hasattr(route, "source") else "Unknown"
                            ),
                        )
                        all_routes.append(route_model)

            except Exception as e:
                self._log_warning(f"Error fetching routes for NIC {nic.name}: {e}")

        return all_routes

    async def _fetch_aad_groups(self, subscription_id, vm):
        """
        Fetch AAD groups for a VM.

        Args:
            subscription_id: Azure subscription ID
            vm: Azure VM object

        Returns:
            List of AADGroupModel objects
        """
        from ..models import AADGroupModel

        aad_groups = []

        try:
            # Get VM identity if available
            if not hasattr(vm, "identity") or not vm.identity:
                return aad_groups

            # Only handle system assigned or user assigned identities
            if not vm.identity.principal_id and (
                not hasattr(vm.identity, "user_assigned_identities")
                or not vm.identity.user_assigned_identities
            ):
                return aad_groups

            # Get authorization client
            auth_client = await self._get_client("authorization", subscription_id)

            # If VM has a system assigned identity
            if vm.identity.principal_id:
                self._log_debug(
                    f"Fetching AAD groups for system assigned identity {vm.identity.principal_id}"
                )

                # List role assignments for the VM's system assigned identity
                for assignment in auth_client.role_assignments.list_for_scope(vm.id):
                    if (
                        hasattr(assignment, "principal_id")
                        and assignment.principal_id == vm.identity.principal_id
                    ):
                        aad_group = AADGroupModel(
                            id=assignment.id, display_name=assignment.name
                        )
                        aad_groups.append(aad_group)

            # If VM has user assigned identities
            if (
                hasattr(vm.identity, "user_assigned_identities")
                and vm.identity.user_assigned_identities
            ):
                for (
                    identity_id,
                    identity,
                ) in vm.identity.user_assigned_identities.items():
                    self._log_debug(
                        f"Fetching AAD groups for user assigned identity {identity_id}"
                    )

                    # List role assignments for each user assigned identity
                    try:
                        for assignment in auth_client.role_assignments.list_for_scope(
                            identity_id
                        ):
                            aad_group = AADGroupModel(
                                id=assignment.id, display_name=assignment.name
                            )
                            aad_groups.append(aad_group)
                    except Exception as e:
                        self._log_warning(
                            f"Error fetching AAD groups for identity {identity_id}: {e}"
                        )

        except Exception as e:
            self._log_warning(f"Error fetching AAD groups: {e}")

        return aad_groups
