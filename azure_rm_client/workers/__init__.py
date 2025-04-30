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
]