from .worker_base import Worker
import requests
import logging

class VMReportsWorker(Worker):
    """
    Worker for handling operations related to VM reports.
    """
    def generate_vm_report(self, refresh_cache: bool = False):
        """
        Generate a comprehensive report of all virtual machines across all subscriptions.

        Args:
            refresh_cache (bool): Whether to bypass cache and fetch fresh data.

        Returns:
            list: A list of virtual machine reports.
        """
        logger = logging.getLogger(__name__)
        base_url = "http://localhost:8000"  # Replace with actual base URL if different
        endpoint = f"{base_url}/api/reports/virtual-machines"
        params = {"refresh-cache": refresh_cache}

        try:
            logger.debug(f"Fetching VM report with refresh_cache={refresh_cache}")
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            vm_report = response.json()
            logger.debug("Fetched VM report")
            return vm_report
        except requests.RequestException as e:
            logger.error(f"Failed to fetch VM report: {e}")
            raise

    def execute(self, *args, **kwargs):
        """
        Execute the worker's task to generate a VM report.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            list: A list of virtual machine reports.
        """
        refresh_cache = kwargs.get("refresh_cache", False)
        return self.generate_vm_report(refresh_cache=refresh_cache)