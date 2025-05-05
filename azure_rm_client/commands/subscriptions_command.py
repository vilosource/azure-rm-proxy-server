import argparse
import logging
from typing import Dict, Any
from azure_rm_client.commands.base_command import BaseCommand
from azure_rm_client.commands import CommandRegistry
from azure_rm_client.formatters import get_formatter
from azure_rm_client.workers.subscriptions_worker import SubscriptionsWorker

logger = logging.getLogger(__name__)

@CommandRegistry.register
class SubscriptionsCommand(BaseCommand):
    """
    Command for listing Azure subscriptions.
    """

    def __init__(self, output_format: str = "table", args: argparse.Namespace = None):
        self.output_format = output_format
        self.args = args  # Store the parsed arguments

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
        subparser.add_argument(
            "--refresh-cache",
            action="store_true",
            help="Bypass cache and fetch fresh data (default: False)"
        )

    @classmethod
    def get_param_mapping(cls) -> Dict[str, str]:
        return {
            'format': 'output_format'
        }

    def execute(self) -> bool:
        logger.debug("Executing SubscriptionsCommand with output_format=%s", self.output_format)

        # Use the SubscriptionsWorker to fetch subscriptions
        worker = SubscriptionsWorker()
        refresh_cache = self.args.get('refresh_cache', False) if isinstance(self.args, dict) else False
        try:
            subscriptions = worker.execute(refresh_cache=refresh_cache)
            logger.debug("Fetched %d subscriptions", len(subscriptions))
        except Exception as e:
            logger.error("Failed to fetch subscriptions: %s", e)
            return False

        # Format and print the subscriptions
        formatter = get_formatter(self.output_format)
        logger.debug("Using formatter: %s", self.output_format)

        print(formatter.format(subscriptions))
        logger.debug("SubscriptionsCommand executed successfully")
        return True