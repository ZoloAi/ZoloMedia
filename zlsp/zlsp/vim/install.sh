#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════
# Zolo LSP Vim Installation Script
# ═══════════════════════════════════════════════════════════════
#
# This script installs Zolo LSP support for Vim/Neovim.
#
# What it does:
#   1. Installs the zolo Python package (LSP server)
#   2. Copies Vim configuration files to your Vim config directory
#   3. Sets up filetype detection for .zolo files
#
# Usage:
#   ./install.sh [--neovim|--vim]
#
# ═══════════════════════════════════════════════════════════════

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Detect editor
EDITOR_TYPE=""
if [ "$1" = "--neovim" ] || [ "$1" = "--nvim" ]; then
    EDITOR_TYPE="neovim"
elif [ "$1" = "--vim" ]; then
    EDITOR_TYPE="vim"
else
    # Auto-detect
    if command -v nvim &> /dev/null; then
        EDITOR_TYPE="neovim"
    elif command -v vim &> /dev/null; then
        EDITOR_TYPE="vim"
    else
        echo -e "${RED}✗ Neither Vim nor Neovim found${NC}"
        exit 1
    fi
fi

echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Zolo LSP Installation for $EDITOR_TYPE${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

# Set config directory
if [ "$EDITOR_TYPE" = "neovim" ]; then
    VIM_DIR="$HOME/.config/nvim"
else
    VIM_DIR="$HOME/.vim"
fi

# Get script directory (where this script is located)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
# Go up 2 levels: zlsp/vim -> zlsp -> zLSP
ZLSP_ROOT="$( cd "$SCRIPT_DIR/../.." && pwd )"

echo -e "${YELLOW}→${NC} Vim config directory: $VIM_DIR"
echo -e "${YELLOW}→${NC} zLSP root: $ZLSP_ROOT"
echo ""

# ───────────────────────────────────────────────────────────────
# Step 1: Install Python package
# ───────────────────────────────────────────────────────────────
echo -e "${BLUE}[1/4]${NC} Installing zolo Python package..."

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python 3 not found${NC}"
    exit 1
fi

# Check if already installed
if python3 -c "import zlsp" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} zlsp package already installed"
else
    echo -e "${YELLOW}→${NC} Installing zlsp package..."
    pip3 install -e "$ZLSP_ROOT" || {
        echo -e "${RED}✗ Failed to install zlsp package${NC}"
        exit 1
    }
    echo -e "${GREEN}✓${NC} zlsp package installed"
fi

# Verify zolo-lsp command
if ! command -v zolo-lsp &> /dev/null; then
    echo -e "${RED}✗ zolo-lsp command not found in PATH${NC}"
    echo -e "${YELLOW}  Try: export PATH=\"\$HOME/.local/bin:\$PATH\"${NC}"
    exit 1
fi
echo -e "${GREEN}✓${NC} zolo-lsp command available"
echo ""

# ───────────────────────────────────────────────────────────────
# Step 2: Create Vim directories
# ───────────────────────────────────────────────────────────────
echo -e "${BLUE}[2/4]${NC} Creating Vim directories..."

mkdir -p "$VIM_DIR/ftdetect"
mkdir -p "$VIM_DIR/ftplugin"
mkdir -p "$VIM_DIR/after/ftplugin"
mkdir -p "$VIM_DIR/indent"
mkdir -p "$VIM_DIR/syntax"

echo -e "${GREEN}✓${NC} Directories created"
echo ""

# ───────────────────────────────────────────────────────────────
# Step 3: Copy configuration files
# ───────────────────────────────────────────────────────────────
echo -e "${BLUE}[3/4]${NC} Installing Vim configuration files..."

# Filetype detection
cp "$SCRIPT_DIR/ftdetect/zolo.vim" "$VIM_DIR/ftdetect/zolo.vim"
echo -e "${GREEN}✓${NC} Installed ftdetect/zolo.vim"

# Filetype plugin (basic settings)
cp "$SCRIPT_DIR/ftplugin/zolo.vim" "$VIM_DIR/ftplugin/zolo.vim"
echo -e "${GREEN}✓${NC} Installed ftplugin/zolo.vim"

# LSP configuration (loads after ftplugin)
cp "$SCRIPT_DIR/lsp_config.vim" "$VIM_DIR/after/ftplugin/zolo.vim"
echo -e "${GREEN}✓${NC} Installed after/ftplugin/zolo.vim (LSP config)"

# Syntax highlighting (fallback)
cp "$SCRIPT_DIR/syntax/zolo.vim" "$VIM_DIR/syntax/zolo.vim"
echo -e "${GREEN}✓${NC} Installed syntax/zolo.vim"

# Indentation
cp "$SCRIPT_DIR/indent/zolo.vim" "$VIM_DIR/indent/zolo.vim"
echo -e "${GREEN}✓${NC} Installed indent/zolo.vim"

echo ""

# ───────────────────────────────────────────────────────────────
# Step 4: Neovim-specific setup
# ───────────────────────────────────────────────────────────────
if [ "$EDITOR_TYPE" = "neovim" ]; then
    echo -e "${BLUE}[4/4]${NC} Neovim-specific setup..."
    
    # Check Neovim version
    NVIM_VERSION=$(nvim --version | head -n1 | grep -oE '[0-9]+\.[0-9]+' | head -n1)
    NVIM_MAJOR=$(echo "$NVIM_VERSION" | cut -d. -f1)
    NVIM_MINOR=$(echo "$NVIM_VERSION" | cut -d. -f2)
    
    if [ "$NVIM_MAJOR" -lt 0 ] || ([ "$NVIM_MAJOR" -eq 0 ] && [ "$NVIM_MINOR" -lt 8 ]); then
        echo -e "${YELLOW}⚠${NC}  Neovim version $NVIM_VERSION detected"
        echo -e "${YELLOW}   LSP requires Neovim 0.8+. Consider upgrading.${NC}"
    else
        echo -e "${GREEN}✓${NC} Neovim $NVIM_VERSION (LSP supported)"
    fi
else
    echo -e "${BLUE}[4/4]${NC} Vim-specific setup..."
    
    # Check if vim-lsp is installed
    if [ -d "$VIM_DIR/pack/*/start/vim-lsp" ] || [ -d "$VIM_DIR/plugged/vim-lsp" ]; then
        echo -e "${GREEN}✓${NC} vim-lsp plugin detected"
    else
        echo -e "${YELLOW}⚠${NC}  vim-lsp plugin not detected"
        echo -e "${YELLOW}   For LSP support in Vim, install: https://github.com/prabirshrestha/vim-lsp${NC}"
        echo -e "${YELLOW}   Or use Neovim 0.8+ for built-in LSP${NC}"
    fi
fi

echo ""

# ───────────────────────────────────────────────────────────────
# Done!
# ───────────────────────────────────────────────────────────────
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  ✓ Installation Complete!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo -e "  1. Restart $EDITOR_TYPE"
echo -e "  2. Open a .zolo file"
echo -e "  3. LSP should activate automatically"
echo ""
echo -e "${BLUE}Verify installation:${NC}"
if [ "$EDITOR_TYPE" = "neovim" ]; then
    echo -e "  nvim test.zolo"
    echo -e "  :LspInfo  (check if zolo-lsp is running)"
else
    echo -e "  vim test.zolo"
    echo -e "  :LspStatus  (if using vim-lsp plugin)"
fi
echo ""
echo -e "${BLUE}Troubleshooting:${NC}"
echo -e "  • Ensure 'zolo-lsp' is in PATH: which zolo-lsp"
echo -e "  • Check LSP logs: tail -f ~/.local/state/nvim/lsp.log"
echo -e "  • Test parser: python3 -c 'from zolo import loads; print(loads(\"key: value\"))'"
echo ""
