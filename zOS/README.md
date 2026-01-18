# zOS  

## **Declare once—run everywhere.**

**zOS** is not just a Command Line Interface, but a **Context Layer Interface**—a declarative cross-platform **Python framework** where context flows through layers to determine how your application manifests.

Write once, adapt to any context: **user role**, **deployment environment**, **device**, or **runtime mode** (**Terminal** or **Web**). **zOS** handles the heavy lifting, turning ideas into working tools faster.

---

## 🚀 Quick Start

```bash
# Install zOS
pip install git+https://github.com/ZoloAi/Zolo.git

# Verify installation
zolo --version

# Start interactive shell
zolo shell
```

**That's it!** You're ready to build declarative applications.

---

## 📚 New to **Zolo**?

Start with **[The zPhilosophy](Documentation/zPhilosophy.md)**.  
It introduces the core concepts of **zOS** and smoothly leads into the layer-by-layer guides with ready-made demos.

### Requirements

- **Python 3.8+** 
- **Git**

> Need help installing requirements on **Windows** or **macOS**?  
> See [**zInstall Guide**](Documentation/zInstall_GUIDE.md) for detailed instructions.

---

## 📦 Installation Options

Pick the installation that fits your needs:

| Package | Use Case | Install Command |
|---------|----------|-----------------|
| **Basic** | SQLite only (fastest) | `pip install git+https://github.com/ZoloAi/Zolo.git` |
| **CSV** | Basic + CSV/Pandas | `pip install "Zolo[csv] @ git+https://github.com/ZoloAi/Zolo.git"` |
| **PostgreSQL** | Basic + PostgreSQL | `pip install "Zolo[postgresql] @ git+https://github.com/ZoloAi/Zolo.git"` |
| **Full** | All backends | `pip install "Zolo[all] @ git+https://github.com/ZoloAi/Zolo.git"` |

### Alternative: UV (10-100x Faster)

For contributors or power users, [UV](https://github.com/astral-sh/uv) provides lightning-fast dependency management:

```bash
# One-off execution (no install!)
uvx Zolo shell

# Or install with UV
uv pip install git+https://github.com/ZoloAi/Zolo.git
```

> **More options**: Editable install, specific versions, troubleshooting  
> See [**zInstall Guide**](Documentation/zInstall_GUIDE.md) for complete instructions.


---

## 🏗️ Architecture

**zOS v1.5+** (Context Layer Interface) follows a **5-layer architecture** inspired by "*Linux From Scratch*"—each subsystem stands alone, tested independently, then composed into higher abstractions.

```
Layer 0: System Foundation (/zSys/)    - Pre-boot utilities (shared by CLI & framework)
Layer 1: Core Infrastructure           - Config, Display, Parsing, Loading
Layer 2: Business Logic                - Data, Auth, Functions, Dialogs
Layer 3: Abstraction & Integration     - Dispatch, Navigation, Wizards
Layer 4: Orchestration                 - CLI, Walker, Shell, Bifrost, Server
```

### Subsystems by Layer

| Subsystem | Purpose |
|-----------|---------|
| **Layer 0:**  | **Foundation** |
| **[zConfig](Documentation/zConfig_GUIDE.md)** | **Self-aware config layer** — **machine → environment → session** hierarchy with **secrets + logging** |
| **[zComm](Documentation/zComm_GUIDE.md)** | **Communication hub** — **HTTP client**, **service orchestration** (PostgreSQL, Redis), **network utilities** |
| | **Layer 1: Core Services** |
| **[zDisplay](Documentation/zDisplay_GUIDE.md)** | **Render everywhere** — **30+ events** (tables, forms, widgets) adapt to **Terminal or GUI** automatically |
| **[zAuth](Documentation/zAuth_GUIDE.md)** | **Three-tier auth system** — **bcrypt + SQLite + RBAC**, manage **platform + multi-app users** simultaneously |
| **[zDispatch](Documentation/zDispatch_GUIDE.md)** | **Universal command router** — **simple modifiers (^~*!)** shape behavior, routes to **7+ subsystems** seamlessly |
| **[zNavigation](Documentation/zNavigation_GUIDE.md)** | **Unified navigation** — **menus + breadcrumbs + state + inter-file links**, all **RBAC-aware** |
| **[zParser](Documentation/zParser_GUIDE.md)** | **Declarative paths & parsing** — **workspace-relative + user dirs + plugin discovery**, 21+ unified methods |
| **[zLoader](Documentation/zLoader_GUIDE.md)** | **Intelligent file loader** — **4-tier cache system** (System + Pinned + Schema + Plugin) with **mtime tracking** |
| **[zUtils](Documentation/zUtils_GUIDE.md)** | **Plugins engine** — **load Python modules**, auto-inject session, expose as methods, **unified cache** with auto-reload |
| | **Layer 2: Business Logic** |
| **[zFunc](Documentation/zFunc_GUIDE.md)** | **Dynamic Python executor** — **cross-language** (using zBifrost) + **internal Python**, auto-injection removes boilerplate |
| **[zDialog](Documentation/zDialog_GUIDE.md)** | **Declarative form engine** — **define once, auto-validate, render everywhere** (Terminal or GUI) |
| **[zOpen](Documentation/zOpen_GUIDE.md)** | **Universal opener** — **cross-OS routing** (URLs, files, zPaths) for **your tools** (session-aware browser + IDE preferences) |
| **[zWizard](Documentation/zWizard_GUIDE.md)** | **Multi-step orchestrator** — **sequential execution + zHat result passing**, enabling workflows **and** navigation |
| **[zData](Documentation/zData_GUIDE.md)** | **Database abstraction** — **backend-agnostic declerations** (SQLite ↔ PostgreSQL ↔ CSV), and **auto migration** |
| | **Layer 3: Orchestration** |
| **[zBifrost](Documentation/zBifrost_GUIDE.md)** | **WebSocket bridge** — **real-time bidirectional** communication (server + **JavaScript client**), enables **Terminal → Web GUI** transformation |
| **[zShell](Documentation/zShell_GUIDE.md)** | **Interactive command center** — **18+ commands + wizard canvas**, persistent history, **direct access** to all subsystems |
| **[zWalker](Documentation/zWalker_GUIDE.md)** | **Declarative UI orchestrator** — **menus + breadcrumb navigation**, coordinates **11 subsystems**, Terminal **and** GUI |
| **[zServer](Documentation/zServer_GUIDE.md)** | **HTTP file server** — **serves HTML/CSS/JS + declarative routing**, zero dependencies (built-in **http.server**), pairs with **zBifrost** |

## Uninstall & cleanup

Run this command in your terminal:

```bash
zolo uninstall
```
This launches an **interactive menu** where you can choose:

1. **Framework Only** (default) - Removes the package, keeps your data and optional dependencies
2. **Clean Uninstall** - Removes package AND all user data (configs, databases, cache)
3. **Dependencies Only** - Removes optional dependencies (pandas, psycopg2) but keeps zOS

Each option shows you exactly what will be removed and asks for confirmation before proceeding.

**[More details →](Documentation/zInstall_GUIDE.md#6-uninstall--cleanup)**


## License

MIT License with Ethical Use Clause

Copyright (c) 2024 Gal Nachshon

**Trademarks:** "Zolo" and "zOS" (Context Layer Interface) are trademarks of Gal Nachshon.

See [LICENSE](LICENSE) for details.

---

## 📖 Documentation

- **[zPhilosophy](Documentation/zPhilosophy.md)** - Core concepts and design principles
- **[Installation Guide](Documentation/zInstall_GUIDE.md)** - Detailed setup instructions (pip, UV, editable)
- **[AI Agent Guide](Documentation/AI_AGENT_GUIDE.md)** - Reference for AI coding assistants
- **[Subsystem Guides](Documentation/)** - Complete documentation for all 20+ subsystems

---

**[Next: The zPhilosophy →](Documentation/zPhilosophy.md)**
