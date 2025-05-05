from azure_rm_client.commands.base_command import BaseCommand
from azure_rm_client.commands import CommandRegistry
from azure_rm_client.workers.virtual_machines_worker import VirtualMachinesWorker
import logging
import json

logger = logging.getLogger(__name__)

@CommandRegistry.register
class VirtualMachinesCommand(BaseCommand):
    @property
    def name(self) -> str:
        return "virtual-machines"

    @property
    def description(self) -> str:
        return "Virtual machine operations."

    @classmethod
    def configure_parser(cls, subparser):
        # Create subcommands
        vm_subparsers = subparser.add_subparsers(dest="vm_operation", help="Virtual machine operations")
        
        # List VMs command
        list_parser = vm_subparsers.add_parser("list", help="List virtual machines in a resource group")
        list_parser.add_argument("--subscription-id", required=True, help="Azure subscription ID")
        list_parser.add_argument("--resource-group", required=True, help="Resource group name")
        list_parser.add_argument("--refresh-cache", action="store_true", help="Refresh the cache")
        list_parser.add_argument("--output", help="Output file to save results (optional)")
        
        # Get VM details command
        details_parser = vm_subparsers.add_parser("get", help="Get details of a virtual machine")
        details_parser.add_argument("--subscription-id", required=True, help="Azure subscription ID")
        details_parser.add_argument("--resource-group", required=True, help="Resource group name")
        details_parser.add_argument("--name", required=True, help="Virtual machine name")
        details_parser.add_argument("--refresh-cache", action="store_true", help="Refresh the cache")
        details_parser.add_argument("--output", help="Output file to save results (optional)")

    def execute(self):
        """Execute the appropriate virtual machine operation based on the subcommand."""
        vm_operation = self.args.get('vm_operation')
        if not vm_operation:
            logger.error("No virtual machine operation specified")
            return

        # Initialize the worker
        vm_worker = VirtualMachinesWorker()

        if vm_operation == "list":
            self._list_virtual_machines(vm_worker)
        elif vm_operation == "get":
            self._get_virtual_machine_details(vm_worker)
        else:
            logger.error(f"Unknown virtual machine operation: {vm_operation}")

    def _list_virtual_machines(self, vm_worker):
        """List virtual machines in a resource group."""
        subscription_id = self.args.get('subscription_id')
        resource_group = self.args.get('resource_group')
        refresh_cache = self.args.get('refresh_cache', False)
        output_file = self.args.get('output')

        logger.debug(f"Listing VMs in subscription {subscription_id}, resource group {resource_group}")
        
        try:
            vms = vm_worker.list_virtual_machines(
                subscription_id=subscription_id,
                resource_group_name=resource_group,
                refresh_cache=refresh_cache
            )
            
            if output_file:
                with open(output_file, 'w') as f:
                    json.dump(vms, f, indent=2)
                print(f"Virtual machines list saved to {output_file}")
            else:
                print(json.dumps(vms, indent=2))
                
            logger.debug(f"Found {len(vms)} VMs in resource group {resource_group}")
            
        except Exception as e:
            logger.error(f"Error listing virtual machines: {e}")
            print(f"Error: {e}")

    def _get_virtual_machine_details(self, vm_worker):
        """Get details of a specific virtual machine."""
        subscription_id = self.args.get('subscription_id')
        resource_group = self.args.get('resource_group')
        vm_name = self.args.get('name')
        refresh_cache = self.args.get('refresh_cache', False)
        output_file = self.args.get('output')

        logger.debug(f"Getting details for VM {vm_name} in subscription {subscription_id}, resource group {resource_group}")
        
        try:
            vm_details = vm_worker.get_virtual_machine_details(
                subscription_id=subscription_id,
                resource_group_name=resource_group,
                vm_name=vm_name,
                refresh_cache=refresh_cache
            )
            
            if output_file:
                with open(output_file, 'w') as f:
                    json.dump(vm_details, f, indent=2)
                print(f"Virtual machine details saved to {output_file}")
            else:
                print(json.dumps(vm_details, indent=2))
                
            logger.debug(f"Successfully retrieved details for VM {vm_name}")
            
        except Exception as e:
            logger.error(f"Error getting virtual machine details: {e}")
            print(f"Error: {e}")