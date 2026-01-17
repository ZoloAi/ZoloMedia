# zOS - System Foundation

**Layer 0** system utilities shared across the Zolo ecosystem.

## Purpose

`zOS` provides foundational utilities needed before framework initialization:

- **Logger**: Unified logging (bootstrap, console, formats)
- **Install**: Installation detection and removal
- **Formatting**: Terminal colors and output utilities
- **Errors**: Error handling (validation, exceptions, traceback)
- **CLI**: Command handlers for the `zolo` terminal command

## Architecture

```
zOS/  (Layer 0 - System Foundation)
├── logger/     → Bootstrap & console logging
├── install/    → Installation detection
├── formatting/ → Terminal colors & output
├── errors/     → Exception handling
└── cli/        → zolo command handlers
```

## Usage

```python
from zOS.logger import BootstrapLogger
from zOS.formatting import Colors
from zOS.errors import zKernelException

boot_logger = BootstrapLogger()
boot_logger.info("Starting application...")
```

## Shared By

- **zKernel**: Framework engine
- **zLSP**: Language server
- **zolo CLI**: Terminal commands

## Installation

```bash
pip install zOS
```

Or as part of the monorepo:

```bash
pip install -e ../zOS
```

## License

MIT License - See [LICENSE](../LICENSE) for details.
