# ZoloMedia

**The Zolo Ecosystem** - Modern, Composable Framework for Data-Driven Applications

🌐 **Website:** [zolo.media](https://zolo.media)  
📦 **Organization:** [github.com/ZoloAi](https://github.com/ZoloAi)

---

## About

ZoloMedia is the coordinating repository for the Zolo ecosystem. Each component is maintained as an independent repository and included here as a git submodule, following the "Linux From Scratch" philosophy of building primitives into complex compounds.

## Architecture

```
ZoloMedia/                  ← This repository (ecosystem coordinator)
├── zlsp/                   ← Language Server Protocol (submodule)
├── zKernel/                ← Core Framework (submodule)
├── zCloud/                 ← Cloud Platform (submodule)
├── zOS/                    ← Operating System Integration (submodule)
└── zTheme/                 ← UI Theme Framework (submodule)
```

## Components

### Core (Primitives)

- **[zlsp](https://github.com/ZoloAi/zlsp)** - Language Server Protocol for `.zolo` files
  - Semantic highlighting, diagnostics, hover, completion
  - Pure LSP architecture (TOML model)
  - Terminal-first (Vim/Neovim), editor-agnostic

### Framework

- **[zKernel](https://github.com/ZoloAi/zKernel)** - Core framework and configuration system
  - String-first philosophy
  - Declarative configuration
  - Event-driven architecture

### Platform

- **[zCloud](https://github.com/ZoloAi/zCloud)** - Cloud-native deployment platform
  - Media management
  - CDN integration
  - Analytics and quota management

### System

- **[zOS](https://github.com/ZoloAi/zOS)** - Operating system integration utilities
  - Cross-platform compatibility
  - System-level abstractions

### UI

- **[zTheme](https://github.com/ZoloAi/zTheme)** - Beautiful, modern UI theme framework
  - CSS framework
  - Component library
  - Responsive design

---

## Installation

### Clone with Submodules

```bash
# Clone the ecosystem
git clone --recurse-submodules git@github.com:ZoloAi/ZoloMedia.git

# Or if already cloned
git submodule update --init --recursive
```

### Install Individual Components

Each component can be installed independently:

```bash
# Just the language server
pip install zlsp

# Core framework
pip install zKernel

# Full stack
pip install zCloud
```

---

## Philosophy

**String-First:** Values are strings by default, with explicit type hints for conversion.

**Pure LSP:** Parser is the single source of truth, no duplicate grammar files.

**Terminal-First:** Vim/Neovim support is first-class, GUI editors follow.

**Composable:** Install only what you need, primitives build into compounds.

**OS-Agnostic:** Works consistently across macOS, Linux, and Windows.

---

## Status

🚧 **Active Development** - Components are being extracted from the monorepo and established as independent repositories.

Current milestone: Extracting `zlsp` as the first standalone primitive component.

---

## Contributing

Each component has its own contribution guidelines. Please see individual component repositories for details.

---

## License

See individual component repositories for license information.

---

## Links

- 🌐 **Website:** [zolo.media](https://zolo.media)
- 📚 **Documentation:** [docs.zolo.media](https://docs.zolo.media) *(coming soon)*
- 💬 **Discussions:** [GitHub Discussions](https://github.com/ZoloAi/ZoloMedia/discussions)
- 🐛 **Issues:** Component-specific issue trackers

---

**Zolo** - Modern, Composable, Beautiful
