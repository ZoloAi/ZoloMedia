"""
Completion Provider for .zolo Language Server (Thin Wrapper)

Provides smart autocomplete for:
- Type hints when typing inside () (from DocumentationRegistry)
- Common values (true, false, null) (from DocumentationRegistry)
- File-type-specific completions (zSpark, zUI, zSchema)
- Context-aware suggestions

This is a THIN WRAPPER that delegates to CompletionRegistry.
All logic is in provider_modules/completion_registry.py for modularity.
"""

from typing import List, Optional
from lsprotocol import types as lsp_types
from .provider_modules.completion_registry import CompletionContext, CompletionRegistry


def get_completions(
    content: str,
    line: int,
    character: int,
    filename: Optional[str] = None
) -> List[lsp_types.CompletionItem]:
    """
    Get completion items at a specific position (thin wrapper).
    
    Detects context and provides appropriate completions:
    1. Inside () → type hint completions (from DocumentationRegistry)
    2. After : → value completions (from DocumentationRegistry)
    3. File-type-specific completions (zSpark, zUI, zSchema)
    4. Context-aware suggestions based on cursor position
    
    Args:
        content: Full .zolo file content
        line: Line number (0-based)
        character: Character position (0-based)
        filename: Optional filename for file-type-specific completions
    
    Returns:
        List of completion items
    
    Implementation:
        This function is a thin wrapper that:
        1. Creates a CompletionContext with cursor position and file info
        2. Delegates to CompletionRegistry for generating completions
        3. Returns context-aware completion items
    
    All completion logic is in provider_modules/completion_registry.py.
    All documentation is in provider_modules/documentation_registry.py.
    Zero duplication!
    """
    # Create completion context
    context = CompletionContext(
        content=content,
        line=line,
        character=character,
        filename=filename
    )
    
    # Delegate to CompletionRegistry
    return CompletionRegistry.get_completions(context)
