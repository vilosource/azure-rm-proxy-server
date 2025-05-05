from .formatter_interface import FormatterInterface, FormatterFactory
from .json_formatter import JsonFormatter
from .text_formatter import TextFormatter
from .markdown_formatter import MarkdownFormatter
from .rich_formatter import RichFormatter
from .mediawiki_formatter import MediaWikiFormatter
from .table_formatter import TableFormatter
from .yaml_formatter import YamlFormatter

# Create the formatter factory and register formatters
formatter_factory = FormatterFactory()
formatter_factory.register_formatter("json", JsonFormatter)
formatter_factory.register_formatter("text", TextFormatter)
formatter_factory.register_formatter("markdown", MarkdownFormatter)
formatter_factory.register_formatter("rich", RichFormatter)
formatter_factory.register_formatter("mediawiki", MediaWikiFormatter)
formatter_factory.register_formatter("table", TableFormatter)  # Register the new TableFormatter
formatter_factory.register_formatter("yaml", YamlFormatter)

# Default formatter
DEFAULT_FORMATTER = "rich"

def get_formatter_factory() -> FormatterFactory:
    """
    Get the formatter factory instance.
    
    Returns:
        The formatter factory
    """
    return formatter_factory

def get_formatter(format_type: str = None) -> FormatterInterface:
    """
    Get a formatter for the specified format type.
    
    Args:
        format_type: The format type identifier (defaults to the DEFAULT_FORMATTER if None)
        
    Returns:
        A formatter instance
        
    Raises:
        ValueError: If the format type is not registered
    """
    if format_type is None:
        format_type = DEFAULT_FORMATTER
    return formatter_factory.create_formatter(format_type)

def get_available_formats() -> list:
    """
    Get a list of all available format types.
    
    Returns:
        List of available format types
    """
    return formatter_factory.get_available_formats()