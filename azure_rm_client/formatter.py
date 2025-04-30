import logging
from typing import Dict, Any, Optional
from azure_rm_client.formatters import get_formatter, get_available_formats

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FormatterFacade:
    """
    Facade for formatter operations.
    
    This class provides a simplified interface for formatting operations.
    It encapsulates the complexity of working with multiple formatters behind a simple interface.
    """
    
    @staticmethod
    def get_available_formats() -> list:
        """
        Get a list of all available format types.
        
        Returns:
            List of available format types
        """
        return get_available_formats()
    
    @staticmethod
    def format_data(data: Dict[str, Any], format_type: Optional[str] = None) -> str:
        """
        Format the provided data using the specified formatter.
        
        Args:
            data: The data to format
            format_type: The format type to use (default: None, uses the default formatter)
            
        Returns:
            Formatted string representation of the data
            
        Raises:
            ValueError: If the format type is not registered
        """
        formatter = get_formatter(format_type)
        return formatter.format_data(data)
    
    @staticmethod
    def save_formatted_data(data: Dict[str, Any], file_path: str, format_type: Optional[str] = None) -> bool:
        """
        Format the provided data and save it to a file.
        
        Args:
            data: The data to format
            file_path: The path to save the formatted data to
            format_type: The format type to use (default: None, uses the default formatter)
            
        Returns:
            True if the data was formatted and saved successfully, False otherwise
            
        Raises:
            ValueError: If the format type is not registered
        """
        try:
            formatted_data = FormatterFacade.format_data(data, format_type)
            with open(file_path, "w") as f:
                f.write(formatted_data)
            logger.info(f"Formatted data saved to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save formatted data to {file_path}: {e}")
            return False