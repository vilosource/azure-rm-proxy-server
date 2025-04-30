import logging
import argparse
from azure_rm_client.commands.base_command import BaseCommand
from azure_rm_client.commands import CommandRegistry
from azure_rm_client.workers import get_worker
from azure_rm_client.client import RestClient, RequestsHttpClient, JsonResponseHandler
from azure_rm_client.formatters import get_formatter, get_available_formats

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@CommandRegistry.register
class ListResourcesCommand(BaseCommand):
    """
    Command for listing available resources from the Azure RM API.
    
    Implements the Command Pattern for encapsulating the action of fetching
    and displaying available resources.
    """
    
    def __init__(self, base_url: str, format_type: str = None):
        """
        Initialize the command with required parameters.
        
        Args:
            base_url: The base URL of the API server
            format_type: The format type to use (default: None, uses the default formatter)
        """
        self.base_url = base_url
        self.format_type = format_type
    
    @property
    def name(self) -> str:
        """
        Get the name of the command.
        
        Returns:
            Name of the command
        """
        return "list-resources"
    
    @property
    def description(self) -> str:
        """
        Get the description of the command.
        
        Returns:
            Description of the command
        """
        return "List available resources from the Azure RM API"
    
    @classmethod
    def configure_parser(cls, subparser: argparse.ArgumentParser) -> None:
        """
        Configure the argument parser for this command.
        
        Args:
            subparser: The subparser to configure
        """
        subparser.add_argument(
            "--format", 
            choices=get_available_formats(), 
            help="Output format"
        )
    
    @classmethod
    def get_param_mapping(cls) -> dict:
        """
        Get a mapping from CLI argument names to constructor parameter names.
        
        Returns:
            A dictionary mapping CLI argument names to constructor parameter names
        """
        return {
            'base_url': 'base_url',
            'format': 'format_type'
        }
    
    def execute(self) -> bool:
        """
        Execute the command to list available resources.
        
        Returns:
            True if the command executed successfully, False otherwise
        """
        logger.info(f"Executing {self.name} command...")
        
        try:
            # Create REST client
            http_client = RequestsHttpClient()
            response_handler = JsonResponseHandler()
            rest_client = RestClient(self.base_url, http_client, response_handler)
            
            # Fetch available resources
            resources = rest_client.get("resources")
            if resources is None:
                logger.error("Failed to fetch available resources")
                return False
            
            # Format and display the resources
            formatter = get_formatter(self.format_type)
            formatted_output = formatter.format_data(resources)
            print(formatted_output)
            
            logger.info("Command executed successfully")
            return True
        except Exception as e:
            logger.error(f"Error executing command: {e}")
            return False