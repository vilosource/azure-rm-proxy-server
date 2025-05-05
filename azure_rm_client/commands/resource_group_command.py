import logging
import argparse
from typing import Dict, Type, Any

from azure_rm_client.commands.base_command import BaseCommand, CommandGroup
from azure_rm_client.commands import CommandRegistry

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@CommandRegistry.register_subcommand("resource")
class ResourceGroupCommand(CommandGroup):
    """
    Command group for resource group operations.
    """
    
    def __init__(self, base_url: str, subscription_id: str = None):
        """
        Initialize the resource group command.
        
        Args:
            base_url: The base URL of the API server
            subscription_id: Optional subscription ID filter
        """
        self.base_url = base_url
        self.subscription_id = subscription_id
    
    @property
    def name(self) -> str:
        """Get the name of the command"""
        return "group"
    
    @property
    def description(self) -> str:
        """Get the description of the command"""
        return "Resource group management commands"
    
    @property
    def default_subcommand(self) -> str:
        """Get the default subcommand"""
        return "list"
    
    @classmethod
    def configure_parser(cls, subparser: argparse.ArgumentParser) -> None:
        """Configure command-specific arguments"""
        subparser.add_argument(
            "--subscription", 
            dest="subscription_id",
            help="Filter by subscription ID"
        )
    
    @classmethod
    def get_param_mapping(cls) -> Dict[str, str]:
        """Map CLI arguments to constructor parameters"""
        return {
            'base_url': 'base_url',
            'subscription_id': 'subscription_id'
        }
    
    def get_subcommands(self) -> Dict[str, Type[BaseCommand]]:
        """Get all subcommands for this command group"""
        # We need to use the full command path for nested subcommands
        return CommandRegistry.get_subcommands(f"resource.{self.name}")
    
    def execute(self) -> bool:
        """Execute the command group (show help if no subcommand is specified)"""
        subcommands = self.get_subcommands()
        if not subcommands:
            logger.info("No subcommands available for resource group")
            logger.info("Use 'resource group list' to list resource groups")
            logger.info("Use 'resource group show --name <n>' to show details of a resource group")
            return False  # Return False to indicate no subcommands were found
            
        logger.info("Available subcommands for resource group:")
        for subcmd_name, subcmd_class in subcommands.items():
            temp_instance = subcmd_class.__new__(subcmd_class)
            description = getattr(temp_instance, 'description', f"Execute the {subcmd_name} subcommand")
            logger.info(f"  {subcmd_name}: {description}")
        
        return True  # Return True to indicate subcommands were successfully listed