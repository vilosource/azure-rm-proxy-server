from abc import ABC, abstractmethod
from typing import Dict, Any, List


class FormatterInterface(ABC):
    """
    Abstract base class for all formatters.
    Enforces implementation of required methods.
    """

    @abstractmethod
    def format(self, data: Any) -> str:
        """
        Format the provided data.

        Args:
            data: The data to format

        Returns:
            String representation of the formatted data
        """
        pass

    @abstractmethod
    def format_data(self, data: Any) -> str:
        """
        Format the provided data (detailed implementation).

        Args:
            data: The data to format

        Returns:
            String representation of the formatted data
        """
        pass


class FormatterFactory:
    """
    Factory for creating formatter instances.
    This follows the Factory Pattern to decouple formatter creation from usage.
    """
    
    def __init__(self):
        self._formatters = {}
    
    def register_formatter(self, format_type: str, formatter_class):
        """
        Register a formatter class for a specific format type.
        
        Args:
            format_type: The format type identifier
            formatter_class: The formatter class to register
        """
        self._formatters[format_type] = formatter_class
    
    def create_formatter(self, format_type: str) -> FormatterInterface:
        """
        Create a formatter instance for the specified format type.
        
        Args:
            format_type: The format type identifier
            
        Returns:
            An instance of the formatter for the specified format type
            
        Raises:
            ValueError: If the format type is not registered
        """
        formatter_class = self._formatters.get(format_type)
        if formatter_class is None:
            raise ValueError(f"No formatter registered for format type: {format_type}")
        return formatter_class()
    
    def get_available_formats(self) -> List[str]:
        """
        Get a list of all available format types.
        
        Returns:
            List of available format types
        """
        return list(self._formatters.keys())