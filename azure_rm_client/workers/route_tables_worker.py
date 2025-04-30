from .worker_base import Worker

class RouteTablesWorker(Worker):
    """
    Worker for handling operations related to route tables.
    """
    def list_route_tables(self, subscription_id: str, refresh_cache: bool = False):
        """
        List all route tables for a specific subscription.
        
        Args:
            subscription_id (str): The ID of the subscription.
            refresh_cache (bool): Whether to bypass cache and fetch fresh data.
        """
        pass

    def execute(self, *args, **kwargs):
        """
        Execute the worker's task.
        """
        pass