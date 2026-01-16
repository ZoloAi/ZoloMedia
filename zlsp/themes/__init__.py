"""
Theme system for zlsp - Single source of truth for all editor color schemes.

Provides utilities to load theme definitions and generate editor-specific configs.

Note: Theme loading requires PyYAML (install with: pip install zlsp[themes])
"""
from pathlib import Path
from typing import Dict, Any, Optional, List
import re


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
        
        # Code actions (LSP quick fixes & refactorings)
        self.code_actions = data.get('code_actions', {})
        self.code_action_config = data.get('code_action_config', {})
    
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
    
    def get_code_action(self, action_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific code action by ID.
        
        Args:
            action_id: Action ID (e.g., 'add_type_hint')
        
        Returns:
            Action configuration dictionary, or None if not found
        """
        return self.code_actions.get(action_id)
    
    def get_enabled_actions(self) -> List[Dict[str, Any]]:
        """
        Get all enabled code actions, sorted by priority.
        
        Returns:
            List of enabled action configurations
        """
        enabled = [
            {**action, '_id': action_id}
            for action_id, action in self.code_actions.items()
            if action.get('enabled', False)
        ]
        
        # Sort by priority (higher first)
        if self.code_action_config.get('sort_by_priority', True):
            enabled.sort(key=lambda a: a.get('priority', 0), reverse=True)
        
        return enabled
    
    def get_actions_by_category(self, category: str) -> List[Dict[str, Any]]:
        """
        Get all enabled actions in a specific category.
        
        Args:
            category: Category name (e.g., 'quickfix', 'refactor')
        
        Returns:
            List of enabled actions in that category
        """
        return [
            action for action in self.get_enabled_actions()
            if action.get('category') == category
        ]


class CodeActionRegistry:
    """
    Registry for managing and querying code actions from a theme.
    
    Provides advanced filtering and matching capabilities for LSP code actions.
    """
    
    def __init__(self, theme: Theme):
        """
        Initialize registry with a theme.
        
        Args:
            theme: Theme object containing code actions
        """
        self.theme = theme
        self.actions = self._load_and_validate_actions()
        self.config = theme.code_action_config
    
    def _load_and_validate_actions(self) -> List[Dict[str, Any]]:
        """
        Load enabled actions and validate their configuration.
        
        Returns:
            List of validated, enabled actions
        """
        actions = []
        for action in self.theme.get_enabled_actions():
            if self._validate_action(action):
                actions.append(action)
            else:
                # Log warning but don't fail
                action_id = action.get('_id', 'unknown')
                print(f"Warning: Invalid action configuration for '{action_id}'")
        
        return actions
    
    def _validate_action(self, action: Dict[str, Any]) -> bool:
        """
        Validate that an action has all required fields.
        
        Args:
            action: Action configuration dictionary
        
        Returns:
            True if valid, False otherwise
        """
        required_fields = ['id', 'title', 'triggers', 'execution']
        return all(field in action for field in required_fields)
    
    def get_actions_for_diagnostic(self, diagnostic_message: str) -> List[Dict[str, Any]]:
        """
        Find actions that match a diagnostic message.
        
        Args:
            diagnostic_message: The diagnostic message text
        
        Returns:
            List of matching actions, sorted by priority
        """
        matching = []
        
        for action in self.actions:
            triggers = action.get('triggers', {})
            diagnostic_patterns = triggers.get('diagnostics', [])
            
            # Check if any pattern matches
            for pattern_config in diagnostic_patterns:
                pattern = pattern_config.get('pattern', '')
                case_sensitive = pattern_config.get('case_sensitive', False)
                
                if self._matches_pattern(diagnostic_message, pattern, case_sensitive):
                    matching.append(action)
                    break  # Don't add same action twice
        
        return matching
    
    def _matches_pattern(self, text: str, pattern: str, case_sensitive: bool) -> bool:
        """
        Check if text contains pattern.
        
        Args:
            text: Text to search in
            pattern: Pattern to search for
            case_sensitive: Whether to match case-sensitively
        
        Returns:
            True if pattern found in text
        """
        if not case_sensitive:
            text = text.lower()
            pattern = pattern.lower()
        
        return pattern in text
    
    def get_actions_for_file(self, filename: str) -> List[Dict[str, Any]]:
        """
        Find actions that apply to a specific file.
        
        Args:
            filename: Name of the file (e.g., 'zSchema.users.zolo')
        
        Returns:
            List of actions that match file patterns
        """
        matching = []
        
        for action in self.actions:
            triggers = action.get('triggers', {})
            file_patterns = triggers.get('file_patterns', [])
            
            if not file_patterns:
                # No file pattern = applies to all files
                matching.append(action)
                continue
            
            # Check if filename matches any pattern
            for pattern in file_patterns:
                if self._matches_file_pattern(filename, pattern):
                    matching.append(action)
                    break
        
        return matching
    
    def _matches_file_pattern(self, filename: str, pattern: str) -> bool:
        """
        Check if filename matches a glob-like pattern.
        
        Args:
            filename: Filename to check
            pattern: Pattern (e.g., 'zSchema.*.zolo')
        
        Returns:
            True if filename matches pattern
        """
        # Convert glob pattern to regex
        regex_pattern = pattern.replace('.', r'\.')
        regex_pattern = regex_pattern.replace('*', '.*')
        regex_pattern = f'^{regex_pattern}$'
        
        return bool(re.match(regex_pattern, filename))
    
    def get_max_actions(self) -> int:
        """Get maximum number of actions to show from config."""
        return self.config.get('max_actions_per_context', 5)
    
    def is_enabled(self) -> bool:
        """Check if code actions system is enabled globally."""
        return self.config.get('enabled', True)


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


__all__ = ['Theme', 'CodeActionRegistry', 'load_theme', 'list_themes']
