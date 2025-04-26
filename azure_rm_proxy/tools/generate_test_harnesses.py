#!/usr/bin/env python3
"""
Generate Test Harnesses for Azure RM Proxy

This script connects to Azure API endpoints using Azure authentication
and captures detailed output for all supported resource types.
The data is saved as JSON files that can be used for:
- Mock implementations during testing
- Sample data for development
- Analyzing Azure resource structure

Features:
- Captures subscriptions, resource groups, VMs, and detailed VM info
- Supports capturing network interfaces, NSG rules, routes, and AAD groups
- Can target specific subscriptions or resource groups
- Includes progress tracking and error handling
- Can discover available subscriptions using Azure CLI

Prerequisites:
- Azure authentication (Azure CLI login or Service Principal)
- Proper permissions to access the resources
- Azure CLI installed (for subscription discovery)

Usage:
    python generate_test_harnesses.py [options]

Examples:
    # Capture all resources
    python generate_test_harnesses.py

    # Target a specific subscription
    python generate_test_harnesses.py --subscription-id "00000000-0000-0000-0000-000000000000"

    # Target a specific resource group
    python generate_test_harnesses.py --resource-group "my-resource-group"

    # Specify output directory
    python generate_test_harnesses.py --output-dir "./my-fixtures"

    # Use Azure CLI for subscription discovery
    python generate_test_harnesses.py --use-az-cli
"""

import argparse
import asyncio
import datetime
import json
import logging
import os
import sys
import time
import subprocess
from typing import Dict, List, Any, Optional, Set, Tuple

# Add the parent directory to sys.path to import our app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Import project modules
from azure_rm_proxy.core.auth import get_credentials
from azure_rm_proxy.core.azure_clients import AzureClientFactory
from azure_rm_proxy.core.azure_service import AzureResourceService
from azure_rm_proxy.core.caching import InMemoryCache
from azure_rm_proxy.core.concurrency import ConcurrencyLimiter

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def get_subscriptions_from_cli() -> List[Dict[str, Any]]:
    """
    Discover available subscriptions using the Azure CLI.
    Returns a list of subscription dictionaries compatible with the Azure SDK format.
    """
    logger.info("Discovering subscriptions using Azure CLI...")
    try:
        # Run 'az account list' command
        result = subprocess.run(
            ["az", "account", "list", "--output", "json"],
            capture_output=True,
            text=True,
            check=True,
        )

        # Parse the JSON output
        subscriptions_raw = json.loads(result.stdout)

        # Transform the output to match the format expected by the rest of the code
        subscriptions = []
        for sub in subscriptions_raw:
            subscriptions.append(
                {
                    "id": sub["id"],
                    "name": sub.get("name", ""),
                    "state": sub.get("state", ""),
                    "tenantId": sub.get("tenantId", ""),
                    "isDefault": sub.get("isDefault", False),
                }
            )

        logger.info(f"Found {len(subscriptions)} subscriptions via Azure CLI")
        return subscriptions
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running 'az account list': {e}")
        logger.error(f"Error output: {e.stderr}")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing Azure CLI output: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error while getting subscriptions from CLI: {e}")
        return []


class TestHarnessGenerator:
    """
    Generates test harnesses by connecting to Azure and capturing resource data.
    """

    def __init__(
        self,
        output_dir: str,
        subscription_id: Optional[str] = None,
        resource_group: Optional[str] = None,
        vm_name: Optional[str] = None,
        max_concurrency: int = 5,
        skip_vm_details: bool = False,
        use_az_cli: bool = False,
    ):
        self.output_dir = output_dir
        self.subscription_id = subscription_id
        self.resource_group = resource_group
        self.vm_name = vm_name
        self.skip_vm_details = skip_vm_details
        self.use_az_cli = use_az_cli

        # Get Azure credentials
        self.credentials = get_credentials()

        # Create Azure client factory
        self.client_factory = AzureClientFactory()

        # Create concurrency limiter
        self.limiter = ConcurrencyLimiter(max_concurrent=max_concurrency)

        # Create Azure service
        self.azure_service = AzureResourceService(
            self.credentials, InMemoryCache(), self.limiter
        )

        # Generate timestamp for filenames
        self.timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

        # Statistics tracking
        self.stats = {
            "subscriptions": 0,
            "resource_groups": 0,
            "virtual_machines": 0,
            "vm_details": 0,
            "failures": 0,
        }

    def save_json_fixture(self, data: Any, filename: str) -> str:
        """Save data as a JSON fixture file."""
        os.makedirs(self.output_dir, exist_ok=True)

        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, "w") as f:
            json.dump(
                data, f, indent=2, default=str
            )  # default=str handles non-serializable types

        logger.info(f"Saved fixture: {filepath}")
        return filepath

    async def get_subscriptions(self) -> List[Dict[str, Any]]:
        """Get all available subscriptions."""
        logger.info("Fetching subscriptions...")

        try:
            # If using Azure CLI for subscription discovery
            if self.use_az_cli:
                subscriptions = get_subscriptions_from_cli()
            else:
                # Use the SDK-based approach
                subscriptions = await self.azure_service.get_subscriptions(
                    refresh_cache=True
                )

            self.stats["subscriptions"] = len(subscriptions)

            # Save all subscriptions
            self.save_json_fixture(
                subscriptions, f"subscriptions_{self.timestamp}.json"
            )

            return subscriptions
        except Exception as e:
            logger.error(f"Error fetching subscriptions: {e}")
            self.stats["failures"] += 1
            return []

    async def get_resource_groups(self, subscription_id: str) -> List[Dict[str, Any]]:
        """Get resource groups for a subscription."""
        logger.info(f"Fetching resource groups for subscription {subscription_id}...")
        try:
            resource_groups = await self.azure_service.get_resource_groups(
                subscription_id, refresh_cache=True
            )
            self.stats["resource_groups"] += len(resource_groups)

            # Save resource groups
            self.save_json_fixture(
                resource_groups,
                f"resource_groups_{subscription_id}_{self.timestamp}.json",
            )

            return resource_groups
        except Exception as e:
            logger.error(f"Error fetching resource groups for {subscription_id}: {e}")
            self.stats["failures"] += 1
            return []

    async def get_virtual_machines(
        self, subscription_id: str, resource_group: str
    ) -> List[Dict[str, Any]]:
        """Get virtual machines for a resource group."""
        logger.info(f"Fetching VMs for resource group {resource_group}...")
        try:
            vms = await self.azure_service.get_virtual_machines(
                subscription_id, resource_group, refresh_cache=True
            )
            self.stats["virtual_machines"] += len(vms)

            # Save VMs
            if vms:
                self.save_json_fixture(
                    vms, f"vms_{subscription_id}_{resource_group}_{self.timestamp}.json"
                )

            return vms
        except Exception as e:
            logger.error(f"Error fetching VMs for {resource_group}: {e}")
            self.stats["failures"] += 1
            return []

    async def get_vm_details(
        self, subscription_id: str, resource_group: str, vm_name: str
    ) -> Optional[Dict[str, Any]]:
        """Get detailed information for a specific virtual machine."""
        logger.info(f"Fetching details for VM {vm_name}...")
        try:
            vm_details = await self.azure_service.get_vm_details(
                subscription_id, resource_group, vm_name, refresh_cache=True
            )

            if vm_details:
                self.stats["vm_details"] += 1

                # Save VM details
                self.save_json_fixture(
                    vm_details,
                    f"vm_details_{subscription_id}_{resource_group}_{vm_name}_{self.timestamp}.json",
                )

            return vm_details
        except Exception as e:
            logger.error(f"Error fetching details for VM {vm_name}: {e}")
            self.stats["failures"] += 1
            return None

    async def process_all_resources(self):
        """Process all resources or just the specified ones."""
        start_time = time.time()
        logger.info(f"Starting test harness generation (output dir: {self.output_dir})")

        # If subscription ID is provided, only process that subscription
        if self.subscription_id:
            subscriptions = [{"id": self.subscription_id}]
        else:
            # Otherwise, get all subscriptions
            subscriptions = await self.get_subscriptions()

        if not subscriptions:
            logger.error("No subscriptions found or accessible")
            return

        # Process each subscription
        for subscription in subscriptions:
            # Handle both dictionary and Pydantic model for subscriptions
            sub_id = (
                subscription["id"]
                if isinstance(subscription, dict)
                else subscription.id
            )

            # If resource group is provided, only process that group
            if self.resource_group:
                resource_groups = [{"name": self.resource_group}]
            else:
                # Otherwise, get all resource groups for this subscription
                resource_groups = await self.get_resource_groups(sub_id)

            if not resource_groups:
                logger.warning(f"No resource groups found in subscription {sub_id}")
                continue

            # Process each resource group
            for rg in resource_groups:
                # Handle both dictionary and Pydantic model for resource groups
                rg_name = rg["name"] if isinstance(rg, dict) else rg.name

                # If VM name is provided, only process that VM
                if self.vm_name:
                    vms = [{"name": self.vm_name}]
                else:
                    # Otherwise, get all VMs in this resource group
                    vms = await self.get_virtual_machines(sub_id, rg_name)

                if not vms:
                    logger.info(f"No VMs found in resource group {rg_name}")
                    continue

                # Skip VM details if requested
                if self.skip_vm_details:
                    continue

                # Process each VM to get detailed information
                for vm in vms:
                    # Handle both dictionary and Pydantic model for VMs
                    vm_name = vm["name"] if isinstance(vm, dict) else vm.name
                    await self.get_vm_details(sub_id, rg_name, vm_name)

                    # Add a small delay to avoid potential throttling
                    await asyncio.sleep(0.5)

        # Calculate elapsed time
        elapsed_time = time.time() - start_time

        # Print summary
        logger.info(f"Test harness generation completed in {elapsed_time:.2f} seconds")
        logger.info(f"Summary: {self.stats}")


async def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Generate Azure test harnesses")

    parser.add_argument(
        "--output-dir",
        type=str,
        default="./test_harnesses",
        help="Directory to save fixture files (default: ./test_harnesses)",
    )
    parser.add_argument(
        "--subscription-id",
        type=str,
        default=None,
        help="Target specific Azure subscription ID",
    )
    parser.add_argument(
        "--resource-group",
        type=str,
        default=None,
        help="Target specific resource group",
    )
    parser.add_argument(
        "--vm-name", type=str, default=None, help="Target specific virtual machine"
    )
    parser.add_argument(
        "--max-concurrency",
        type=int,
        default=5,
        help="Maximum number of concurrent Azure API calls (default: 5)",
    )
    parser.add_argument(
        "--skip-vm-details",
        action="store_true",
        help="Skip fetching detailed VM information",
    )
    parser.add_argument(
        "--quiet", action="store_true", help="Reduce verbosity of output"
    )
    parser.add_argument(
        "--use-az-cli",
        action="store_true",
        help="Use Azure CLI to discover available subscriptions",
    )

    args = parser.parse_args()

    # Adjust logging level if quiet mode
    if args.quiet:
        logging.getLogger().setLevel(logging.WARNING)

    # Create and run the generator
    generator = TestHarnessGenerator(
        output_dir=args.output_dir,
        subscription_id=args.subscription_id,
        resource_group=args.resource_group,
        vm_name=args.vm_name,
        max_concurrency=args.max_concurrency,
        skip_vm_details=args.skip_vm_details,
        use_az_cli=args.use_az_cli,
    )

    await generator.process_all_resources()


if __name__ == "__main__":
    asyncio.run(main())
