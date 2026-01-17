# Zolo Language Support for Cursor IDE

Zero-configuration LSP integration for `.zolo` declarative files in Cursor IDE

> **Note:** Cursor IDE is a VS Code fork with AI features. Our extension works identically to VS Code with the same zero-config experience. See [VS Code Integration](../vscode/README.md) for comprehensive documentation.

---

## Quick Setup

### Prerequisites

- Cursor IDE (any version)
- Python 3.8+
- zlsp package installed

### Installation

```bash
# Install zlsp
pip install zlsp

# Install Cursor extension (one command!)
zlsp-install-cursor

# Reload Cursor: Cmd+Shift+P > "Reload Window"
```

**That's it!** Open any `.zolo` file and enjoy full LSP features.

---

## Features

- **Semantic Highlighting** - Context-aware syntax highlighting
- **Real-time Diagnostics** - Catch errors as you type
- **Hover Information** - Type hints and documentation
- **Code Completion** - Smart completions for keys and values
- **Special File Types** - zSpark, zEnv, zUI, zConfig, zSchema support
- **Theme Integration** - Works with ANY Cursor theme
- **Zero Configuration** - Install and it just works

---

## What Gets Installed

### Extension Files
```
~/.cursor/extensions/zolo-lsp-1.0.0/
├── package.json
├── language-configuration.json
├── syntaxes/zolo.tmLanguage.json
├── out/extension.js
└── node_modules/
```

### Settings Injection
```
~/Library/Application Support/Cursor/User/settings.json
└── editor.semanticTokenColorCustomizations
    └── 40 token color rules injected (works with ANY theme)
```

---

## Cursor-Specific Details

### Differences from VS Code

| Aspect | Cursor | VS Code |
|--------|--------|---------|
| Installation | `zlsp-install-cursor` | `zlsp-install-vscode` |
| Extension Dir | `~/.cursor/extensions/` | `~/.vscode/extensions/` |
| Settings Path (macOS) | `~/Library/.../Cursor/User/` | `~/Library/.../Code/User/` |
| Settings Path (Linux) | `~/.config/Cursor/User/` | `~/.config/Code/User/` |
| LSP Features | Identical | Identical |
| Colors | Identical | Identical |
| AI Features | Yes (Cursor-specific) | No |

### Extension Registry

Unlike VS Code, Cursor requires registration in `extensions.json`. Our installer handles this automatically.

---

## Troubleshooting

### Colors Not Showing

```bash
# Check installation
ls ~/.cursor/extensions/ | grep zolo-lsp
which zolo-lsp

# Reinstall if needed
zlsp-uninstall-cursor
zlsp-install-cursor
```

### LSP Server Not Found

```bash
# Install/upgrade zlsp
pip install --upgrade zlsp

# Verify
zolo-lsp --version
```

### Extension Not Activating

1. Open Command Palette (`Cmd+Shift+P`)
2. Type: "Developer: Show Logs"
3. Select "Extension Host"
4. Look for "zolo-lsp" errors

**Common causes:**
- Node modules not installed
- Conflicting `.zolo` extension
- Cursor needs full restart (not just reload)

### Full Troubleshooting

See [VS Code Integration](../vscode/README.md#troubleshooting) for comprehensive troubleshooting (same process for Cursor).

---

## Uninstallation

### Complete Cleanup (Recommended)

```bash
zlsp-uninstall-cursor
```

Removes:
- Extension directory (`~/.cursor/extensions/zolo-lsp-*`)
- Settings injection (with backup)

### UI Uninstall (Partial)

Right-click extension → "Uninstall"

**Note:** This only removes the extension directory, not settings. Use `zlsp-uninstall-cursor` for complete cleanup.

---

## Platform Support

| Platform | Status | Settings Path |
|----------|--------|---------------|
| macOS | Tested | `~/Library/Application Support/Cursor/User/settings.json` |
| Linux | Supported | `~/.config/Cursor/User/settings.json` |
| Windows | Supported | `%APPDATA%\Cursor\User\settings.json` |

---

## Advanced Configuration

### Debugging

Enable verbose logging in `settings.json`:
```json
{
  "zolo.trace.server": "verbose"
}
```

View logs: Command Palette → "Zolo LSP" output channel

### Customizing Colors

Override token colors in `settings.json`:
```json
{
  "editor.semanticTokenColorCustomizations": {
    "rules": {
      "comment": "#FF0000",
      "number": "#00FF00"
    }
  }
}
```

---

## More Information

- **Main Project:** [zlsp](https://github.com/ZoloAi/zlsp)
- **Full Documentation:** [VS Code Integration](../vscode/README.md) (applies to Cursor)
- **Vim Integration:** [vim/README.md](../vim/README.md)
- **Installation Guide:** [Documentation/INSTALLATION.md](../../Documentation/INSTALLATION.md)

---

## Summary

**What makes zlsp + Cursor special:**

- Zero-config installation
- Works with ANY Cursor theme
- Cross-editor consistency (identical colors in Vim, VS Code, Cursor)
- Single source of truth (all colors from canonical theme)
- Cursor-native (uses same extension format as VS Code)
- AI-enhanced editing with Cursor's features

**Version:** 1.0.0  
**Last Updated:** January 17, 2026
