"""
Theme system for zlsp - Single source of truth for all editor color schemes.

Provides utilities to load theme definitions and generate editor-specific configs.

Note: Theme loading requires PyYAML (install with: pip install zlsp[themes])
"""
from pathlib import Path
from typing import Dict, Any, Optional


class Theme:
    """Represents a zlsp color theme."""
    
    def __init__(self, data: Dict[str, Any]):
        self.data = data
        self.name = data.get('name', 'Unnamed Theme')
        self.description = data.get('description', '')
        self.version = data.get('version', '1.0.0')
        self.author = data.get('author', '')
        
        self.palette = data.get('palette', {})
        self.tokens = data.get('tokens', {})
        self.overrides = data.get('overrides', {})
        self.metadata = data.get('metadata', {})
    
    def get_color(self, color_name: str, format: str = 'hex') -> Optional[str]:
        """
        Get a color from the palette in the specified format.
        
        Args:
            color_name: Name of the color (e.g., 'salmon_orange')
            format: Format to return ('hex', 'ansi', 'rgb')
        
        Returns:
            Color value in the requested format, or None if not found
        """
        if color_name not in self.palette:
            return None
        
        color_data = self.palette[color_name]
        
        if format == 'hex':
            return color_data.get('hex')
        elif format == 'ansi':
            return color_data.get('ansi')
        elif format == 'rgb':
            return color_data.get('rgb')
        else:
            return color_data.get(format)
    
    def get_token_style(self, token_type: str) -> Optional[Dict[str, Any]]:
        """
        Get the complete style definition for a token type.
        
        Args:
            token_type: Token type (e.g., 'rootKey', 'string')
        
        Returns:
            Dictionary with 'color', 'style', and 'description' keys
        """
        if token_type not in self.tokens:
            return None
        
        token_data = self.tokens[token_type]
        color_name = token_data.get('color')
        
        # Resolve color to full palette entry
        color_data = self.palette.get(color_name, {})
        
        return {
            'color_name': color_name,
            'color_data': color_data,
            'style': token_data.get('style', 'none'),
            'description': token_data.get('description', ''),
            'hex': color_data.get('hex'),
            'ansi': color_data.get('ansi'),
            'rgb': color_data.get('rgb'),
        }
    
    def get_editor_overrides(self, editor: str) -> Dict[str, Any]:
        """
        Get editor-specific overrides.
        
        Args:
            editor: Editor name (e.g., 'vim', 'vscode')
        
        Returns:
            Dictionary of overrides for that editor
        """
        return self.overrides.get(editor, {})


def load_theme(name: str = 'zolo_default') -> Theme:
    """
    Load a theme by name.
    
    Args:
        name: Theme name (without .yaml extension)
    
    Returns:
        Theme object
    
    Raises:
        FileNotFoundError: If theme file doesn't exist
        ImportError: If PyYAML is not installed
        yaml.YAMLError: If theme file is invalid
    """
    try:
        import yaml
    except ImportError:
        raise ImportError(
            "PyYAML is required for theme loading. "
            "Install it with: pip install zlsp[themes]"
        ) from None
    
    themes_dir = Path(__file__).parent
    theme_file = themes_dir / f'{name}.yaml'
    
    if not theme_file.exists():
        raise FileNotFoundError(f"Theme '{name}' not found at {theme_file}")
    
    with open(theme_file, 'r') as f:
        data = yaml.safe_load(f)
    
    return Theme(data)


def list_themes() -> list[str]:
    """
    List all available themes.
    
    Returns:
        List of theme names (without .yaml extension)
    """
    themes_dir = Path(__file__).parent
    theme_files = themes_dir.glob('*.yaml')
    return [f.stem for f in theme_files]


__all__ = ['Theme', 'load_theme', 'list_themes']
