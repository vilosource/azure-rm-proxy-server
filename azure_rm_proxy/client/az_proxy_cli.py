#!/usr/bin/env python3
"""
Azure RM Proxy CLI - Command-line client for the Azure RM Proxy Server.

This tool allows you to interact with the Azure RM Proxy Server API from the command line.
"""

import argparse
import json
import sys
from typing import Optional, Dict, Any, List
import asyncio
from datetime import datetime

import httpx
from rich.console import Console
from rich.table import Table
from rich.progress import Progress

# Console for rich output
console = Console()

# Default settings
DEFAULT_BASE_URL = "http://localhost:8000"


async def fetch_data(url: str, params: Optional[Dict[str, Any]] = None) -> Any:
    """Fetch data from the API."""
    async with httpx.AsyncClient() as client:
        try:
            with Progress() as progress:
                task = progress.add_task(f"[cyan]Fetching data from {url}...", total=1)
                response = await client.get(url, params=params)
                progress.update(task, completed=1)

            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            console.print(
                f"[red]Error: HTTP {e.response.status_code} - {e.response.text}"
            )
            sys.exit(1)
        except httpx.RequestError as e:
            console.print(f"[red]Error: {str(e)}")
            sys.exit(1)


def display_subscriptions(
    subscriptions: List[Dict[str, Any]], output_format: str
) -> None:
    """Display a list of subscriptions."""
    if output_format == "json":
        console.print(json.dumps(subscriptions, indent=2))
    else:  # table format
        table = Table(title="Azure Subscriptions")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Display Name", style="yellow")
        table.add_column("State", style="magenta")

        for sub in subscriptions:
            table.add_row(
                sub["id"], sub["name"], sub.get("display_name", ""), sub["state"]
            )

        console.print(table)


def display_resource_groups(
    resource_groups: List[Dict[str, Any]], output_format: str
) -> None:
    """Display a list of resource groups."""
    if output_format == "json":
        console.print(json.dumps(resource_groups, indent=2))
    else:  # table format
        table = Table(title="Resource Groups")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Location", style="yellow")
        table.add_column("Tags", style="magenta")

        for rg in resource_groups:
            # Format tags as a string if present
            tags_str = (
                json.dumps(rg.get("tags", {}), separators=(",", ":"))
                if rg.get("tags")
                else ""
            )

            table.add_row(rg["id"], rg["name"], rg["location"], tags_str)

        console.print(table)


def display_virtual_machines(vms: List[Dict[str, Any]], output_format: str) -> None:
    """Display a list of virtual machines."""
    if output_format == "json":
        console.print(json.dumps(vms, indent=2))
    else:  # table format
        table = Table(title="Virtual Machines")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Location", style="yellow")
        table.add_column("Size", style="blue")
        table.add_column("OS Type", style="magenta")
        table.add_column("Power State", style="red")

        for vm in vms:
            table.add_row(
                vm["id"],
                vm["name"],
                vm["location"],
                vm["vm_size"],
                vm.get("os_type", ""),
                vm.get("power_state", ""),
            )

        console.print(table)


def display_vm_details(vm: Dict[str, Any], output_format: str) -> None:
    """Display details of a specific virtual machine."""
    if output_format == "json":
        console.print(json.dumps(vm, indent=2))
    else:  # table format
        # Basic VM info
        console.print(f"[bold cyan]VM Details: {vm['name']}[/bold cyan]")
        console.print(f"ID: {vm['id']}")
        console.print(f"Location: {vm['location']}")
        console.print(f"Size: {vm['vm_size']}")
        if vm.get("os_type"):
            console.print(f"OS Type: {vm['os_type']}")
        if vm.get("power_state"):
            console.print(f"Power State: {vm['power_state']}")

        console.print()

        # Network interfaces
        if "network_interfaces" in vm:
            table = Table(title="Network Interfaces")
            table.add_column("Name", style="green")
            table.add_column("Private IPs", style="yellow")
            table.add_column("Public IPs", style="red")

            for nic in vm["network_interfaces"]:
                table.add_row(
                    nic["name"],
                    ", ".join(nic["private_ip_addresses"]),
                    ", ".join(nic["public_ip_addresses"]),
                )

            console.print(table)
            console.print()

        # NSG Rules
        if "effective_nsg_rules" in vm and vm["effective_nsg_rules"]:
            table = Table(title="Effective NSG Rules")
            table.add_column("Name", style="green")
            table.add_column("Direction", style="yellow")
            table.add_column("Protocol", style="blue")
            table.add_column("Port Range", style="magenta")
            table.add_column("Access", style="red")

            for rule in vm["effective_nsg_rules"]:
                table.add_row(
                    rule["name"],
                    rule["direction"],
                    rule["protocol"],
                    rule["port_range"],
                    rule["access"],
                )

            console.print(table)
            console.print()

        # Routes
        if "effective_routes" in vm and vm["effective_routes"]:
            table = Table(title="Effective Routes")
            table.add_column("Address Prefix", style="green")
            table.add_column("Next Hop Type", style="yellow")
            table.add_column("Next Hop IP", style="blue")
            table.add_column("Origin", style="magenta")

            for route in vm["effective_routes"]:
                table.add_row(
                    route["address_prefix"],
                    route["next_hop_type"],
                    route["next_hop_ip"] or "",
                    route["route_origin"],
                )

            console.print(table)
            console.print()

        # AAD Groups
        if "aad_groups" in vm and vm["aad_groups"]:
            table = Table(title="Azure AD Group Access")
            table.add_column("ID", style="green")
            table.add_column("Display Name", style="yellow")

            for group in vm["aad_groups"]:
                table.add_row(group["id"], group.get("display_name", ""))

            console.print(table)


async def list_subscriptions(args: argparse.Namespace) -> None:
    """List Azure subscriptions."""
    url = f"{args.base_url}/subscriptions/"
    params = {"refresh-cache": "true"} if args.refresh_cache else None

    subscriptions = await fetch_data(url, params)
    display_subscriptions(subscriptions, args.output)


async def list_resource_groups(args: argparse.Namespace) -> None:
    """List resource groups in a subscription."""
    url = f"{args.base_url}/subscriptions/{args.subscription_id}/resource-groups/"
    params = {"refresh-cache": "true"} if args.refresh_cache else None

    resource_groups = await fetch_data(url, params)
    display_resource_groups(resource_groups, args.output)


async def list_vms(args: argparse.Namespace) -> None:
    """List virtual machines in a resource group."""
    url = f"{args.base_url}/subscriptions/{args.subscription_id}/resource-groups/{args.resource_group}/virtual-machines/"
    params = {"refresh-cache": "true"} if args.refresh_cache else None

    vms = await fetch_data(url, params)
    display_virtual_machines(vms, args.output)


async def get_vm_details(args: argparse.Namespace) -> None:
    """Get detailed information about a specific virtual machine."""
    url = f"{args.base_url}/subscriptions/{args.subscription_id}/resource-groups/{args.resource_group}/virtual-machines/{args.vm_name}"
    params = {"refresh-cache": "true"} if args.refresh_cache else None

    vm_details = await fetch_data(url, params)
    display_vm_details(vm_details, args.output)


def main():
    """Main entry point for the CLI application."""
    parser = argparse.ArgumentParser(
        description="Azure RM Proxy CLI - Command-line client for the Azure RM Proxy Server"
    )
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help=f"Base URL of the Azure RM Proxy Server (default: {DEFAULT_BASE_URL})",
    )
    parser.add_argument(
        "--refresh-cache", action="store_true", help="Force refresh of cached data"
    )
    parser.add_argument(
        "--output",
        choices=["table", "json"],
        default="table",
        help="Output format (default: table)",
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # List subscriptions
    subparsers.add_parser("list-subscriptions", help="List Azure subscriptions")

    # List resource groups
    rg_parser = subparsers.add_parser(
        "list-resource-groups", help="List resource groups in a subscription"
    )
    rg_parser.add_argument("--subscription-id", required=True, help="Subscription ID")

    # List VMs
    vm_parser = subparsers.add_parser(
        "list-vms", help="List virtual machines in a resource group"
    )
    vm_parser.add_argument("--subscription-id", required=True, help="Subscription ID")
    vm_parser.add_argument(
        "--resource-group", required=True, help="Resource group name"
    )

    # Get VM details
    vm_details_parser = subparsers.add_parser(
        "get-vm-details",
        help="Get detailed information about a specific virtual machine",
    )
    vm_details_parser.add_argument(
        "--subscription-id", required=True, help="Subscription ID"
    )
    vm_details_parser.add_argument(
        "--resource-group", required=True, help="Resource group name"
    )
    vm_details_parser.add_argument(
        "--vm-name", required=True, help="Virtual machine name"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Execute the appropriate command
    if args.command == "list-subscriptions":
        asyncio.run(list_subscriptions(args))
    elif args.command == "list-resource-groups":
        asyncio.run(list_resource_groups(args))
    elif args.command == "list-vms":
        asyncio.run(list_vms(args))
    elif args.command == "get-vm-details":
        asyncio.run(get_vm_details(args))


if __name__ == "__main__":
    main()
