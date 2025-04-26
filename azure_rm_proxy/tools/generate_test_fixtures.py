#!/usr/bin/env python3
"""
Generate Test Fixtures for Azure RM Proxy

This script connects to Azure API endpoints using the Azure CLI authentication
and saves the output as JSON files that can be used as mock data in tests.

Prerequisites:
    - Azure CLI must be installed and logged in
    - Azure SDK for Python must be installed

Usage:
    python generate_test_fixtures.py [--output-dir OUTPUT_DIR] [--sub-id SUBSCRIPTION_ID]
"""

import argparse
import asyncio
import datetime
import json
import logging
import os
import sys
from typing import Dict, List, Any, Optional

# Add the parent directory to sys.path to import our app modules
# Adjust the path to include the root project directory
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, project_root)

# Import our core Azure service using absolute imports
from azure_rm_proxy.core.azure_service import AzureResourceService
from azure_rm_proxy.core.auth import get_credentials
from azure_rm_proxy.core.caching import InMemoryCache
from azure_rm_proxy.core.concurrency import ConcurrencyLimiter

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def save_json_fixture(data: Any, filename: str, output_dir: str):
    """Save data as a JSON fixture file."""
    os.makedirs(output_dir, exist_ok=True)

    # Convert Pydantic models to dict if needed
    if isinstance(data, list):
        # For lists of objects
        if hasattr(data[0], "model_dump") if data else False:
            # For Pydantic v2
            data_to_save = [
                item.model_dump() if hasattr(item, "model_dump") else item
                for item in data
            ]
        elif hasattr(data[0], "dict") if data else False:
            # For older Pydantic versions
            data_to_save = [
                item.dict() if hasattr(item, "dict") else item for item in data
            ]
        else:
            data_to_save = data
    else:
        # For single objects
        if hasattr(data, "model_dump"):
            data_to_save = data.model_dump()
        elif hasattr(data, "dict"):
            data_to_save = data.dict()
        else:
            data_to_save = data

    filepath = os.path.join(output_dir, filename)
    with open(filepath, "w") as f:
        json.dump(
            data_to_save, f, indent=2, default=str
        )  # default=str handles non-serializable types

    logger.info(f"Saved fixture: {filepath}")


async def generate_fixtures(output_dir: str, subscription_id: Optional[str] = None):
    """Generate all test fixtures."""
    try:
        # Initialize Azure service
        logger.info("Initializing Azure service...")
        credentials = get_credentials()

        # Create cache and concurrency limiter
        cache = InMemoryCache()
        limiter = ConcurrencyLimiter(max_concurrent=5)

        # Initialize the service with all required parameters
        azure_service = AzureResourceService(credentials, cache, limiter)

        # Generate timestamp for filenames
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

        # Get subscriptions
        logger.info("Fetching subscriptions...")
        subscriptions = await azure_service.get_subscriptions()

        # Save subscriptions fixture
        save_json_fixture(subscriptions, f"subscriptions_{timestamp}.json", output_dir)

        # If no subscription ID was provided, use the first one from the list
        if not subscription_id and subscriptions:
            # Handle both Pydantic models and dictionaries
            first_sub = subscriptions[0]
            if hasattr(first_sub, "id"):
                subscription_id = first_sub.id
            else:
                subscription_id = first_sub.get("id")

            logger.info(f"Using subscription: {subscription_id}")

        if not subscription_id:
            logger.error("No subscription ID provided or available")
            return

        # Get resource groups
        logger.info(f"Fetching resource groups for subscription {subscription_id}...")
        resource_groups = await azure_service.get_resource_groups(subscription_id)

        # Save resource groups fixture
        save_json_fixture(
            resource_groups,
            f"resource_groups_{subscription_id}_{timestamp}.json",
            output_dir,
        )

        # For each resource group, get VMs
        for rg in resource_groups:
            # Handle both Pydantic models and dictionaries
            if hasattr(rg, "name"):
                rg_name = rg.name
            else:
                rg_name = rg.get("name")

            logger.info(f"Fetching VMs for resource group {rg_name}...")

            try:
                vms = await azure_service.get_virtual_machines(subscription_id, rg_name)

                # Save VMs fixture
                if vms:
                    save_json_fixture(
                        vms,
                        f"vms_{subscription_id}_{rg_name}_{timestamp}.json",
                        output_dir,
                    )

                    # For each VM, get details
                    for vm in vms:
                        # Handle both Pydantic models and dictionaries
                        if hasattr(vm, "name"):
                            vm_name = vm.name
                        else:
                            vm_name = vm.get("name")

                        logger.info(f"Fetching details for VM {vm_name}...")

                        try:
                            vm_details = await azure_service.get_vm_details(
                                subscription_id, rg_name, vm_name
                            )

                            # Save VM details fixture
                            if vm_details:
                                save_json_fixture(
                                    vm_details,
                                    f"vm_details_{subscription_id}_{rg_name}_{vm_name}_{timestamp}.json",
                                    output_dir,
                                )
                        except Exception as e:
                            logger.error(
                                f"Error fetching details for VM {vm_name}: {e}"
                            )
            except Exception as e:
                logger.error(f"Error fetching VMs for resource group {rg_name}: {e}")

        logger.info("Fixture generation complete!")

    except Exception as e:
        logger.error(f"Error generating fixtures: {e}")
        import traceback

        traceback.print_exc()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Generate Azure test fixtures")
    parser.add_argument(
        "--output-dir",
        type=str,
        default="./test_fixtures",
        help="Directory to save fixture files (default: ./test_fixtures)",
    )
    parser.add_argument(
        "--sub-id",
        type=str,
        default=None,
        help="Azure subscription ID to use (default: use first available)",
    )

    args = parser.parse_args()

    # Run the fixture generator
    asyncio.run(generate_fixtures(args.output_dir, args.sub_id))


if __name__ == "__main__":
    main()
