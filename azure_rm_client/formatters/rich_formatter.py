from typing import Dict, Any, List
from .formatter_interface import FormatterInterface
import io
from rich.console import Console
from rich.table import Table
from rich.panel import Panel


class RichFormatter(FormatterInterface):
    """
    Formatter for Rich console output.
    
    This formatter uses the Rich library to create visually appealing console output.
    """
    
    def format_data(self, data: Dict[str, Any]) -> str:
        """
        Format the provided data using Rich.
        
        Args:
            data: The data to format
            
        Returns:
            String representation of the Rich formatted output
        """
        string_io = io.StringIO()
        console = Console(file=string_io, width=100)
        
        # Create a panel with a title for the main data
        panel = Panel(self._format_dict_as_rich(data), title="Azure Resource Manager API")
        console.print(panel)
        
        return string_io.getvalue()
    
    def _format_dict_as_rich(self, data: Dict[str, Any]) -> Table:
        """
        Format a dictionary as a Rich table.
        
        Args:
            data: The dictionary to format
            
        Returns:
            Rich Table object
        """
        table = Table(show_header=True, header_style="bold")
        table.add_column("Property")
        table.add_column("Value")
        
        for key, value in data.items():
            if isinstance(value, dict):
                nested_table = self._format_dict_as_rich(value)
                table.add_row(key, nested_table)
            elif isinstance(value, list):
                nested_table = self._format_list_as_rich(value)
                table.add_row(key, nested_table)
            else:
                table.add_row(key, str(value))
        
        return table
    
    def _format_list_as_rich(self, data: List[Any]) -> Table:
        """
        Format a list as a Rich table.
        
        Args:
            data: The list to format
            
        Returns:
            Rich Table object
        """
        table = Table(show_header=True, header_style="bold")
        table.add_column("Index")
        table.add_column("Value")
        
        for i, item in enumerate(data):
            if isinstance(item, dict):
                nested_table = self._format_dict_as_rich(item)
                table.add_row(str(i), nested_table)
            elif isinstance(item, list):
                nested_table = self._format_list_as_rich(item)
                table.add_row(str(i), nested_table)
            else:
                table.add_row(str(i), str(item))
        
        return table