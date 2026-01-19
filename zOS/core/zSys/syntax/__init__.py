"""
zSys Syntax Highlighting Module

Custom syntax highlighting for zOS-specific languages:
- .zolo (declarative configuration)

Provides Pygments lexers for Terminal syntax highlighting.
"""

from .zolo_lexer import ZoloLexer

__all__ = ['ZoloLexer']
