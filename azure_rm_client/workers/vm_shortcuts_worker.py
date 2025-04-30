from .worker_base import Worker

class VMShortcutsWorker(Worker):
    """
    Worker for handling VM shortcut operations.
    """
    def list_all_virtual_machines(self, refresh_cache: bool = False):
        """
        List all virtual machines across all subscriptions and resource groups.
        
        Args:
            refresh_cache (bool): Whether to bypass cache and fetch fresh data.
        """
        pass

    def get_vm_by_name(self, vm_name: str, refresh_cache: bool = False, debug: bool = False):
        """
        Find a virtual machine by name across all subscriptions and resource groups.
        
        Args:
            vm_name (str): The name of the virtual machine.
            refresh_cache (bool): Whether to bypass cache and fetch fresh data.
            debug (bool): Enable extra debug logging.
        """
        pass

    def execute(self, *args, **kwargs):
        """
        Execute the worker's task.
        """
        pass