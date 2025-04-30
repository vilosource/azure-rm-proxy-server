from abc import ABC, abstractmethod
import requests
import logging
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HttpClientInterface(ABC):
    """Interface for HTTP clients following the Interface Segregation Principle."""
    
    @abstractmethod
    def request(self, method: str, url: str, **kwargs) -> Any:
        """
        Make an HTTP request.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            url: The URL to make the request to
            **kwargs: Additional arguments for the request
            
        Returns:
            Response object
        """
        pass


class RequestsHttpClient(HttpClientInterface):
    """Concrete implementation of HttpClientInterface using the requests library."""
    
    def request(self, method: str, url: str, **kwargs) -> requests.Response:
        """
        Make an HTTP request using the requests library.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            url: The URL to make the request to
            **kwargs: Additional arguments for the request
            
        Returns:
            Response from the requests library
        """
        return requests.request(method, url, **kwargs)


class ResponseHandler(ABC):
    """Interface for handling responses following the Single Responsibility Principle."""
    
    @abstractmethod
    def handle_response(self, response: Any) -> Dict[str, Any]:
        """
        Handle a response from an HTTP request.
        
        Args:
            response: Response from an HTTP request
            
        Returns:
            Processed response data
        """
        pass


class JsonResponseHandler(ResponseHandler):
    """Concrete implementation of ResponseHandler for JSON responses."""
    
    def handle_response(self, response: requests.Response) -> Optional[Dict[str, Any]]:
        """
        Handle a JSON response from an HTTP request.
        
        Args:
            response: Response from an HTTP request
            
        Returns:
            JSON data from the response or None if an error occurs
        """
        try:
            response.raise_for_status()
            return response.json()
        except (requests.exceptions.RequestException, ValueError) as e:
            logger.error(f"Error handling response: {e}")
            return None


class RestClient:
    """
    Client for making REST API requests.
    
    This class follows the Dependency Inversion Principle by depending on
    abstractions (HttpClientInterface, ResponseHandler) rather than concrete implementations.
    """
    
    def __init__(self, base_url: str, http_client: HttpClientInterface, response_handler: ResponseHandler):
        """
        Initialize the RestClient.
        
        Args:
            base_url: The base URL for the API
            http_client: An implementation of HttpClientInterface
            response_handler: An implementation of ResponseHandler
        """
        self.base_url = base_url
        self.http_client = http_client
        self.response_handler = response_handler
    
    def request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Make a request to the specified API endpoint.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: The API endpoint to make the request to
            **kwargs: Additional arguments for the request
            
        Returns:
            Processed response data
        """
        url = f"{self.base_url}/{endpoint}"
        try:
            response = self.http_client.request(method, url, **kwargs)
            return self.response_handler.handle_response(response)
        except Exception as e:
            logger.error(f"Error making request to {url}: {e}")
            return None
    
    def get(self, endpoint: str, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Make a GET request to the specified API endpoint.
        
        Args:
            endpoint: The API endpoint to make the request to
            **kwargs: Additional arguments for the request
            
        Returns:
            Processed response data
        """
        return self.request("GET", endpoint, **kwargs)
    
    def post(self, endpoint: str, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Make a POST request to the specified API endpoint.
        
        Args:
            endpoint: The API endpoint to make the request to
            **kwargs: Additional arguments for the request
            
        Returns:
            Processed response data
        """
        return self.request("POST", endpoint, **kwargs)
    
    # Additional methods for other HTTP methods (PUT, DELETE, etc.) can be added here