import os
import json
import logging
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
from azure_rm_client.client import RestClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Worker(ABC):
    """
    Abstract base class for workers following the Single Responsibility Principle.
    Each worker is responsible for a specific task.
    """
    
    @abstractmethod
    def execute(self, *args, **kwargs):
        """
        Execute the worker's task.
        
        Args:
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments
            
        Returns:
            Result of the worker's task
        """
        pass


class AzureRMApiWorker(Worker):
    """
    Worker for fetching and handling Azure RM API data.
    """
    
    def __init__(self, rest_client: RestClient):
        """
        Initialize the worker with a REST client.
        
        Args:
            rest_client: A RestClient instance for making API requests
        """
        self.rest_client = rest_client
    
    def execute(self, endpoint: str = "openapi.json") -> Optional[Dict[str, Any]]:
        """
        Execute the worker's task to fetch Azure RM API data.
        
        Args:
            endpoint: The API endpoint to fetch data from (default: "openapi.json")
            
        Returns:
            Azure RM API data or None if the request fails
        """
        logger.info(f"Fetching Azure RM API data from endpoint: {endpoint}")
        return self.rest_client.get(endpoint)
    
    def save_to_file(self, data: Dict[str, Any], file_path: str) -> bool:
        """
        Save Azure RM API data to a file.
        
        Args:
            data: The data to save
            file_path: The path to save the data to
            
        Returns:
            True if the data was saved successfully, False otherwise
        """
        try:
            with open(file_path, "w") as f:
                json.dump(data, f, indent=2)
            logger.info(f"Azure RM API data saved to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save Azure RM API data to {file_path}: {e}")
            return False


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