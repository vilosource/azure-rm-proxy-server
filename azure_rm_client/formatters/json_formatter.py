import json
from typing import Dict, Any
from .formatter_interface import FormatterInterface


class JsonFormatter(FormatterInterface):
    """
    Formatter for JSON output.

    This formatter outputs data as a formatted JSON string.
    """

    def format(self, data: Any) -> str:
        """
        Format the provided data as a JSON string (alias for format_data).

        Args:
            data: The data to format

        Returns:
            JSON string representation of the data
        """
        return self.format_data(data)

    def format_data(self, data: Any) -> str:
        """
        Format the provided data as a JSON string.

        Args:
            data: The data to format

        Returns:
            JSON string representation of the data
        """
        return json.dumps(data, indent=2)