from typing import Dict, Any, List
from .formatter_interface import FormatterInterface
import io
from rich.console import Console
from rich.table import Table


class TableFormatter(FormatterInterface):
    """
    Formatter for tabular output using Rich library.
    This formatter specializes in presenting data in a clean, tabular format
    that's easy to read in the terminal.
    """

    def format(self, data: Any) -> str:
        """
        Format the provided data as a table (alias for format_data).

        Args:
            data: The data to format

        Returns:
            String representation of the tabular output
        """
        return self.format_data(data)

    def format_data(self, data: Any) -> str:
        """
        Format the provided data as a table.

        Args:
            data: The data to format (list of dictionaries expected)

        Returns:
            String representation of the tabular output
        """
        string_io = io.StringIO()
        console = Console(file=string_io, width=100)

        if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
            # Format list of dictionaries as table with column headers
            console.print(self._format_list_of_dicts(data))
        elif isinstance(data, dict):
            # Format dictionary as key-value pairs
            console.print(self._format_dict_as_table(data))
        elif isinstance(data, list):
            # Format list as indexed values
            console.print(self._format_list_as_table(data))
        else:
            # Fallback for other data types
            console.print(str(data))

        return string_io.getvalue()

    def _format_list_of_dicts(self, data_list: List[Dict[str, Any]]) -> Table:
        """
        Format a list of dictionaries as a table with column headers.

        Args:
            data_list: List of dictionaries to format

        Returns:
            Rich Table object
        """
        if not data_list:
            return Table(title="No data")

        # Create table with columns from the first item's keys
        table = Table(show_header=True, header_style="bold")
        for key in data_list[0].keys():
            # Convert keys like snake_case or camelCase to Title Case for display
            header = key.replace('_', ' ').title()
            table.add_column(header)

        # Add rows from each dictionary
        for item in data_list:
            row_values = []
            for key in data_list[0].keys():
                value = item.get(key, "")
                if isinstance(value, (dict, list)):
                    # For complex types, show a summary
                    value = f"[{type(value).__name__}: {len(value)} items]"
                elif value is None:
                    value = ""
                row_values.append(str(value))

            table.add_row(*row_values)

        return table

    def _format_dict_as_table(self, data: Dict[str, Any]) -> Table:
        """
        Format a dictionary as a key-value table.

        Args:
            data: Dictionary to format

        Returns:
            Rich Table object
        """
        table = Table(show_header=True, header_style="bold")
        table.add_column("Property")
        table.add_column("Value")

        for key, value in data.items():
            formatted_key = key.replace('_', ' ').title()

            if isinstance(value, dict):
                value_str = f"[Dictionary: {len(value)} items]"
            elif isinstance(value, list):
                value_str = f"[List: {len(value)} items]"
            elif value is None:
                value_str = ""
            else:
                value_str = str(value)

            table.add_row(formatted_key, value_str)

        return table

    def _format_list_as_table(self, data: List[Any]) -> Table:
        """
        Format a list as a table with index column.

        Args:
            data: List to format

        Returns:
            Rich Table object
        """
        table = Table(show_header=True, header_style="bold")
        table.add_column("Index")
        table.add_column("Value")

        for i, item in enumerate(data):
            if isinstance(item, dict):
                value_str = f"[Dictionary: {len(item)} items]"
            elif isinstance(item, list):
                value_str = f"[List: {len(item)} items]"
            elif item is None:
                value_str = ""
            else:
                value_str = str(item)

            table.add_row(str(i), value_str)

        return table