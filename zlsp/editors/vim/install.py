"""
Vim Integration Installer for zlsp

Fully automated installer that:
1. Installs Vim plugin files to auto-loading directories
2. No .vimrc modification required (except vim-lsp plugin)
3. Everything "just works" for .zolo files
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path


def detect_editor():
    """Detect which editor to install for."""
    nvim_dir = Path.home() / '.config' / 'nvim'
    vim_dir = Path.home() / '.vim'
    
    # Check if user has Neovim config
    if nvim_dir.exists():
        return 'neovim', nvim_dir
    
    # Default to Vim
    return 'vim', vim_dir


def check_vim_lsp_installed(target_dir):
    """Check if vim-lsp is already installed."""
    plugged_dir = target_dir / 'plugged' / 'vim-lsp'
    vimrc = Path.home() / '.vimrc'
    
    # Check if vim-lsp is in plugged directory
    if plugged_dir.exists():
        return True, "installed via vim-plug"
    
    # Check if mentioned in .vimrc
    if vimrc.exists():
        content = vimrc.read_text()
        if 'prabirshrestha/vim-lsp' in content:
            return True, "configured in .vimrc"
    
    return False, "not found"


def create_directories(base_dir):
    """Create necessary Vim auto-loading directories."""
    dirs = [
        base_dir / 'ftdetect',
        base_dir / 'ftplugin',
        base_dir / 'syntax',
        base_dir / 'indent',
        base_dir / 'plugin',
        base_dir / 'after' / 'ftplugin',
        base_dir / 'colors',
    ]
    
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    
    return dirs


def install_files(source_dir, target_dir):
    """Copy Vim plugin files to auto-loading directories."""
    config_dir = source_dir / 'config'
    
    files_to_copy = [
        # File type detection (auto-runs on startup)
        ('config/ftdetect/zolo.vim', 'ftdetect/zolo.vim'),
        
        # Basic file type settings (auto-runs for .zolo)
        ('config/ftplugin/zolo.vim', 'ftplugin/zolo.vim'),
        
        # Syntax highlighting fallback (auto-runs for .zolo)
        ('config/syntax/zolo.vim', 'syntax/zolo.vim'),
        
        # Indentation rules (auto-runs for .zolo)
        ('config/indent/zolo.vim', 'indent/zolo.vim'),
        
        # LSP global setup (auto-runs on startup)
        ('config/plugin/zolo_lsp.vim', 'plugin/zolo_lsp.vim'),
        
        # LSP per-file setup (auto-runs AFTER vim-lsp loads)
        ('config/after/ftplugin/zolo.vim', 'after/ftplugin/zolo.vim'),
        
        # Color scheme (loaded by after/ftplugin)
        ('config/colors/zolo_lsp.vim', 'colors/zolo_lsp.vim'),
    ]
    
    installed = []
    skipped = []
    
    for src, dest in files_to_copy:
        src_path = source_dir / src
        dest_path = target_dir / dest
        
        if not src_path.exists():
            skipped.append(f"{src} (not found)")
            continue
        
        # Create parent directories if needed
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Copy file
        shutil.copy2(src_path, dest_path)
        installed.append(dest)
    
    return installed, skipped


def print_vim_lsp_instructions():
    """Print instructions for installing vim-lsp."""
    print()
    print("  ╔═══════════════════════════════════════════════════════════╗")
    print("  ║  vim-lsp Plugin Required                                  ║")
    print("  ╚═══════════════════════════════════════════════════════════╝")
    print()
    print("  To enable LSP features, add to your ~/.vimrc:")
    print()
    print("    " + "─" * 55)
    print("    call plug#begin('~/.vim/plugged')")
    print("    Plug 'prabirshrestha/vim-lsp'")
    print("    call plug#end()")
    print("    " + "─" * 55)
    print()
    print("  Then restart Vim and run:  :PlugInstall")
    print()
    print("  Alternative: Use Neovim (has built-in LSP support)")
    print()


def main():
    """Main installation function - fully automated."""
    print("═" * 70)
    print("  zlsp Vim Integration Installer")
    print("  (Auto-loading, Non-Destructive)")
    print("═" * 70)
    print()
    
    # Get source directory (where this script is)
    source_dir = Path(__file__).parent
    
    # Detect editor
    editor_type, target_dir = detect_editor()
    
    print(f"→ Editor: {editor_type}")
    print(f"→ Target: {target_dir}")
    print()
    
    # Step 1: Create directories
    print("[1/4] Creating auto-loading directories...")
    try:
        create_directories(target_dir)
        print("  ✓ Directories ready")
    except Exception as e:
        print(f"  ✗ Failed to create directories: {e}")
        sys.exit(1)
    
    print()
    
    # Step 2: Install Vim files
    print("[2/4] Installing Vim plugin files...")
    try:
        installed, skipped = install_files(source_dir, target_dir)
        
        for f in installed:
            print(f"  ✓ {f}")
        
        if skipped:
            print()
            print("  Skipped:")
            for s in skipped:
                print(f"    ⊗ {s}")
    except Exception as e:
        print(f"  ✗ Failed to copy files: {e}")
        sys.exit(1)
    
    print()
    
    # Step 3: Check vim-lsp
    print("[3/4] Checking for vim-lsp...")
    vim_lsp_found, vim_lsp_status = check_vim_lsp_installed(target_dir)
    
    if vim_lsp_found:
        print(f"  ✓ vim-lsp {vim_lsp_status}")
    else:
        print(f"  ⚠ vim-lsp {vim_lsp_status}")
        print_vim_lsp_instructions()
    
    print()
    
    # Step 4: Verify requirements
    print("[4/4] Verifying installation...")
    
    # Check if zolo-lsp is available
    if shutil.which('zolo-lsp'):
        print("  ✓ zolo-lsp server available")
    else:
        print("  ⚠ zolo-lsp not found in PATH")
        print("    Run: pip install zlsp")
    
    print()
    print("═" * 70)
    
    if vim_lsp_found:
        print("  ✓ Installation Complete!")
    else:
        print("  ⚠ Installation Complete (vim-lsp setup needed)")
    
    print("═" * 70)
    print()
    
    # Print usage
    if vim_lsp_found:
        print("🎉 Ready to use!")
        print()
        print("Try it now:")
        print(f"  {'nvim' if editor_type == 'neovim' else 'vim'} test.zolo")
        print()
        print("Features:")
        print("  • Semantic highlighting (colors from LSP)")
        print("  • Real-time diagnostics")
        print("  • Hover info (press 'K')")
        print("  • Auto-completion")
        print("  • Go to definition (gd)")
        print()
        print("Check LSP status:")
        print("  :LspStatus")
    else:
        print("⚠️  Basic syntax only (LSP features disabled)")
        print()
        print("To enable full LSP features:")
        print("  1. Add vim-lsp to your .vimrc (see instructions above)")
        print("  2. Restart Vim and run :PlugInstall")
        print("  3. Re-run: zlsp-vim-install")
    
    print()
    print("Documentation:")
    print(f"  • Vim guide: {source_dir}/README.md")
    print(f"  • Color scheme: {target_dir}/colors/zolo_lsp.vim")
    print()
    
    # Print what was installed
    print("Installed files:")
    print(f"  • Auto-detection:      {target_dir}/ftdetect/zolo.vim")
    print(f"  • File type settings:  {target_dir}/ftplugin/zolo.vim")
    print(f"  • Syntax (fallback):   {target_dir}/syntax/zolo.vim")
    print(f"  • LSP setup:           {target_dir}/plugin/zolo_lsp.vim")
    print(f"  • LSP per-file:        {target_dir}/after/ftplugin/zolo.vim")
    print(f"  • Colors:              {target_dir}/colors/zolo_lsp.vim")
    print()
    print("✨ No .vimrc modification needed!")
    print("   (except vim-lsp plugin if not already installed)")
    print()


if __name__ == '__main__':
    main()
