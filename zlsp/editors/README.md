# zlsp Editor Integrations

Support for different text editors and IDEs

Each editor gets its own subfolder with installation scripts, configuration files, and documentation.

## Structure

```
editors/
├── _shared/         # Shared utilities for VS Code-based editors
│   └── vscode_base.py  # Base installer class
│
├── vim/             # Vim/Neovim integration
│   ├── install.py
│   ├── config/
│   └── README.md
│
├── vscode/          # VS Code extension
│   ├── install.py
│   └── README.md
│
└── cursor/          # Cursor IDE extension
    ├── install.py
    └── README.md
```

## Current Status

### Vim/Neovim (Complete)
- Full LSP integration via vim-lsp
- Semantic token highlighting
- Filetype detection
- Syntax highlighting (fallback)
- Indentation rules
- One-command installation: `zlsp-install-vim`

### VS Code (Complete)
- Extension using vscode-languageclient
- Semantic token provider
- TextMate grammar (fallback)
- Settings injection (zero-config)
- One-command installation: `zlsp-install-vscode`

### Cursor IDE (Complete)
- Uses VS Code extension format (Cursor is a VS Code fork)
- Identical features to VS Code
- Settings injection (zero-config)
- One-command installation: `zlsp-install-cursor`

## Design Philosophy

1. **LSP-first** - All editors use the same LSP server from core/
2. **Thin clients** - Editors are just LSP clients, no grammar duplication
3. **One-command install** - Simple installation for users
4. **Fallback support** - Basic syntax when LSP isn't available
5. **DRY principle** - VS Code-based editors share common code

## How It Works

```
Editor → LSP Client → core/server/lsp_server.py → core/parser/
```

All editors get the same features automatically:
- Semantic highlighting
- Diagnostics
- Hover info
- Completion
- Go-to-definition (future)

No grammar files needed - parser is the source of truth!

## Adding a New Editor

### For VS Code-based Editors (e.g., Windsurf, Zed)

1. Create `editors/youreditor/` folder
2. Create thin wrapper using `VSCodeBasedInstaller`:
   ```python
   from editors._shared import VSCodeBasedInstaller
   
   def main():
       installer = VSCodeBasedInstaller(
           editor_name="Your Editor",
           dir_name=".youreditor",
           settings_name="YourEditor",
           requires_registry=False  # True if editor needs extensions.json
       )
       return installer.install()
   ```
3. Add entry to `pyproject.toml` scripts section
4. Document in `README.md`

### For Other Editors

1. Create `editors/youreditor/` folder
2. Implement custom LSP client for your editor
3. Add installation script
4. Test semantic tokens work
5. Document in README.md

See `editors/vim/` for a non-VS Code reference implementation.

---

**All 3 editors fully supported and production-ready!**
