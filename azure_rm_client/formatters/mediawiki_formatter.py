from typing import Dict, Any, List
from .formatter_interface import FormatterInterface


class MediaWikiFormatter(FormatterInterface):
    """
    Formatter for MediaWiki output.
    
    This formatter outputs data in MediaWiki markup format.
    """
    
    def format_data(self, data: Dict[str, Any]) -> str:
        """
        Format the provided data as MediaWiki markup.
        
        Args:
            data: The data to format
            
        Returns:
            MediaWiki markup representation of the data
        """
        lines = ["= Azure Resource Manager API =", ""]
        self._format_dict(data, lines, 2)
        return "\n".join(lines)
    
    def _format_dict(self, data: Dict[str, Any], lines: List[str], heading_level: int) -> None:
        """
        Format a dictionary as MediaWiki markup.
        
        Args:
            data: The dictionary to format
            lines: The list of lines to append to
            heading_level: The heading level (1-6)
        """
        heading_markers = "=" * heading_level
        
        for key, value in data.items():
            if isinstance(value, dict):
                lines.append(f"{heading_markers} {key} {heading_markers}")
                lines.append("")
                self._format_dict(value, lines, heading_level + 1)
            elif isinstance(value, list):
                lines.append(f"{heading_markers} {key} {heading_markers}")
                lines.append("")
                self._format_list(value, lines)
                lines.append("")
            else:
                lines.append(f"'''{key}''': {value}")
                lines.append("")
    
    def _format_list(self, data: List[Any], lines: List[str]) -> None:
        """
        Format a list as MediaWiki bullet points.
        
        Args:
            data: The list to format
            lines: The list of lines to append to
        """
        for item in data:
            if isinstance(item, dict):
                # Create a table for dictionary items
                lines.append("{| class=\"wikitable\"")
                lines.append("! Key !! Value")
                
                for k, v in item.items():
                    if isinstance(v, (dict, list)):
                        lines.append("|-")
                        lines.append(f"| '''{k}''' || ''(complex type)''")
                    else:
                        lines.append("|-")
                        lines.append(f"| '''{k}''' || {v}")
                
                lines.append("|}")
                lines.append("")
            else:
                lines.append(f"* {item}")
                lines.append("")