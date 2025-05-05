#!/usr/bin/env python3
"""
Mock Azure Service

This module provides a mock implementation of the Azure Resource Service
that uses JSON fixtures instead of making actual API calls to Azure.
It's designed to be used in tests and development environments.
"""

import glob
import json
import logging
import os
from typing import Dict, List, Any, Optional, Union
import re
from datetime import datetime

from ..core.models import (
    SubscriptionModel,
    ResourceGroupModel,
    VirtualMachineModel,
    VirtualMachineDetail,
)
from ..core.caching import CacheStrategy, InMemoryCache

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Common network address literals used in mock data
ADDR_LOCAL_SUBNET = "10.0.0.0/24"
ADDR_DEFAULT_ROUTE = "0.0.0.0/0"
ADDR_ON_PREM_NETWORK = "10.0.0.0/16"


class MockAzureResourceService:
    """
    A mock implementation of the Azure Resource Service.

    This class mimics the behavior of the real Azure service but uses
    JSON fixtures instead of making actual API calls.
    """

    def __init__(
        self,
        credential=None,  # Not used, but kept for API compatibility
        cache: CacheStrategy = None,
        limiter=None,  # Not used, but kept for API compatibility
        fixtures_dir: str = "./test_harnesses",
    ):
        """
        Initialize the mock service with fixtures from the specified directory.

        Args:
            credential: Azure credential (not used, but included for API compatibility)
            cache: Cache strategy (optional)
            limiter: Concurrency limiter (not used, but included for API compatibility)
            fixtures_dir: Directory containing JSON fixture files
        """
        self.fixtures_dir = fixtures_dir
        self.cache = cache or InMemoryCache()
        self._load_fixtures()
        logger.info(
            f"MockAzureResourceService initialized with fixtures from {fixtures_dir}"
        )

    def _load_fixtures(self):
        """Load all JSON fixtures from the fixtures directory."""
        self.fixtures = {}

        # Ensure fixtures directory exists
        if not os.path.exists(self.fixtures_dir):
            logger.warning(f"Fixtures directory not found: {self.fixtures_dir}")
            return

        # Load all JSON files
        fixture_count = 0
        for file_path in glob.glob(os.path.join(self.fixtures_dir, "*.json")):
            try:
                with open(file_path, "r") as f:
                    fixture_name = os.path.basename(file_path)
                    self.fixtures[fixture_name] = json.load(f)
                    fixture_count += 1
                    logger.debug(f"Loaded fixture: {fixture_name}")
            except Exception as e:
                logger.error(f"Failed to load fixture {file_path}: {e}")

        logger.info(f"Loaded {fixture_count} fixtures from {self.fixtures_dir}")

    def _find_latest_fixture(self, pattern: str) -> Optional[Any]:
        """
        Find the most recent fixture file that matches the given pattern.

        Args:
            pattern: A string pattern to match against fixture filenames

        Returns:
            The fixture data if found, None otherwise
        """
        matching_fixtures = []

        for name, data in self.fixtures.items():
            if pattern in name:
                matching_fixtures.append((name, data))

        if not matching_fixtures:
            return None

        # Extract timestamps and find the latest
        latest_fixture = None
        latest_timestamp = None

        for name, data in matching_fixtures:
            # Extract timestamp from filename (format: YYYYMMDDHHMMSS)
            match = re.search(r"_(\d{14})\.json$", name)
            if match:
                timestamp_str = match.group(1)
                try:
                    timestamp = datetime.strptime(timestamp_str, "%Y%m%d%H%M%S")
                    if latest_timestamp is None or timestamp > latest_timestamp:
                        latest_timestamp = timestamp
                        latest_fixture = data
                except ValueError:
                    # If timestamp parsing fails, still consider the fixture
                    if latest_fixture is None:
                        latest_fixture = data
            else:
                # If no timestamp found, still consider the fixture
                if latest_fixture is None:
                    latest_fixture = data

        return latest_fixture

    def _parse_resource_group_string(self, rg_string: str) -> dict:
        """
        Parse a resource group string representation into a dictionary.

        Input format example:
        "id='/subscriptions/123/resourceGroups/my-rg' name='my-rg' location='westus' tags={}"

        Args:
            rg_string: String representation of a resource group

        Returns:
            Dictionary with resource group properties
        """
        if not isinstance(rg_string, str):
            return rg_string

        # Extract values using regular expressions
        id_match = re.search(r"id='([^']*)'", rg_string)
        name_match = re.search(r"name='([^']*)'", rg_string)
        location_match = re.search(r"location='([^']*)'", rg_string)
        tags_match = re.search(r"tags=(.*?)($|'| )", rg_string)

        # Create dictionary with extracted values
        rg_dict = {
            "id": id_match.group(1) if id_match else None,
            "name": name_match.group(1) if name_match else None,
            "location": location_match.group(1) if location_match else None,
        }

        # Parse tags if available
        if tags_match:
            tags_str = tags_match.group(1)
            if tags_str == "None":
                rg_dict["tags"] = None
            elif tags_str == "{}":
                rg_dict["tags"] = {}
            else:
                # Try to parse as JSON
                try:
                    rg_dict["tags"] = json.loads(tags_str.replace("'", '"'))
                except json.JSONDecodeError:
                    rg_dict["tags"] = {}

        return rg_dict

    def _parse_virtual_machine_string(self, vm_string: str) -> dict:
        """
        Parse a virtual machine string representation into a dictionary.

        Input format example:
        "id='/subscriptions/123/resourceGroups/my-rg/providers/Microsoft.Compute/virtualMachines/my-vm'
         name='my-vm' location='westus' vm_size='Standard_D2s_v4' os_type='Linux' power_state=None"

        Args:
            vm_string: String representation of a virtual machine

        Returns:
            Dictionary with virtual machine properties
        """
        if not isinstance(vm_string, str):
            return vm_string

        # Extract values using regular expressions
        id_match = re.search(r"id='([^']*)'", vm_string)
        name_match = re.search(r"name='([^']*)'", vm_string)
        location_match = re.search(r"location='([^']*)'", vm_string)
        vm_size_match = re.search(r"vm_size='([^']*)'", vm_string)
        os_type_match = re.search(r"os_type='([^']*)'", vm_string)
        power_state_match = re.search(r"power_state=([^ |$]*)", vm_string)

        # Create dictionary with extracted values
        vm_dict = {
            "id": id_match.group(1) if id_match else None,
            "name": name_match.group(1) if name_match else None,
            "location": location_match.group(1) if location_match else None,
            "vm_size": vm_size_match.group(1) if vm_size_match else "Standard_D2s_v4",
        }

        # Add optional fields
        if os_type_match:
            vm_dict["os_type"] = os_type_match.group(1)

        if power_state_match:
            power_state = power_state_match.group(1)
            if power_state == "None":
                vm_dict["power_state"] = None
            else:
                vm_dict["power_state"] = power_state

        return vm_dict

    async def get_subscriptions(
        self, refresh_cache: bool = False
    ) -> List[SubscriptionModel]:
        """
        Get all available subscriptions.

        Args:
            refresh_cache: Whether to bypass cache and fetch fresh data
        """
        cache_key = "subscriptions"

        if not refresh_cache:
            cached_data = self.cache.get(cache_key)
            if cached_data:
                logger.debug("Cache hit for subscriptions")
                return cached_data

        logger.info("Fetching mock subscriptions")
        fixture = self._find_latest_fixture("subscriptions_")

        if fixture:
            # Convert to SubscriptionModel objects
            subscriptions = []
            for sub_data in fixture:
                if isinstance(sub_data, dict):
                    # Ensure required fields exist
                    if not all(k in sub_data for k in ["id", "name", "state"]):
                        # Add missing fields with default values
                        sub_data = {
                            "id": sub_data.get("id", "unknown-id"),
                            "name": sub_data.get("name", "Unknown Subscription"),
                            "state": sub_data.get("state", "Enabled"),
                            **sub_data,
                        }
                    subscriptions.append(SubscriptionModel.parse_obj(sub_data))

            self.cache.set(cache_key, subscriptions)
            return subscriptions

        return []

    async def get_resource_groups(
        self, subscription_id: str, refresh_cache: bool = False
    ) -> List[ResourceGroupModel]:
        """
        Get all resource groups in the specified subscription.

        Args:
            subscription_id: Azure subscription ID
            refresh_cache: Whether to bypass cache and fetch fresh data
        """
        cache_key = f"resource_groups:{subscription_id}"

        if not refresh_cache:
            cached_data = self.cache.get(cache_key)
            if cached_data:
                logger.debug(
                    f"Cache hit for resource groups in subscription {subscription_id}"
                )
                return cached_data

        logger.info(f"Fetching mock resource groups for subscription {subscription_id}")
        fixture = self._find_latest_fixture(f"resource_groups_{subscription_id}")

        if fixture:
            # Convert to ResourceGroupModel objects
            resource_groups = []
            for rg_data in fixture:
                # Parse the string representation if needed
                if isinstance(rg_data, str):
                    rg_data = self._parse_resource_group_string(rg_data)

                if isinstance(rg_data, dict):
                    # Ensure required fields exist
                    if not all(k in rg_data for k in ["id", "name", "location"]):
                        # Add missing fields with default values
                        rg_data = {
                            "id": rg_data.get(
                                "id",
                                f"/subscriptions/{subscription_id}/resourceGroups/{rg_data.get('name', 'unknown')}",
                            ),
                            "name": rg_data.get("name", "Unknown Resource Group"),
                            "location": rg_data.get("location", "westus"),
                            "tags": rg_data.get("tags", {}),
                            **rg_data,
                        }
                    resource_groups.append(ResourceGroupModel.parse_obj(rg_data))

            self.cache.set(cache_key, resource_groups)
            return resource_groups

        return []

    async def get_virtual_machines(
        self,
        subscription_id: str,
        resource_group_name: str,
        refresh_cache: bool = False,
    ) -> List[VirtualMachineModel]:
        """
        Get all virtual machines in the specified resource group.

        Args:
            subscription_id: Azure subscription ID
            resource_group_name: Resource group name
            refresh_cache: Whether to bypass cache and fetch fresh data
        """
        cache_key = f"vms:{subscription_id}:{resource_group_name}"

        if not refresh_cache:
            cached_data = self.cache.get(cache_key)
            if cached_data:
                logger.debug(
                    f"Cache hit for VMs in resource group {resource_group_name}"
                )
                return cached_data

        logger.info(
            f"Fetching mock VMs for resource group {resource_group_name} in subscription {subscription_id}"
        )
        fixture = self._find_latest_fixture(
            f"vms_{subscription_id}_{resource_group_name}"
        )

        if fixture:
            # Convert to VirtualMachineModel objects
            virtual_machines = []
            for vm_data in fixture:
                # Parse the string representation if needed
                if isinstance(vm_data, str):
                    vm_data = self._parse_virtual_machine_string(vm_data)

                if isinstance(vm_data, dict):
                    # Ensure required fields exist
                    if not all(
                        k in vm_data for k in ["id", "name", "location", "vm_size"]
                    ):
                        # Add missing fields with default values
                        vm_data = {
                            "id": vm_data.get(
                                "id",
                                f"/subscriptions/{subscription_id}/resourceGroups/{resource_group_name}/providers/Microsoft.Compute/virtualMachines/{vm_data.get('name', 'unknown')}",
                            ),
                            "name": vm_data.get("name", "Unknown VM"),
                            "location": vm_data.get("location", "westus"),
                            "vm_size": vm_data.get("vm_size", "Standard_DS1_v2"),
                            "os_type": vm_data.get("os_type", "Linux"),
                            "power_state": vm_data.get("power_state", "running"),
                            **vm_data,
                        }
                    virtual_machines.append(VirtualMachineModel.parse_obj(vm_data))

            self.cache.set(cache_key, virtual_machines)
            return virtual_machines

        return []

    async def get_vm_details(
        self,
        subscription_id: str,
        resource_group_name: str,
        vm_name: str,
        refresh_cache: bool = False,
    ) -> Dict:
        """
        Get details for a specific virtual machine.

        Args:
            subscription_id: Azure subscription ID
            resource_group_name: Resource group name
            vm_name: Virtual machine name
            refresh_cache: Whether to bypass cache and fetch fresh data
        """
        cache_key = f"vm_details:{subscription_id}:{resource_group_name}:{vm_name}"

        if not refresh_cache:
            cached_data = self.cache.get(cache_key)
            if cached_data:
                logger.debug(f"Cache hit for VM details of {vm_name}")
                return cached_data

        logger.info(
            f"Fetching mock VM details for {vm_name} in resource group {resource_group_name}"
        )

        # First, try to find a specific VM details fixture
        fixture = self._find_latest_fixture(
            f"vm_details_{subscription_id}_{resource_group_name}_{vm_name}"
        )

        if fixture:
            self.cache.set(cache_key, fixture)
            return fixture

        # If not found, create a basic VM details response
        vm_details = {
            "id": f"/subscriptions/{subscription_id}/resourceGroups/{resource_group_name}/providers/Microsoft.Compute/virtualMachines/{vm_name}",
            "name": vm_name,
            "location": "swedencentral",
            "vm_size": "Standard_D2s_v3",
            "os_type": "Linux",
            "os_disk": {
                "name": f"{vm_name}-osdisk",
                "disk_size_gb": 128,
                "managed_disk": {
                    "id": f"/subscriptions/{subscription_id}/resourceGroups/{resource_group_name}/providers/Microsoft.Compute/disks/{vm_name}-osdisk"
                },
            },
            "network_interfaces": [
                {
                    "id": f"/subscriptions/{subscription_id}/resourceGroups/{resource_group_name}/providers/Microsoft.Network/networkInterfaces/{vm_name}-nic",
                    "name": f"{vm_name}-nic",
                    "primary": True,
                    "ip_configurations": [
                        {
                            "name": "ipconfig1",
                            "private_ip_address": "10.1.0.4",
                            "private_ip_allocation_method": "Dynamic",
                            "public_ip_address": None,
                            "subnet": {
                                "id": f"/subscriptions/{subscription_id}/resourceGroups/{resource_group_name}/providers/Microsoft.Network/virtualNetworks/vnet-{resource_group_name}/subnets/default"
                            },
                        }
                    ],
                }
            ],
            "effective_nsg_rules": [
                {
                    "name": "AllowVnetInBound",
                    "priority": 65000,
                    "direction": "Inbound",
                    "access": "Allow",
                    "protocol": "*",
                    "source_address_prefix": "VirtualNetwork",
                    "source_port_range": "*",
                    "destination_address_prefix": "VirtualNetwork",
                    "destination_port_range": "*",
                },
                {
                    "name": "AllowAzureLoadBalancerInBound",
                    "priority": 65001,
                    "direction": "Inbound",
                    "access": "Allow",
                    "protocol": "*",
                    "source_address_prefix": "AzureLoadBalancer",
                    "source_port_range": "*",
                    "destination_address_prefix": "*",
                    "destination_port_range": "*",
                },
                {
                    "name": "DenyAllInBound",
                    "priority": 65500,
                    "direction": "Inbound",
                    "access": "Deny",
                    "protocol": "*",
                    "source_address_prefix": "*",
                    "source_port_range": "*",
                    "destination_address_prefix": "*",
                    "destination_port_range": "*",
                },
            ],
            "hostname": f"{vm_name}.internal.cloudapp.net",
            "effective_routes": [
                {
                    "address_prefix": ADDR_LOCAL_SUBNET,
                    "next_hop_type": "VnetLocal",
                    "next_hop_ip_address": None,
                    "source": "Default",
                },
                {
                    "address_prefix": ADDR_DEFAULT_ROUTE,
                    "next_hop_type": "Internet",
                    "next_hop_ip_address": None,
                    "source": "Default",
                },
            ],
        }

        self.cache.set(cache_key, vm_details)
        return vm_details

    async def get_vm_hostnames(self, refresh_cache: bool = False) -> List[Dict]:
        """
        Get hostnames for all virtual machines.

        Args:
            refresh_cache: Whether to bypass cache and fetch fresh data
        """
        cache_key = "vm_hostnames"

        if not refresh_cache:
            cached_data = self.cache.get(cache_key)
            if cached_data:
                logger.debug("Cache hit for VM hostnames")
                return cached_data

        logger.info("Fetching mock VM hostnames")

        # Try to find a VM hostnames fixture
        fixture = self._find_latest_fixture("vm_hostnames")

        if fixture:
            self.cache.set(cache_key, fixture)
            return fixture

        # Get the first subscription to use for the sample data
        subscriptions = await self.get_subscriptions()
        if not subscriptions:
            return []

        sub = subscriptions[0]

        # Return simple mock hostname data instead of iterating through all RGs and VMs
        hostnames = [
            {
                "vm_name": "vm-abad-awms-demo-fi-1",
                "hostname": "vm-abad-awms-demo-fi-1.internal.cloudapp.net",
                "subscription_id": sub.id,
                "subscription_name": sub.name,
                "resource_group_name": "rg-abad-services-prod-swedencentral-01",
            },
            {
                "vm_name": "vm-abad-lms-1",
                "hostname": "vm-abad-lms-1.internal.cloudapp.net",
                "subscription_id": sub.id,
                "subscription_name": sub.name,
                "resource_group_name": "rg-abad-services-prod-swedencentral-01",
            },
            {
                "vm_name": "vm-abad-proxy-1",
                "hostname": "vm-abad-proxy-1.internal.cloudapp.net",
                "subscription_id": sub.id,
                "subscription_name": sub.name,
                "resource_group_name": "rg-abad-services-prod-swedencentral-01",
            },
            {
                "vm_name": "vm-abad-tms-demo-fi-1",
                "hostname": "vm-abad-tms-demo-fi-1.internal.cloudapp.net",
                "subscription_id": sub.id,
                "subscription_name": sub.name,
                "resource_group_name": "rg-abad-services-prod-swedencentral-01",
            },
        ]

        self.cache.set(cache_key, hostnames)
        return hostnames

    async def get_route_tables(
        self, subscription_id: str, refresh_cache: bool = False
    ) -> List[Dict]:
        """
        Get all route tables in the specified subscription.

        Args:
            subscription_id: Azure subscription ID
            refresh_cache: Whether to bypass cache and fetch fresh data
        """
        cache_key = f"route_tables:{subscription_id}"

        if not refresh_cache:
            cached_data = self.cache.get(cache_key)
            if cached_data:
                logger.debug(
                    f"Cache hit for route tables in subscription {subscription_id}"
                )
                return cached_data

        logger.info(f"Fetching mock route tables for subscription {subscription_id}")
        fixture = self._find_latest_fixture(f"routetables_{subscription_id}")

        if fixture:
            # Return route tables list from fixture
            self.cache.set(cache_key, fixture)
            return fixture

        # If no fixture found, create some sample route tables
        route_tables = [
            {
                "id": f"/subscriptions/{subscription_id}/resourceGroups/rg-sample-01/providers/Microsoft.Network/routeTables/rt-sample-01",
                "name": "rt-sample-01",
                "location": "westus",
                "resource_group": "rg-sample-01",
                "route_count": 2,
                "subnet_count": 1,
            }
        ]

        self.cache.set(cache_key, route_tables)
        return route_tables

    async def get_route_table_details(
        self,
        subscription_id: str,
        resource_group_name: str,
        route_table_name: str,
        refresh_cache: bool = False,
    ) -> Dict:
        """
        Get details for a specific route table.

        Args:
            subscription_id: Azure subscription ID
            resource_group_name: Resource group name
            route_table_name: Route table name
            refresh_cache: Whether to bypass cache and fetch fresh data
        """
        cache_key = f"route_table_details:{subscription_id}:{resource_group_name}:{route_table_name}"

        if not refresh_cache:
            cached_data = self.cache.get(cache_key)
            if cached_data:
                logger.debug(f"Cache hit for route table details of {route_table_name}")
                return cached_data

        logger.info(
            f"Fetching mock route table details for {route_table_name} in resource group {resource_group_name}"
        )
        fixture = self._find_latest_fixture(
            f"routetable_details_{subscription_id}_{resource_group_name}_{route_table_name}"
        )

        if fixture:
            self.cache.set(cache_key, fixture)
            return fixture

        # If no fixture found, create a sample route table details response
        route_table_details = {
            "id": f"/subscriptions/{subscription_id}/resourceGroups/{resource_group_name}/providers/Microsoft.Network/routeTables/{route_table_name}",
            "name": route_table_name,
            "location": "westus",
            "resource_group": resource_group_name,
            "routes": [
                {
                    "name": "default-to-internet",
                    "address_prefix": ADDR_DEFAULT_ROUTE,
                    "next_hop_type": "Internet",
                    "next_hop_ip_address": None,
                },
                {
                    "name": "to-on-prem",
                    "address_prefix": ADDR_ON_PREM_NETWORK,
                    "next_hop_type": "VirtualNetworkGateway",
                    "next_hop_ip_address": None,
                },
            ],
            "subnets": [
                {
                    "id": f"/subscriptions/{subscription_id}/resourceGroups/{resource_group_name}/providers/Microsoft.Network/virtualNetworks/vnet-{resource_group_name}/subnets/default",
                    "name": "default",
                    "address_prefixes": [ADDR_LOCAL_SUBNET],
                }
            ],
        }

        self.cache.set(cache_key, route_table_details)
        return route_table_details

    async def get_vm_effective_routes(
        self,
        subscription_id: str,
        resource_group_name: str,
        vm_name: str,
        refresh_cache: bool = False,
    ) -> List[Dict]:
        """
        Get effective routes for a specific virtual machine.

        Args:
            subscription_id: Azure subscription ID
            resource_group_name: Resource group name
            vm_name: Virtual machine name
            refresh_cache: Whether to bypass cache and fetch fresh data
        """
        # First try to get VM details which should contain effective routes
        vm_details = await self.get_vm_details(
            subscription_id, resource_group_name, vm_name, refresh_cache
        )

        if vm_details and "effective_routes" in vm_details:
            return vm_details["effective_routes"]

        # Fallback to a dedicated fixture if VM details are not available or don't contain routes
        cache_key = (
            f"vm_effective_routes:{subscription_id}:{resource_group_name}:{vm_name}"
        )

        if not refresh_cache:
            cached_data = self.cache.get(cache_key)
            if cached_data:
                logger.debug(f"Cache hit for VM effective routes of {vm_name}")
                return cached_data

        logger.info(
            f"Fetching mock VM effective routes for {vm_name} in resource group {resource_group_name}"
        )

        # Try to get routes from a specific fixture
        fixture = self._find_latest_fixture(
            f"vm_routes_{subscription_id}_{resource_group_name}_{vm_name}"
        )

        if fixture:
            self.cache.set(cache_key, fixture)
            return fixture

        # If no specific fixture is found, return some sample routes instead of empty list
        sample_routes = [
            {
                "address_prefix": ADDR_LOCAL_SUBNET,
                "next_hop_type": "VnetLocal",
                "next_hop_ip_address": None,
                "source": "Default",
            },
            {
                "address_prefix": ADDR_DEFAULT_ROUTE,
                "next_hop_type": "Internet",
                "next_hop_ip_address": None,
                "source": "Default",
            },
        ]

        self.cache.set(cache_key, sample_routes)
        return sample_routes

    async def get_nic_effective_routes(
        self,
        subscription_id: str,
        resource_group_name: str,
        nic_name: str,
        refresh_cache: bool = False,
    ) -> List[Dict]:
        """
        Get effective routes for a specific network interface.

        Args:
            subscription_id: Azure subscription ID
            resource_group_name: Resource group name
            nic_name: Network interface name
            refresh_cache: Whether to bypass cache and fetch fresh data
        """
        cache_key = (
            f"nic_effective_routes:{subscription_id}:{resource_group_name}:{nic_name}"
        )

        if not refresh_cache:
            cached_data = self.cache.get(cache_key)
            if cached_data:
                logger.debug(f"Cache hit for NIC effective routes of {nic_name}")
                return cached_data

        logger.info(
            f"Fetching mock NIC effective routes for {nic_name} in resource group {resource_group_name}"
        )

        # Try to get routes from a specific fixture
        fixture = self._find_latest_fixture(
            f"nic_routes_{subscription_id}_{resource_group_name}_{nic_name}"
        )

        if fixture:
            self.cache.set(cache_key, fixture)
            return fixture

        # If no specific fixture is found, return some sample routes
        sample_routes = [
            {
                "address_prefix": ADDR_LOCAL_SUBNET,
                "next_hop_type": "VnetLocal",
                "next_hop_ip_address": None,
                "source": "Default",
            },
            {
                "address_prefix": ADDR_DEFAULT_ROUTE,
                "next_hop_type": "Internet",
                "next_hop_ip_address": None,
                "source": "Default",
            },
        ]

        self.cache.set(cache_key, sample_routes)
        return sample_routes

    async def get_all_virtual_machines(self, refresh_cache: bool = False) -> List[Dict]:
        """
        Get all virtual machines across all subscriptions and resource groups.

        Args:
            refresh_cache: Whether to bypass cache and fetch fresh data

        Returns:
            List of virtual machines with subscription and resource group context
        """
        cache_key = "all_vms"

        if not refresh_cache:
            cached_data = self.cache.get(cache_key)
            if cached_data:
                logger.debug("Cache hit for all VMs")
                return cached_data

        logger.info("Fetching mock all VMs")

        # Try to find a specific fixture for all VMs
        fixture = self._find_latest_fixture("all_vms")

        if fixture:
            self.cache.set(cache_key, fixture)
            return fixture

        # If no fixture found, create sample VMs with context
        all_vms = []

        # Get the first subscription to use for the sample data
        subscriptions = await self.get_subscriptions()
        if not subscriptions:
            return []

        sub = subscriptions[0]

        # Create sample VMs for this subscription
        sample_vms = [
            {
                "id": f"/subscriptions/{sub.id}/resourceGroups/rg-sample-01/providers/Microsoft.Compute/virtualMachines/vm-sample-01",
                "name": "vm-sample-01",
                "location": "swedencentral",
                "vm_size": "Standard_D2s_v3",
                "os_type": "Linux",
                "power_state": "running",
                "subscription_id": sub.id,
                "subscription_name": sub.name,
                "resource_group_name": "rg-sample-01",
                "detail_url": "/api/subscriptions/virtual_machines/vm-sample-01",
            },
            {
                "id": f"/subscriptions/{sub.id}/resourceGroups/rg-sample-01/providers/Microsoft.Compute/virtualMachines/vm-sample-02",
                "name": "vm-sample-02",
                "location": "swedencentral",
                "vm_size": "Standard_D4s_v3",
                "os_type": "Windows",
                "power_state": "running",
                "subscription_id": sub.id,
                "subscription_name": sub.name,
                "resource_group_name": "rg-sample-01",
                "detail_url": "/api/subscriptions/virtual_machines/vm-sample-02",
            },
        ]

        all_vms.extend(sample_vms)
        self.cache.set(cache_key, all_vms)
        return all_vms


def get_mock_azure_service() -> MockAzureResourceService:
    """
    Dependency function for FastAPI to get a MockAzureResourceService instance.

    This can be used as a drop-in replacement for the real Azure service in tests
    and development environments. Usage example with FastAPI:
    
    ```python
    from fastapi import Depends, APIRouter
    from ..tools.mock_azure_service import get_mock_azure_service
    from ..core.azure_service import AzureResourceService
    
    router = APIRouter()
    
    @router.get("/subscriptions")
    async def list_subscriptions(
        azure_service: AzureResourceService = Depends(get_mock_azure_service)
    ):
        return await azure_service.get_subscriptions()
    ```

    Returns:
        A configured MockAzureResourceService instance
    """
    return MockAzureResourceService(
        cache=InMemoryCache(), fixtures_dir="./test_harnesses"
    )


# Standalone example usage
async def example_usage():
    """Example of how to use the mock service."""
    mock_service = MockAzureResourceService()

    # Get subscriptions
    subscriptions = await mock_service.get_subscriptions()

    # Get resource groups for the first subscription
    if subscriptions:
        sub_id = subscriptions[0].id
        resource_groups = await mock_service.get_resource_groups(sub_id)

        # Get VMs for the first resource group
        if resource_groups:
            rg_name = resource_groups[0].name
            vms = await mock_service.get_virtual_machines(sub_id, rg_name)

            # Get details for the first VM
            if vms:
                vm_name = vms[0].name
                vm_details = await mock_service.get_vm_details(sub_id, rg_name, vm_name)
                if vm_details:
                    print(f"VM Details: {vm_details.json(indent=2)}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(example_usage())
