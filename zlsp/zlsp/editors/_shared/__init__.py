"""
Shared utilities for editor integrations.

This module provides common functionality for VS Code-based editors
(VS Code, Cursor, etc.) to avoid code duplication.
"""

from .vscode_base import VSCodeBasedInstaller

__all__ = ['VSCodeBasedInstaller']
