"""
Hover Provider for .zolo Language Server (Thin Wrapper)

Provides hover information showing:
- Type hints and their meanings (from DocumentationRegistry)
- Detected value types
- Key documentation
- Valid values

This is a THIN WRAPPER that delegates to HoverRenderer.
All logic is in provider_modules/hover_renderer.py for modularity.
"""

from typing import Optional
from ..parser.parser import tokenize
from .provider_modules.hover_renderer import HoverRenderer


def get_hover_info(content: str, line: int, character: int) -> Optional[str]:
    """
    Get hover information at a specific position (thin wrapper).
    
    Args:
        content: Full .zolo file content
        line: Line number (0-based)
        character: Character position (0-based)
    
    Returns:
        Markdown string with hover information, or None
    
    Examples:
        >>> content = "port(int): 8080"
        >>> info = get_hover_info(content, 0, 5)  # Hovering over "int"
        >>> "Integer" in info
        True
    
    Implementation:
        This function is a thin wrapper that:
        1. Tokenizes the content using the parser
        2. Delegates to HoverRenderer for formatting
        3. Returns formatted markdown
    
    All hover logic is in provider_modules/hover_renderer.py.
    All documentation is in provider_modules/documentation_registry.py.
    Zero duplication!
    """
    # Parse content and get tokens
    try:
        result = tokenize(content)
        tokens = result.tokens
    except Exception:
        return None
    
    # Delegate to HoverRenderer
    return HoverRenderer.render(content, line, character, tokens)
