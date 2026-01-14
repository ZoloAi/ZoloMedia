"""
Provider Modules - Modular LSP Provider Components

This package contains focused modules for LSP provider functionality:
- documentation_registry: Single Source of Truth for all documentation
- completion_registry: Context-aware completion generation
- hover_renderer: Hover information formatting
- completion_context: Cursor context detection
- diagnostic_formatter: Diagnostic message formatting

Following the same modular architecture as parser_modules/.
"""

from .documentation_registry import (
    Documentation,
    DocumentationType,
    DocumentationRegistry,
)

from .completion_registry import (
    CompletionContext,
    CompletionRegistry,
)

from .hover_renderer import (
    HoverRenderer,
)

from .diagnostic_formatter import (
    DiagnosticFormatter,
)

__all__ = [
    # Documentation Registry
    'Documentation',
    'DocumentationType',
    'DocumentationRegistry',
    # Completion Registry
    'CompletionContext',
    'CompletionRegistry',
    # Hover Renderer
    'HoverRenderer',
    # Diagnostic Formatter
    'DiagnosticFormatter',
]
