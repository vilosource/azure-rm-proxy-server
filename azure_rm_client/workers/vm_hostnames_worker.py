from .worker_base import Worker

class VMHostnamesWorker(Worker):
    """
    Worker for handling operations related to VM hostnames.
    """
    def list_vm_hostnames(self, subscription_id: str = None, refresh_cache: bool = False):
        """
        List VM names and their hostnames from tags.

        Args:
            subscription_id (str, optional): The ID of the subscription to filter by.
            refresh_cache (bool): Whether to bypass cache and fetch fresh data.

        Returns:
            list: A list of VM names and their hostnames.
        """
        import requests
        import logging

        logger = logging.getLogger(__name__)
        base_url = "http://localhost:8000"  # Replace with actual base URL if different
        endpoint = f"{base_url}/api/subscriptions/hostnames/"
        params = {"subscription-id": subscription_id, "refresh-cache": refresh_cache}

        try:
            logger.debug(f"Fetching VM hostnames with subscription_id={subscription_id} and refresh_cache={refresh_cache}")
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            vm_hostnames = response.json()
            logger.debug(f"Fetched VM hostnames: {vm_hostnames}")
            return vm_hostnames
        except requests.RequestException as e:
            logger.error(f"Failed to fetch VM hostnames: {e}")
            raise

    def execute(self, output_dir: str, subscription_id: str = None, refresh_cache: bool = False):
        """
        Execute the worker's task to fetch VM hostnames and save them to a file.

        Args:
            output_dir (str): The directory to save the VM hostnames file.
            subscription_id (str, optional): The ID of the subscription to filter by.
            refresh_cache (bool): Whether to bypass cache and fetch fresh data.
        """
        import os
        import json

        vm_hostnames = self.list_vm_hostnames(subscription_id=subscription_id, refresh_cache=refresh_cache)

        output_file = os.path.join(output_dir, "vm-name_hostname_list.json")
        with open(output_file, "w") as file:
            json.dump(vm_hostnames, file, indent=2)

        logging.getLogger(__name__).debug(f"VM hostnames saved to {output_file}")