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

    def execute(self, *args, **kwargs):
        """
        Execute the worker's task.
        """
        pass