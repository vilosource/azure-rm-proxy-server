#!/usr/bin/env python3
"""
Test Mock Azure Service

This script tests the MockAzureResourceService with the generated test harnesses.
It performs a series of API calls to validate that the mock service correctly
returns data from the test harnesses.

Usage:
    python -m azure_rm_proxy.tests.scripts.test_mock_service
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
import pytest  # Add pytest import

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Adjust path to include project root
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from azure_rm_proxy.tools.mock_azure_service import MockAzureResourceService


@pytest.mark.asyncio  # Add this marker to tell pytest this is an async test
async def test_mock_service():
    """Test the MockAzureResourceService with generated test harnesses."""
    # Initialize the mock service with test harnesses
    fixtures_dir = os.environ.get("MOCK_FIXTURES_DIR", "./test_harnesses")
    logger.info(f"Using test harnesses from: {fixtures_dir}")

    mock_service = MockAzureResourceService(fixtures_dir=fixtures_dir)

    # 1. Get subscriptions
    logger.info("Fetching subscriptions...")
    subscriptions = await mock_service.get_subscriptions()

    if not subscriptions:
        logger.error("No subscriptions found! Make sure test harnesses are generated.")
        return

    logger.info(f"Found {len(subscriptions)} subscriptions")
    for i, sub in enumerate(subscriptions):
        logger.info(f"  Subscription {i+1}: {sub.id} - {sub.name}")

    # Choose first subscription for testing
    sub_id = subscriptions[0].id

    # 2. Get resource groups for the subscription
    logger.info(f"Fetching resource groups for subscription {sub_id}...")
    resource_groups = await mock_service.get_resource_groups(sub_id)

    if not resource_groups:
        logger.error(f"No resource groups found for subscription {sub_id}!")
        return

    logger.info(f"Found {len(resource_groups)} resource groups")
    for i, rg in enumerate(resource_groups[:5]):  # Show first 5 only
        logger.info(f"  Resource Group {i+1}: {rg.name} - {rg.location}")

    if len(resource_groups) > 5:
        logger.info(f"  ... and {len(resource_groups) - 5} more resource groups")

    # Choose first resource group for testing
    rg_name = resource_groups[0].name

    # 3. Get VMs for the resource group
    logger.info(f"Fetching VMs for resource group {rg_name}...")
    vms = await mock_service.get_virtual_machines(sub_id, rg_name)

    if not vms:
        logger.info(f"No VMs found in resource group {rg_name}")
        # Try another resource group if no VMs found
        for rg in resource_groups[1:]:
            rg_name = rg.name
            logger.info(f"Trying resource group {rg_name}...")
            vms = await mock_service.get_virtual_machines(sub_id, rg_name)
            if vms:
                break

    if not vms:
        logger.error("No VMs found in any resource group!")
        return

    logger.info(f"Found {len(vms)} VMs in resource group {rg_name}")
    for i, vm in enumerate(vms[:5]):  # Show first 5 only
        logger.info(f"  VM {i+1}: {vm.name} - {vm.vm_size} - {vm.os_type}")

    if len(vms) > 5:
        logger.info(f"  ... and {len(vms) - 5} more VMs")

    # 4. Get details for the first VM
    if vms:
        vm_name = vms[0].name
        logger.info(f"Fetching details for VM {vm_name}...")
        vm_details = await mock_service.get_vm_details(sub_id, rg_name, vm_name)

        if vm_details:
            logger.info(f"Successfully retrieved details for VM {vm_name}")
            logger.info(f"  Location: {vm_details.location}")
            logger.info(f"  Size: {vm_details.vm_size}")
            logger.info(f"  OS Type: {vm_details.os_type}")

            if vm_details.network_interfaces:
                logger.info(
                    f"  Network Interfaces: {len(vm_details.network_interfaces)}"
                )
                for i, nic in enumerate(vm_details.network_interfaces):
                    logger.info(f"    NIC {i+1}: {nic.name}")
                    logger.info(
                        f"      Private IPs: {', '.join(nic.private_ip_addresses) if nic.private_ip_addresses else 'None'}"
                    )
                    logger.info(
                        f"      Public IPs: {', '.join(nic.public_ip_addresses) if nic.public_ip_addresses else 'None'}"
                    )

            if vm_details.effective_nsg_rules:
                logger.info(f"  NSG Rules: {len(vm_details.effective_nsg_rules)}")
                for i, rule in enumerate(
                    vm_details.effective_nsg_rules[:3]
                ):  # Show first 3 only
                    logger.info(
                        f"    Rule {i+1}: {rule.name} - {rule.direction} - {rule.protocol} - {rule.port_range} - {rule.access}"
                    )

                if len(vm_details.effective_nsg_rules) > 3:
                    logger.info(
                        f"    ... and {len(vm_details.effective_nsg_rules) - 3} more NSG rules"
                    )
        else:
            logger.warning(f"No details found for VM {vm_name}")

    # Test successful
    logger.info("Mock service test completed successfully")


if __name__ == "__main__":
    asyncio.run(test_mock_service())
