# VS Code Integration for Zolo LSP

Complete Visual Studio Code integration for `.zolo` files with LSP support.

## Features

- **Zero Configuration** - Install and it works! No theme activation required
- **Works with ANY Theme** - Dark+, Light+, Monokai, or your favorite
- **Full LSP Features** - Hover, completion, diagnostics, and more
- **Non-Destructive** - Only affects `.zolo` files, leaves everything else alone
- **Automatic** - Colors injected into your settings, persistent across sessions

---

## Quick Setup

### Prerequisites

- **Visual Studio Code** 1.75 or later
- **Python 3.8+** (for zlsp installation)

### Installation Options

**Recommended: Python Installer (Primary)**

```bash
pip install zlsp
zlsp-install-vscode
```

Then reload VS Code: `Cmd+Shift+P` → "Reload Window"

**Alternative: VS Code Marketplace (Future)**

Coming soon! The extension will be available on VS Code Marketplace with the same zero-config experience:

1. Install from marketplace: Search "Zolo Language Support"
2. Extension auto-detects if `zolo-lsp` is installed
3. If not found, shows prompt: "Install LSP server: `pip install zlsp`"
4. After installing, reload VS Code
5. Colors auto-inject via VS Code API

**Both methods maintain single source of truth and work identically!**

---

## What Gets Installed?

The installer does **two things**:

### 1. VS Code Extension
Installs to `~/.vscode/extensions/zolo-lsp-1.0.0/`:

```
~/.vscode/extensions/zolo-lsp-1.0.0/
├── package.json                   # Extension manifest (40 semantic token types)
├── language-configuration.json    # Language settings (brackets, comments)
├── syntaxes/
│   └── zolo.tmLanguage.json      # TextMate grammar (fallback highlighting)
├── out/
│   └── extension.js              # LSP client (connects to zolo-lsp server)
└── README.md                      # Extension documentation
```

### 2. User Settings (The Secret Sauce!)
Injects semantic token colors into `~/Library/Application Support/Code/User/settings.json`:

```json
{
  "editor.semanticTokenColorCustomizations": {
    "[zolo]": {
      "enabled": true,
      "rules": {
        "comment": {"foreground": "#6F6F62", "fontStyle": "italic"},
        "rootKey": {"foreground": "#ffaf87"},
        "nestedKey": {"foreground": "#ffd787"},
        "string": {"foreground": "#fffbcb"},
        "number": {"foreground": "#FF8C00"},
        "boolean": {"foreground": "#0087ff"},
        // ... 35 more token types
      }
    }
  }
}
```

**Why settings injection?**
- ✅ Works with **any** VS Code theme (not locked to one)
- ✅ Colors persist across all sessions and workspaces
- ✅ Zero manual configuration
- ✅ Language-scoped (only affects `.zolo` files)

---

## Color Scheme

Carefully tuned semantic token colors (matches Vim exactly):

| Element | Color | Hex | Description |
|---------|-------|-----|-------------|
| Root keys | Salmon/Orange | `#ffaf87` | Top-level configuration keys |
| Nested keys | Golden Yellow | `#ffd787` | Nested object keys |
| Strings | Light Cream | `#fffbcb` | String values |
| Numbers | Dark Orange | `#FF8C00` | Numeric values |
| Type hints | Cyan | `#5fd7ff` | Type annotations `(str)`, `(int)` |
| Type hint `()` | Soft Yellow | `#ffff5f` | Parentheses in type hints |
| Array `[]` | Light Pink | `#ffd7ff` | Array structural brackets |
| Object `{}` | Light Pink | `#ffd7ff` | Object structural braces |
| Booleans | Deep Blue | `#0087ff` | `true`, `false` |
| Comments | Gray (italic) | `#6F6F62` | `# comments` and `#> inline <#` |
| Commas/Colons | Soft Yellow | `#ffff5f` | Structural punctuation |

### Works with Your Theme!

Unlike traditional LSP extensions that require theme activation, zlsp works with **any active theme**:

- ✅ Dark+ (default dark)
- ✅ Light+ (default light)
- ✅ Dark Modern
- ✅ Monokai
- ✅ Solarized
- ✅ Your custom theme!

The semantic token colors are **language-scoped** to `.zolo` files only, so your other files remain unaffected.

---

## Usage

Open any `.zolo` file:

```bash
code test.zolo
```

### LSP Features

| Feature | Action | Description |
|---------|--------|-------------|
| **Hover** | Hover over key/value | Show documentation |
| **Completion** | `Ctrl+Space` | Suggest keys and values |
| **Diagnostics** | Automatic | Red squiggles for errors |
| **Semantic Highlighting** | Automatic | Context-aware colors |

### Check LSP Status

1. Open Output panel: `Cmd+Shift+U` (macOS) or `Ctrl+Shift+U` (Windows/Linux)
2. Select "Zolo LSP" from dropdown
3. Look for: `Zolo Language Server initialized`

---

## How It Works

### Architecture (Dual Paths, Same Source)

```
┌──────────────────────────────────────┐
│ themes/zolo_default.yaml             │  ← Single Source of Truth
│ (40 semantic token definitions)      │
└──────────────────────────────────────┘
                 ↓
        [VSCodeGenerator]
                 ↓
    ┌────────────┴────────────────┐
    ↓                              ↓
[Python Installer]        [Marketplace Extension]
zlsp-vscode-install       (future)
    ↓                              ↓
Writes to                  Writes via
settings.json              VS Code API
(file system)              (ConfigurationTarget.Global)
    ↓                              ↓
    └────────────┬─────────────────┘
                 ↓
         Same Result:
    settings.json updated
    40 token colors injected
```

**Key Principle:** Both paths maintain single source of truth (`themes/zolo_default.yaml`).

**Installation Method Comparison:**

| Aspect | Python Installer | Marketplace |
|--------|-----------------|-------------|
| **Color Source** | zolo_default.yaml | zolo_default.yaml (bundled) |
| **Settings Injection** | File write | VS Code API |
| **LSP Server** | Checked, assumed installed | Checked, prompts if missing |
| **User Experience** | 2 commands | 1 click + 1 command |
| **Maintains SSOT** | ✅ Yes | ✅ Yes |
| **Zero Config** | ✅ Yes | ✅ Yes |

**Both are valid, both maintain architectural integrity!**

### Zero-Config Experience

Traditional LSP extensions:
```
1. Install extension
2. Activate bundled theme (manual)
3. Configure settings (manual)
4. Hope colors match across editors
```

zlsp:
```
1. Run zlsp-install-vscode
2. Reload VS Code
✓ Done! Works with any theme!
```

### Why This Is Better

**Settings injection is unconventional but superior:**

| Approach | Pros | Cons |
|----------|------|------|
| **Bundled Theme** (traditional) | Simple extension | ❌ Manual activation<br>❌ Can't use other themes<br>❌ Inconsistent across editors |
| **Settings Injection** (zlsp) | ✅ Zero config<br>✅ Any theme<br>✅ Cross-editor consistency | Modifies user settings |

We chose **user experience over technical purity**. The result: true zero-config installation.

---

## Troubleshooting

### Colors not showing?

**1. Check VS Code version:**
```bash
code --version  # Should be 1.75+
```

**2. Verify LSP server is running:**
- Open Output panel: `Cmd+Shift+U`
- Select "Zolo LSP" from dropdown
- Look for: `Zolo Language Server initialized`

**3. Check settings were injected:**
- Open Settings: `Cmd+,` → Search "semantic token"
- Look for `editor.semanticTokenColorCustomizations`
- Should see `"[zolo]"` section with 40 rules

**4. Reload VS Code:**
```
Cmd+Shift+P → "Reload Window"
```

### LSP Server not found?

**Verify zlsp is installed:**
```bash
pip show zlsp
which zolo-lsp  # Should show path
```

**Reinstall if needed:**
```bash
pip install --upgrade --force-reinstall zlsp
zlsp-install-vscode
```

### Extension not activating?

**Check for conflicting extensions:**
1. Go to Extensions: `Cmd+Shift+X`
2. Search for "zolo"
3. Disable any other `.zolo` extensions
4. Reload VS Code

**Verify extension is installed:**
```bash
ls ~/.vscode/extensions/ | grep zolo-lsp
# Should show: zolo-lsp-1.0.0
```

### Bracket colors interfering?

This should be automatic, but if bracket pair colorization is overriding our colors:

1. Open Settings: `Cmd+,`
2. Search: `bracket pair colorization`
3. Uncheck: `Editor › Bracket Pair Colorization: Enabled`
4. Reload VS Code

### Settings backup?

If your `settings.json` was invalid JSON, the installer creates a backup:

```bash
ls ~/Library/Application\ Support/Code/User/settings.json.backup.*
```

To restore:
```bash
cp ~/Library/Application\ Support/Code/User/settings.json.backup.TIMESTAMP \
   ~/Library/Application\ Support/Code/User/settings.json
```

---

## Advanced

### Customizing Colors

Edit your VS Code `settings.json` directly:

```json
{
  "editor.semanticTokenColorCustomizations": {
    "[zolo]": {
      "rules": {
        "comment": {"foreground": "#YOUR_COLOR", "fontStyle": "italic"},
        "rootKey": {"foreground": "#YOUR_COLOR"}
        // ... customize any token type
      }
    }
  }
}
```

### All Token Types

The extension defines 40 semantic token types:

**Keys:** `rootKey`, `nestedKey`, `zmetaKey`, `zkernelDataKey`, `zschemaPropertyKey`, `bifrostKey`, `uiElementKey`, `zconfigKey`, `zsparkKey`, `zenvConfigKey`, `znavbarNestedKey`, `zsubKey`, `zsparkNestedKey`, `zrbacKey`, `zrbacOptionKey`, `zmachineEditableKey`, `zmachineLockedKey`

**Values:** `string`, `number`, `boolean`, `null`, `versionString`, `timestampString`, `timeString`, `ratioString`, `zpathValue`, `envConfigValue`, `zsparkModeValue`, `zsparkVaFileValue`, `zsparkSpecialValue`

**Structural:** `bracketStructural`, `braceStructural`, `stringBracket`, `stringBrace`, `colon`, `comma`

**Type Hints:** `typeHint`, `typeHintParen`

**Comments:** `comment`

**Escape Sequences:** `escapeSequence`

### Debugging Output

Enable trace logging:

1. Open Settings: `Cmd+,`
2. Search: `zolo.trace.server`
3. Set to: `verbose`
4. Reload VS Code
5. Check Output panel → "Zolo LSP"

---

## Uninstallation

### Complete Cleanup (Recommended)

Use our Python uninstaller for complete removal:

```bash
zlsp-uninstall-vscode
```

**This will:**
1. ✅ Remove extension directory: `~/.vscode/extensions/zolo-lsp-1.0.0/`
2. ✅ Clean up settings: Remove `"[zolo]"` section from `settings.json`
3. ✅ Create backup: `settings.json.backup.TIMESTAMP` (safety!)
4. ✅ Confirm before removing

**Example output:**
```
[1/3] Checking for installed extension...
  ✓ Found: ~/.vscode/extensions/zolo-lsp-1.0.0

[2/3] Checking for settings...
  ✓ Found Zolo settings: ~/Library/Application Support/Code/User/settings.json

Will remove:
  • Extension: ~/.vscode/extensions/zolo-lsp-1.0.0
  • Settings: '[zolo]' section in settings.json

Proceed with uninstallation? (y/N): y

[3/3] Uninstalling...
  ✓ Backup created: settings.json.backup.20260115_143022
  ✓ Extension directory removed
  ✓ Removed '[zolo]' section from semantic token customizations

✓ Uninstallation Complete!
```

---

### VS Code UI Uninstall (Partial Cleanup)

**If you uninstall via VS Code Extensions UI:**
- ✅ Extension directory removed automatically
- ❌ Settings remain in `settings.json` (VS Code limitation)

**To clean up settings after VS Code UI uninstall:**
```bash
# Option 1: Use our cleanup (doesn't require extension)
python3 -c "from editors.vscode.uninstall import remove_semantic_token_colors_from_settings, get_vscode_user_settings_path; remove_semantic_token_colors_from_settings(get_vscode_user_settings_path())"

# Option 2: Manual cleanup
code ~/Library/Application\ Support/Code/User/settings.json
# Delete the "[zolo]" section under "editor.semanticTokenColorCustomizations"
```

**Note:** Industry standard - most VS Code extensions (rust-analyzer, Pylance, ESLint) leave settings after uninstall. This is a VS Code API limitation (no uninstall hooks).

---

### Manual Uninstallation

**macOS:**
```bash
# Remove extension
rm -rf ~/.vscode/extensions/zolo-lsp-*

# Remove settings
code ~/Library/Application\ Support/Code/User/settings.json
# Delete the "[zolo]" section
```

**Linux:**
```bash
# Remove extension
rm -rf ~/.vscode/extensions/zolo-lsp-*

# Remove settings
code ~/.config/Code/User/settings.json
# Delete the "[zolo]" section
```

**Windows:**
```bash
# Remove extension
rmdir /s "%USERPROFILE%\.vscode\extensions\zolo-lsp-*"

# Remove settings
code %APPDATA%\Code\User\settings.json
# Delete the "[zolo]" section
```

---

## Platform Support

| Platform | Status | Settings Path |
|----------|--------|---------------|
| **macOS** | ✅ Tested | `~/Library/Application Support/Code/User/settings.json` |
| **Linux** | ✅ Supported | `~/.config/Code/User/settings.json` |
| **Windows** | ⏸️ Future | `%APPDATA%\Code\User\settings.json` |

---

## Architecture

```
zlsp/editors/
├── _shared/
│   └── vscode_base.py       # Shared installer base class (VSCode/Cursor)
│       ├── generate_package_json()
│       ├── generate_textmate_grammar()
│       ├── generate_extension_js()
│       └── inject_semantic_token_colors_into_settings()  ← The magic!
├── vscode/
│   ├── install.py           # VSCode installer (thin wrapper, 43 lines)
│   ├── uninstall.py         # Cleanup script
│   └── README.md            # This file
└── cursor/
    └── install.py           # Cursor installer (thin wrapper, 45 lines)

zlsp/themes/generators/vscode.py
├── generate_textmate_grammar()         # Basic syntax highlighting
├── generate_semantic_tokens_legend()   # 40 token types
└── generate_semantic_token_color_customizations()  # Rules for settings.json
```

**Design Philosophy:**
1. **Single Source of Truth:** `themes/zolo_default.yaml`
2. **DRY Architecture:** Shared base class for VSCode-based editors
3. **Python-First:** No npm, no TypeScript compilation
4. **Theme-Generated:** All colors from canonical theme
5. **Zero-Config:** Settings injection for automatic setup

---

## Comparison with Other Editors

| Feature | Vim/Neovim | VS Code |
|---------|------------|---------|
| **Installation** | `zlsp-install-vim` | `zlsp-install-vscode` |
| **Colors** | Direct ANSI injection | Settings injection |
| **Theme Requirement** | None | None (works with any) |
| **Manual Setup** | None | None |
| **Color Consistency** | Matches VS Code | Matches Vim |

**Both editors get identical colors from the same canonical theme!**

---

## More Info

- [LSP Server Docs](../../Documentation/ARCHITECTURE.md)
- [Zolo Format Spec](../../README.md)
- [Vim Integration](../vim/README.md)
- [Installation Guide](../../Documentation/INSTALLATION.md)

---

## Contributing

Found a bug or have a suggestion?

1. Check the Output panel (`Zolo LSP`) for error messages
2. Open an issue with:
   - VS Code version (`code --version`)
   - zlsp version (`pip show zlsp`)
   - Error messages from Output panel
   - Your `settings.json` (relevant section)

---

**Made by Zolo Media**
