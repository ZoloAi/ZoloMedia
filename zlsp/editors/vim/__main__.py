"""
Allow running zlsp Vim installer as a module.

Usage:
    python -m zlsp.vim
"""
from .install import main

if __name__ == '__main__':
    main()
