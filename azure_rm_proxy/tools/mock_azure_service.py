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
    VirtualMachineDetail
)
from ..core.caching import CacheStrategy, InMemoryCache

# Set up logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MockAzureResourceService:
    """
    A mock implementation of the Azure Resource Service.
    
    This class mimics the behavior of the real Azure service but uses
    JSON fixtures instead of making actual API calls.
    """
    
    def __init__(self, 
                 credential=None,  # Not used, but kept for API compatibility
                 cache: CacheStrategy = None,
                 limiter = None,  # Not used, but kept for API compatibility
                 fixtures_dir: str = './test_harnesses'):
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
        logger.info(f"MockAzureResourceService initialized with fixtures from {fixtures_dir}")
    
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
                with open(file_path, 'r') as f:
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
            match = re.search(r'_(\d{14})\.json$', name)
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
            if tags_str == 'None':
                rg_dict["tags"] = None
            elif tags_str == '{}':
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
    
    async def get_subscriptions(self, refresh_cache: bool = False) -> List[SubscriptionModel]:
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
                            **sub_data
                        }
                    subscriptions.append(SubscriptionModel.parse_obj(sub_data))
            
            self.cache.set(cache_key, subscriptions)
            return subscriptions
        
        return []
    
    async def get_resource_groups(self, subscription_id: str, refresh_cache: bool = False) -> List[ResourceGroupModel]:
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
                logger.debug(f"Cache hit for resource groups in subscription {subscription_id}")
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
                            "id": rg_data.get("id", f"/subscriptions/{subscription_id}/resourceGroups/{rg_data.get('name', 'unknown')}"),
                            "name": rg_data.get("name", "Unknown Resource Group"),
                            "location": rg_data.get("location", "westus"),
                            "tags": rg_data.get("tags", {}),
                            **rg_data
                        }
                    resource_groups.append(ResourceGroupModel.parse_obj(rg_data))
            
            self.cache.set(cache_key, resource_groups)
            return resource_groups
        
        return []
    
    async def get_virtual_machines(self, subscription_id: str, resource_group_name: str, refresh_cache: bool = False) -> List[VirtualMachineModel]:
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
                logger.debug(f"Cache hit for VMs in resource group {resource_group_name}")
                return cached_data
        
        logger.info(f"Fetching mock VMs for resource group {resource_group_name} in subscription {subscription_id}")
        fixture = self._find_latest_fixture(f"vms_{subscription_id}_{resource_group_name}")
        
        if fixture:
            # Convert to VirtualMachineModel objects
            virtual_machines = []
            for vm_data in fixture:
                # Parse the string representation if needed
                if isinstance(vm_data, str):
                    vm_data = self._parse_virtual_machine_string(vm_data)
                
                if isinstance(vm_data, dict):
                    # Ensure required fields exist
                    if not all(k in vm_data for k in ["id", "name", "location", "vm_size"]):
                        # Add missing fields with default values
                        vm_data = {
                            "id": vm_data.get("id", f"/subscriptions/{subscription_id}/resourceGroups/{resource_group_name}/providers/Microsoft.Compute/virtualMachines/{vm_data.get('name', 'unknown')}"),
                            "name": vm_data.get("name", "Unknown VM"),
                            "location": vm_data.get("location", "westus"),
                            "vm_size": vm_data.get("vm_size", "Standard_DS1_v2"),
                            "os_type": vm_data.get("os_type", "Linux"),
                            "power_state": vm_data.get("power_state", "running"),
                            **vm_data
                        }
                    virtual_machines.append(VirtualMachineModel.parse_obj(vm_data))
            
            self.cache.set(cache_key, virtual_machines)
            return virtual_machines
        
        return []
    
    async def get_vm_details(self, subscription_id: str, resource_group_name: str, vm_name: str, refresh_cache: bool = False) -> Union[VirtualMachineDetail, None]:
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
        
        logger.info(f"Fetching mock VM details for {vm_name} in resource group {resource_group_name}")
        fixture = self._find_latest_fixture(f"vm_details_{subscription_id}_{resource_group_name}_{vm_name}")
        
        if fixture:
            # If we don't have detailed VM data, try to construct it from the basic VM data
            if not fixture.get("network_interfaces"):
                # Get the basic VM data
                vms = await self.get_virtual_machines(subscription_id, resource_group_name, refresh_cache)
                vm_basic = next((vm for vm in vms if vm.name == vm_name), None)
                
                if vm_basic:
                    # Convert to VirtualMachineDetail with empty collections
                    vm_details = VirtualMachineDetail(
                        id=vm_basic.id,
                        name=vm_basic.name,
                        location=vm_basic.location,
                        vm_size=vm_basic.vm_size,
                        os_type=vm_basic.os_type,
                        power_state=vm_basic.power_state,
                        network_interfaces=[],
                        effective_nsg_rules=[],
                        effective_routes=[],
                        aad_groups=[]
                    )
                    self.cache.set(cache_key, vm_details)
                    return vm_details
            else:
                # We have detailed VM data
                vm_details = VirtualMachineDetail.parse_obj(fixture)
                self.cache.set(cache_key, vm_details)
                return vm_details
        
        return None


def get_mock_azure_service() -> MockAzureResourceService:
    """
    Dependency function for FastAPI to get a MockAzureResourceService instance.
    
    This can be used as a drop-in replacement for the real Azure service in tests
    and development environments.
    
    Returns:
        A configured MockAzureResourceService instance
    """
    return MockAzureResourceService(
        cache=InMemoryCache(),
        fixtures_dir="./test_harnesses"
    )


# Example usage as a FastAPI dependency
"""
# In your API router:
from fastapi import Depends, APIRouter
from ..tools.mock_azure_service import get_mock_azure_service
from ..core.azure_service import AzureResourceService

router = APIRouter()

@router.get("/subscriptions")
async def list_subscriptions(
    azure_service: AzureResourceService = Depends(get_mock_azure_service)
):
    return await azure_service.get_subscriptions()
"""

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