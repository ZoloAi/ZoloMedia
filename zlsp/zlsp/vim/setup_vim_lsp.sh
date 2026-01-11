#!/bin/bash
# Setup vim-lsp plugin for Vim 9+
# This script installs vim-plug and configures vim-lsp

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  vim-lsp Setup for Zolo LSP${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo ""

# Check if Vim is available
if ! command -v vim &> /dev/null; then
    echo -e "${RED}✗ Vim not found${NC}"
    exit 1
fi

# Check Vim version
VIM_VERSION=$(vim --version | head -n1 | grep -oE '[0-9]+\.[0-9]+' | head -n1)
echo -e "${BLUE}→${NC} Vim version: ${VIM_VERSION}"

# Warn if Vim < 9
if [[ "${VIM_VERSION}" < "9.0" ]]; then
    echo -e "${YELLOW}⚠  Warning: Vim ${VIM_VERSION} detected. LSP features require Vim 9.0+${NC}"
    echo -e "${YELLOW}   Consider upgrading: brew install vim${NC}"
    echo ""
fi

# Check if vim-plug is installed
echo ""
echo -e "${BLUE}[1/3] Checking vim-plug...${NC}"
if [ -f ~/.vim/autoload/plug.vim ]; then
    echo -e "${GREEN}✓${NC} vim-plug already installed"
else
    echo -e "${YELLOW}→${NC} Installing vim-plug..."
    curl -fLo ~/.vim/autoload/plug.vim --create-dirs \
        https://raw.githubusercontent.com/junegunn/vim-plug/master/plug.vim
    echo -e "${GREEN}✓${NC} vim-plug installed"
fi

# Backup existing .vimrc
echo ""
echo -e "${BLUE}[2/3] Configuring ~/.vimrc...${NC}"
if [ -f ~/.vimrc ]; then
    echo -e "${YELLOW}→${NC} Backing up existing .vimrc to ~/.vimrc.backup"
    cp ~/.vimrc ~/.vimrc.backup
fi

# Check if vim-lsp is already in .vimrc
if grep -q "prabirshrestha/vim-lsp" ~/.vimrc 2>/dev/null; then
    echo -e "${GREEN}✓${NC} vim-lsp already configured in .vimrc"
else
    echo -e "${YELLOW}→${NC} Adding vim-lsp to .vimrc..."
    
    # Create new .vimrc with plugin section at the top
    cat > ~/.vimrc.new << 'VIMRC'
" vim-plug plugin manager
call plug#begin('~/.vim/plugged')

" LSP client for Vim
Plug 'prabirshrestha/vim-lsp'

call plug#end()

VIMRC
    
    # Append existing .vimrc content (if it exists)
    if [ -f ~/.vimrc ]; then
        echo "" >> ~/.vimrc.new
        echo '" ════════════════════════════════════════════════════════════' >> ~/.vimrc.new
        echo '" Existing configuration' >> ~/.vimrc.new
        echo '" ════════════════════════════════════════════════════════════' >> ~/.vimrc.new
        cat ~/.vimrc >> ~/.vimrc.new
    fi
    
    # Replace .vimrc
    mv ~/.vimrc.new ~/.vimrc
    echo -e "${GREEN}✓${NC} vim-lsp added to .vimrc"
fi

# Install plugins
echo ""
echo -e "${BLUE}[3/3] Installing vim plugins...${NC}"
echo -e "${YELLOW}→${NC} Running :PlugInstall..."
vim +PlugInstall +qall
echo -e "${GREEN}✓${NC} Plugins installed"

echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  ✓ vim-lsp Setup Complete!${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo ""
echo "Next steps:"
echo "  1. Open a .zolo file: vim test.zolo"
echo "  2. Check LSP status: :LspStatus"
echo "  3. Test hover: Move to a key and press 'K'"
echo ""
echo "Troubleshooting:"
echo "  • LSP logs: tail -f ~/.vim/lsp.log"
echo "  • Check zolo-lsp: which zolo-lsp"
echo "  • Plugin status: :PlugStatus"
echo ""
