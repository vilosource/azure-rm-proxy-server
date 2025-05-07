"""Command to fetch virtual network peering reports."""

import logging
from typing import Dict, Any, List, Optional
import asyncio

from .base_command import BaseCommand
from . import CommandRegistry

logger = logging.getLogger(__name__)


@CommandRegistry.register
class VNetPeeringReportCommand(BaseCommand):
    """Command to fetch virtual network peering reports."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        """Initialize the command."""
        super().__init__(
            name="vnet-peering-report",
            description="Get a report of virtual network peerings showing both sides of connections",
            aliases=["vnet-peerings", "peering-report"],
            base_url=base_url
        )

    def add_arguments(self, parser):
        """Add command-specific arguments."""
        parser.add_argument(
            "-s",
            "--subscription",
            help="Subscription ID to query",
            required=True,
        )
        parser.add_argument(
            "-g",
            "--resource-group",
            help="Filter by resource group name",
            required=False,
        )
        parser.add_argument(
            "--refresh-cache",
            help="Force refresh of cached data",
            action="store_true",
            default=False,
        )
        # Add standard formatter options through the parent class
        self.add_formatter_arguments(parser)

    async def execute_async(self, args) -> Dict[str, Any]:
        """
        Execute the command to get virtual network peering report.

        Args:
            args: Command line arguments

        Returns:
            Dictionary with report data
        """
        # Build API endpoint URL
        base_url = f"{args.base_url}/api/vnet-peering-report/subscriptions/{args.subscription}"
        
        # Add optional parameters
        params = {"refresh-cache": args.refresh_cache}
        if args.resource_group:
            params["resource_group"] = args.resource_group
            
        # Call the API
        response = await self.http_get(base_url, params=params)
        
        # Format the data for better display
        result = self._format_peering_data(response)
        
        # Add a summary of peering health
        result["summary"] = self._generate_summary(response)
        
        return result
    
    def execute(self) -> bool:
        """
        Execute the command synchronously by running the async version in a loop.
        
        Returns:
            True if the command executed successfully, False otherwise
        """
        try:
            # Create event loop and run the async method
            loop = asyncio.get_event_loop()
            result = loop.run_until_complete(self.execute_async(self.args))
            
            # Format and print the result
            output = self.format_output(result)
            print(output)
            return True
        except Exception as e:
            logger.error(f"Failed to execute command: {e}")
            return False
        
    def _format_peering_data(self, peerings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Format peering data for better display.
        
        Args:
            peerings: List of peering data from API
            
        Returns:
            Formatted data
        """
        result = {
            "peerings": [],
            "total_count": len(peerings),
        }
        
        for peering in peerings:
            formatted_peering = {
                "peering_id": peering.get("peering_id"),
                "connection_status": "Connected" if peering.get("connected") else "Partial/Disconnected",
                "vnet1": {
                    "name": peering.get("vnet1_name"),
                    "resource_group": peering.get("vnet1_resource_group"),
                    "subscription_id": peering.get("vnet1_subscription_id"),
                    "state": peering.get("vnet1_to_vnet2_state"),
                },
                "vnet2": {
                    "name": peering.get("vnet2_name"),
                    "resource_group": peering.get("vnet2_resource_group"),
                    "subscription_id": peering.get("vnet2_subscription_id"),
                    "state": peering.get("vnet2_to_vnet1_state"),
                },
                "settings": {
                    "allow_virtual_network_access": peering.get("allow_virtual_network_access"),
                    "allow_forwarded_traffic": peering.get("allow_forwarded_traffic"),
                    "allow_gateway_transit": peering.get("allow_gateway_transit"),
                    "use_remote_gateways": peering.get("use_remote_gateways"),
                },
                "provisioning_state": peering.get("provisioning_state")
            }
            result["peerings"].append(formatted_peering)
            
        return result
        
    def _generate_summary(self, peerings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate a summary of peering health.
        
        Args:
            peerings: List of peering data from API
            
        Returns:
            Summary data
        """
        total = len(peerings)
        connected = sum(1 for p in peerings if p.get("connected", False))
        
        return {
            "total_peering_connections": total,
            "connected_count": connected,
            "partial_count": total - connected,
            "connectivity_percentage": round((connected / total) * 100, 2) if total > 0 else 0,
        }