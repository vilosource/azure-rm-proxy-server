from .worker_base import Worker

class WorkerFactory:
    """
    Factory for creating worker instances.
    This follows the Factory Pattern to decouple worker creation from usage.
    """
    
    def __init__(self):
        self._workers = {}
    
    def register_worker(self, worker_type: str, worker_class):
        """
        Register a worker class for a specific worker type.
        
        Args:
            worker_type: The worker type identifier
            worker_class: The worker class to register
        """
        self._workers[worker_type] = worker_class
    
    def create_worker(self, worker_type: str, **kwargs) -> Worker:
        """
        Create a worker instance for the specified worker type.
        
        Args:
            worker_type: The worker type identifier
            **kwargs: Arguments to pass to the worker constructor
            
        Returns:
            An instance of the worker for the specified worker type
            
        Raises:
            ValueError: If the worker type is not registered
        """
        worker_class = self._workers.get(worker_type)
        if worker_class is None:
            raise ValueError(f"No worker registered for worker type: {worker_type}")
        return worker_class(**kwargs)