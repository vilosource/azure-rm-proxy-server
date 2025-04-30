from .worker_base import Worker

class VMReportsWorker(Worker):
    """
    Worker for handling operations related to VM reports.
    """
    def generate_vm_report(self, refresh_cache: bool = False):
        """
        Generate a comprehensive report of all virtual machines across all subscriptions.
        
        Args:
            refresh_cache (bool): Whether to bypass cache and fetch fresh data.
        """
        pass

    def execute(self, *args, **kwargs):
        """
        Execute the worker's task.
        """
        pass