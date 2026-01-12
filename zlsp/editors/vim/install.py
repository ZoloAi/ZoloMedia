"""
Vim Integration Installer for zlsp

Fully automated installer that:
1. Installs Vim plugin files
2. Sets up vim-lsp (for Vim 9+)
3. Ensures everything works out of the box
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


def check_vim_version():
    """Check Vim version to determine if vim-lsp is needed."""
    try:
        result = subprocess.run(['vim', '--version'], 
                              capture_output=True, text=True, timeout=2)
        version_line = result.stdout.split('\n')[0]
        # Extract version like "9.1" from "VIM - Vi IMproved 9.1"
        version = version_line.split()[4] if len(version_line.split()) > 4 else "0"
        major = int(version.split('.')[0])
        return major >= 9, version
    except:
        return False, "unknown"


def install_vim_plug():
    """Install vim-plug plugin manager."""
    plug_path = Path.home() / '.vim' / 'autoload' / 'plug.vim'
    
    if plug_path.exists():
        return True, "already installed"
    
    try:
        plug_path.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run([
            'curl', '-fLo', str(plug_path), '--create-dirs',
            'https://raw.githubusercontent.com/junegunn/vim-plug/master/plug.vim'
        ], check=True, capture_output=True, timeout=30)
        return True, "installed"
    except Exception as e:
        return False, str(e)


def configure_vim_lsp():
    """Add vim-lsp to .vimrc if not already present."""
    vimrc_path = Path.home() / '.vimrc'
    
    # Read existing .vimrc
    existing_content = ""
    if vimrc_path.exists():
        existing_content = vimrc_path.read_text()
    
    # Check if already configured
    if 'prabirshrestha/vim-lsp' in existing_content and 'zolo-lsp' in existing_content:
        return True, "already configured"
    
    # Backup existing .vimrc
    if vimrc_path.exists():
        backup_path = vimrc_path.with_suffix('.vimrc.backup')
        shutil.copy2(vimrc_path, backup_path)
    
    # Create new .vimrc with vim-lsp and zolo-lsp server registration
    new_content = """\
" vim-plug plugin manager
call plug#begin('~/.vim/plugged')

" LSP client for Vim (required for zlsp)
Plug 'prabirshrestha/vim-lsp'

call plug#end()

" ═══════════════════════════════════════════════════════════════
" Zolo LSP Server Registration
" ═══════════════════════════════════════════════════════════════
" Register zolo-lsp server with vim-lsp
" This must come AFTER plug#end() so vim-lsp is loaded
if executable('zolo-lsp')
  augroup ZoloLSP
    autocmd!
    autocmd User lsp_setup call lsp#register_server({
      \\ 'name': 'zolo-lsp',
      \\ 'cmd': {server_info->['zolo-lsp']},
      \\ 'allowlist': ['zolo'],
      \\ 'workspace_config': {},
      \\ })
  augroup END
endif

"""
    
    # Append existing content
    if existing_content:
        new_content += "\n" + '" ' + "="*60 + "\n"
        new_content += '" Existing configuration\n'
        new_content += '" ' + "="*60 + "\n"
        new_content += existing_content
    
    try:
        vimrc_path.write_text(new_content)
        return True, "configured"
    except Exception as e:
        return False, str(e)


def install_vim_plugins():
    """Run :PlugInstall to install vim-lsp."""
    try:
        subprocess.run(['vim', '+PlugInstall', '+qall'], 
                      check=True, capture_output=True, timeout=60)
        return True, "installed"
    except Exception as e:
        return False, str(e)


def create_directories(base_dir):
    """Create necessary Vim directories."""
    dirs = [
        base_dir / 'ftdetect',
        base_dir / 'ftplugin',
        base_dir / 'after' / 'ftplugin',
        base_dir / 'syntax',
        base_dir / 'indent',
    ]
    
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    
    return dirs


def install_files(source_dir, target_dir):
    """Copy Vim plugin files to target directory."""
    files_to_copy = [
        ('ftdetect/zolo.vim', 'ftdetect/zolo.vim'),
        ('ftplugin/zolo.vim', 'ftplugin/zolo.vim'),
        ('lsp_config.vim', 'after/ftplugin/zolo.vim'),
        ('syntax/zolo.vim', 'syntax/zolo.vim'),
        ('indent/zolo.vim', 'indent/zolo.vim'),
    ]
    
    installed = []
    for src, dest in files_to_copy:
        src_path = source_dir / src
        dest_path = target_dir / dest
        
        if not src_path.exists():
            print(f"⚠  Warning: {src} not found, skipping...")
            continue
        
        shutil.copy2(src_path, dest_path)
        installed.append(dest)
    
    return installed


def main():
    """Main installation function - fully automated."""
    print("═" * 60)
    print("  zlsp Vim Integration Installer")
    print("  (Fully Automated)")
    print("═" * 60)
    print()
    
    # Get source directory (where this script is)
    source_dir = Path(__file__).parent
    
    # Detect editor
    editor_type, target_dir = detect_editor()
    
    print(f"→ Editor: {editor_type}")
    print(f"→ Target: {target_dir}")
    print()
    
    # Step 1: Create directories
    print("[1/5] Creating directories...")
    try:
        create_directories(target_dir)
        print("  ✓ Directories created")
    except Exception as e:
        print(f"  ✗ Failed to create directories: {e}")
        sys.exit(1)
    
    print()
    
    # Step 2: Install Vim files
    print("[2/5] Installing Vim files...")
    try:
        installed = install_files(source_dir, target_dir)
        for f in installed:
            print(f"  ✓ {f}")
    except Exception as e:
        print(f"  ✗ Failed to copy files: {e}")
        sys.exit(1)
    
    print()
    
    # Step 3: Check if vim-lsp is needed (Vim 9+ only)
    needs_vim_lsp = False
    if editor_type == 'vim':
        print("[3/5] Checking Vim version...")
        is_vim9, version = check_vim_version()
        print(f"  → Vim version: {version}")
        
        if is_vim9:
            needs_vim_lsp = True
            print(f"  → vim-lsp plugin required for LSP features")
        else:
            print(f"  ⚠ Vim < 9 detected - LSP features limited")
            print(f"    Recommendation: upgrade to Vim 9+ or use Neovim")
    else:
        print("[3/5] Neovim detected...")
        print("  ✓ Built-in LSP support - no plugin needed!")
    
    print()
    
    # Step 4: Auto-install vim-lsp (if needed)
    if needs_vim_lsp:
        print("[4/5] Setting up vim-lsp...")
        
        # Install vim-plug
        print("  → Installing vim-plug...")
        success, msg = install_vim_plug()
        if success:
            print(f"  ✓ vim-plug {msg}")
        else:
            print(f"  ✗ vim-plug failed: {msg}")
            print(f"    Manual installation may be required")
        
        # Configure .vimrc
        print("  → Configuring ~/.vimrc...")
        success, msg = configure_vim_lsp()
        if success:
            print(f"  ✓ vim-lsp {msg}")
            if msg == "configured":
                print(f"    (Backup saved to ~/.vimrc.backup)")
        else:
            print(f"  ✗ Configuration failed: {msg}")
        
        # Install plugins
        print("  → Installing vim-lsp plugin...")
        success, msg = install_vim_plugins()
        if success:
            print(f"  ✓ vim-lsp plugin {msg}")
        else:
            print(f"  ⚠ Plugin installation may need manual run")
            print(f"    Run in Vim: :PlugInstall")
    else:
        print("[4/5] vim-lsp setup...")
        print("  ⊗ Skipped (not needed)")
    
    print()
    
    # Step 5: Verify requirements
    print("[5/5] Verifying installation...")
    
    # Check if zolo-lsp is available
    if shutil.which('zolo-lsp'):
        print("  ✓ zolo-lsp command available")
    else:
        print("  ⚠ zolo-lsp not found in PATH")
        print("    Make sure zlsp is installed: pip install zlsp")
    
    print()
    print("═" * 60)
    print("  ✓ Installation Complete!")
    print("═" * 60)
    print()
    
    # Print next steps
    if editor_type == 'vim':
        if needs_vim_lsp:
            print("🎉 Ready to use!")
            print()
            print("Try it now:")
            print("  vim test.zolo")
            print()
            print("Features:")
            print("  • Press 'K' on a key for hover info")
            print("  • Type '(int):' for completion")
            print("  • Syntax errors shown in real-time")
            print()
            print("Check LSP status:")
            print("  :LspStatus")
        else:
            print("⚠ Limited features (basic syntax only)")
            print()
            print("For full LSP features:")
            print("  1. Upgrade Vim: brew install vim")
            print("  2. Re-run: zolo-vim-install")
            print("  OR use Neovim: brew install neovim")
    else:
        print("🎉 Ready to use!")
        print()
        print("Try it now:")
        print("  nvim test.zolo")
        print()
        print("Features:")
        print("  • Semantic highlighting")
        print("  • Real-time diagnostics")
        print("  • Hover information (press 'K')")
        print("  • Auto-completion")
    
    print()
    print("Documentation:")
    print(f"  • Vim guide: {source_dir}/README.md")
    print("  • Troubleshooting: zLSP/INSTALLATION.md")
    print()


if __name__ == '__main__':
    main()
