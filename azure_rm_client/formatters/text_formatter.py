from typing import Dict, Any
from .formatter_interface import FormatterInterface


class TextFormatter(FormatterInterface):
    """
    Formatter for plain text output.
    
    This formatter outputs data as a simple text representation.
    """
    
    def format_data(self, data: Dict[str, Any]) -> str:
        """
        Format the provided data as plain text.
        
        Args:
            data: The data to format
            
        Returns:
            Plain text representation of the data
        """
        lines = []
        self._format_dict(data, lines, 0)
        return "\n".join(lines)
    
    def _format_dict(self, data: Dict[str, Any], lines: list, indent: int) -> None:
        """
        Format a dictionary as plain text.
        
        Args:
            data: The dictionary to format
            lines: The list of lines to append to
            indent: The indentation level
        """
        for key, value in data.items():
            indent_str = "  " * indent
            if isinstance(value, dict):
                lines.append(f"{indent_str}{key}:")
                self._format_dict(value, lines, indent + 1)
            elif isinstance(value, list):
                lines.append(f"{indent_str}{key}:")
                self._format_list(value, lines, indent + 1)
            else:
                lines.append(f"{indent_str}{key}: {value}")
    
    def _format_list(self, data: list, lines: list, indent: int) -> None:
        """
        Format a list as plain text.
        
        Args:
            data: The list to format
            lines: The list of lines to append to
            indent: The indentation level
        """
        indent_str = "  " * indent
        for i, item in enumerate(data):
            if isinstance(item, dict):
                lines.append(f"{indent_str}- Item {i+1}:")
                self._format_dict(item, lines, indent + 1)
            elif isinstance(item, list):
                lines.append(f"{indent_str}- Item {i+1}:")
                self._format_list(item, lines, indent + 1)
            else:
                lines.append(f"{indent_str}- {item}")