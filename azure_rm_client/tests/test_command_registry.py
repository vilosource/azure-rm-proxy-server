"""
Tests for the command registry with support for subcommands.
"""
import pytest
from typing import Dict, Any

from azure_rm_client.commands import CommandRegistry
from azure_rm_client.commands.base_command import BaseCommand, CommandGroup


@pytest.mark.skipif(True, reason="This is a helper class, not a test class")
class TestCommand(BaseCommand):
    """
    Test command implementation.
    """
    
    def __init__(self, base_url: str, test_param: str = None):
        self.base_url = base_url
        self.test_param = test_param
    
    @property
    def name(self) -> str:
        return "test-command"
    
    @property
    def description(self) -> str:
        return "Test command for unit tests"
    
    @classmethod
    def get_param_mapping(cls) -> Dict[str, str]:
        return {
            'base_url': 'base_url',
            'test_param': 'test_param'
        }
    
    def execute(self) -> bool:
        return True


@pytest.mark.skipif(True, reason="This is a helper class, not a test class")
class TestGroup(CommandGroup):
    """
    Test command group implementation.
    """
    
    def __init__(self, base_url: str, group_param: str = None):
        self.base_url = base_url
        self.group_param = group_param
    
    @property
    def name(self) -> str:
        return "test-group"
    
    @property
    def description(self) -> str:
        return "Test command group for unit tests"
    
    @property
    def default_subcommand(self) -> str:
        return "sub1"
    
    @classmethod
    def get_param_mapping(cls) -> Dict[str, str]:
        return {
            'base_url': 'base_url',
            'group_param': 'group_param'
        }
    
    def get_subcommands(self) -> Dict[str, type]:
        return CommandRegistry.get_subcommands(self.name)
    
    def execute(self) -> bool:
        return True


@pytest.mark.skipif(True, reason="This is a helper class, not a test class")
class TestSubCommand1(BaseCommand):
    """
    Test subcommand implementation.
    """
    
    def __init__(self, base_url: str, sub_param: str = None):
        self.base_url = base_url
        self.sub_param = sub_param
    
    @property
    def name(self) -> str:
        return "sub1"
    
    @property
    def description(self) -> str:
        return "Test subcommand 1 for unit tests"
    
    @classmethod
    def get_param_mapping(cls) -> Dict[str, str]:
        return {
            'base_url': 'base_url',
            'sub_param': 'sub_param'
        }
    
    def execute(self) -> bool:
        return True


@pytest.mark.skipif(True, reason="This is a helper class, not a test class")
class TestSubCommand2(BaseCommand):
    """
    Test subcommand implementation.
    """
    
    def __init__(self, base_url: str, sub_param: str = None):
        self.base_url = base_url
        self.sub_param = sub_param
    
    @property
    def name(self) -> str:
        return "sub2"
    
    @property
    def description(self) -> str:
        return "Test subcommand 2 for unit tests"
    
    @classmethod
    def get_param_mapping(cls) -> Dict[str, str]:
        return {
            'base_url': 'base_url',
            'sub_param': 'sub_param'
        }
    
    def execute(self) -> bool:
        return True


@pytest.mark.skipif(True, reason="This is a helper class, not a test class")
class TestNestedGroup(CommandGroup):
    """
    Test nested command group implementation.
    """
    
    def __init__(self, base_url: str, nested_param: str = None):
        self.base_url = base_url
        self.nested_param = nested_param
    
    @property
    def name(self) -> str:
        return "nested"
    
    @property
    def description(self) -> str:
        return "Test nested command group for unit tests"
    
    @classmethod
    def get_param_mapping(cls) -> Dict[str, str]:
        return {
            'base_url': 'base_url',
            'nested_param': 'nested_param'
        }
    
    def get_subcommands(self) -> Dict[str, type]:
        return CommandRegistry.get_subcommands(f"test-group.{self.name}")
    
    def execute(self) -> bool:
        return True


@pytest.mark.skipif(True, reason="This is a helper class, not a test class")
class TestNestedSubCommand(BaseCommand):
    """
    Test nested subcommand implementation.
    """
    
    def __init__(self, base_url: str, nested_sub_param: str = None):
        self.base_url = base_url
        self.nested_sub_param = nested_sub_param
    
    @property
    def name(self) -> str:
        return "nested-sub"
    
    @property
    def description(self) -> str:
        return "Test nested subcommand for unit tests"
    
    @classmethod
    def get_param_mapping(cls) -> Dict[str, str]:
        return {
            'base_url': 'base_url',
            'nested_sub_param': 'nested_sub_param'
        }
    
    def execute(self) -> bool:
        return True


@pytest.fixture
def setup_test_commands():
    """
    Set up test commands and command groups in the registry.
    """
    # Clear the registry first to ensure a clean state
    CommandRegistry._commands.clear()
    CommandRegistry._command_hierarchy.clear()
    
    # Register a test command
    CommandRegistry.register(TestCommand)
    
    # Register a test command group
    CommandRegistry.register(TestGroup)
    
    # Register subcommands
    CommandRegistry.register_subcommand("test-group", TestSubCommand1)
    CommandRegistry.register_subcommand("test-group", TestSubCommand2)
    
    # Register a nested command group
    CommandRegistry.register_subcommand("test-group", TestNestedGroup)
    
    # Register a nested subcommand
    CommandRegistry.register_subcommand("test-group.nested", TestNestedSubCommand)
    
    yield
    
    # Clear the registry after the test
    CommandRegistry._commands.clear()
    CommandRegistry._command_hierarchy.clear()


def test_command_registration(setup_test_commands):
    """
    Test that commands are properly registered in the registry.
    """
    # Check that commands are registered
    assert "test-command" in CommandRegistry.get_available_commands()
    assert "test-group" in CommandRegistry.get_available_commands()
    
    # Check that command classes can be retrieved
    assert CommandRegistry.get_command("test-command") == TestCommand
    assert CommandRegistry.get_command("test-group") == TestGroup


def test_subcommand_registration(setup_test_commands):
    """
    Test that subcommands are properly registered in the registry.
    """
    # Check that subcommands are registered
    subcommands = CommandRegistry.get_subcommands("test-group")
    assert "sub1" in subcommands
    assert "sub2" in subcommands
    assert "nested" in subcommands
    
    # Check that subcommand classes can be retrieved
    assert subcommands["sub1"] == TestSubCommand1
    assert subcommands["sub2"] == TestSubCommand2
    assert subcommands["nested"] == TestNestedGroup


def test_nested_subcommand_registration(setup_test_commands):
    """
    Test that nested subcommands are properly registered in the registry.
    """
    # Check that nested subcommands are registered
    nested_subcommands = CommandRegistry.get_subcommands("test-group.nested")
    assert "nested-sub" in nested_subcommands
    
    # Check that nested subcommand classes can be retrieved
    assert nested_subcommands["nested-sub"] == TestNestedSubCommand


def test_has_subcommands(setup_test_commands):
    """
    Test the has_subcommands method of the registry.
    """
    # Check that has_subcommands returns True for command groups
    assert CommandRegistry.has_subcommands("test-group")
    assert CommandRegistry.has_subcommands("test-group.nested")
    
    # Check that has_subcommands returns False for commands without subcommands
    assert not CommandRegistry.has_subcommands("test-command")
    assert not CommandRegistry.has_subcommands("test-group.sub1")


def test_command_creation(setup_test_commands):
    """
    Test that commands can be created from the registry.
    """
    # Create a command
    command = CommandRegistry.create_command("test-command", base_url="http://test", test_param="value")
    
    # Check that the command is of the correct type
    assert isinstance(command, TestCommand)
    
    # Check that the command has the correct properties
    assert command.base_url == "http://test"
    assert command.test_param == "value"


def test_subcommand_groups(setup_test_commands):
    """
    Test the behavior of command groups.
    """
    # Create a command group
    group = CommandRegistry.create_command("test-group", base_url="http://test", group_param="value")
    
    # Check that the group is of the correct type
    assert isinstance(group, TestGroup)
    
    # Check that the group has the correct properties
    assert group.base_url == "http://test"
    assert group.group_param == "value"
    
    # Check that the group returns the correct subcommands
    subcommands = group.get_subcommands()
    assert "sub1" in subcommands
    assert "sub2" in subcommands
    assert "nested" in subcommands
    
    # Check that the group has the correct default subcommand
    assert group.default_subcommand == "sub1"