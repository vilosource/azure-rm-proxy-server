import argparse
from typing import Dict, Any
from azure_rm_client.commands.base_command import BaseCommand
from azure_rm_client.commands import CommandRegistry
from azure_rm_client.formatters import get_formatter

@CommandRegistry.register
class SubscriptionsCommand(BaseCommand):
    """
    Command for listing Azure subscriptions.
    """

    def __init__(self, output_format: str = "table"):
        self.output_format = output_format

    @property
    def name(self) -> str:
        return "subscriptions"

    @property
    def description(self) -> str:
        return "List all Azure subscriptions."

    @classmethod
    def configure_parser(cls, subparser: argparse.ArgumentParser) -> None:
        subparser.add_argument(
            "--format",
            default="table",
            choices=["table", "json", "yaml"],
            help="Output format (default: table)"
        )

    @classmethod
    def get_param_mapping(cls) -> Dict[str, str]:
        return {
            'format': 'output_format'
        }

    def execute(self) -> bool:
        # Mocked subscription data for demonstration purposes
        subscriptions = [
            {"id": "sub1", "name": "Subscription One", "state": "Enabled"},
            {"id": "sub2", "name": "Subscription Two", "state": "Disabled"},
        ]

        formatter = get_formatter(self.output_format)
        print(formatter.format(subscriptions))
        return True