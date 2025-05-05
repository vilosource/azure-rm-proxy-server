from azure_rm_client.commands.base_command import BaseCommand
from azure_rm_client.commands import CommandRegistry
from azure_rm_client.workers.vm_hostnames_worker import VMHostnamesWorker
import logging
import json

logger = logging.getLogger(__name__)

@CommandRegistry.register
class VMHostnamesCommand(BaseCommand):
    @property
    def name(self) -> str:
        return "vm-hostnames"

    @property
    def description(self) -> str:
        return "Virtual machine hostname operations."

    @classmethod
    def configure_parser(cls, subparser):
        # Configure command options
        subparser.add_argument("--subscription-id", help="Filter by Azure subscription ID (optional)")
        subparser.add_argument("--refresh-cache", action="store_true", help="Refresh the cache")
        subparser.add_argument("--output", help="Output file to save results (optional)")

    def execute(self):
        """List VM hostnames."""
        subscription_id = self.args.get('subscription_id')
        refresh_cache = self.args.get('refresh_cache', False)
        output_file = self.args.get('output')

        if subscription_id:
            logger.debug(f"Listing VM hostnames for subscription {subscription_id}")
        else:
            logger.debug("Listing VM hostnames across all subscriptions")
        
        try:
            # Initialize the worker
            hostnames_worker = VMHostnamesWorker()
            
            # Get VM hostnames
            vm_hostnames = hostnames_worker.execute(
                subscription_id=subscription_id,
                refresh_cache=refresh_cache
            )
            
            # Output the hostnames
            if output_file:
                with open(output_file, 'w') as f:
                    json.dump(vm_hostnames, f, indent=2)
                print(f"VM hostnames saved to {output_file}")
            else:
                print(json.dumps(vm_hostnames, indent=2))
                
            logger.debug(f"Found {len(vm_hostnames)} VM hostnames")
            
        except Exception as e:
            logger.error(f"Error listing VM hostnames: {e}")
            print(f"Error: {e}")