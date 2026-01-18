# Zolo Media<br>
**A Declerative-Driven Ecosystem**

**Website:** [zolo.media](https://zolo.media)  
**Organization:** [github.com/ZoloAi](https://github.com/ZoloAi)

## About

**Zolo Media** is the official **open-source monorepo** for the **zEcosystem**, housing **zLSP**, **zOS**, and **zKernel**.  
Following the *"Linux From Scratch"* philosophy of building primitives into complex compounds.

> **⚠️ Important:** There is NO package called `zolo` - use `zlsp` and `zOS` as the correct package names. A public `zolo` package exists on PyPI that is unrelated to this project and will cause import conflicts.

## Monorepo's Structure
```
ZoloMedia/
├── zlsp/                   ← Language Server Protocol
├── zOS/                    ← OS Integration Utilities
└── zKernel/                ← Core Framework
    ├── zBifrost/           ← Websocket Communications
    └── zTheme/             ← UI Framework
```

## Packages

### **zlsp** - Language Server Protocol

Language Server Protocol implementation for `.zolo` declarative files.

- **Pure LSP Architecture** - Parser is the source of truth
- **String-First Philosophy** - Values are strings by default
- **Editor Agnostic** - Works with Vim, VSCode, Cursor, and any LSP-compatible editor
- **Semantic Features** - Highlighting, diagnostics, hover, completion
- **Zero Dependencies** - Primitive component

**Install:**
```bash
pip install zlsp
zlsp-install-vim      # Automated Vim integration
zlsp-install-vscode   # Automated VSCode integration
zlsp-install-cursor   # Automated Cursor integration
zlsp-install-all      # Install for all supported editors
```

**Learn More**: See [zlsp/README.md](zlsp/README.md) for detailed documentation, architecture, and advanced usage.

---

### **zOS** - Operating System Integration

**Status:** Coming Next | Depends on zlsp

Cross-platform OS utilities and system-level abstractions.

- File system operations
- Process management
- Environment configuration
- Platform detection

---

### **zKernel** - Core Framework

**Status:** Planned | Depends on zlsp + zOS

Core framework and configuration system.

- Declarative configuration (uses zlsp parser)
- Event-driven architecture
- Plugin system
- Application framework

---

### **zCloud** - Cloud Platform

**Status:** Planned | Depends on zKernel

Cloud-native deployment and media management platform.

- Media management
- CDN integration
- Analytics and quota management
- Deployment automation

---

### **zTheme** - UI Framework

**Status:** Planned

Beautiful, modern UI theme framework.

- CSS framework
- Component library
- Responsive design

---

## Development Philosophy

**Dependency Flow:**
```
zlsp (no deps)
  ↓
zOS (depends on zlsp)
  ↓
zKernel (depends on zlsp + zOS)
  ↓
zCloud (depends on zKernel)
```

**Approach:**
1. Build and perfect each component in order
2. Maintain tight coupling during development (monorepo)
3. Test integration continuously
4. Before publication: Extract to independent repos
5. Publish to PyPI as standalone packages

---

## Installation (Development)

### Clone Repository

```bash
git clone git@github.com:ZoloAi/ZoloMedia.git
cd ZoloMedia
```

### Install zlsp (Current Component)

```bash
cd zlsp
pip install -e .
zlsp-install-vim  # Automated Vim integration
```

Test:
```bash
vim zlsp/examples/basic.zolo
```

---

## Philosophy

**String-First:** Values are strings by default, with explicit type hints for conversion.

**Pure LSP:** Parser is the single source of truth, no duplicate grammar files.

**Terminal-First:** Vim/Neovim support is first-class, GUI editors follow.

**Composable:** Install only what you need, primitives build into compounds.

**OS-Agnostic:** Works consistently across macOS, Linux, and Windows.

---

## Status & Roadmap

### Phase 1: zlsp (COMPLETE)
- [x] Pure LSP implementation
- [x] Vim integration with vim-lsp
- [x] Semantic highlighting
- [x] Diagnostics, hover, completion
- [x] Automated installation
- [x] Production ready

### Phase 2: zOS (IN PROGRESS)
- [ ] Port from old Zolo repo
- [ ] Clean up dependencies
- [ ] Integrate with zlsp
- [ ] Test suite
- [ ] Documentation

### Phase 3: zKernel (NEXT)
- [ ] Port from old Zolo repo
- [ ] Integrate with zlsp + zOS
- [ ] Plugin system
- [ ] Test suite
- [ ] Documentation

### Phase 4: zCloud (PLANNED)
- [ ] Clean architecture
- [ ] Media management
- [ ] CDN integration
- [ ] Deployment

### Phase 5: Publication (FUTURE)
- [ ] Extract components to independent repos
- [ ] Publish to PyPI
- [ ] Update ZoloMedia to reference published packages
- [ ] Production deployment

---

## Contributing

We're in active development! Contributions welcome after Phase 5 (publication).

For now, this is a development monorepo for the core team.

---

## License

See individual component LICENSE files.

- `zlsp/` - MIT License

---

## Links

- **Website:** [zolo.media](https://zolo.media)
- **Documentation:** [docs.zolo.media](https://docs.zolo.media) *(coming soon)*
- **Discussions:** [GitHub Discussions](https://github.com/ZoloAi/ZoloMedia/discussions)
- **Issues:** [GitHub Issues](https://github.com/ZoloAi/ZoloMedia/issues)

---

**Zolo** - Modern, Composable, Beautiful
