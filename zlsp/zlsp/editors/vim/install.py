"""
Vim Integration Installer for zlsp

Fully automated installer that:
1. Installs Vim plugin files to auto-loading directories
2. Generates colors from canonical theme (themes/zolo_default.yaml)
3. No .vimrc modification required (except vim-lsp plugin)
4. Everything "just works" for .zolo files
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

# Import theme system
try:
    from themes import load_theme
    from themes.generators.vim import VimGenerator
except ImportError:
    # Fallback if running from different context
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from themes import load_theme
    from themes.generators.vim import VimGenerator


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
        base_dir / 'after' / 'syntax',
        base_dir / 'colors',
    ]
    
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    
    return dirs


def generate_ftplugin_with_colors(theme, target_dir):
    """Generate after/ftplugin/zolo.vim with colors from theme."""
    generator = VimGenerator(theme)
    
    # Generate the ftplugin content with embedded colors
    lines = []
    lines.append('" ═══════════════════════════════════════════════════════════════')
    lines.append('" Zolo LSP - File Type Plugin (Auto-loads for .zolo files)')
    lines.append('" ═══════════════════════════════════════════════════════════════')
    lines.append('" File: after/ftplugin/zolo.vim')
    lines.append('" Purpose: Runs AFTER vim-lsp loads, when opening .zolo files')
    lines.append(f'" Generated from: themes/{theme.name}')
    lines.append('" ═══════════════════════════════════════════════════════════════')
    lines.append('')
    lines.append('" Only run once per buffer')
    lines.append("if exists('b:did_zolo_lsp_ftplugin')")
    lines.append('  finish')
    lines.append('endif')
    lines.append("let b:did_zolo_lsp_ftplugin = 1")
    lines.append('')
    lines.append('" Buffer-local LSP settings')
    lines.append("setlocal omnifunc=lsp#complete")
    lines.append('setlocal signcolumn=yes')
    lines.append('setlocal updatetime=300')
    lines.append('')
    lines.append('" LSP keybindings (only for .zolo files)')
    lines.append('nnoremap <buffer> K :LspHover<CR>')
    lines.append('nnoremap <buffer> gd :LspDefinition<CR>')
    lines.append('nnoremap <buffer> gr :LspReferences<CR>')
    lines.append('nnoremap <buffer> gi :LspImplementation<CR>')
    lines.append('nnoremap <buffer> <leader>rn :LspRename<CR>')
    lines.append('nnoremap <buffer> [d :LspPreviousDiagnostic<CR>')
    lines.append('nnoremap <buffer> ]d :LspNextDiagnostic<CR>')
    lines.append('')
    lines.append('" Enable LSP formatting on save (optional)')
    lines.append('" autocmd BufWritePre <buffer> LspDocumentFormat')
    lines.append('')
    lines.append('" ═══════════════════════════════════════════════════════════════')
    lines.append('" Colors - Generated from theme')
    lines.append('" ═══════════════════════════════════════════════════════════════')
    lines.append('')
    
    # Add generated colors
    lines.append(generator.generate())
    lines.append('')
    lines.append('" ═══════════════════════════════════════════════════════════════')
    lines.append('" Note: Syntax clearing moved to after/syntax/zolo.vim')
    lines.append('" ═══════════════════════════════════════════════════════════════')
    lines.append('" The after/syntax/ directory loads AFTER syntax/zolo.vim,')
    lines.append('" ensuring highlights are cleared at the right time.')
    
    # Write to file
    dest_path = target_dir / 'after' / 'ftplugin' / 'zolo.vim'
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    dest_path.write_text('\n'.join(lines))
    
    return dest_path


def install_files(source_dir, target_dir, theme):
    """Install Vim plugin files (copy static, generate dynamic)."""
    config_dir = source_dir / 'config'
    
    # Static files to copy (don't change)
    static_files = [
        ('config/ftdetect/zolo.vim', 'ftdetect/zolo.vim'),
        ('config/ftplugin/zolo.vim', 'ftplugin/zolo.vim'),
        ('config/syntax/zolo.vim', 'syntax/zolo.vim'),
        ('config/indent/zolo.vim', 'indent/zolo.vim'),
        ('config/plugin/zolo_lsp.vim', 'plugin/zolo_lsp.vim'),
        ('config/after/syntax/zolo.vim', 'after/syntax/zolo.vim'),
    ]
    
    installed = []
    skipped = []
    
    # Copy static files
    for src, dest in static_files:
        src_path = source_dir / src
        dest_path = target_dir / dest
        
        if not src_path.exists():
            skipped.append(f"{src} (not found)")
            continue
        
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_path, dest_path)
        installed.append(dest)
    
    # Generate dynamic after/ftplugin with colors from theme
    try:
        ftplugin_path = generate_ftplugin_with_colors(theme, target_dir)
        installed.append('after/ftplugin/zolo.vim (generated from theme)')
    except Exception as e:
        skipped.append(f"after/ftplugin/zolo.vim (generation failed: {e})")
    
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
    print("  (Auto-loading, Non-Destructive, Theme-Driven)")
    print("═" * 70)
    print()
    
    # Get source directory (where this script is)
    source_dir = Path(__file__).parent
    
    # Load theme
    print("[1/5] Loading color theme...")
    try:
        theme = load_theme('zolo_default')
        print(f"  ✓ Loaded theme: {theme.name} v{theme.version}")
    except Exception as e:
        print(f"  ✗ Failed to load theme: {e}")
        sys.exit(1)
    
    print()
    
    # Detect editor
    editor_type, target_dir = detect_editor()
    
    print(f"→ Editor: {editor_type}")
    print(f"→ Target: {target_dir}")
    print()
    
    # Step 2: Create directories
    print("[2/5] Creating auto-loading directories...")
    try:
        create_directories(target_dir)
        print("  ✓ Directories ready")
    except Exception as e:
        print(f"  ✗ Failed to create directories: {e}")
        sys.exit(1)
    
    print()
    
    # Step 3: Install Vim files (with theme-generated colors)
    print("[3/5] Installing Vim plugin files...")
    try:
        installed, skipped = install_files(source_dir, target_dir, theme)
        
        for f in installed:
            print(f"  ✓ {f}")
        
        if skipped:
            print()
            print("  Skipped:")
            for s in skipped:
                print(f"    ⊗ {s}")
    except Exception as e:
        print(f"  ✗ Failed to install files: {e}")
        sys.exit(1)
    
    print()
    
    # Step 4: Check vim-lsp
    print("[4/5] Checking for vim-lsp...")
    vim_lsp_found, vim_lsp_status = check_vim_lsp_installed(target_dir)
    
    if vim_lsp_found:
        print(f"  ✓ vim-lsp {vim_lsp_status}")
    else:
        print(f"  ⚠ vim-lsp {vim_lsp_status}")
        print_vim_lsp_instructions()
    
    print()
    
    # Step 5: Verify requirements
    print("[5/5] Verifying installation...")
    
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
