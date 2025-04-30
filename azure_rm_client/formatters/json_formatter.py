import json
from typing import Dict, Any
from .formatter_interface import FormatterInterface


class JsonFormatter(FormatterInterface):
    """
    Formatter for JSON output.
    
    This formatter outputs data as a formatted JSON string.
    """
    
    def format_data(self, data: Dict[str, Any]) -> str:
        """
        Format the provided data as a JSON string.
        
        Args:
            data: The data to format
            
        Returns:
            JSON string representation of the data
        """
        return json.dumps(data, indent=2)