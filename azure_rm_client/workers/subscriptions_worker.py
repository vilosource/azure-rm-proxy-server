from .worker_base import Worker

class SubscriptionsWorker(Worker):
    """
    Worker for handling operations related to subscriptions.
    """
    def list_subscriptions(self, refresh_cache: bool = False):
        """
        List all subscriptions.
        
        Args:
            refresh_cache (bool): Whether to bypass cache and fetch fresh data.
        """
        pass

    def execute(self, *args, **kwargs):
        """
        Execute the worker's task.
        """
        pass