"""
zSys Accessibility Module

Provides accessibility features across the zOS framework, including:
- Emoji descriptions for screen readers and Terminal mode
- ARIA label generation for web interfaces
- Accessibility utilities

Author: zOS Framework
Version: 1.0.0
"""

from .emoji_descriptions import (
    EmojiDescriptions,
    get_emoji_descriptions,
)

__all__ = [
    'EmojiDescriptions',
    'get_emoji_descriptions',
]
