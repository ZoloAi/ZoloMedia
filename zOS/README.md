# zOS - System Foundation

**Version:** 1.0.0  
**Layer 0** - OS primitives for the Zolo ecosystem

---

## About

`zOS` provides foundational OS-level utilities that form the base layer for all Zolo applications. It contains **no framework dependencies** and focuses purely on operating system primitives.

**What is Layer 0?**
- **Layer 0 (zOS):** OS primitives - logging, paths, machine detection, CLI
- **Layer 1 (zlsp):** Language server and parser
- **Layer 2 (zKernel):** Application framework engine

zOS is the foundation that both zlsp and zKernel depend on.

---

## Features

- **Unified Logging** - Bootstrap and console loggers with consistent formatting
- **Machine Detection** - Auto-detect system specs and generate `zConfig.machine.zolo`
- **Path Management** - Cross-platform paths using `platformdirs`
- **Terminal Formatting** - ANSI colors and output utilities
- **File Opening** - Primitive file and URL opening (without UI frameworks)
- **Installation Tools** - Package detection and removal utilities
- **CLI Commands** - `zolo` terminal command for system operations

---

## Installation

```bash
pip install zOS
```

Or as part of the ZoloMedia monorepo:

```bash
cd ZoloMedia/zOS
pip install -e .
```

---

## Architecture

```
zOS/  (Layer 0 - OS Primitives)
├── logger/         → Unified logging system
│   ├── bootstrap.py   - Bootstrap logger (early initialization)
│   ├── console.py     - Console logger (application logging)
│   ├── formats.py     - Log formatters
│   └── ecosystem.py   - Ecosystem-wide logging
│
├── machine/        → Machine detection & configuration
│   ├── config.py      - zConfig.machine.zolo generation
│   └── detectors/     - Hardware/software detection
│
├── utils/          → Utility functions
│   └── open/          - File and URL opening primitives
│
├── formatting/     → Terminal output
│   ├── colors.py      - ANSI color codes
│   ├── terminal.py    - Terminal utilities
│   └── zConfig.colors.zolo - Color definitions
│
├── install/        → Package management
│   ├── detection.py   - Installation type detection
│   └── removal.py     - Package removal utilities
│
├── errors/         → OS-level exceptions
│   └── exceptions.py  - zMachinePathError, UnsupportedOSError
│
├── cli/            → Command-line interface
│   ├── main.py        - zolo command entry point
│   ├── cli_commands.py - Command implementations
│   └── parser.py      - Argument parsing
│
└── paths.py        → Cross-platform path resolution
```

---

## Usage

### Logger

```python
from zOS.logger import BootstrapLogger, ConsoleLogger

# Early initialization logging
boot_logger = BootstrapLogger()
boot_logger.info("Starting application...")

# Application logging
console = ConsoleLogger(name="MyApp")
console.info("Application running")
console.error("Something went wrong")
```

### Colors & Formatting

```python
from zOS.formatting import Colors

print(f"{Colors.GREEN}Success!{Colors.RESET}")
print(f"{Colors.RED}Error!{Colors.RESET}")
```

### Machine Detection

```python
from zOS.machine import get_machine_info

machine = get_machine_info()
print(f"OS: {machine['os']}")
print(f"Browser: {machine['browser']}")
print(f"IDE: {machine['ide']}")
```

### File Opening

```python
from zOS.utils.open import open_file, open_url

# Open file in configured IDE
open_file("/path/to/file.py")

# Open URL in configured browser
open_url("https://example.com")

# Explicit application
open_file("/path/to/file.py", editor="cursor")
open_url("https://example.com", browser="chrome")
```

### Paths

```python
from zOS.paths import get_ecosystem_root, get_product_logs

# Get Zolo ecosystem root
root = get_ecosystem_root()  # ~/Library/Application Support/Zolo

# Get product-specific logs
logs = get_product_logs("MyApp")  # ~/Library/Application Support/Zolo/MyApp/logs
```

---

## CLI Commands

The `zolo` command provides system-level operations:

```bash
zolo                    # Show system info and open zConfig
zolo info               # Display package information
zolo open <path>        # Open file or URL
zolo edit               # Edit zConfig.machine.zolo
```

See [CLI_GUIDE.md](CLI_GUIDE.md) for comprehensive documentation.

---

## Dependencies

- **Python 3.9+**
- **platformdirs** - Cross-platform path resolution
- **PyYAML** - YAML parsing (for color configs)
- **zlsp** - Zolo language server (for parsing .zolo files)

---

## Used By

- **[zlsp](../zlsp)** - Zolo Language Server Protocol implementation
- **zKernel** - Zolo application framework (coming soon to monorepo)
- **User applications** - Any Python app needing Zolo ecosystem integration

---

## Framework vs OS Layer

**What's in zOS:**
- OS primitives (paths, logging, machine detection)
- No UI frameworks
- No zKernel dependencies
- Returns simple types (bool, dict, str)

**What's in zKernel:**
- Framework operations (zOpen with dialogs, hooks)
- UI components (Walker, zDisplay, zDialog)
- Framework exceptions (zKernelException and subclasses)
- Returns framework types ("zBack", "stop", Walker instances)

---

## Development

### Running in Editable Mode

```bash
cd ZoloMedia/zOS
pip install -e .
```

### Running Tests

```bash
pytest tests/
```

---

## Related Packages

- **[zlsp](../zlsp)** - Language server for .zolo files
- **zKernel** - Application framework (coming to monorepo)

---

## License

MIT License - See [LICENSE](LICENSE) for details.

---

**Maintained by:** Gal Nachshon  
**Repository:** [ZoloMedia Monorepo](https://github.com/ZoloAi/ZoloMedia)
