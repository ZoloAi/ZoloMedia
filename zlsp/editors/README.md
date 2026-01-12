# zlsp Editor Integrations

**Support for different text editors and IDEs**

Each editor gets its own subfolder with installation scripts, configuration files, and documentation.

## Structure

```
editors/
├── vim/        # Vim/Neovim integration ✅ COMPLETE
│   ├── install.py         # Installation script
│   ├── config/            # Vim config files
│   └── README.md
│
├── vscode/     # VS Code extension (future)
│   ├── package.json
│   ├── extension.js
│   └── README.md
│
└── cursor/     # Cursor IDE extension (future)
    ├── package.json
    ├── extension.js
    └── README.md
```

## Current Status

### ✅ Vim (Complete)
- Full LSP integration via vim-lsp
- Semantic token highlighting
- Filetype detection
- Syntax highlighting (fallback)
- Indentation rules
- One-command installation: `zolo-vim-install`

### 🔜 VS Code (Planned)
- Extension using vscode-languageclient
- Semantic token provider
- TextMate grammar (fallback)
- Marketplace publication

### 🔜 Cursor (Planned)
- Fork of VS Code extension
- Cursor-specific optimizations
- AI context integration

## Design Philosophy

1. **LSP-first** - All editors use the same LSP server from core/
2. **Thin clients** - Editors are just LSP clients, no grammar duplication
3. **One-command install** - Simple installation for users
4. **Fallback support** - Basic syntax when LSP isn't available
5. **Extractable** - Each can become standalone extension repo

## How It Works

```
Editor → LSP Client → core/server/lsp_server.py → core/parser/
```

All editors get the same features automatically:
- Semantic highlighting
- Diagnostics
- Hover info
- Completion
- Go-to-definition

No grammar files needed - parser is the source of truth!

## Adding a New Editor

1. Create `editors/youreditor/` folder
2. Implement LSP client for your editor
3. Add installation script
4. Test semantic tokens work
5. Document in README.md

See `editors/vim/` as a reference implementation.
