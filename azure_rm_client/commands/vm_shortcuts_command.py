from azure_rm_client.commands.base_command import BaseCommand
from azure_rm_client.commands import CommandRegistry
from azure_rm_client.workers.vm_shortcuts_worker import VMShortcutsWorker
import logging
import json

logger = logging.getLogger(__name__)

@CommandRegistry.register
class VMShortcutsCommand(BaseCommand):
    @property
    def name(self) -> str:
        return "vm-shortcuts"

    @property
    def description(self) -> str:
        return "VM shortcut operations across subscriptions and resource groups."

    @classmethod
    def configure_parser(cls, subparser):
        # Create subcommands
        vm_subparsers = subparser.add_subparsers(dest="vm_shortcut_operation", help="VM shortcut operations")
        
        # List all VMs command
        list_parser = vm_subparsers.add_parser("list-all", help="List all VMs across all subscriptions and resource groups")
        list_parser.add_argument("--refresh-cache", action="store_true", help="Refresh the cache")
        list_parser.add_argument("--output", help="Output file to save results (optional)")
        
        # Get VM by name command
        get_parser = vm_subparsers.add_parser("get-by-name", help="Find VM by name across all subscriptions and resource groups")
        get_parser.add_argument("--name", required=True, help="Virtual machine name")
        get_parser.add_argument("--refresh-cache", action="store_true", help="Refresh the cache")
        get_parser.add_argument("--debug", action="store_true", help="Enable debug logging")
        get_parser.add_argument("--output", help="Output file to save results (optional)")

    def execute(self):
        """Execute the appropriate VM shortcut operation based on the subcommand."""
        vm_operation = self.args.get('vm_shortcut_operation')
        if not vm_operation:
            logger.error("No VM shortcut operation specified")
            return

        # Initialize the worker
        vm_shortcuts_worker = VMShortcutsWorker()

        if vm_operation == "list-all":
            self._list_all_vms(vm_shortcuts_worker)
        elif vm_operation == "get-by-name":
            self._get_vm_by_name(vm_shortcuts_worker)
        else:
            logger.error(f"Unknown VM shortcut operation: {vm_operation}")

    def _list_all_vms(self, vm_shortcuts_worker):
        """List all virtual machines across all subscriptions and resource groups."""
        refresh_cache = self.args.get('refresh_cache', False)
        output_file = self.args.get('output')

        logger.debug("Listing all VMs across all subscriptions and resource groups")
        
        try:
            all_vms = vm_shortcuts_worker.list_all_virtual_machines(
                refresh_cache=refresh_cache
            )
            
            if output_file:
                with open(output_file, 'w') as f:
                    json.dump(all_vms, f, indent=2)
                print(f"All VMs list saved to {output_file}")
            else:
                print(json.dumps(all_vms, indent=2))
                
            logger.debug(f"Found {len(all_vms)} VMs across all subscriptions and resource groups")
            
        except Exception as e:
            logger.error(f"Error listing all VMs: {e}")
            print(f"Error: {e}")

    def _get_vm_by_name(self, vm_shortcuts_worker):
        """Find a VM by name across all subscriptions and resource groups."""
        vm_name = self.args.get('name')
        refresh_cache = self.args.get('refresh_cache', False)
        debug = self.args.get('debug', False)
        output_file = self.args.get('output')

        logger.debug(f"Finding VM with name {vm_name} across all subscriptions and resource groups")
        
        try:
            vm_details = vm_shortcuts_worker.get_vm_by_name(
                vm_name=vm_name,
                refresh_cache=refresh_cache,
                debug=debug
            )
            
            if output_file:
                with open(output_file, 'w') as f:
                    json.dump(vm_details, f, indent=2)
                print(f"VM details saved to {output_file}")
            else:
                print(json.dumps(vm_details, indent=2))
                
            logger.debug(f"Successfully found VM with name {vm_name}")
            
        except Exception as e:
            logger.error(f"Error finding VM with name {vm_name}: {e}")
            print(f"Error: {e}")