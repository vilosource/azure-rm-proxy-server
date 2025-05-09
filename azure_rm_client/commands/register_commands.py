"""Register all commands with the CommandRegistry."""

from . import CommandRegistry
from .subscriptions_command import SubscriptionsCommand
from .resource_groups_command import ResourceGroupsCommand
from .resource_group_command import ResourceGroupCommand
from .resource_group_commands import CreateResourceGroupCommand, DeleteResourceGroupCommand
from .virtual_machines_command import VirtualMachinesCommand
from .vm_connectivity_command import VMConnectivityCommand
from .vm_shortcuts_command import VMShortcutsCommand
from .vm_hostnames_command import VMHostnamesCommand
from .vm_reports_command import VMReportsCommand
from .route_tables_command import RouteTablesCommand
from .list_resources_command import ListResourcesCommand
from .vnet_peering_report_command import VNetPeeringReportCommand
from .resource_command import ResourceCommand  # Import the ResourceCommand

# Register top-level commands
CommandRegistry.register(SubscriptionsCommand)
CommandRegistry.register(ResourceGroupsCommand)
CommandRegistry.register(VirtualMachinesCommand)
CommandRegistry.register(VMConnectivityCommand)
CommandRegistry.register(VMShortcutsCommand)
CommandRegistry.register(VMHostnamesCommand)
CommandRegistry.register(VMReportsCommand)
CommandRegistry.register(RouteTablesCommand)
CommandRegistry.register(ListResourcesCommand)
CommandRegistry.register(VNetPeeringReportCommand)  # Register our new command
CommandRegistry.register(ResourceCommand)  # Register the ResourceCommand

# Register subcommands
CommandRegistry.register_subcommand("resource-groups")(ResourceGroupCommand)
CommandRegistry.register_subcommand("resource-group")(CreateResourceGroupCommand)
CommandRegistry.register_subcommand("resource-group")(DeleteResourceGroupCommand)
