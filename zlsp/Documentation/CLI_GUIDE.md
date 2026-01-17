# zlsp CLI Guide

Complete reference for the zlsp command-line interface.

---

## Overview

The `zlsp` CLI provides commands for verifying installation, running tests, starting the LSP server, and getting package information.

```bash
zlsp <command> [options]
```

**Available Commands:**
- `verify` - Verify installation health
- `test` - Run test suite
- `server` - Start LSP server
- `info` - Show package information

---

## Commands

### zlsp verify

Verify that zlsp is correctly installed and functioning.

```bash
zlsp verify              # Quick health check (5 checks)
zlsp verify --verbose    # Detailed check (includes example files)
```

**What it checks:**
1. Python version (3.8+ required)
2. Core dependencies (pygls, lsprotocol)
3. Parser functionality (loads, dumps)
4. LSP server availability
5. Semantic tokenizer
6. Editor integrations (optional)
7. Example files (verbose mode only)

**Exit codes:**
- `0` - All checks passed
- `1` - One or more checks failed

**Example output:**

```
╔═══════════════════════════════════════╗
║   zlsp Health Check                  ║
╚═══════════════════════════════════════╝

Checking Python version...
   ✓ Python 3.11.5 (OK)

Checking dependencies...
   ✓ pygls installed (OK)
   ✓ lsprotocol installed (OK)

Testing parser...
   ✓ Parser loads() working
   ✓ Parser dumps() working

Checking LSP server...
   ✓ LSP server module available

Checking semantic tokenizer...
   ✓ Semantic tokenizer working

Checking editor integrations...
   ✓ Installed for: Vim, Cursor

==========================================
Health Check Summary
==========================================
   Checks passed: 5/5

✅ All checks passed! zlsp is working correctly.
```

**When to use:**
- After initial installation
- When troubleshooting LSP issues
- After upgrading zlsp
- Before reporting bugs

---

### zlsp test

Run the test suite with various modes and options.

#### Basic Usage

```bash
zlsp test                # Run all tests (full suite)
zlsp test --quick        # Quick tests (unit + integration, skip slow)
zlsp test --unit         # Unit tests only
zlsp test --integration  # Integration tests only
zlsp test --e2e          # End-to-end tests only
```

#### Advanced Options

```bash
# Run with coverage report
zlsp test --coverage

# Run specific test by name
zlsp test -k test_parser_basic

# Stop on first failure (fail-fast)
zlsp test -x

# Verbose output
zlsp test -v

# Combine options
zlsp test --unit --coverage -v
zlsp test --quick -x
```

#### Test Modes Explained

**Full Suite** (default)
```bash
zlsp test
```
Runs all tests including unit, integration, and e2e tests. Use this for comprehensive testing before releases.

**Quick Mode**
```bash
zlsp test --quick
```
Runs unit and integration tests, skips slow e2e tests. Best for rapid development cycles.

**Unit Tests**
```bash
zlsp test --unit
```
Fast tests for individual functions and modules. No external dependencies.

**Integration Tests**
```bash
zlsp test --integration
```
Tests for component interactions, includes semantic token snapshot tests.

**End-to-End Tests**
```bash
zlsp test --e2e
```
Full workflow tests. Slowest but most comprehensive.

#### Coverage Reports

```bash
zlsp test --coverage
```

Generates two coverage reports:
- **Terminal:** Immediate summary with line-by-line missing coverage
- **HTML:** Detailed report in `htmlcov/` directory

View HTML report:
```bash
zlsp test --coverage
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

#### Examples

**Development workflow:**
```bash
# Quick iteration
zlsp test --quick -x

# Test specific feature
zlsp test -k completion

# Full test before commit
zlsp test --coverage
```

**CI/CD pipeline:**
```bash
# Fast feedback
zlsp test --quick

# Full validation
zlsp test --coverage
```

---

### zlsp server

Start the LSP server for editor integration.

```bash
zlsp server
```

**Note:** This command is typically called by your editor's LSP client, not manually. You usually don't need to run this yourself.

**When editors call this:**
- Vim/Neovim: via `vim-lsp` configuration
- VSCode/Cursor: via extension's LSP client

**Manual usage:**
Useful for debugging LSP communication:
```bash
zlsp server 2> lsp_stderr.log
```

---

### zlsp info

Display zlsp package information and available commands.

```bash
zlsp info
```

**Example output:**

```
╔═══════════════════════════════════════╗
║   Zolo Language Server Protocol      ║
╚═══════════════════════════════════════╝

Version: 1.1.0
Installation: /path/to/zlsp

Features:
  • String-first philosophy
  • Semantic token highlighting
  • Real-time diagnostics
  • Code completion
  • Hover information

Commands:
  zlsp verify            - Verify installation health
  zlsp test              - Run all tests (full suite)
  zlsp test --quick      - Run quick tests
  zlsp server            - Start LSP server
  zlsp info              - Show this information

More info: https://github.com/ZoloAi/ZoloMedia/tree/main/zlsp
```

---

## Common Workflows

### Initial Setup

```bash
# Install package
pip install zlsp

# Verify installation
zlsp verify

# Install editor integration
zlsp-install-vim     # or vscode, cursor
```

### Development Cycle

```bash
# Quick iteration
zlsp test --quick -x

# Test specific feature
zlsp test -k hover

# Full validation before commit
zlsp test --coverage
```

### Troubleshooting

```bash
# Check installation health
zlsp verify --verbose

# Get package information
zlsp info

# Test specific component
zlsp test -k parser -v
```

### CI/CD Pipeline

```bash
# Fast feedback (pull requests)
zlsp test --quick

# Full validation (main branch)
zlsp test --coverage

# Health check (deployment)
zlsp verify
```

---

## Troubleshooting

### "pytest not installed"

**Problem:** `zlsp test` fails with "pytest not installed"

**Solution:**
```bash
pip install pytest
# Or install with dev dependencies:
pip install zlsp[dev]
```

### "pygls not found"

**Problem:** `zlsp verify` reports missing dependencies

**Solution:**
```bash
pip install --upgrade zlsp
# Or manually:
pip install pygls lsprotocol
```

### "No editor integrations detected"

**Problem:** `zlsp verify` doesn't find your editor integration

**Solution:**
```bash
# Run the installer for your editor
zlsp-install-vim
zlsp-install-vscode
zlsp-install-cursor
```

### "Python version too old"

**Problem:** `zlsp verify` reports Python version < 3.8

**Solution:**
Upgrade Python to 3.8 or higher:
```bash
# Check your version
python --version

# Upgrade via system package manager or pyenv
```

### "Parser test failed"

**Problem:** Parser checks fail in `zlsp verify`

**Solution:**
1. Reinstall zlsp:
   ```bash
   pip uninstall zlsp
   pip install zlsp
   ```
2. Check for conflicting packages:
   ```bash
   pip list | grep zolo
   ```
3. If problem persists, run with verbose mode:
   ```bash
   zlsp verify --verbose
   ```

### "LSP server unavailable"

**Problem:** Server check fails in `zlsp verify`

**Solution:**
1. Check installation:
   ```bash
   which zolo-lsp
   ```
2. Reinstall if missing:
   ```bash
   pip install --force-reinstall zlsp
   ```

---

## Exit Codes

All commands use standard Unix exit codes:

| Code | Meaning |
|------|---------|
| `0` | Success |
| `1` | Failure or errors detected |

**Usage in scripts:**
```bash
# Exit on failure
zlsp verify || exit 1

# Continue on failure
zlsp test --quick || echo "Tests failed but continuing..."

# Conditional logic
if zlsp verify --verbose; then
    echo "Installation OK"
else
    echo "Installation has issues"
    exit 1
fi
```

---

## Environment Variables

zlsp respects standard Python environment variables:

**PYTHONPATH**
```bash
# Add custom modules
export PYTHONPATH="/path/to/modules:$PYTHONPATH"
zlsp test
```

**PYTEST_ADDOPTS**
```bash
# Custom pytest options
export PYTEST_ADDOPTS="-v --tb=short"
zlsp test
```

---

## Tips and Best Practices

### Fast Feedback Loop

Use `--quick` and `-x` for rapid iteration:
```bash
zlsp test --quick -x
```

### Targeted Testing

Test only what you changed:
```bash
# Test specific module
zlsp test -k parser

# Test specific file
zlsp test tests/unit/test_parser.py
```

### Coverage-Driven Development

Run with coverage to identify untested code:
```bash
zlsp test --coverage
open htmlcov/index.html
```

### Pre-Commit Checks

Add to your pre-commit script:
```bash
#!/bin/bash
zlsp verify || exit 1
zlsp test --quick || exit 1
```

### CI Integration

**GitHub Actions:**
```yaml
- name: Verify zlsp
  run: zlsp verify

- name: Run tests
  run: zlsp test --coverage
```

**GitLab CI:**
```yaml
test:
  script:
    - zlsp verify
    - zlsp test --coverage
```

---

## Related Documentation

- [INSTALLATION.md](./INSTALLATION.md) - Installation guide
- [ARCHITECTURE.md](./ARCHITECTURE.md) - Architecture overview
- [FILE_TYPES.md](./FILE_TYPES.md) - File type detection

---

**Last Updated:** January 2026
