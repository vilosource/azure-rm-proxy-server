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
        """
        pass

    def execute(self, *args, **kwargs):
        """
        Execute the worker's task.
        """
        pass