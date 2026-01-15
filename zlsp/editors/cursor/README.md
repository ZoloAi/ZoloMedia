# Zolo Language Support for Cursor IDE

**Zero-configuration LSP integration for `.zolo` declarative files in Cursor IDE**

> **Note:** Cursor IDE is a VS Code fork with AI features. Our extension works identically to VS Code with the same zero-config experience!

---

## ✨ Features

- 🎨 **Semantic Highlighting** - Context-aware syntax highlighting
- 🔍 **Real-time Diagnostics** - Catch errors as you type
- 💡 **Hover Information** - Type hints and documentation
- ⚡ **Code Completion** - Smart completions for keys and values
- 🎯 **Special File Types** - zSpark, zEnv, zUI, zConfig, zSchema support
- 🌈 **Theme Integration** - Works with ANY Cursor theme
- 🚀 **Zero Configuration** - Install and it just works!

---

## 🚀 Quick Setup

### Prerequisites

- **Cursor IDE** (any version)
- **Python 3.8+**
- **zlsp** package installed

### Installation (2 Steps)

```bash
# 1. Install zlsp
pip install zlsp

# 2. Install Cursor extension (one command!)
zlsp-cursor-install

# 3. Reload Cursor
# Cmd+Shift+P > "Reload Window"
```

**That's it!** Open any `.zolo` file and enjoy full LSP features.

---

## 📦 What Gets Installed

### Extension Files
```
~/.cursor/extensions/zolo-lsp-1.0.0/
├── package.json                   # Extension manifest
├── language-configuration.json    # Language settings
├── syntaxes/zolo.tmLanguage.json  # TextMate grammar
├── out/extension.js               # LSP client
├── node_modules/                  # LSP client dependencies
└── README.md                      # Extension docs
```

### Settings Injection (The Secret Sauce!)
```
~/Library/Application Support/Cursor/User/settings.json
└── editor.semanticTokenColorCustomizations["[zolo]"]
    └── 40 token color rules injected ✅
```

**Why settings injection?**
- ✅ Zero manual configuration
- ✅ Works with ANY theme (Dark+, Light+, Monokai, etc.)
- ✅ Persists across Cursor updates
- ✅ Only affects `.zolo` files (language-scoped)

---

## 🎨 Color Scheme

All colors match Vim exactly (single source of truth: `themes/zolo_default.yaml`)

| Token Type | Color | Example |
|------------|-------|---------|
| Comments | Gray italic | `# This is a comment` |
| Root Keys | Bright Blue | `zSpark:`, `zUI:`, `name:` |
| Type Hints | Cyan | `port(int):`, `enabled(bool):` |
| Strings | Light Yellow | `"Hello, World!"` |
| Numbers | Dark Orange | `8080`, `3.14` |
| Booleans | Light Green | `true`, `false` |
| Null | Light Gray | `null` |

**40 semantic token types** in total, all perfectly color-coded!

---

## 💻 Usage

### Open a .zolo File

```bash
cursor examples/zSpark.example.zolo
```

You'll immediately see:
- ✅ Syntax highlighting (semantic, context-aware)
- ✅ Diagnostics in the Problems panel
- ✅ Hover information on keys/values
- ✅ Code completion as you type

### LSP Features Available

| Feature | Keyboard Shortcut | Description |
|---------|------------------|-------------|
| **Hover** | Hover with mouse | Shows type hint documentation |
| **Completion** | `Ctrl+Space` | Suggests keys, values, type hints |
| **Diagnostics** | Automatic | Real-time error detection |
| **Go to Definition** | `F12` | (Future feature) |
| **Find References** | `Shift+F12` | (Future feature) |

---

## 🛠️ How It Works

### Architecture

```
┌────────────────────────────────────────────────────┐
│ themes/zolo_default.yaml (Single Source of Truth) │
└─────────────────┬──────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────────────┐
│ VSCodeGenerator (Cursor uses same format!)        │
│ • TextMate grammar                                  │
│ • Semantic token legend                             │
│ • Color rules                                       │
└─────────────────┬───────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────────────┐
│ zlsp-cursor-install (Python installer)             │
│ 1. Generate extension files from theme             │
│ 2. Install to ~/.cursor/extensions/                │
│ 3. Inject colors into settings.json                │
└─────────────────┬───────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────────────┐
│ Cursor IDE                                          │
│ • Loads extension automatically                     │
│ • Connects to zolo-lsp server                       │
│ • Applies semantic token colors                     │
│ • Works with ANY theme! ✅                          │
└─────────────────────────────────────────────────────┘
```

### Zero-Config Experience

**Traditional LSPs:**
1. Install extension ❌
2. Reload editor ❌
3. Activate bundled theme ❌
4. Configure settings ❌

**zlsp for Cursor:**
1. Run `zlsp-cursor-install` ✅
2. Reload Cursor ✅
3. **Done!** Works with any theme ✅

---

## 🐛 Troubleshooting

### 1. Colors Not Showing

**Check:**
```bash
# Is extension installed?
ls ~/.cursor/extensions/ | grep zolo-lsp

# Is zolo-lsp server available?
which zolo-lsp

# Is settings.json updated?
cat ~/Library/Application\ Support/Cursor/User/settings.json | grep zolo
```

**Fix:**
```bash
# Reinstall
zlsp-cursor-uninstall
zlsp-cursor-install
```

### 2. LSP Server Not Found

**Error:** `Cannot find module 'zolo-lsp'`

**Fix:**
```bash
# Ensure zlsp is installed
pip install --upgrade zlsp

# Verify command exists
zolo-lsp --version
```

### 3. Extension Not Activating

**Check Cursor logs:**
1. Open Command Palette (`Cmd+Shift+P`)
2. Type: "Developer: Show Logs"
3. Select "Extension Host"
4. Look for "zolo-lsp" errors

**Common causes:**
- Node modules not installed: `cd ~/.cursor/extensions/zolo-lsp-* && npm install`
- Conflicting `.zolo` extension installed
- Cursor needs full restart (not just reload)

### 4. Settings Injection Failed

**Symptoms:** Extension works but colors are basic/wrong

**Fix:**
```bash
# Manual cleanup
mv ~/Library/Application\ Support/Cursor/User/settings.json ~/Desktop/settings.json.backup

# Reinstall (will create new settings.json)
zlsp-cursor-install
```

---

## 🗑️ Uninstallation

### Complete Cleanup (Recommended)

```bash
zlsp-cursor-uninstall
```

**Removes:**
- ✅ Extension directory (`~/.cursor/extensions/zolo-lsp-*`)
- ✅ Settings injection (`settings.json` cleaned up with backup)

### Cursor UI Uninstall (Partial)

Right-click extension → "Uninstall"

**Only removes:**
- ✅ Extension directory

**Does NOT remove:**
- ❌ Settings injection (industry-standard VS Code/Cursor behavior)

**To fully clean up after UI uninstall:**
```bash
# Remove Zolo settings manually (backup created automatically)
zlsp-cursor-uninstall
```

Or edit `settings.json` manually:
```json
{
  "editor.semanticTokenColorCustomizations": {
    "[zolo]": { ... }  ← Remove this section
  }
}
```

---

## 🌍 Platform Support

| Platform | Status | Settings Path |
|----------|--------|---------------|
| **macOS** | ✅ Tested | `~/Library/Application Support/Cursor/User/settings.json` |
| **Linux** | ✅ Should work | `~/.config/Cursor/User/settings.json` |
| **Windows** | ✅ Should work | `%APPDATA%\Cursor\User\settings.json` |

---

## 🆚 Cursor vs VS Code

| Feature | Cursor | VS Code | Notes |
|---------|--------|---------|-------|
| Extension Format | ✅ Same | ✅ Same | Cursor is a VS Code fork |
| Installation | `zlsp-cursor-install` | `zlsp-vscode-install` | Same process |
| Extension Dir | `~/.cursor/extensions/` | `~/.vscode/extensions/` | Different paths |
| Settings Path | `~/Library/.../Cursor/User/` | `~/Library/.../Code/User/` | Different paths |
| LSP Features | ✅ Identical | ✅ Identical | Same `zolo-lsp` server |
| Colors | ✅ Identical | ✅ Identical | Same theme source |
| AI Features | ✅ Cursor-specific | ❌ N/A | Cursor adds AI |

**Both work perfectly!** Choose based on your preference for AI features.

---

## 🔧 Advanced

### Debugging

Enable LSP server logs in `settings.json`:
```json
{
  "zolo.trace.server": "verbose"
}
```

View logs:
- Command Palette → "Zolo LSP" output channel

### Customizing Colors

Override any token color in your `settings.json`:
```json
{
  "editor.semanticTokenColorCustomizations": {
    "[zolo]": {
      "enabled": true,
      "rules": {
        "comment": "#FF0000",  // Make comments red
        "number": "#00FF00"    // Make numbers green
      }
    }
  }
}
```

### All 40 Semantic Token Types

```
comment, rootKey, nestedKey, zmetaKey, zkernelDataKey,
zschemaPropertyKey, bifrostKey, uiElementKey, zconfigKey,
zsparkKey, zenvConfigKey, znavbarNestedKey, zsubKey,
zsparkNestedKey, zsparkModeValue, zsparkVaFileValue,
zsparkSpecialValue, envConfigValue, zrbacKey, zrbacOptionKey,
typeHint, number, string, boolean, null,
bracketStructural, braceStructural, stringBracket, stringBrace,
colon, comma, escapeSequence, versionString, timestampString,
timeString, ratioString, zpathValue, zmachineEditableKey,
zmachineLockedKey, typeHintParen
```

---

## 📚 More Information

- **Main Project:** [zlsp](https://github.com/ZoloAi/zlsp)
- **Documentation:** [Documentation/](../../Documentation/)
- **Vim Integration:** [editors/vim/README.md](../vim/README.md)
- **VS Code Integration:** [editors/vscode/README.md](../vscode/README.md)
- **Issues:** [GitHub Issues](https://github.com/ZoloAi/zlsp/issues)

---

## 🎉 Summary

**What makes zlsp + Cursor special:**

1. ✅ **Zero-config** - Install and it just works
2. ✅ **Theme-agnostic** - Works with ANY Cursor theme
3. ✅ **Cross-editor consistency** - Identical colors in Vim, VS Code, Cursor
4. ✅ **Single source of truth** - All colors from one canonical theme file
5. ✅ **Production-ready** - 590 tests, 81% coverage
6. ✅ **Fast** - LSP server responds instantly
7. ✅ **Cursor-native** - Uses Cursor's exact same extension format as VS Code

**Enjoy coding in `.zolo` with full IDE support!** 🚀

---

**Version:** 1.0.0  
**Last Updated:** January 15, 2026
