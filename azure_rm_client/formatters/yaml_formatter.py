import yaml
from typing import Any
from .formatter_interface import FormatterInterface

class YamlFormatter(FormatterInterface):
    """
    Formatter for YAML output.

    This formatter outputs data as a formatted YAML string.
    """

    def format(self, data: Any) -> str:
        """
        Format the provided data as a YAML string (alias for format_data).

        Args:
            data: The data to format

        Returns:
            YAML string representation of the data
        """
        return self.format_data(data)

    def format_data(self, data: Any) -> str:
        """
        Format the provided data as a YAML string.

        Args:
            data: The data to format

        Returns:
            YAML string representation of the data
        """
        return yaml.dump(data, default_flow_style=False, sort_keys=False)