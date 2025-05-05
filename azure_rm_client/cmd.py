#!/usr/bin/env python3
import argparse
import importlib
import logging
import os
import pkgutil
import sys
from typing import List, Optional, Dict, Any, Tuple

# Import the registry (but not individual commands)
from azure_rm_client.commands import CommandRegistry, get_command
from azure_rm_client.commands.base_command import CommandGroup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def discover_commands():
    """
    Discover and import all command modules to ensure they are registered.
    This automatically finds and imports any modules in the commands package.
    """
    commands_package = 'azure_rm_client.commands'
    package = importlib.import_module(commands_package)
    
    # Import all modules in the commands package
    prefix = package.__name__ + "."
    for _, module_name, is_pkg in pkgutil.iter_modules(package.__path__, prefix):
        # Skip the base_command module and __init__.py
        if not module_name.endswith('base_command') and not module_name.endswith('__init__'):
            try:
                importlib.import_module(module_name)
                logger.debug(f"Imported command module: {module_name}")
            except Exception as e:
                logger.error(f"Error importing command module {module_name}: {e}")
    
    logger.debug(f"Discovered commands: {CommandRegistry.get_available_commands()}")


def configure_parser_recursively(
    subparsers: argparse._SubParsersAction,
    command_name: str,
    command_class: type,
    path_prefix: str = ""
) -> None:
    """
    Recursively configure the parser for a command and its subcommands.
    
    Args:
        subparsers: The subparsers action to add the command to
        command_name: The name of the command
        command_class: The command class
        path_prefix: The command path prefix (for nested subcommands)
    """
    # Get the command description
    temp_instance = command_class.__new__(command_class)
    description = getattr(temp_instance, 'description', f"Execute the {command_name} command")
    
    # Create the subparser
    cmd_parser = subparsers.add_parser(command_name, help=description)
    
    # Let the command configure its own parser
    command_class.configure_parser(cmd_parser)
    
    # Full command path for subcommand lookup
    full_path = f"{path_prefix}.{command_name}" if path_prefix else command_name
    
    # If this command has subcommands, add them
    if CommandRegistry.has_subcommands(full_path):
        # Subcommand destination must be unique across the entire command hierarchy
        subcmd_parsers = cmd_parser.add_subparsers(
            dest=full_path.replace('.', '_') + "_subcommand",
            help=f"{command_name} subcommands"
        )
        
        # Get all subcommands for this command
        subcommand_classes = CommandRegistry.get_subcommands(full_path)
        
        # Create a subparser for each subcommand
        for subcmd_name, subcmd_class in subcommand_classes.items():
            # Recursively configure subcommands
            configure_parser_recursively(
                subcmd_parsers,
                subcmd_name,
                subcmd_class,
                full_path
            )


def parse_args(args: List[str]) -> argparse.Namespace:
    """Parse command-line arguments with support for nested subcommands"""
    # Ensure all commands are discovered and registered first
    discover_commands()
    
    parser = argparse.ArgumentParser(
        description="Azure Resource Manager REST Client",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Common options
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--base-url", default="http://localhost:8000", help="Base URL for the API server")
    
    # Create subparsers for each command
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Get all registered commands
    command_classes = {
        name: CommandRegistry.get_command(name) 
        for name in CommandRegistry.get_available_commands()
    }
    
    # Create a subparser for each command and let the command configure it
    for command_name, command_class in command_classes.items():
        configure_parser_recursively(subparsers, command_name, command_class)
    
    return parser.parse_args(args)


def extract_subcommand_chain(args_dict: Dict[str, Any]) -> Tuple[str, List[str]]:
    """
    Extract the chain of subcommands from parsed arguments.
    
    Args:
        args_dict: Dictionary of parsed command-line arguments
        
    Returns:
        Tuple of (main command name, list of subcommand names)
    """
    main_command = args_dict.get('command')
    if not main_command:
        return "", []
    
    subcommands = []
    current_path = main_command
    
    # Check each possible subcommand argument
    while True:
        subcommand_arg = current_path.replace('.', '_') + "_subcommand"
        if subcommand_arg in args_dict and args_dict[subcommand_arg]:
            subcommand = args_dict[subcommand_arg]
            subcommands.append(subcommand)
            current_path = f"{current_path}.{subcommand}"
        else:
            break
    
    return main_command, subcommands


def execute_command_or_subcommand(
    main_command: str,
    subcommands: List[str],
    args_dict: Dict[str, Any]
) -> bool:
    """
    Execute a command or its deepest specified subcommand.
    
    Args:
        main_command: The main command name
        subcommands: List of subcommand names in order
        args_dict: Dictionary of parsed command-line arguments
        
    Returns:
        True if the command executed successfully, False otherwise
    """
    # Base parameters for all commands
    command_params = {}
    if 'base_url' in args_dict:
        command_params['base_url'] = args_dict['base_url']
    
    # If no subcommands, execute the main command
    if not subcommands:
        command_class = CommandRegistry.get_command(main_command)
        command = command_class.create_from_args(args_dict)
        # Assign parsed arguments to the command instance
        command.args = args_dict
        return command.execute()
    
    # Build the full command path
    command_path = main_command
    
    # Process each subcommand in the chain
    for i, subcommand in enumerate(subcommands):
        # Get the subcommands at this level
        available_subcommands = CommandRegistry.get_subcommands(command_path)
        
        if subcommand not in available_subcommands:
            logger.error(f"Unknown subcommand: {subcommand} for command {command_path}")
            return False
        
        # Last subcommand in the chain - execute it
        if i == len(subcommands) - 1:
            subcommand_class = available_subcommands[subcommand]
            
            # Build parameter mapping for the subcommand
            param_mapping = subcommand_class.get_param_mapping()
            
            # Map CLI arguments to constructor parameters
            for arg_name, param_name in param_mapping.items():
                if arg_name in args_dict and args_dict[arg_name] is not None:
                    command_params[param_name] = args_dict[arg_name]
            
            # Create and execute the subcommand
            command = subcommand_class(**command_params)
            # Assign parsed arguments to the command instance
            command.args = args_dict
            return command.execute()
        
        # Not the last subcommand - update path and continue
        command_path = f"{command_path}.{subcommand}"
    
    # We should never reach here
    logger.error("Error executing command chain")
    return False


def main(args: Optional[List[str]] = None) -> int:
    """Main entry point for the command-line interface with nested subcommand support"""
    if args is None:
        args = sys.argv[1:]
    
    if not args:  # If no arguments are provided, show help
        args = ['--help']
    
    parsed_args = parse_args(args)
    
    # Set up logging level
    if parsed_args.debug:
        print("Debug mode enabled")
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug logging is enabled")
    
    # Execute the command if specified
    if parsed_args.command:
        # Convert parsed_args to a dict for the command constructor
        cmd_args = vars(parsed_args)
        
        # Remove debug flag since we've handled it already
        cmd_args.pop('debug', False)
        
        # Extract the command and subcommand chain
        main_command, subcommands = extract_subcommand_chain(cmd_args)
        
        try:
            # Execute the command or its deepest specified subcommand
            success = execute_command_or_subcommand(main_command, subcommands, cmd_args)
            return 0 if success else 1
        except Exception as e:
            logger.error(f"Error executing command: {e}")
            return 1
    else:
        logger.error("No command specified")
        available_commands = CommandRegistry.get_available_commands()
        logger.info(f"Available commands: {', '.join(available_commands)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

