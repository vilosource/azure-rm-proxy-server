from .workers.worker_factory import WorkerFactory
from .workers.azurerm_api_worker import AzureRMApiWorker

# Update: Workers should be created in the workers module going forward.

# This change ensures that all worker-related logic is centralized and adheres to the new organizational structure.

# Create the worker factory and register workers
worker_factory = WorkerFactory()
worker_factory.register_worker("azurermapi", AzureRMApiWorker)

# Register a worker for the 'openapi' type
worker_factory.register_worker("openapi", AzureRMApiWorker)

def get_worker_factory() -> WorkerFactory:
    """
    Get the worker factory instance.
    
    Returns:
        The worker factory
    """
    return worker_factory

def get_worker(worker_type: str, **kwargs) -> Worker:
    """
    Get a worker for the specified worker type.
    
    Args:
        worker_type: The worker type identifier
        **kwargs: Arguments to pass to the worker constructor
        
    Returns:
        A worker instance
        
    Raises:
        ValueError: If the worker type is not registered
    """
    return worker_factory.create_worker(worker_type, **kwargs)