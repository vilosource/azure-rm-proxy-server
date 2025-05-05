# Initialize the azure_rm_client.workers module

from .azurerm_api_worker import AzureRMApiWorker
from .resource_groups_worker import ResourceGroupsWorker
from .route_tables_worker import RouteTablesWorker
from .subscriptions_worker import SubscriptionsWorker
from .virtual_machines_worker import VirtualMachinesWorker
from .vm_hostnames_worker import VMHostnamesWorker
from .vm_reports_worker import VMReportsWorker
from .vm_shortcuts_worker import VMShortcutsWorker
from .worker_base import WorkerBase
from .worker_factory import WorkerFactory

# Create a global instance of the worker factory
_worker_factory = WorkerFactory()

# Register all worker types
_worker_factory.register_worker("azurerm_api", AzureRMApiWorker)
_worker_factory.register_worker("resource_groups", ResourceGroupsWorker)
_worker_factory.register_worker("route_tables", RouteTablesWorker)
_worker_factory.register_worker("subscriptions", SubscriptionsWorker)
_worker_factory.register_worker("virtual_machines", VirtualMachinesWorker)
_worker_factory.register_worker("vm_hostnames", VMHostnamesWorker)
_worker_factory.register_worker("vm_reports", VMReportsWorker)
_worker_factory.register_worker("vm_shortcuts", VMShortcutsWorker)

def get_worker(worker_type: str, **kwargs):
    """
    Get a worker instance for the specified worker type.
    
    Args:
        worker_type: The worker type identifier
        **kwargs: Arguments to pass to the worker constructor
            
    Returns:
        An instance of the worker for the specified worker type
            
    Raises:
        ValueError: If the worker type is not registered
    """
    return _worker_factory.create_worker(worker_type, **kwargs)

__all__ = [
    "AzureRMApiWorker",
    "ResourceGroupsWorker",
    "RouteTablesWorker",
    "SubscriptionsWorker",
    "VirtualMachinesWorker",
    "VMHostnamesWorker",
    "VMReportsWorker",
    "VMShortcutsWorker",
    "WorkerBase",
    "WorkerFactory",
    "get_worker",  # Added the get_worker function to __all__
]