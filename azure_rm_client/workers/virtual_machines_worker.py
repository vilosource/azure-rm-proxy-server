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

        Returns:
            list: A list of virtual machines.
        """
        import requests
        import logging

        logger = logging.getLogger(__name__)
        base_url = "http://localhost:8000"  # Replace with actual base URL if different
        endpoint = f"{base_url}/api/subscriptions/{subscription_id}/resource-groups/{resource_group_name}/virtual-machines/"
        params = {"refresh-cache": refresh_cache}

        try:
            logger.debug(f"Fetching virtual machines for subscription {subscription_id}, resource group {resource_group_name} with refresh_cache={refresh_cache}")
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            virtual_machines = response.json()
            logger.debug(f"Fetched {len(virtual_machines)} virtual machines for resource group {resource_group_name}")
            return virtual_machines
        except requests.RequestException as e:
            logger.error(f"Failed to fetch virtual machines for resource group {resource_group_name}: {e}")
            raise

    def get_virtual_machine_details(self, subscription_id: str, resource_group_name: str, vm_name: str, refresh_cache: bool = False):
        """
        Get details of a specific virtual machine.

        Args:
            subscription_id (str): The ID of the subscription.
            resource_group_name (str): The name of the resource group.
            vm_name (str): The name of the virtual machine.
            refresh_cache (bool): Whether to bypass cache and fetch fresh data.

        Returns:
            dict: Details of the virtual machine.
        """
        import requests
        import logging

        logger = logging.getLogger(__name__)
        base_url = "http://localhost:8000"  # Replace with actual base URL if different
        endpoint = f"{base_url}/api/subscriptions/{subscription_id}/resource-groups/{resource_group_name}/virtual-machines/{vm_name}"
        params = {"refresh-cache": refresh_cache}

        try:
            logger.debug(f"Fetching details for VM {vm_name} in subscription {subscription_id}, resource group {resource_group_name} with refresh_cache={refresh_cache}")
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            vm_details = response.json()
            logger.debug("Fetched details for VM {vm_name}")
            return vm_details
        except requests.RequestException as e:
            logger.error(f"Failed to fetch details for VM {vm_name}: {e}")
            raise

    def execute(self, *args, **kwargs):
        """
        Execute the worker's task.
        """
        pass