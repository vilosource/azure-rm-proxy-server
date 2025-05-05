import logging
import argparse
from typing import Dict, Type, Any

from azure_rm_client.commands.base_command import BaseCommand, CommandGroup
from azure_rm_client.commands import CommandRegistry

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@CommandRegistry.register
class ResourceCommand(CommandGroup):
    """
    Command group for resource-related operations.
    """
    
    def __init__(self, base_url: str, resource_group: str = None):
        """
        Initialize the resource command group.
        
        Args:
            base_url: The base URL of the API server
            resource_group: Optional resource group name filter
        """
        self.base_url = base_url
        self.resource_group = resource_group
    
    @property
    def name(self) -> str:
        """Get the name of the command"""
        return "resource"
    
    @property
    def description(self) -> str:
        """Get the description of the command"""
        return "Azure resource management commands"
    
    @property
    def default_subcommand(self) -> str:
        """Get the default subcommand"""
        return "list"
    
    @classmethod
    def configure_parser(cls, subparser: argparse.ArgumentParser) -> None:
        """Configure command-specific arguments"""
        subparser.add_argument(
            "--resource-group", 
            help="Filter by resource group name"
        )
    
    @classmethod
    def get_param_mapping(cls) -> Dict[str, str]:
        """Map CLI arguments to constructor parameters"""
        return {
            'base_url': 'base_url',
            'resource_group': 'resource_group'
        }
    
    def get_subcommands(self) -> Dict[str, Type[BaseCommand]]:
        """Get all subcommands for this command group"""
        return CommandRegistry.get_subcommands(self.name)
    
    def execute(self) -> bool:
        """Execute the command group (show help if no subcommand is specified)"""
        subcommands = self.get_subcommands()
        if not subcommands:
            logger.info("No subcommands available")
            return False
            
        logger.info(f"Available subcommands for {self.name}:")
        for subcmd_name, subcmd_class in subcommands.items():
            temp_instance = subcmd_class.__new__(subcmd_class)
            description = getattr(temp_instance, 'description', f"Execute the {subcmd_name} subcommand")
            logger.info(f"  {subcmd_name}: {description}")
        
        return True


@CommandRegistry.register_subcommand("resource")
class ResourceListCommand(BaseCommand):
    """
    Command for listing resources.
    """
    
    def __init__(self, base_url: str, resource_group: str = None, output_format: str = "table"):
        """
        Initialize the resource list command.
        
        Args:
            base_url: The base URL of the API server
            resource_group: Optional resource group name filter
            output_format: Output format (table, json, yaml)
        """
        self.base_url = base_url
        self.resource_group = resource_group
        self.output_format = output_format
    
    @property
    def name(self) -> str:
        """Get the name of the command"""
        return "list"
    
    @property
    def description(self) -> str:
        """Get the description of the command"""
        return "List Azure resources"
    
    @classmethod
    def configure_parser(cls, subparser: argparse.ArgumentParser) -> None:
        """Configure command-specific arguments"""
        subparser.add_argument(
            "--format", 
            default="table",
            choices=["table", "json", "yaml"],
            help="Output format"
        )
    
    @classmethod
    def get_param_mapping(cls) -> Dict[str, str]:
        """Map CLI arguments to constructor parameters"""
        return {
            'base_url': 'base_url',
            'resource_group': 'resource_group',
            'format': 'output_format'
        }
    
    def execute(self) -> bool:
        """Execute the list resources command"""
        logger.info(f"Listing resources in {self.output_format} format")
        
        # Apply resource group filter if provided
        if self.resource_group:
            logger.info(f"Filtering by resource group: {self.resource_group}")
        
        # In a real implementation, we would fetch resources from the API
        # and format them according to the output format
        
        # For demo purposes, just return success
        return True


@CommandRegistry.register_subcommand("resource")
class ResourceShowCommand(BaseCommand):
    """
    Command for showing details of a specific resource.
    """
    
    def __init__(self, base_url: str, resource_id: str, resource_group: str = None, output_format: str = "json"):
        """
        Initialize the resource show command.
        
        Args:
            base_url: The base URL of the API server
            resource_id: ID of the resource to show
            resource_group: Optional resource group name
            output_format: Output format (json, yaml)
        """
        self.base_url = base_url
        self.resource_id = resource_id
        self.resource_group = resource_group
        self.output_format = output_format
    
    @property
    def name(self) -> str:
        """Get the name of the command"""
        return "show"
    
    @property
    def description(self) -> str:
        """Get the description of the command"""
        return "Show details of a specific resource"
    
    @classmethod
    def configure_parser(cls, subparser: argparse.ArgumentParser) -> None:
        """Configure command-specific arguments"""
        subparser.add_argument(
            "--id", 
            required=True,
            dest="resource_id",
            help="Resource ID"
        )
        subparser.add_argument(
            "--format", 
            default="json",
            choices=["json", "yaml"],
            help="Output format"
        )
    
    @classmethod
    def get_param_mapping(cls) -> Dict[str, str]:
        """Map CLI arguments to constructor parameters"""
        return {
            'base_url': 'base_url',
            'resource_group': 'resource_group',
            'resource_id': 'resource_id',
            'format': 'output_format'
        }
    
    def execute(self) -> bool:
        """Execute the show resource command"""
        logger.info(f"Showing resource details for ID: {self.resource_id}")
        logger.info(f"Output format: {self.output_format}")
        
        if self.resource_group:
            logger.info(f"Resource group context: {self.resource_group}")
        
        # In a real implementation, we would fetch resource details from the API
        # and format them according to the output format
        
        # For demo purposes, just return success
        return True