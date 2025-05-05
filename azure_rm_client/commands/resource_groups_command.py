from azure_rm_client.commands.base_command import BaseCommand
from azure_rm_client.commands import CommandRegistry
from azure_rm_client.workers.resource_groups_worker import ResourceGroupsWorker
import logging
import json

logger = logging.getLogger(__name__)

@CommandRegistry.register
class ResourceGroupsCommand(BaseCommand):
    @property
    def name(self) -> str:
        return "resource-groups"

    @property
    def description(self) -> str:
        return "Resource group operations."

    @classmethod
    def configure_parser(cls, subparser):
        # Create subcommands
        rg_subparsers = subparser.add_subparsers(dest="rg_operation", help="Resource group operations")
        
        # List resource groups command
        list_parser = rg_subparsers.add_parser("list", help="List resource groups in a subscription")
        list_parser.add_argument("--subscription-id", required=True, help="Azure subscription ID")
        list_parser.add_argument("--refresh-cache", action="store_true", help="Refresh the cache")
        list_parser.add_argument("--output", help="Output file to save results (optional)")

    def execute(self):
        """Execute the appropriate resource group operation based on the subcommand."""
        rg_operation = self.args.get('rg_operation')
        if not rg_operation:
            logger.error("No resource group operation specified")
            return

        # Initialize the worker
        rg_worker = ResourceGroupsWorker()

        if rg_operation == "list":
            self._list_resource_groups(rg_worker)
        else:
            logger.error(f"Unknown resource group operation: {rg_operation}")

    def _list_resource_groups(self, rg_worker):
        """List resource groups in a subscription."""
        subscription_id = self.args.get('subscription_id')
        refresh_cache = self.args.get('refresh_cache', False)
        output_file = self.args.get('output')

        logger.debug(f"Listing resource groups in subscription {subscription_id}")
        
        try:
            resource_groups = rg_worker.execute(
                subscription_id=subscription_id,
                refresh_cache=refresh_cache
            )
            
            if output_file:
                with open(output_file, 'w') as f:
                    json.dump(resource_groups, f, indent=2)
                print(f"Resource groups list saved to {output_file}")
            else:
                print(json.dumps(resource_groups, indent=2))
                
            logger.debug(f"Found {len(resource_groups)} resource groups in subscription {subscription_id}")
            
        except Exception as e:
            logger.error(f"Error listing resource groups: {e}")
            print(f"Error: {e}")