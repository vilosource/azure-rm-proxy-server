from abc import ABC, abstractmethod
import logging
import argparse
from typing import Any, Optional, Dict, List, Type

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BaseCommand(ABC):
    """
    Abstract base class for commands following the Command Pattern.
    Each command encapsulates a specific action to be performed.
    """
    
    @abstractmethod
    def execute(self) -> Any:
        """
        Execute the command's action.
        
        Returns:
            Result of the command execution
        """
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """
        Get the name of the command.
        
        Returns:
            Name of the command
        """
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """
        Get the description of the command.
        
        Returns:
            Description of the command
        """
        pass
    
    @classmethod
    def configure_parser(cls, subparser: argparse.ArgumentParser) -> None:
        """
        Configure the argument parser for this command.
        
        Args:
            subparser: The subparser to configure
        """
        pass  # Default implementation does nothing
    
    @classmethod
    def get_param_mapping(cls) -> Dict[str, str]:
        """
        Get a mapping from CLI argument names to constructor parameter names.
        Override this method to provide custom mapping.
        
        Returns:
            A dictionary mapping CLI argument names to constructor parameter names
        """
        return {}  # Default implementation returns an empty mapping
    
    @classmethod
    def create_from_args(cls, args_dict: Dict[str, Any]) -> 'BaseCommand':
        """
        Create a command instance from parsed arguments.
        
        Args:
            args_dict: Dictionary of parsed command-line arguments
            
        Returns:
            An instance of the command
        """
        # Get parameter mapping
        param_mapping = cls.get_param_mapping()
        
        # Build constructor parameters
        constructor_params = {}
        
        # Map CLI arguments to constructor parameters
        for arg_name, param_name in param_mapping.items():
            if arg_name in args_dict:
                constructor_params[param_name] = args_dict[arg_name]
        
        # Create and return the command instance
        return cls(**constructor_params)


class CommandGroup(BaseCommand):
    """
    A command that can contain subcommands.
    """
    
    @abstractmethod
    def get_subcommands(self) -> Dict[str, Type[BaseCommand]]:
        """
        Get all subcommands for this command group.
        
        Returns:
            A dictionary mapping subcommand names to command classes
        """
        pass
    
    @classmethod
    def has_subcommands(cls) -> bool:
        """
        Check if this command has subcommands.
        
        Returns:
            True if this command has subcommands, False otherwise
        """
        return True
    
    @property
    def default_subcommand(self) -> Optional[str]:
        """
        Get the default subcommand to execute when none is specified.
        
        Returns:
            The name of the default subcommand, or None if there is no default
        """
        return None