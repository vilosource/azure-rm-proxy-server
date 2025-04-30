import logging
import argparse
from typing import Dict, Type, Any

from azure_rm_client.commands.base_command import BaseCommand
from azure_rm_client.commands import CommandRegistry

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@CommandRegistry.register_subcommand("resource.group")
class ResourceGroupListCommand(BaseCommand):
    """
    Command for listing resource groups.
    """
    
    def __init__(self, base_url: str, subscription_id: str = None, output_format: str = "table"):
        """
        Initialize the resource group list command.
        
        Args:
            base_url: The base URL of the API server
            subscription_id: Optional subscription ID filter
            output_format: Output format (table, json, yaml)
        """
        self.base_url = base_url
        self.subscription_id = subscription_id
        self.output_format = output_format
    
    @property
    def name(self) -> str:
        """Get the name of the command"""
        return "list"
    
    @property
    def description(self) -> str:
        """Get the description of the command"""
        return "List resource groups"
    
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
            'subscription_id': 'subscription_id',
            'format': 'output_format'
        }
    
    def execute(self) -> bool:
        """Execute the list resource groups command"""
        logger.info(f"Listing resource groups in {self.output_format} format")
        
        # Apply subscription filter if provided
        if self.subscription_id:
            logger.info(f"Filtering by subscription ID: {self.subscription_id}")
        
        # In a real implementation, we would fetch resource groups from the API
        # and format them according to the output format
        
        # For demo purposes, just return success
        return True


@CommandRegistry.register_subcommand("resource.group")
class ResourceGroupShowCommand(BaseCommand):
    """
    Command for showing details of a specific resource group.
    """
    
    def __init__(self, base_url: str, name: str, subscription_id: str = None, output_format: str = "json"):
        """
        Initialize the resource group show command.
        
        Args:
            base_url: The base URL of the API server
            name: Name of the resource group to show
            subscription_id: Optional subscription ID
            output_format: Output format (json, yaml)
        """
        self.base_url = base_url
        self.name = name
        self.subscription_id = subscription_id
        self.output_format = output_format
    
    @property
    def name(self) -> str:
        """Get the name of the command"""
        return "show"
    
    @property
    def description(self) -> str:
        """Get the description of the command"""
        return "Show details of a specific resource group"
    
    @classmethod
    def configure_parser(cls, subparser: argparse.ArgumentParser) -> None:
        """Configure command-specific arguments"""
        subparser.add_argument(
            "--name", 
            required=True,
            help="Resource group name"
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
            'subscription_id': 'subscription_id',
            'name': 'name',
            'format': 'output_format'
        }
    
    def execute(self) -> bool:
        """Execute the show resource group command"""
        logger.info(f"Showing resource group details for: {self.name}")
        logger.info(f"Output format: {self.output_format}")
        
        if self.subscription_id:
            logger.info(f"Subscription context: {self.subscription_id}")
        
        # In a real implementation, we would fetch resource group details from the API
        # and format them according to the output format
        
        # For demo purposes, just return success
        return True


@CommandRegistry.register_subcommand("resource.group")
class ResourceGroupCreateCommand(BaseCommand):
    """
    Command for creating a new resource group.
    """
    
    def __init__(self, base_url: str, name: str, location: str, subscription_id: str = None):
        """
        Initialize the resource group create command.
        
        Args:
            base_url: The base URL of the API server
            name: Name of the resource group to create
            location: Azure region for the resource group
            subscription_id: Optional subscription ID
        """
        self.base_url = base_url
        self.group_name = name
        self.location = location
        self.subscription_id = subscription_id
    
    @property
    def name(self) -> str:
        """Get the name of the command"""
        return "create"
    
    @property
    def description(self) -> str:
        """Get the description of the command"""
        return "Create a new resource group"
    
    @classmethod
    def configure_parser(cls, subparser: argparse.ArgumentParser) -> None:
        """Configure command-specific arguments"""
        subparser.add_argument(
            "--name", 
            required=True,
            help="Resource group name"
        )
        subparser.add_argument(
            "--location", 
            required=True,
            help="Azure region for the resource group"
        )
    
    @classmethod
    def get_param_mapping(cls) -> Dict[str, str]:
        """Map CLI arguments to constructor parameters"""
        return {
            'base_url': 'base_url',
            'subscription_id': 'subscription_id',
            'name': 'name',
            'location': 'location'
        }
    
    def execute(self) -> bool:
        """Execute the create resource group command"""
        logger.info(f"Creating resource group: {self.group_name} in {self.location}")
        
        if self.subscription_id:
            logger.info(f"Using subscription: {self.subscription_id}")
        
        # In a real implementation, we would create the resource group via the API
        
        # For demo purposes, just return success
        return True