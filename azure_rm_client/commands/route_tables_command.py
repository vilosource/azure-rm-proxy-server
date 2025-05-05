from azure_rm_client.commands.base_command import BaseCommand
from azure_rm_client.commands import CommandRegistry
from azure_rm_client.workers.route_tables_worker import RouteTablesWorker
import logging
import json

logger = logging.getLogger(__name__)

# Constants for commonly used strings
HELP_SUBSCRIPTION_ID = "Azure subscription ID"
HELP_REFRESH_CACHE = "Refresh the cache"
HELP_OUTPUT_FILE = "Output file to save results (optional)"
HELP_RESOURCE_GROUP = "Resource group name"

@CommandRegistry.register
class RouteTablesCommand(BaseCommand):
    @property
    def name(self) -> str:
        return "route-tables"

    @property
    def description(self) -> str:
        return "Route table operations."

    @classmethod
    def configure_parser(cls, subparser):
        # Create subcommands
        rt_subparsers = subparser.add_subparsers(dest="rt_operation", help="Route table operations")
        
        # List route tables command
        list_parser = rt_subparsers.add_parser("list", help="List route tables in a subscription")
        list_parser.add_argument("--subscription-id", required=True, help=HELP_SUBSCRIPTION_ID)
        list_parser.add_argument("--refresh-cache", action="store_true", help=HELP_REFRESH_CACHE)
        list_parser.add_argument("--output", help=HELP_OUTPUT_FILE)
        
        # Get route table details command
        details_parser = rt_subparsers.add_parser("get", help="Get details of a route table")
        details_parser.add_argument("--subscription-id", required=True, help=HELP_SUBSCRIPTION_ID)
        details_parser.add_argument("--resource-group", required=True, help=HELP_RESOURCE_GROUP)
        details_parser.add_argument("--name", required=True, help="Route table name")
        details_parser.add_argument("--refresh-cache", action="store_true", help=HELP_REFRESH_CACHE)
        details_parser.add_argument("--output", help=HELP_OUTPUT_FILE)
        
        # Get VM effective routes command
        vm_routes_parser = rt_subparsers.add_parser("vm-routes", help="Get effective routes for a virtual machine")
        vm_routes_parser.add_argument("--subscription-id", required=True, help=HELP_SUBSCRIPTION_ID)
        vm_routes_parser.add_argument("--resource-group", required=True, help=HELP_RESOURCE_GROUP)
        vm_routes_parser.add_argument("--vm-name", required=True, help="Virtual machine name")
        vm_routes_parser.add_argument("--refresh-cache", action="store_true", help=HELP_REFRESH_CACHE)
        vm_routes_parser.add_argument("--output", help=HELP_OUTPUT_FILE)
        
        # Get NIC effective routes command
        nic_routes_parser = rt_subparsers.add_parser("nic-routes", help="Get effective routes for a network interface")
        nic_routes_parser.add_argument("--subscription-id", required=True, help=HELP_SUBSCRIPTION_ID)
        nic_routes_parser.add_argument("--resource-group", required=True, help=HELP_RESOURCE_GROUP)
        nic_routes_parser.add_argument("--nic-name", required=True, help="Network interface name")
        nic_routes_parser.add_argument("--refresh-cache", action="store_true", help=HELP_REFRESH_CACHE)
        nic_routes_parser.add_argument("--output", help=HELP_OUTPUT_FILE)

    def execute(self):
        """Execute the appropriate route table operation based on the subcommand."""
        rt_operation = self.args.get('rt_operation')
        if not rt_operation:
            logger.error("No route table operation specified")
            return

        # Initialize the worker
        rt_worker = RouteTablesWorker()

        if rt_operation == "list":
            self._list_route_tables(rt_worker)
        elif rt_operation == "get":
            self._get_route_table_details(rt_worker)
        elif rt_operation == "vm-routes":
            self._get_vm_effective_routes(rt_worker)
        elif rt_operation == "nic-routes":
            self._get_nic_effective_routes(rt_worker)
        else:
            logger.error(f"Unknown route table operation: {rt_operation}")

    def _list_route_tables(self, rt_worker):
        """List route tables in a subscription."""
        subscription_id = self.args.get('subscription_id')
        refresh_cache = self.args.get('refresh_cache', False)
        output_file = self.args.get('output')

        logger.debug(f"Listing route tables in subscription {subscription_id}")
        
        try:
            route_tables = rt_worker.list_route_tables(
                subscription_id=subscription_id,
                refresh_cache=refresh_cache
            )
            
            if output_file:
                with open(output_file, 'w') as f:
                    json.dump(route_tables, f, indent=2)
                print(f"Route tables list saved to {output_file}")
            else:
                print(json.dumps(route_tables, indent=2))
                
            logger.debug(f"Found {len(route_tables)} route tables in subscription {subscription_id}")
            
        except Exception as e:
            logger.error(f"Error listing route tables: {e}")
            print(f"Error: {e}")

    def _get_route_table_details(self, rt_worker):
        """Get details of a specific route table."""
        subscription_id = self.args.get('subscription_id')
        resource_group = self.args.get('resource_group')
        route_table_name = self.args.get('name')
        refresh_cache = self.args.get('refresh_cache', False)
        output_file = self.args.get('output')

        logger.debug(f"Getting details for route table {route_table_name} in subscription {subscription_id}")
        
        try:
            route_table_details = rt_worker.get_route_table_details(
                subscription_id=subscription_id,
                resource_group_name=resource_group,
                route_table_name=route_table_name,
                refresh_cache=refresh_cache
            )
            
            if output_file:
                with open(output_file, 'w') as f:
                    json.dump(route_table_details, f, indent=2)
                print(f"Route table details saved to {output_file}")
            else:
                print(json.dumps(route_table_details, indent=2))
                
            logger.debug(f"Successfully retrieved details for route table {route_table_name}")
            
        except Exception as e:
            logger.error(f"Error getting route table details: {e}")
            print(f"Error: {e}")

    def _get_vm_effective_routes(self, rt_worker):
        """Get effective routes for a specific virtual machine."""
        subscription_id = self.args.get('subscription_id')
        resource_group = self.args.get('resource_group')
        vm_name = self.args.get('vm_name')
        refresh_cache = self.args.get('refresh_cache', False)
        output_file = self.args.get('output')

        logger.debug(f"Getting effective routes for VM {vm_name} in subscription {subscription_id}")
        
        try:
            vm_routes = rt_worker.get_vm_effective_routes(
                subscription_id=subscription_id,
                resource_group_name=resource_group,
                vm_name=vm_name,
                refresh_cache=refresh_cache
            )
            
            if output_file:
                with open(output_file, 'w') as f:
                    json.dump(vm_routes, f, indent=2)
                print(f"VM effective routes saved to {output_file}")
            else:
                print(json.dumps(vm_routes, indent=2))
                
            logger.debug(f"Successfully retrieved effective routes for VM {vm_name}")
            
        except Exception as e:
            logger.error(f"Error getting VM effective routes: {e}")
            print(f"Error: {e}")

    def _get_nic_effective_routes(self, rt_worker):
        """Get effective routes for a specific network interface."""
        subscription_id = self.args.get('subscription_id')
        resource_group = self.args.get('resource_group')
        nic_name = self.args.get('nic_name')
        refresh_cache = self.args.get('refresh_cache', False)
        output_file = self.args.get('output')

        logger.debug(f"Getting effective routes for NIC {nic_name} in subscription {subscription_id}")
        
        try:
            nic_routes = rt_worker.get_nic_effective_routes(
                subscription_id=subscription_id,
                resource_group_name=resource_group,
                nic_name=nic_name,
                refresh_cache=refresh_cache
            )
            
            if output_file:
                with open(output_file, 'w') as f:
                    json.dump(nic_routes, f, indent=2)
                print(f"NIC effective routes saved to {output_file}")
            else:
                print(json.dumps(nic_routes, indent=2))
                
            logger.debug(f"Successfully retrieved effective routes for NIC {nic_name}")
            
        except Exception as e:
            logger.error(f"Error getting NIC effective routes: {e}")
            print(f"Error: {e}")