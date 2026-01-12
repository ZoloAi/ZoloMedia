"""
Generator framework for converting themes to editor-specific formats.

Base class for all editor generators.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any
from ..  import Theme


class BaseGenerator(ABC):
    """
    Abstract base class for theme generators.
    
    Each editor (Vim, VS Code, Cursor) implements this interface
    to convert the canonical theme format to editor-specific config.
    """
    
    def __init__(self, theme: Theme):
        """
        Initialize generator with a theme.
        
        Args:
            theme: Theme object to generate from
        """
        self.theme = theme
        self.editor_name = self._get_editor_name()
        self.overrides = theme.get_editor_overrides(self.editor_name)
    
    @abstractmethod
    def _get_editor_name(self) -> str:
        """Return the editor name (e.g., 'vim', 'vscode')."""
        pass
    
    @abstractmethod
    def generate(self) -> str:
        """
        Generate editor-specific configuration.
        
        Returns:
            String containing the editor-specific config
            (e.g., Vim script, JSON, XML)
        """
        pass
    
    def _format_style(self, style: str) -> Dict[str, Any]:
        """
        Convert generic style (none, bold, italic) to editor format.
        
        Override in subclasses for editor-specific formatting.
        
        Args:
            style: Generic style string
        
        Returns:
            Dictionary with editor-specific style attributes
        """
        return {
            'bold': style == 'bold',
            'italic': style == 'italic',
            'none': style == 'none',
        }


__all__ = ['BaseGenerator']
