"""
zTheme to ANSI Color Mapper - Phase 2

Maps zTheme CSS color classes to ANSI terminal codes.
Provides the bridge between web styling and terminal display.

Example:
    <span class="zText-error">text</span> → red ANSI text (no HTML)
    
Author: zOS Framework
Version: 1.0.0 (Phase 2)
"""

try:
    from .colors import Colors
except ImportError:
    # Fallback for direct imports
    from colors import Colors


# Map zTheme text color classes to Colors.py ANSI codes
ZTHEME_TEXT_COLOR_MAP = {
    # Semantic colors (aligned with CSS variables)
    'zText-error': Colors.zError,       # Red
    'zText-danger': Colors.zError,      # Alias for error
    'zText-success': Colors.zSuccess,   # Green
    'zText-warning': Colors.zWarning,   # Orange/Yellow
    'zText-info': Colors.zInfo,         # Blue
    
    # Brand colors
    'zText-primary': Colors.PRIMARY,    # Light green
    'zText-secondary': Colors.SECONDARY,  # Purple
    'zText-accent': Colors.CYAN,        # Cyan
    
    # Utility colors
    'zText-muted': Colors.ANSI_DIM if hasattr(Colors, 'ANSI_DIM') else '\033[2m',  # Dim/gray
    'zText-white': '\033[97m',          # Bright white
    'zText-dark': '\033[90m',           # Dark gray
    
    # Background colors (for callouts, etc.)
    'zBg-error': Colors.ERROR,          # Dark red bg
    'zBg-warning': Colors.WARNING,      # Orange bg
    'zBg-success': '\033[42m',          # Green bg
    'zBg-info': '\033[44m',             # Blue bg
    'zBg-light': '\033[47m',            # Light/white bg
    'zBg-dark': '\033[40m',             # Dark/black bg
}

# Map zTheme font weight classes to ANSI codes
ZTHEME_FONT_WEIGHT_MAP = {
    'zFont-bold': '\033[1m',            # Bold
    'zFw-bold': '\033[1m',              # Shorthand
    'zFont-normal': '\033[22m',         # Normal weight (cancel bold)
    'zFw-normal': '\033[22m',           # Shorthand
}

# Map zTheme font style classes to ANSI codes
ZTHEME_FONT_STYLE_MAP = {
    'zFont-italic': '\033[3m',          # Italic (not all terminals)
    'zFs-italic': '\033[3m',            # Shorthand
    'zFont-normal': '\033[23m',         # Normal style (cancel italic)
}


def map_ztheme_class_to_ansi(class_name: str) -> str:
    """
    Convert a single zTheme class to its ANSI code.
    
    Args:
        class_name: zTheme CSS class (e.g., 'zText-error', 'zFont-bold')
        
    Returns:
        ANSI code string, or empty string if class not recognized
        
    Example:
        >>> map_ztheme_class_to_ansi('zText-error')
        '\033[38;5;203m'  # Red color code
    """
    # Check text colors
    if class_name in ZTHEME_TEXT_COLOR_MAP:
        return ZTHEME_TEXT_COLOR_MAP[class_name]
    
    # Check font weight
    if class_name in ZTHEME_FONT_WEIGHT_MAP:
        return ZTHEME_FONT_WEIGHT_MAP[class_name]
    
    # Check font style
    if class_name in ZTHEME_FONT_STYLE_MAP:
        return ZTHEME_FONT_STYLE_MAP[class_name]
    
    # Class not recognized - return empty string
    return ''


def map_ztheme_classes_to_ansi(classes: list) -> str:
    """
    Convert multiple zTheme classes to combined ANSI codes.
    
    Handles multiple classes like: class="zText-error zFont-bold"
    
    Args:
        classes: List of class names
        
    Returns:
        Combined ANSI codes string
        
    Example:
        >>> map_ztheme_classes_to_ansi(['zText-error', 'zFont-bold'])
        '\033[38;5;203m\033[1m'  # Red + bold
    """
    ansi_codes = []
    
    for class_name in classes:
        code = map_ztheme_class_to_ansi(class_name.strip())
        if code:
            ansi_codes.append(code)
    
    return ''.join(ansi_codes)


def get_reset_code() -> str:
    """
    Get the ANSI reset code to restore default formatting.
    
    Returns:
        ANSI reset code
    """
    return Colors.RESET


# Convenience function for the most common use case
def colorize_with_class(text: str, class_name: str) -> str:
    """
    Apply zTheme class color to text with ANSI codes.
    
    Args:
        text: Text to colorize
        class_name: zTheme class name
        
    Returns:
        Text wrapped in ANSI color codes
        
    Example:
        >>> colorize_with_class('Error!', 'zText-error')
        '\033[38;5;203mError!\033[0m'
    """
    ansi_code = map_ztheme_class_to_ansi(class_name)
    if ansi_code:
        return f"{ansi_code}{text}{Colors.RESET}"
    return text


# Export main functions
__all__ = [
    'map_ztheme_class_to_ansi',
    'map_ztheme_classes_to_ansi',
    'get_reset_code',
    'colorize_with_class',
    'ZTHEME_TEXT_COLOR_MAP',
]
