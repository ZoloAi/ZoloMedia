"""
zlsp Vim Integration

This package contains Vim plugin files for .zolo file support.

To install the Vim integration:
    python -m zlsp.vim

Or use the convenience command:
    zolo-vim-install
"""

from .install import main as install_vim

__all__ = ['install_vim']
