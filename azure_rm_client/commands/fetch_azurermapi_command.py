import os
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
class FetchAzureRMApiCommand(BaseCommand):
    """
    Command for fetching Azure RM API data from the server.
    
    Implements the Command Pattern for encapsulating the action of fetching
    and saving Azure RM API data.
    """
    
    def __init__(self, base_url: str, output_file: str, format_type: str = None):
        """
        Initialize the command with required parameters.
        
        Args:
            base_url: The base URL of the API server
            output_file: The file path to save the data to
            format_type: The format type to use (default: None, uses the default formatter)
        """
        self.base_url = base_url
        self.output_file = output_file
        self.format_type = format_type
    
    @property
    def name(self) -> str:
        """
        Get the name of the command.
        
        Returns:
            Name of the command
        """
        return "fetch-azurermapi"
    
    @property
    def description(self) -> str:
        """
        Get the description of the command.
        
        Returns:
            Description of the command
        """
        return "Fetch Azure RM API data from the server"
    
    @classmethod
    def configure_parser(cls, subparser: argparse.ArgumentParser) -> None:
        """
        Configure the argument parser for this command.
        
        Args:
            subparser: The subparser to configure
        """
        subparser.add_argument(
            "--output", 
            default="./openapi.json", 
            help="Output file path (default: ./openapi.json)"
        )
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
            'output': 'output_file',
            'format': 'format_type'
        }
    
    def execute(self) -> bool:
        """
        Execute the command to fetch and save Azure RM API data.
        
        Returns:
            True if the command executed successfully, False otherwise
        """
        logger.info(f"Executing {self.name} command...")
        
        try:
            # Create REST client
            http_client = RequestsHttpClient()
            response_handler = JsonResponseHandler()
            rest_client = RestClient(self.base_url, http_client, response_handler)
            
            # Create worker with the correct endpoint
            worker = get_worker("openapi", rest_client=rest_client)
            
            # Fetch data
            data = worker.execute()
            if data is None:
                logger.error("Failed to fetch Azure RM API data")
                return False
            
            # Save data to file
            if not worker.save_to_file(data, self.output_file):
                logger.error("Failed to save Azure RM API data to file")
                return False
            
            # Format and display data if a format type is specified
            if self.format_type:
                formatter = get_formatter(self.format_type)
                formatted_output = formatter.format_data(data)
                print(formatted_output)
            
            logger.info("Command executed successfully")
            return True
        except Exception as e:
            logger.error(f"Error executing command: {e}")
            return False