from .worker_base import Worker

class ResourceGroupsWorker(Worker):
    """
    Worker for handling operations related to resource groups.
    """
    def list_resource_groups(self, subscription_id: str, refresh_cache: bool = False):
        """
        List resource groups for a specific subscription.
        
        Args:
            subscription_id (str): The ID of the subscription.
            refresh_cache (bool): Whether to bypass cache and fetch fresh data.
        """
        pass

    def execute(self, subscription_id: str, refresh_cache: bool = False):
        """
        Execute the worker's task to list resource groups for a specific subscription.

        Args:
            subscription_id (str): The ID of the subscription.
            refresh_cache (bool): Whether to bypass cache and fetch fresh data.

        Returns:
            list: A list of resource groups.
        """
        import requests
        import logging

        logger = logging.getLogger(__name__)
        base_url = "http://localhost:8000"  # Replace with actual base URL if different
        endpoint = f"{base_url}/api/subscriptions/{subscription_id}/resource-groups/"
        params = {"refresh-cache": refresh_cache}

        try:
            logger.debug(f"Fetching resource groups for subscription {subscription_id} with refresh_cache={refresh_cache}")
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            resource_groups = response.json()
            logger.debug(f"Fetched {len(resource_groups)} resource groups for subscription {subscription_id}")
            return resource_groups
        except requests.RequestException as e:
            logger.error(f"Failed to fetch resource groups for subscription {subscription_id}: {e}")
            raise