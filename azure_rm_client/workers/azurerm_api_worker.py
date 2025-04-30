import json
from typing import Dict, Any, Optional
from azure_rm_client.client import RestClient
from .worker_base import Worker

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