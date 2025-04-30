from typing import Dict, Any, List
from .formatter_interface import FormatterInterface


class MarkdownFormatter(FormatterInterface):
    """
    Formatter for Markdown output.
    
    This formatter outputs data as a Markdown document.
    """
    
    def format_data(self, data: Dict[str, Any]) -> str:
        """
        Format the provided data as Markdown.
        
        Args:
            data: The data to format
            
        Returns:
            Markdown representation of the data
        """
        lines = ["# Azure Resource Manager API", ""]
        self._format_dict(data, lines, 1)
        return "\n".join(lines)
    
    def _format_dict(self, data: Dict[str, Any], lines: List[str], heading_level: int) -> None:
        """
        Format a dictionary as Markdown.
        
        Args:
            data: The dictionary to format
            lines: The list of lines to append to
            heading_level: The heading level (1-6)
        """
        for key, value in data.items():
            heading_prefix = "#" * min(heading_level, 6)
            if isinstance(value, dict):
                lines.append(f"{heading_prefix} {key}")
                lines.append("")
                self._format_dict(value, lines, heading_level + 1)
            elif isinstance(value, list):
                lines.append(f"{heading_prefix} {key}")
                lines.append("")
                self._format_list(value, lines)
            else:
                lines.append(f"**{key}**: {value}")
                lines.append("")
    
    def _format_list(self, data: List[Any], lines: List[str]) -> None:
        """
        Format a list as Markdown bullet points.
        
        Args:
            data: The list to format
            lines: The list of lines to append to
        """
        for item in data:
            if isinstance(item, dict):
                lines.append("<details>")
                lines.append("<summary>Details</summary>")
                lines.append("")
                
                # Create a nested list for the dictionary items
                item_lines = []
                for k, v in item.items():
                    if isinstance(v, (dict, list)):
                        item_lines.append(f"- **{k}**: (complex type)")
                    else:
                        item_lines.append(f"- **{k}**: {v}")
                
                lines.extend(item_lines)
                lines.append("")
                lines.append("</details>")
                lines.append("")
            else:
                lines.append(f"- {item}")
                lines.append("")