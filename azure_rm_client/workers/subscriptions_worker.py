import logging
import requests
from azure.identity import DefaultAzureCredential
from azure.mgmt.resource import SubscriptionClient
from .worker_base import Worker

logger = logging.getLogger(__name__)

class SubscriptionsWorker(Worker):
    """
    Worker for handling operations related to subscriptions.
    """
    def __init__(self):
        super().__init__()
        self.credential = DefaultAzureCredential()
        self.client = SubscriptionClient(self.credential)

    def list_subscriptions(self, refresh_cache: bool = False):
        """
        List all subscriptions.

        Args:
            refresh_cache (bool): Whether to bypass cache and fetch fresh data.

        Returns:
            list: A list of subscription dictionaries.
        """
        logger.debug("list_subscriptions called with refresh_cache=%s", refresh_cache)

        if not refresh_cache:
            logger.debug("Cache miss: Fetching subscriptions from API")

        # Make an API call to fetch subscriptions
        base_url = "http://localhost:8000"  # Replace with actual base URL if different
        endpoint = f"{base_url}/api/subscriptions/"
        params = {"refresh-cache": refresh_cache}

        try:
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            subscriptions = response.json()

            logger.debug("Fetched %d subscriptions from API", len(subscriptions))

            return subscriptions
        except requests.RequestException as e:
            logger.error("Error fetching subscriptions from API: %s", e)
            raise

    def execute(self, *args, **kwargs):
        """
        Execute the worker's task.

        Args:
            *args: Positional arguments.
            **kwargs: Keyword arguments.

        Returns:
            Any: The result of the worker's task.
        """
        logger.debug("execute called with args=%s, kwargs=%s", args, kwargs)
        refresh_cache = kwargs.get("refresh_cache", False)
        result = self.list_subscriptions(refresh_cache=refresh_cache)
        logger.debug("execute completed with result: %s", result)
        return result