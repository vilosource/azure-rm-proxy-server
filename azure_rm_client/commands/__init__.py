from typing import Dict, Type, List, Callable, Optional
from azure_rm_client.commands.base_command import BaseCommand

class CommandRegistry:
    """
    Registry for commands using the Registry Pattern.
    This allows automatic registration of command classes through a decorator.
    """
    
    _commands: Dict[str, Type[BaseCommand]] = {}
    _command_hierarchy: Dict[str, Dict[str, Type[BaseCommand]]] = {}
    
    @classmethod
    def register(cls, command_class: Type[BaseCommand] = None) -> Callable:
        """
        Decorator for registering commands in the registry.
        
        Can be used as @CommandRegistry.register or @CommandRegistry.register()
        
        Args:
            command_class: The command class to register (optional, used when decorator is called without parentheses)
            
        Returns:
            Decorator function or the original class if used directly
        """
        def decorator(cmd_class: Type[BaseCommand]) -> Type[BaseCommand]:
            # Create a temporary instance to get the name
            temp_instance = cmd_class.__new__(cmd_class)
            command_name = getattr(temp_instance, 'name', None)
            if command_name is None:
                raise ValueError(f"Command class {cmd_class.__name__} does not have a name property")
            
            # Register the command
            cls._commands[command_name] = cmd_class
            return cmd_class
        
        # Handle both @CommandRegistry.register and @CommandRegistry.register()
        if command_class is not None:
            return decorator(command_class)
        return decorator
    
    @classmethod
    def register_subcommand(cls, parent_command: str, command_class: Type[BaseCommand] = None) -> Callable:
        """
        Decorator for registering subcommands.
        
        Usage:
            @CommandRegistry.register_subcommand("parent-command")
            class MySubCommand(BaseCommand):
                ...
                
        Args:
            parent_command: The name of the parent command or parent command path (e.g., "resource.group")
            command_class: The command class to register (optional, used when decorator is called without parentheses)
            
        Returns:
            Decorator function or the original class if used directly
        """
        def decorator(cmd_class: Type[BaseCommand]) -> Type[BaseCommand]:
            # Create a temporary instance to get the name
            temp_instance = cmd_class.__new__(cmd_class)
            command_name = getattr(temp_instance, 'name', None)
            if command_name is None:
                raise ValueError(f"Command class {cmd_class.__name__} does not have a name property")
            
            # Split parent command path into segments
            parent_path = parent_command.split('.')
            
            # If it's a direct subcommand of a top-level command
            if len(parent_path) == 1:
                # Ensure parent command exists
                if parent_path[0] not in cls._commands:
                    raise ValueError(f"Parent command '{parent_path[0]}' does not exist")
                
                # Initialize hierarchy if needed
                if parent_path[0] not in cls._command_hierarchy:
                    cls._command_hierarchy[parent_path[0]] = {}
                
                # Register the subcommand
                cls._command_hierarchy[parent_path[0]][command_name] = cmd_class
            else:
                # For nested subcommands (e.g., "resource.group")
                # Ensure top-level parent command exists
                if parent_path[0] not in cls._commands:
                    raise ValueError(f"Top-level parent command '{parent_path[0]}' does not exist")
                
                # Initialize hierarchy for the top-level command if needed
                if parent_path[0] not in cls._command_hierarchy:
                    cls._command_hierarchy[parent_path[0]] = {}
                
                # Handle multi-level nesting by using a command path key in the hierarchy
                nested_key = '.'.join(parent_path)
                if nested_key not in cls._command_hierarchy:
                    cls._command_hierarchy[nested_key] = {}
                
                # Register the nested subcommand
                cls._command_hierarchy[nested_key][command_name] = cmd_class
            
            return cmd_class
        
        # Handle both forms of decorator usage
        if command_class is not None:
            return decorator(command_class)
        return decorator
    
    @classmethod
    def get_command(cls, command_name: str) -> Type[BaseCommand]:
        """
        Get a command class for the specified command name.
        
        Args:
            command_name: The command name
            
        Returns:
            The command class
            
        Raises:
            ValueError: If the command name is not registered
        """
        command_class = cls._commands.get(command_name)
        if command_class is None:
            raise ValueError(f"No command registered with name: {command_name}")
        return command_class
    
    @classmethod
    def create_command(cls, command_name: str, **kwargs) -> BaseCommand:
        """
        Create a command instance for the specified command name.
        
        Args:
            command_name: The command name
            **kwargs: Arguments to pass to the command constructor
            
        Returns:
            An instance of the command
            
        Raises:
            ValueError: If the command name is not registered
        """
        command_class = cls.get_command(command_name)
        return command_class(**kwargs)
    
    @classmethod
    def get_available_commands(cls) -> List[str]:
        """
        Get a list of all available command names.
        
        Returns:
            List of available command names
        """
        return list(cls._commands.keys())
    
    @classmethod
    def get_subcommands(cls, parent_command: str) -> Dict[str, Type[BaseCommand]]:
        """
        Get all subcommands for a parent command or command path.
        
        Args:
            parent_command: The parent command name or command path (e.g., "resource.group")
            
        Returns:
            Dictionary mapping subcommand names to command classes
        """
        return cls._command_hierarchy.get(parent_command, {})
    
    @classmethod
    def has_subcommands(cls, command_name: str) -> bool:
        """
        Check if a command has subcommands.
        
        Args:
            command_name: The command name or command path
            
        Returns:
            True if the command has subcommands, False otherwise
        """
        return command_name in cls._command_hierarchy and bool(cls._command_hierarchy[command_name])

# Backward compatibility functions
def get_command(command_name: str, **kwargs) -> BaseCommand:
    """
    Get a command instance for the specified command name.
    
    Args:
        command_name: The command name
        **kwargs: Arguments to pass to the command constructor
        
    Returns:
        A command instance
        
    Raises:
        ValueError: If the command name is not registered
    """
    return CommandRegistry.create_command(command_name, **kwargs)

def get_command_factory():
    """
    Get the command registry for backward compatibility.
    
    Returns:
        The command registry
    """
    return CommandRegistry