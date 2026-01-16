"""
Cursor IDE Integration Installer for zlsp

Fully automated installer that:
1. Generates extension files from canonical theme (themes/zolo_default.yaml)
2. Installs to Cursor extensions directory (~/.cursor/extensions/)
3. No manual configuration required
4. Everything "just works" for .zolo files

Note: Cursor IDE is a VS Code fork, so we use the same extension format!
"""
import json
import os
import shutil
import sys
import uuid
from datetime import datetime
from pathlib import Path

# Import theme system and VS Code generator (Cursor uses same format!)
try:
    from themes import load_theme
    from themes.generators.vscode import VSCodeGenerator
    from core.version import __version__
except ImportError:
    # Fallback if running from different context
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from themes import load_theme
    from themes.generators.vscode import VSCodeGenerator
    from core.version import __version__


def detect_cursor_dir():
    """Detect Cursor extensions directory."""
    cursor_dir = Path.home() / '.cursor' / 'extensions'
    
    if not cursor_dir.exists():
        # Try to create it
        cursor_dir.mkdir(parents=True, exist_ok=True)
    
    return cursor_dir


def detect_cursor_user_settings():
    """
    Detect Cursor user settings.json location.
    
    Returns:
        Path to settings.json (may not exist yet)
    """
    system = os.uname().sysname if hasattr(os, 'uname') else os.name
    
    if system == 'Darwin':  # macOS
        settings_path = Path.home() / 'Library' / 'Application Support' / 'Cursor' / 'User' / 'settings.json'
    elif system == 'Linux':
        settings_path = Path.home() / '.config' / 'Cursor' / 'User' / 'settings.json'
    elif system in ('Windows', 'nt'):
        appdata = os.getenv('APPDATA')
        if appdata:
            settings_path = Path(appdata) / 'Cursor' / 'User' / 'settings.json'
        else:
            settings_path = Path.home() / 'AppData' / 'Roaming' / 'Cursor' / 'User' / 'settings.json'
    else:
        # Unknown system, try Linux-style path
        settings_path = Path.home() / '.config' / 'Cursor' / 'User' / 'settings.json'
    
    return settings_path


def inject_semantic_token_colors_into_settings(settings_path, generator):
    """
    Inject semantic token colors directly into Cursor's settings.json.
    
    This is the "zero-config" approach - colors are injected automatically
    and work with ANY theme the user has active.
    
    Args:
        settings_path: Path to Cursor's settings.json
        generator: VSCodeGenerator instance
    """
    print("\n[5/8] Configuring semantic token colors...")
    
    # Generate semantic token color rules from theme
    rules = generator.generate_semantic_token_color_customizations()
    
    # Prepare the settings structure we want to inject
    zolo_customizations = {
        "enabled": True,
        "rules": rules
    }
    
    # Read existing settings (or create new)
    settings = {}
    if settings_path.exists():
        try:
            with open(settings_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)
        except json.JSONDecodeError:
            print(f"⚠️  Warning: {settings_path} is not valid JSON")
            # Create backup of invalid file
            backup_path = settings_path.with_suffix('.json.backup')
            shutil.copy(settings_path, backup_path)
            print(f"   Created backup: {backup_path}")
            settings = {}
    else:
        # Settings file doesn't exist yet - create parent directory
        settings_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Inject our semantic token colors globally (works with any theme)
    if "editor.semanticTokenColorCustomizations" not in settings:
        settings["editor.semanticTokenColorCustomizations"] = {}
    
    # Clean up old theme-scoped "[zolo]" section from previous installations
    if "[zolo]" in settings["editor.semanticTokenColorCustomizations"]:
        del settings["editor.semanticTokenColorCustomizations"]["[zolo]"]
        print("  ℹ️  Cleaned up old '[zolo]' theme-scoped colors")
    
    # Merge rules into global "rules" key
    if "rules" not in settings["editor.semanticTokenColorCustomizations"]:
        settings["editor.semanticTokenColorCustomizations"]["rules"] = {}
    
    # Update with our zolo token colors
    settings["editor.semanticTokenColorCustomizations"]["rules"].update(rules)
    
    # Also ensure enabled is true at the top level
    settings["editor.semanticTokenColorCustomizations"]["enabled"] = True
    
    # Write back to settings.json
    with open(settings_path, 'w', encoding='utf-8') as f:
        json.dump(settings, f, indent=4)
    
    print(f"✓ Semantic token colors injected into: {settings_path}")
    print(f"  → {len(rules)} token color rules configured")
    print(f"  → Works with ANY Cursor theme (no theme activation needed!)")


def register_extension_in_cursor_registry(ext_dir, publisher="zolo-ai", ext_name="zolo-lsp", version="1.0.0"):
    """
    Register the extension in Cursor's extensions.json registry.
    
    This is CRITICAL - Cursor won't recognize the extension without this!
    
    Args:
        ext_dir: Path to the extension directory
        publisher: Publisher ID
        ext_name: Extension name
        version: Extension version
    """
    cursor_extensions_dir = ext_dir.parent
    extensions_json_path = cursor_extensions_dir / 'extensions.json'
    
    # Generate UUIDs for the extension
    ext_uuid = str(uuid.uuid4())
    publisher_uuid = str(uuid.uuid4())
    
    # Create the extension entry
    ext_id = f"{publisher}.{ext_name}"
    ext_entry = {
        "identifier": {
            "id": ext_id,
            "uuid": ext_uuid
        },
        "version": version,
        "location": {
            "$mid": 1,
            "path": str(ext_dir),
            "scheme": "file"
        },
        "relativeLocation": ext_dir.name,
        "metadata": {
            "installedTimestamp": int(datetime.now().timestamp() * 1000),
            "pinned": False,
            "source": "local",
            "id": ext_uuid,
            "publisherId": publisher_uuid,
            "publisherDisplayName": "Zolo Language Support",
            "targetPlatform": "undefined",
            "updated": False,
            "isPreReleaseVersion": False,
            "hasPreReleaseVersion": False
        }
    }
    
    # Read existing extensions.json
    if extensions_json_path.exists():
        with open(extensions_json_path, 'r', encoding='utf-8') as f:
            extensions_list = json.load(f)
    else:
        extensions_list = []
    
    # Remove any existing zolo-lsp entries
    extensions_list = [ext for ext in extensions_list if not ext.get('identifier', {}).get('id', '').startswith('zolo')]
    
    # Add our extension
    extensions_list.append(ext_entry)
    
    # Write back
    with open(extensions_json_path, 'w', encoding='utf-8') as f:
        json.dump(extensions_list, f, indent=4)
    
    print(f"✓ Registered extension in Cursor registry")


def main():
    """
    Cursor IDE integration installer - fully automated.
    
    Single-command installation:
    1. Load theme
    2. Detect Cursor
    3. Generate extension files from theme
    4. Inject semantic token colors into settings
    5. Done!
    """
    print("=" * 70)
    print("Cursor IDE Integration Installer for zlsp")
    print("=" * 70)
    print()
    
    # Step 1: Load canonical theme
    print("[1/8] Loading color theme...")
    try:
        theme = load_theme('zolo_default')
        print("✓ Loaded: themes/zolo_default.yaml")
    except Exception as e:
        print(f"✗ Error loading theme: {e}")
        return 1
    
    # Step 2: Create generator
    print("\n[2/8] Initializing extension generator...")
    generator = VSCodeGenerator(theme)
    print("✓ VSCodeGenerator ready (Cursor uses same format!)")
    
    # Step 3: Detect Cursor
    print("\n[3/8] Detecting Cursor installation...")
    try:
        cursor_dir = detect_cursor_dir()
        print(f"✓ Cursor extensions directory: {cursor_dir}")
    except Exception as e:
        print(f"✗ Error: Could not find/create Cursor extensions directory")
        print(f"   {e}")
        return 1
    
    # Step 4: Generate and install extension files
    print("\n[4/8] Generating extension files...")
    
    # Create extension directory
    ext_dir = cursor_dir / f'zolo-lsp-{__version__}'
    if ext_dir.exists():
        print(f"⚠️  Extension already exists at: {ext_dir}")
        print("   Removing old version...")
        shutil.rmtree(ext_dir)
    
    ext_dir.mkdir(parents=True, exist_ok=True)
    
    # Create subdirectories
    (ext_dir / 'syntaxes').mkdir(exist_ok=True)
    (ext_dir / 'out').mkdir(exist_ok=True)
    (ext_dir / 'icons').mkdir(exist_ok=True)
    
    # Generate all extension files (same format as VS Code)
    try:
        # 1. package.json
        semantic_legend = generator.generate_semantic_tokens_legend()
        package_json = {
            "name": "zolo-lsp",
            "displayName": "Zolo Language Support",
            "description": "Language Server Protocol support for .zolo files with semantic highlighting",
            "version": __version__,
            "publisher": "zolo-ai",
            "icon": "icons/zolo_filetype.png",
            "repository": {
                "type": "git",
                "url": "https://github.com/zolomedia/zlsp"
            },
            "engines": {
                "vscode": "^1.75.0"
            },
            "categories": [
                "Programming Languages"
            ],
            "activationEvents": [
                "onLanguage:zolo"
            ],
            "main": "./out/extension.js",
            "contributes": {
                "languages": [{
                    "id": "zolo",
                    "aliases": ["Zolo", "zolo"],
                    "extensions": [".zolo"],
                    "configuration": "./language-configuration.json",
                    "icon": {
                        "light": "./icons/zolo_filetype.png",
                        "dark": "./icons/zolo_filetype.png"
                    }
                }],
                "grammars": [{
                    "language": "zolo",
                    "scopeName": "source.zolo",
                    "path": "./syntaxes/zolo.tmLanguage.json"
                }],
                "semanticTokenTypes": semantic_legend["tokenTypes"],
                "semanticTokenModifiers": semantic_legend["tokenModifiers"]
            },
            "configuration": {
                "title": "Zolo",
                "properties": {
                    "zolo.trace.server": {
                        "type": "string",
                        "enum": ["off", "messages", "verbose"],
                        "default": "off",
                        "description": "Traces the communication between Cursor and the Zolo language server."
                    }
                }
            },
            "configurationDefaults": {
                "[zolo]": {
                    "editor.semanticHighlighting.enabled": True,
                    "editor.bracketPairColorization.enabled": False,
                    "editor.guides.bracketPairs": False
                }
            }
        }
        
        with open(ext_dir / 'package.json', 'w', encoding='utf-8') as f:
            json.dump(package_json, f, indent=2)
        print("✓ Generated: package.json")
        
        # 2. language-configuration.json
        lang_config = {
            "comments": {
                "lineComment": "#"
            },
            "folding": {
                "markers": {
                    "start": "^\\s*#\\s*region",
                    "end": "^\\s*#\\s*endregion"
                }
            }
        }
        
        with open(ext_dir / 'language-configuration.json', 'w', encoding='utf-8') as f:
            json.dump(lang_config, f, indent=2)
        print("✓ Generated: language-configuration.json")
        
        # 3. syntaxes/zolo.tmLanguage.json
        tm_grammar = generator.generate_textmate_grammar()
        with open(ext_dir / 'syntaxes' / 'zolo.tmLanguage.json', 'w', encoding='utf-8') as f:
            json.dump(tm_grammar, f, indent=2)
        print("✓ Generated: syntaxes/zolo.tmLanguage.json")
        
        # 4. out/extension.js (minimal LSP client)
        extension_js = '''const { LanguageClient, TransportKind } = require('vscode-languageclient/node');
const vscode = require('vscode');
const { execSync } = require('child_process');

let client;

function activate(context) {
    // Check if zolo-lsp is available
    try {
        execSync('which zolo-lsp', { stdio: 'pipe' });
    } catch (error) {
        vscode.window.showErrorMessage(
            'Zolo LSP server not found. Install with: pip install zlsp',
            'Install Now'
        ).then(selection => {
            if (selection === 'Install Now') {
                const terminal = vscode.window.createTerminal('Zolo LSP Install');
                terminal.sendText('pip install zlsp');
                terminal.show();
            }
        });
        return;
    }

    const serverOptions = {
        command: 'zolo-lsp',
        args: [],
        transport: TransportKind.stdio
    };

    const clientOptions = {
        documentSelector: [{ scheme: 'file', language: 'zolo' }],
        synchronize: {
            fileEvents: vscode.workspace.createFileSystemWatcher('**/*.zolo')
        }
    };

    client = new LanguageClient(
        'zoloLanguageServer',
        'Zolo Language Server',
        serverOptions,
        clientOptions
    );

    client.start();
}

function deactivate() {
    if (!client) {
        return undefined;
    }
    return client.stop();
}

module.exports = {
    activate,
    deactivate
};
'''
        
        with open(ext_dir / 'out' / 'extension.js', 'w', encoding='utf-8') as f:
            f.write(extension_js)
        print("✓ Generated: out/extension.js")
        
        # 5. README.md
        readme_content = f"""# Zolo Language Support for Cursor

LSP integration for `.zolo` declarative files.

## Features

- ✅ Semantic highlighting (context-aware)
- ✅ Real-time diagnostics
- ✅ Hover information (type hints)
- ✅ Code completion
- ✅ Zero configuration required

## Installation

Installed via: `zlsp-cursor-install`

For more information: https://github.com/ZoloAi/zlsp

## Version

{__version__}
"""
        with open(ext_dir / 'README.md', 'w', encoding='utf-8') as f:
            f.write(readme_content)
        print("✓ Generated: README.md")
        
        # 6. Copy file type icon
        icon_src = Path(__file__).parent.parent.parent / 'assets' / 'zolo_filetype.png'
        icon_dest = ext_dir / 'icons' / 'zolo_filetype.png'
        if icon_src.exists():
            shutil.copy2(icon_src, icon_dest)
            print("✓ Copied: icons/zolo_filetype.png")
        else:
            print("⚠️  Warning: Icon file not found at assets/zolo_filetype.png")
        
    except Exception as e:
        print(f"✗ Error generating extension files: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # Step 5: Inject semantic token colors into Cursor settings
    try:
        settings_path = detect_cursor_user_settings()
        inject_semantic_token_colors_into_settings(settings_path, generator)
    except Exception as e:
        print(f"⚠️  Warning: Could not inject semantic token colors: {e}")
        print(f"   Extension will still work, but colors may not be optimal")
    
    # Step 6: Register extension in Cursor's registry (CRITICAL!)
    print("\n[6/8] Registering extension in Cursor...")
    try:
        register_extension_in_cursor_registry(ext_dir, version=__version__)
    except Exception as e:
        print(f"✗ Error registering extension: {e}")
        import traceback
        traceback.print_exc()
        print("   Extension may not be recognized by Cursor")
    
    # Step 7: Verify icon file exists
    print("\n[7/8] Verifying file type icon...")
    icon_path = ext_dir / 'icons' / 'zolo_filetype.png'
    if icon_path.exists():
        print(f"✓ Icon verified: {icon_path}")
    else:
        print(f"⚠️  Warning: Icon not found, .zolo files may not show custom icon")
    
    # Step 8: Install npm dependencies for LSP client
    print("\n[8/8] Installing extension dependencies...")
    try:
        import subprocess
        result = subprocess.run(
            ['npm', 'install', 'vscode-languageclient@8.0.2'],
            cwd=ext_dir,
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode == 0:
            print("✓ npm dependencies installed")
        else:
            print("⚠️  Warning: npm install had issues:")
            print(f"   {result.stderr}")
            print("   Extension may still work if dependencies are cached")
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        print(f"⚠️  Warning: Could not run npm install: {e}")
        print("   Please run manually: cd ~/.cursor/extensions/zolo-lsp-*/  && npm install")
    
    # Success!
    print("\n" + "=" * 70)
    print("✓ Cursor IDE integration installed successfully!")
    print("=" * 70)
    print()
    print("📂 Extension installed to:")
    print(f"   {ext_dir}")
    print()
    print("🎨 Semantic token colors configured:")
    print(f"   {detect_cursor_user_settings()}")
    print()
    print("🚀 Next steps:")
    print("   1. Reload Cursor: Cmd+Shift+P > 'Reload Window'")
    print("   2. Open any .zolo file")
    print("   3. Enjoy semantic highlighting, diagnostics, hover, and completion!")
    print()
    print("💡 The extension works with ANY Cursor theme (no theme activation needed)")
    print()
    print("📚 For troubleshooting, see: editors/cursor/README.md")
    print()
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
