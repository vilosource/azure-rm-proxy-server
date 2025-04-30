from .worker_base import Worker

class VirtualMachinesWorker(Worker):
    """
    Worker for handling operations related to virtual machines.
    """
    def list_virtual_machines(self, subscription_id: str, resource_group_name: str, refresh_cache: bool = False):
        """
        List virtual machines in a specific resource group.
        
        Args:
            subscription_id (str): The ID of the subscription.
            resource_group_name (str): The name of the resource group.
            refresh_cache (bool): Whether to bypass cache and fetch fresh data.
        """
        pass

    def get_virtual_machine_details(self, subscription_id: str, resource_group_name: str, vm_name: str, refresh_cache: bool = False):
        """
        Get details of a specific virtual machine.
        
        Args:
            subscription_id (str): The ID of the subscription.
            resource_group_name (str): The name of the resource group.
            vm_name (str): The name of the virtual machine.
            refresh_cache (bool): Whether to bypass cache and fetch fresh data.
        """
        pass

    def execute(self, *args, **kwargs):
        """
        Execute the worker's task.
        """
        pass