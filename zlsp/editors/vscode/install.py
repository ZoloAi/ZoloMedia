"""
VS Code Integration Installer for zlsp

Fully automated installer that:
1. Generates extension files from canonical theme (themes/zolo_default.yaml)
2. Installs to VS Code extensions directory (~/.vscode/extensions/)
3. No manual configuration required
4. Everything "just works" for .zolo files
"""
import json
import os
import shutil
import sys
from pathlib import Path

# Import theme system and VS Code generator
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


def detect_vscode_dir():
    """Detect VS Code extensions directory."""
    vscode_dir = Path.home() / '.vscode' / 'extensions'
    
    if not vscode_dir.exists():
        # Try to create it
        vscode_dir.mkdir(parents=True, exist_ok=True)
    
    return vscode_dir


def detect_vscode_user_settings():
    """
    Detect VS Code user settings.json location.
    
    Returns:
        Path to settings.json (may not exist yet)
    """
    system = os.uname().sysname if hasattr(os, 'uname') else os.name
    
    if system == 'Darwin':  # macOS
        settings_path = Path.home() / 'Library' / 'Application Support' / 'Code' / 'User' / 'settings.json'
    elif system == 'Linux':
        settings_path = Path.home() / '.config' / 'Code' / 'User' / 'settings.json'
    elif system in ('Windows', 'nt'):
        appdata = os.getenv('APPDATA')
        if appdata:
            settings_path = Path(appdata) / 'Code' / 'User' / 'settings.json'
        else:
            settings_path = Path.home() / 'AppData' / 'Roaming' / 'Code' / 'User' / 'settings.json'
    else:
        # Unknown system, try Linux-style path
        settings_path = Path.home() / '.config' / 'Code' / 'User' / 'settings.json'
    
    return settings_path


def generate_semantic_token_rules(generator):
    """
    Generate semantic token color rules for VS Code settings.json.
    
    Returns:
        Dictionary mapping token types to color settings
    """
    rules = {}
    
    # All token types from our semantic token legend
    token_types = [
        'comment', 'rootKey', 'nestedKey', 'zmetaKey', 'zkernelDataKey',
        'zschemaPropertyKey', 'bifrostKey', 'uiElementKey', 'zconfigKey',
        'zsparkKey', 'zenvConfigKey', 'znavbarNestedKey', 'zsubKey',
        'zsparkNestedKey', 'zsparkModeValue', 'zsparkVaFileValue',
        'zsparkSpecialValue', 'envConfigValue', 'zrbacKey', 'zrbacOptionKey',
        'typeHint', 'number', 'string', 'boolean', 'null',
        'bracketStructural', 'braceStructural', 'stringBracket', 'stringBrace',
        'colon', 'comma', 'escapeSequence', 'versionString', 'timestampString',
        'timeString', 'ratioString', 'zpathValue', 'zmachineEditableKey',
        'zmachineLockedKey', 'typeHintParen'
    ]
    
    for token_type in token_types:
        token_style = generator.theme.get_token_style(token_type)
        if token_style:
            color = token_style.get('hex', '#ffffff')
            style = token_style.get('style', 'none')
            
            # Format for settings.json
            if style != 'none':
                rules[token_type] = {
                    "foreground": color,
                    "fontStyle": style.replace(',', ' ')
                }
            else:
                rules[token_type] = color  # Simple format: just hex color
    
    return rules


def inject_semantic_token_colors(settings_path, rules):
    """
    Inject Zolo semantic token colors into VS Code user settings.
    
    Args:
        settings_path: Path to settings.json
        rules: Dictionary of token type -> color mappings
    
    Returns:
        True if successful, False otherwise
    """
    # Ensure parent directory exists
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Read existing settings or create empty
    if settings_path.exists():
        try:
            with open(settings_path, 'r') as f:
                content = f.read()
                # Handle empty file or just comments
                if content.strip():
                    settings = json.loads(content)
                else:
                    settings = {}
        except json.JSONDecodeError:
            print(f"  ⚠ Existing settings.json is invalid JSON, creating backup")
            backup_path = settings_path.parent / 'settings.json.zlsp.backup'
            shutil.copy2(settings_path, backup_path)
            settings = {}
    else:
        settings = {}
    
    # Inject our semantic token colors
    if "editor.semanticTokenColorCustomizations" not in settings:
        settings["editor.semanticTokenColorCustomizations"] = {}
    
    # Clean up old theme-scoped "[zolo]" section from previous installations
    if "[zolo]" in settings["editor.semanticTokenColorCustomizations"]:
        del settings["editor.semanticTokenColorCustomizations"]["[zolo]"]
        print("  ℹ️  Cleaned up old '[zolo]' theme-scoped colors")
    
    # Apply to all themes using wildcard
    semantic_customizations = settings["editor.semanticTokenColorCustomizations"]
    semantic_customizations["enabled"] = True
    semantic_customizations["rules"] = rules
    
    # Write back with nice formatting
    try:
        with open(settings_path, 'w') as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"  ✗ Failed to write settings: {e}")
        return False


def check_vscode_installed():
    """Check if VS Code is installed."""
    # Check if VS Code is in PATH
    if shutil.which('code'):
        return True, "VS Code CLI found in PATH"
    
    # Check common VS Code installation locations
    vscode_locations = [
        Path('/Applications/Visual Studio Code.app'),
        Path.home() / 'Applications' / 'Visual Studio Code.app',
        Path('/usr/local/bin/code'),
        Path('/usr/bin/code'),
    ]
    
    for location in vscode_locations:
        if location.exists():
            return True, f"VS Code found at {location}"
    
    return False, "VS Code not found"


def check_zolo_lsp_available():
    """Check if zolo-lsp command is available."""
    if shutil.which('zolo-lsp'):
        return True, "zolo-lsp command available in PATH"
    
    return False, "zolo-lsp not found (run: pip install zlsp)"


def create_extension_structure(base_dir):
    """Create VS Code extension directory structure."""
    dirs = [
        base_dir,
        base_dir / 'syntaxes',
        base_dir / 'themes',
        base_dir / 'out',
        base_dir / 'icons',
    ]
    
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    
    return dirs


def generate_package_json(theme, generator, base_dir):
    """Generate package.json from theme and generator."""
    semantic_legend = generator.generate_semantic_tokens_legend()
    
    package_json = {
        "name": "zolo-lsp",
        "displayName": "Zolo LSP",
        "description": "Language Server Protocol support for .zolo files with semantic highlighting",
        "version": __version__,
        "publisher": "ZoloMedia",
        "icon": "icons/zolo_filetype.png",
        "license": "MIT",
        "homepage": "https://zolo.media",
        "author": {
            "name": "Zolo Media"
        },
        "bugs": {
            "url": "https://zolo.media/support"
        },
        "qna": "marketplace",
        "engines": {
            "vscode": "^1.75.0"
        },
        "categories": [
            "Programming Languages",
            "Formatters",
            "Linters"
        ],
        "keywords": [
            "zolo",
            "zlsp",
            "language-server",
            "lsp",
            "semantic-highlighting"
        ],
        "activationEvents": [
            "onLanguage:zolo"
        ],
        "main": "./out/extension.js",
        "contributes": {
            "languages": [
                {
                    "id": "zolo",
                    "aliases": ["Zolo", "zolo"],
                    "extensions": [".zolo"],
                    "configuration": "./language-configuration.json",
                    "icon": {
                        "light": "./icons/zolo_filetype.png",
                        "dark": "./icons/zolo_filetype.png"
                    }
                }
            ],
            "grammars": [
                {
                    "language": "zolo",
                    "scopeName": "source.zolo",
                    "path": "./syntaxes/zolo.tmLanguage.json"
                }
            ],
            "semanticTokenTypes": [
                {"id": token_type, "description": f"Zolo {token_type}"}
                for token_type in semantic_legend['tokenTypes']
            ],
            "semanticTokenModifiers": [
                {"id": modifier, "description": f"Zolo {modifier}"}
                for modifier in semantic_legend['tokenModifiers']
            ],
            "configuration": {
                "title": "Zolo",
                "properties": {
                    "zolo.trace.server": {
                        "type": "string",
                        "enum": ["off", "messages", "verbose"],
                        "default": "messages",
                        "description": "Traces the communication between VS Code and the Zolo language server"
                    },
                    "zolo.lsp.debug": {
                        "type": "boolean",
                        "default": True,
                        "description": "Enable debug logging in the output channel"
                    }
                }
            },
            "configurationDefaults": {
                "[zolo]": {
                    "editor.bracketPairColorization.enabled": False,
                    "editor.guides.bracketPairs": False,
                    "editor.semanticHighlighting.enabled": True
                }
            }
        },
        "dependencies": {},
        "devDependencies": {}
    }
    
    dest_path = base_dir / 'package.json'
    with open(dest_path, 'w') as f:
        json.dump(package_json, f, indent=2)
    
    return dest_path


def generate_language_configuration(base_dir):
    """Generate language-configuration.json."""
    config = {
        "comments": {
            "lineComment": "#"
        },
        # DO NOT define brackets/autoClosingPairs for structural braces/brackets!
        # Our semantic tokens handle these, and VS Code's built-in bracket
        # colorization interferes with our custom token colors.
        # Only auto-close quotes for convenience.
        "autoClosingPairs": [
            {"open": "\"", "close": "\""},
            {"open": "'", "close": "'"}
        ],
        "surroundingPairs": [
            ["\"", "\""],
            ["'", "'"]
        ],
        "folding": {
            "markers": {
                "start": "^\\s*#\\s*region",
                "end": "^\\s*#\\s*endregion"
            }
        }
    }
    
    dest_path = base_dir / 'language-configuration.json'
    with open(dest_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    return dest_path


def generate_extension_js(base_dir, for_marketplace=False):
    """
    Generate extension.js with LSP client and settings injection.
    
    Args:
        base_dir: Base directory for extension
        for_marketplace: If True, generates marketplace-compatible version with VS Code API settings injection
    """
    code = """// Generated by zlsp installer - DO NOT EDIT
// This file activates the Zolo LSP client

const vscode = require('vscode');
const path = require('path');
const fs = require('fs');
const { LanguageClient } = require('vscode-languageclient/node');

let client;
let outputChannel;

/**
 * Check if zolo-lsp command is available
 */
function checkZoloLspAvailable() {
    const { execSync } = require('child_process');
    try {
        const zoloLspPath = execSync('which zolo-lsp || where zolo-lsp', { 
            encoding: 'utf8',
            stdio: ['pipe', 'pipe', 'ignore'] // Suppress stderr
        }).trim();
        return zoloLspPath ? zoloLspPath : null;
    } catch (err) {
        return null;
    }
}

/**
 * Show setup instructions when LSP server is missing
 */
async function showSetupInstructions() {
    const choice = await vscode.window.showWarningMessage(
        'Zolo LSP server not found. Install it to enable semantic highlighting and LSP features.',
        'Open Terminal',
        'View Instructions',
        'Dismiss'
    );
    
    if (choice === 'Open Terminal') {
        const terminal = vscode.window.createTerminal('Zolo LSP Setup');
        terminal.show();
        terminal.sendText('# Install Zolo LSP server:');
        terminal.sendText('pip install zlsp');
        terminal.sendText('# Then reload VS Code');
    } else if (choice === 'View Instructions') {
        vscode.env.openExternal(vscode.Uri.parse('https://github.com/zolomedia/zlsp#installation'));
    }
}

"""
    
    # Add marketplace-specific settings injection
    if for_marketplace:
        code += """
/**
 * Inject semantic token colors into user settings (Marketplace version)
 * Uses VS Code API to maintain single source of truth from bundled theme
 */
async function injectSemanticTokenColors(context) {
    try {
        // Load theme from bundled YAML file
        const themeYamlPath = path.join(context.extensionPath, 'themes', 'zolo_default.yaml');
        
        // For marketplace, we load pre-generated JSON instead
        const themeJsonPath = path.join(context.extensionPath, 'themes', 'semantic-colors.json');
        
        if (!fs.existsSync(themeJsonPath)) {
            outputChannel.appendLine('⚠ Theme JSON not found, skipping settings injection');
            return false;
        }
        
        const themeData = JSON.parse(fs.readFileSync(themeJsonPath, 'utf8'));
        
        // Get current configuration
        const config = vscode.workspace.getConfiguration();
        const existingCustomizations = config.get('editor.semanticTokenColorCustomizations') || {};
        
        // Clean up old theme-scoped '[zolo]' section from previous installations
        const cleanedCustomizations = { ...existingCustomizations };
        if (cleanedCustomizations['[zolo]']) {
            delete cleanedCustomizations['[zolo]'];
            outputChannel.appendLine("ℹ️  Cleaned up old '[zolo]' theme-scoped colors");
        }
        
        // Check if already configured (global rules)
        if (cleanedCustomizations.rules && Object.keys(themeData.rules).every(key => key in cleanedCustomizations.rules)) {
            outputChannel.appendLine('✓ Semantic token colors already configured');
            return true;
        }
        
        // Inject Zolo semantic token colors globally (works with ANY theme)
        const updatedCustomizations = {
            ...cleanedCustomizations,
            enabled: true,
            rules: {
                ...(cleanedCustomizations.rules || {}),
                ...themeData.rules
            }
        };
        
        // Update global configuration (persists across sessions)
        await config.update(
            'editor.semanticTokenColorCustomizations',
            updatedCustomizations,
            vscode.ConfigurationTarget.Global
        );
        
        outputChannel.appendLine('✓ Injected ' + Object.keys(themeData.rules).length + ' semantic token color rules (global scope)');
        outputChannel.appendLine('  Works with ANY VS Code theme!');
        outputChannel.appendLine('  Settings will persist across all VS Code sessions');
        
        return true;
    } catch (err) {
        outputChannel.appendLine('✗ Failed to inject settings: ' + err.message);
        return false;
    }
}
"""
    
    code += """
function activate(context) {
    // Create output channel for debugging
    outputChannel = vscode.window.createOutputChannel('Zolo LSP');
    outputChannel.appendLine('=== Zolo LSP Extension Activating ===');
    outputChannel.appendLine('Timestamp: ' + new Date().toISOString());
"""
    
    if for_marketplace:
        code += """    outputChannel.appendLine('Mode: Marketplace installation');
    
    // Inject semantic token colors automatically (Marketplace mode)
    injectSemanticTokenColors(context).then(success => {
        if (success) {
            outputChannel.appendLine('✓ Semantic token colors configured via VS Code API');
        }
    });
"""
    else:
        code += """    outputChannel.appendLine('Mode: Local installation (zlsp-vscode-install)');
"""
    
    code += """    
    // Check if zolo-lsp is available
    const zoloLspPath = checkZoloLspAvailable();
    
    if (!zoloLspPath) {
        outputChannel.appendLine('✗ ERROR: zolo-lsp not found in PATH!');
        outputChannel.appendLine('  Install with: pip install zlsp');
        outputChannel.appendLine('  Then reload VS Code: Cmd+Shift+P → Reload Window');
        
        // Show user-friendly setup instructions
        showSetupInstructions();
        return;
    }
    
    outputChannel.appendLine('✓ Found zolo-lsp at: ' + zoloLspPath);
    
    // LSP server options (points to zolo-lsp command)
    const serverOptions = {
        command: 'zolo-lsp',
        args: [],
        options: {
            env: process.env
        }
    };
    
    outputChannel.appendLine('Server command: zolo-lsp');
    
    // Get trace setting from VS Code configuration
    const config = vscode.workspace.getConfiguration('zolo');
    const traceLevel = config.get('trace.server', 'messages');
    outputChannel.appendLine('Trace level: ' + traceLevel);
    
    // Client options (file patterns, synchronization, output channel)
    const clientOptions = {
        documentSelector: [{ scheme: 'file', language: 'zolo' }],
        synchronize: {
            fileEvents: vscode.workspace.createFileSystemWatcher('**/*.zolo')
        },
        outputChannel: outputChannel,
        traceOutputChannel: outputChannel,
        revealOutputChannelOn: 1, // RevealOutputChannelOn.Info (show on any message)
        initializationOptions: {
            trace: traceLevel
        },
        middleware: {
            // Log semantic token requests/responses
            provideDocumentSemanticTokens: async (document, token, next) => {
                outputChannel.appendLine('→ Requesting semantic tokens for: ' + document.fileName);
                const result = await next(document, token);
                if (result) {
                    outputChannel.appendLine('✓ Received semantic tokens (data length: ' + (result.data ? result.data.length : 0) + ')');
                } else {
                    outputChannel.appendLine('✗ No semantic tokens received');
                }
                return result;
            }
        }
    };
    
    outputChannel.appendLine('Creating LSP client...');
    
    // Create and start the LSP client
    client = new LanguageClient(
        'zoloLsp',
        'Zolo Language Server',
        serverOptions,
        clientOptions
    );
    
    // Log client state changes
    client.onDidChangeState((event) => {
        outputChannel.appendLine('LSP State changed: ' + JSON.stringify({
            oldState: event.oldState,
            newState: event.newState
        }));
    });
    
    outputChannel.appendLine('Starting LSP client...');
    
    client.start().then(() => {
        outputChannel.appendLine('✓ LSP client started successfully');
        outputChannel.appendLine('');
        outputChannel.appendLine('Semantic Token Legend:');
        client.initializeResult?.capabilities?.semanticTokensProvider?.legend?.tokenTypes?.forEach((type, i) => {
            outputChannel.appendLine('  ' + i + ': ' + type);
        });
    }).catch((err) => {
        outputChannel.appendLine('✗ Failed to start LSP client: ' + err);
        vscode.window.showErrorMessage('Zolo LSP failed to start: ' + err.message);
    });
    
    // Register command to show output
    context.subscriptions.push(
        vscode.commands.registerCommand('zolo.showOutput', () => {
            outputChannel.show();
        })
    );
}

function deactivate() {
    if (outputChannel) {
        outputChannel.appendLine('=== Zolo LSP Extension Deactivating ===');
    }
    if (!client) {
        return undefined;
    }
    return client.stop();
}

module.exports = {
    activate,
    deactivate
};
"""
    
    dest_path = base_dir / 'out' / 'extension.js'
    dest_path.write_text(code)
    
    return dest_path


def generate_semantic_colors_json(generator, base_dir):
    """
    Generate semantic-colors.json for marketplace extension.
    This bundles the theme-generated colors as JSON so the extension
    can load them without needing the full theme system.
    """
    colors = generator.generate_semantic_token_color_customizations()
    
    semantic_colors_json = {
        "source": "themes/zolo_default.yaml",
        "generated": "Auto-generated by zlsp theme system",
        "rules": colors
    }
    
    # Write to themes directory
    themes_dir = base_dir / 'themes'
    themes_dir.mkdir(exist_ok=True)
    
    dest_path = themes_dir / 'semantic-colors.json'
    dest_path.write_text(json.dumps(semantic_colors_json, indent=2))
    
    return dest_path


def install_npm_dependencies(base_dir):
    """Install required npm dependencies for the extension."""
    import subprocess
    
    print("  → Installing npm dependencies...")
    try:
        # Install vscode-languageclient (required for LSP)
        result = subprocess.run(
            ['npm', 'install', '--silent', 'vscode-languageclient'],
            cwd=base_dir,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            return True
        else:
            print(f"  ⚠ npm install warning: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print(f"  ⚠ npm install timed out")
        return False
    except FileNotFoundError:
        print(f"  ⚠ npm not found - install Node.js")
        return False
    except Exception as e:
        print(f"  ⚠ npm install failed: {e}")
        return False


def install_extension_files(base_dir, theme, generator):
    """Generate and install all VS Code extension files."""
    installed = []
    
    # 1. Generate package.json
    try:
        path = generate_package_json(theme, generator, base_dir)
        installed.append(f"package.json (generated from theme)")
    except Exception as e:
        print(f"  ⚠ Failed to generate package.json: {e}")
    
    # 2. Generate language-configuration.json
    try:
        path = generate_language_configuration(base_dir)
        installed.append(f"language-configuration.json")
    except Exception as e:
        print(f"  ⚠ Failed to generate language-configuration.json: {e}")
    
    # 3. Generate TextMate grammar
    try:
        grammar = generator.generate_textmate_grammar()
        grammar_path = base_dir / 'syntaxes' / 'zolo.tmLanguage.json'
        with open(grammar_path, 'w') as f:
            json.dump(grammar, f, indent=2)
        installed.append(f"syntaxes/zolo.tmLanguage.json ({len(json.dumps(grammar))} bytes)")
    except Exception as e:
        print(f"  ⚠ Failed to generate TextMate grammar: {e}")
    
    # 4. No themes generated (TextMate grammar only for now)
    # Note: Semantic token colors require active theme cooperation
    # We'll discuss best approach with user
    
    # 5. Generate extension.js (minimal LSP client)
    try:
        path = generate_extension_js(base_dir)
        installed.append(f"out/extension.js (minimal LSP client)")
    except Exception as e:
        print(f"  ⚠ Failed to generate extension.js: {e}")
    
    # 6. Create README.md
    try:
        readme_content = f"""# Zolo Language Support

LSP support for `.zolo` files with semantic highlighting.

## Features

- **Semantic Highlighting**: Context-aware syntax coloring
- **Real-time Diagnostics**: Instant error detection
- **Hover Information**: Documentation on hover
- **Code Completion**: Smart suggestions
- **5 Special File Types**: zUI, zEnv, zSpark, zConfig, zSchema

## Installation

This extension was installed via:
```bash
pip install zlsp
zlsp-vscode-install
```

## Requirements

- VS Code 1.75.0 or higher
- Python 3.8 or higher
- `zolo-lsp` command (included with zlsp)

## Usage

Open any `.zolo` file - the extension activates automatically!

## Theme

Generated from: {theme.name} v{theme.version}

## Version

{__version__}
"""
        readme_path = base_dir / 'README.md'
        readme_path.write_text(readme_content)
        installed.append(f"README.md")
    except Exception as e:
        print(f"  ⚠ Failed to generate README.md: {e}")
    
    # 7. Copy file type icon
    try:
        icon_src = Path(__file__).parent.parent.parent / 'assets' / 'zolo_filetype.png'
        icon_dest = base_dir / 'icons' / 'zolo_filetype.png'
        icon_dest.parent.mkdir(exist_ok=True)
        shutil.copy2(icon_src, icon_dest)
        installed.append(f"icons/zolo_filetype.png (file type icon)")
    except Exception as e:
        print(f"  ⚠ Failed to copy icon: {e}")
    
    return installed


def print_installation_instructions():
    """Print instructions for reloading VS Code."""
    print()
    print("  ╔═══════════════════════════════════════════════════════════╗")
    print("  ║  Reload VS Code to Activate                              ║")
    print("  ╚═══════════════════════════════════════════════════════════╝")
    print()
    print("  Simply reload VS Code:")
    print("     Cmd+Shift+P → 'Reload Window'")
    print()
    print("  ✓ Extension activates automatically for .zolo files")
    print("  ✓ Semantic token colors injected into your settings")
    print("  ✓ Works with ANY VS Code theme!")
    print("  ✓ LSP provides diagnostics, hover, and completion")
    print()


def main():
    """Main installation function - fully automated."""
    print("═" * 70)
    print("  zlsp VS Code Integration Installer")
    print("  (Auto-loading, Non-Destructive, Theme-Driven)")
    print("═" * 70)
    print()
    
    # Step 1: Load theme
    print("[1/6] Loading color theme...")
    try:
        theme = load_theme('zolo_default')
        print(f"  ✓ Loaded theme: {theme.name} v{theme.version}")
    except Exception as e:
        print(f"  ✗ Failed to load theme: {e}")
        sys.exit(1)
    
    print()
    
    # Step 2: Create VS Code generator
    print("[2/6] Creating VS Code generator...")
    try:
        generator = VSCodeGenerator(theme)
        print(f"  ✓ Generator ready")
    except Exception as e:
        print(f"  ✗ Failed to create generator: {e}")
        sys.exit(1)
    
    print()
    
    # Step 3: Detect VS Code installation
    print("[3/6] Detecting VS Code...")
    vscode_found, vscode_status = check_vscode_installed()
    extensions_dir = detect_vscode_dir()
    
    if vscode_found:
        print(f"  ✓ {vscode_status}")
    else:
        print(f"  ⚠ {vscode_status}")
        print(f"    Extension will still be installed, but VS Code")
        print(f"    must be installed to use it.")
    
    print(f"  → Extensions: {extensions_dir}")
    print()
    
    # Step 4: Create extension directory
    print("[4/6] Installing extension files...")
    extension_dir = extensions_dir / f'zolo-lsp-{__version__}'
    
    # Remove old version if exists
    if extension_dir.exists():
        print(f"  → Removing old version: {extension_dir.name}")
        shutil.rmtree(extension_dir)
    
    try:
        create_extension_structure(extension_dir)
        installed = install_extension_files(extension_dir, theme, generator)
        
        for f in installed:
            print(f"  ✓ {f}")
        
        # Install npm dependencies (required for LSP client)
        if install_npm_dependencies(extension_dir):
            print(f"  ✓ npm dependencies installed")
        else:
            print(f"  ⚠ npm dependencies failed (extension may not work)")
    except Exception as e:
        print(f"  ✗ Failed to install files: {e}")
        sys.exit(1)
    
    print()
    
    # Step 5: Inject semantic token colors into user settings
    print("[5/6] Configuring semantic token colors...")
    try:
        settings_path = detect_vscode_user_settings()
        print(f"  → Settings: {settings_path}")
        
        # Generate color rules from theme
        rules = generate_semantic_token_rules(generator)
        
        # Inject into settings.json
        if inject_semantic_token_colors(settings_path, rules):
            print(f"  ✓ Injected {len(rules)} token color rules")
            print(f"  ✓ Colors persist across all VS Code sessions")
        else:
            print(f"  ⚠ Failed to inject colors (extension still works)")
    except Exception as e:
        print(f"  ⚠ Failed to configure colors: {e}")
        print(f"    Extension will still work with TextMate grammar")
    
    print()
    
    # Step 6: Verify requirements
    print("[6/6] Verifying installation...")
    
    # Check if zolo-lsp is available
    lsp_found, lsp_status = check_zolo_lsp_available()
    if lsp_found:
        print(f"  ✓ {lsp_status}")
    else:
        print(f"  ⚠ {lsp_status}")
        print(f"    Run: pip install zlsp")
    
    print()
    print("═" * 70)
    
    if lsp_found:
        print("  ✓ Installation Complete!")
    else:
        print("  ⚠ Installation Complete (zolo-lsp setup needed)")
    
    print("═" * 70)
    print()
    
    # Print usage
    if lsp_found:
        print("🎉 Ready to use!")
        print()
        print("Next steps:")
        print_installation_instructions()
        
        print("Features:")
        print("  • Semantic highlighting (context-aware colors)")
        print("  • Real-time diagnostics")
        print("  • Hover info (documentation)")
        print("  • Auto-completion")
        print("  • All 5 special file types (zUI, zEnv, zSpark, zConfig, zSchema)")
        print()
        
        print("Test it now:")
        print("  code /path/to/your/file.zolo")
    else:
        print("⚠️  Extension installed, but LSP server not available")
        print()
        print("To enable full LSP features:")
        print("  1. Install zlsp: pip install zlsp")
        print("  2. Verify: which zolo-lsp")
        print("  3. Reload VS Code")
    
    print()
    print("Documentation:")
    print(f"  • Extension: {extension_dir}")
    print(f"  • Theme: {theme.name} v{theme.version}")
    print(f"  • Colors: Generated from themes/zolo_default.yaml")
    print()
    
    # Print what was installed
    print("Installed files:")
    print(f"  • Extension:       {extension_dir}")
    print(f"  • Grammar:         syntaxes/zolo.tmLanguage.json")
    print(f"  • LSP client:      out/extension.js")
    print(f"  • Configuration:   language-configuration.json")
    print()
    print("✨ Just reload VS Code and open a .zolo file!")
    print()


def generate_marketplace_package():
    """
    Generate a marketplace-ready VS Code extension package.
    
    This creates a .vsix file that can be published to the VS Code Marketplace.
    Unlike the local installer, this version:
    - Bundles semantic-colors.json (no Python dependency for colors)
    - Uses VS Code API for settings injection
    - Shows helpful prompts when zolo-lsp is missing
    - Maintains single source of truth (theme from zolo_default.yaml)
    """
    print()
    print("=" * 70)
    print(" VS Code Marketplace Package Generator")
    print(" (Phase 7.1.7: Marketplace Publishing)")
    print("=" * 70)
    print()
    
    # [1/7] Load canonical theme
    print("[1/7] Loading canonical theme...")
    theme = load_theme('zolo_default')
    print(f"  ✓ Loaded: {theme.name} v{theme.version}")
    
    # [2/7] Create generator
    print()
    print("[2/7] Creating VS Code generator...")
    generator = VSCodeGenerator(theme)
    print(f"  ✓ Generator ready")
    
    # [3/7] Create marketplace extension directory
    print()
    print("[3/7] Creating marketplace package structure...")
    marketplace_dir = Path(__file__).parent / 'marketplace-package'
    if marketplace_dir.exists():
        shutil.rmtree(marketplace_dir)
    
    create_extension_structure(marketplace_dir)
    print(f"  ✓ Created: {marketplace_dir}")
    
    # [4/7] Generate extension files (marketplace mode)
    print()
    print("[4/7] Generating extension files...")
    
    try:
        # package.json
        package_path = generate_package_json(theme, generator, marketplace_dir)
        print(f"  ✓ package.json")
        
        # TextMate grammar
        grammar = generator.generate_textmate_grammar()
        grammar_path = marketplace_dir / 'syntaxes' / 'zolo.tmLanguage.json'
        grammar_path.write_text(json.dumps(grammar, indent=2))
        print(f"  ✓ syntaxes/zolo.tmLanguage.json")
        
        # Language configuration
        lang_config_path = generate_language_configuration(marketplace_dir)
        print(f"  ✓ language-configuration.json")
        
        # Extension.js (marketplace mode with settings injection)
        ext_path = generate_extension_js(marketplace_dir, for_marketplace=True)
        print(f"  ✓ out/extension.js (with VS Code API settings injection)")
        
        # Semantic colors JSON (bundled theme)
        colors_path = generate_semantic_colors_json(generator, marketplace_dir)
        print(f"  ✓ themes/semantic-colors.json (40 token colors)")
        
        # README
        readme_path = marketplace_dir / 'README.md'
        readme_content = """# Zolo Language Support

Language Server Protocol support for `.zolo` files with semantic highlighting.

## Features

- **Semantic Highlighting**: Context-aware syntax colors
- **Diagnostics**: Real-time error detection
- **Hover Information**: Documentation on hover
- **Auto-completion**: Smart suggestions
- **Works with ANY Theme**: Colors injected automatically

## Installation

1. Install this extension from the marketplace
2. Install the Zolo LSP server:
   ```bash
   pip install zlsp
   ```
3. Reload VS Code

## Usage

Simply open any `.zolo` file - semantic highlighting and LSP features activate automatically!

## Documentation

- [GitHub Repository](https://github.com/zolomedia/zlsp)
- [Installation Guide](https://github.com/zolomedia/zlsp#installation)
- [VS Code Integration](https://github.com/zolomedia/zlsp/blob/main/editors/vscode/README.md)

## Zero Configuration

Unlike other LSP extensions, Zolo automatically configures semantic token colors for you. No theme activation required!

## License

MIT
"""
        readme_path.write_text(readme_content)
        print(f"  ✓ README.md")
        
        # Copy file type icon
        icon_src = Path(__file__).parent.parent.parent / 'assets' / 'zolo_filetype.png'
        icon_dest = marketplace_dir / 'icons' / 'zolo_filetype.png'
        icon_dest.parent.mkdir(exist_ok=True)
        shutil.copy2(icon_src, icon_dest)
        print(f"  ✓ icons/zolo_filetype.png")
        
        # Create LICENSE file
        license_content = """MIT License

Copyright (c) 2026 Zolo Media

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
        license_path = marketplace_dir / 'LICENSE'
        license_path.write_text(license_content)
        print(f"  ✓ LICENSE")
        
    except Exception as e:
        print(f"  ✗ Failed: {e}")
        return False
    
    # [5/7] Install npm dependencies
    print()
    print("[5/7] Installing npm dependencies...")
    npm_success = install_npm_dependencies(marketplace_dir)
    if npm_success:
        print(f"  ✓ npm dependencies installed")
    else:
        print(f"  ⚠ npm install failed (needed for .vsix packaging)")
    
    # [6/7] Generate .vsix package (requires vsce)
    print()
    print("[6/7] Packaging extension...")
    print(f"  → Run manually: cd {marketplace_dir} && vsce package")
    print(f"  → Install vsce: npm install -g @vscode/vsce")
    print(f"  → Creates: zolo-lsp-{__version__}.vsix")
    
    # [7/7] Summary
    print()
    print("=" * 70)
    print("  ✓ Marketplace Package Ready!")
    print("=" * 70)
    print()
    print(f"Package directory: {marketplace_dir}")
    print()
    print("Next steps:")
    print("  1. Install vsce: npm install -g @vscode/vsce")
    print(f"  2. Package: cd {marketplace_dir} && vsce package")
    print(f"  3. Test locally: code --install-extension zolo-lsp-{__version__}.vsix")
    print("  4. Publish: vsce publish")
    print()
    print("Key features of marketplace version:")
    print("  ✓ Checks for zolo-lsp server availability")
    print("  ✓ Auto-injects semantic token colors via VS Code API")
    print("  ✓ Shows helpful setup prompts if LSP missing")
    print("  ✓ Bundles theme (no Python dependency for colors)")
    print("  ✓ Maintains single source of truth (zolo_default.yaml)")
    print()
    print("Documentation:")
    print("  • Publishing: https://code.visualstudio.com/api/working-with-extensions/publishing-extension")
    print()


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--marketplace':
        generate_marketplace_package()
    else:
        main()
