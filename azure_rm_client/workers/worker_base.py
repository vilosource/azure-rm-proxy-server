import logging
from abc import ABC, abstractmethod

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

# Alias Worker as WorkerBase for backward compatibility
WorkerBase = Worker