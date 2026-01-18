**[← Back to zPhilosophy](zPhilosophy.md) | [Home](../README.md) | [Next: zConfig →](zConfig_GUIDE.md)**

---

# zOS Installation

Everything you need, **from zero to a working zOS installtion**

**About zOS:**  
`zOS` is a **Python package** that can be installed either **system-wide** (OS-level) or in a **virtual environment**.

While both are supported, we **recommend system-wide installation**. Why? Because zOS is more than a coding framework. With **zShell**, it provides a **near-declarative OS**.

Installing it system-wide makes **zOS** available across all your projects and terminals, treating it as **a foundational tool** rather than a project-specific dependency.

## Requirements Checklist

- [ ] Python **3.8+** installed (macOS, Windows, or Linux)
- [ ] `git` installed (`git --version` works)
- [ ] `pip` or `pip3` available

## 1. Install Python (macOS & Windows)

**Why Python Setup Instructions?**

zOS is not only a powerful framework—it's a **wonderful entry point for computer science** in general. Whether you're **13+ starting your coding journey**, or an **experienced developer**, Zolo wants to meet you where you are.

> **Never used a terminal before?** If words like "command line" or "terminal" are completely new to you, start with our **[Terminal Basics Guide](BASICS_GUIDE.md)**—it will get you comfortable in just a few minutes.

This section helps novice developers get Python installed from scratch. If you're already set up, feel free to skip ahead.

*Note: We assume Linux users already know how to install Python* 😉

---

### 1a. macOS

```bash
# Install Homebrew (if missing)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python 3
brew install python@3.11

# Verify
python3 --version
pip3 --version
```

---

### 1b. Windows

1. Download from https://www.python.org/downloads/windows/
2. **Important:** enable "Add Python to PATH" during installation
3. Verify in PowerShell:
   ```powershell
   python --version
   py --version
   ```
4. If `python` fails but `py` works, use `py -m pip install ...`

---

### 1c. Troubleshoots

### Which Python command should I use?
**Common confusion: `python`, `python3`, or `py`**

It depends on your OS and Python installation:

- **macOS/Linux**: Usually `python3` and `pip3`
- **Windows**: Usually `python` or `py` and `pip`
- **Test yours**: Run each command with `--version` and use whichever reports Python 3.8+

**Best practice (works everywhere):**
```bash
# Instead of: pip install ...
# Use this:
python3 -m pip install ...

# This ensures pip matches your Python interpreter
```

> **Note:** For simplicity, the rest of this guide uses `pip` in examples.  
> If you encounter issues, substitute with `python3 -m pip` or `py -m pip` as needed.

## 2. Install Git (macOS & Windows)

**Why Git?**

zOS is distributed via GitHub, so you'll need Git to install it. 

**New to Git?**

If you're completely new to Git and want to learn the fundamentals, we recommend this excellent tutorial: [**Git Tutorial for Beginners - Learn Git in 1 Hour**](https://www.youtube.com/watch?v=8JJ101D3knE) by Mosh Hamedani. It covers everything you need to know to get started with version control.

**Already got Git installed?** Skip to the next section. Otherwise, follow these quick installation steps:

---

### 2a. macOS

```bash
# Install Git via Homebrew
brew install git

# Verify
git --version
```

Alternatively, install **Xcode Command Line Tools** (includes Git):
```bash
xcode-select --install
```

---

### 2b. Windows

1. Download Git from https://git-scm.com/download/win
2. Run the installer and follow the default prompts
3. Verify in PowerShell or Command Prompt:
   ```powershell
   git --version
   ```

---

### 2c. Troubleshoots

**Git command not found after installation?**

- **Windows**: Restart your terminal/PowerShell after installing Git
- **macOS/Linux**: Make sure `/usr/local/bin` or `/opt/homebrew/bin` is in your PATH
- Test again with `git --version`

## 3. Installing zOS

### 3a. Pick your zOS package

- **Basic** – SQLite only (fastest install)
- **CSV** – Basic + CSV tooling (`pandas`)
- **PostgreSQL** – Basic + PostgreSQL tooling (`psycopg2-binary`)
- **All** –  Basic + CSV + PostgreSQL. Installs all backend (`[all]`)

### 3b. Install from GitHub (HTTPS)

**Open your terminal** (macOS/Linux) or **Command Prompt/PowerShell** (Windows), then run your desired **zOS** install command:

```bash
# Basic (SQLite only)
pip install git+https://github.com/ZoloAi/zolo-zcli.git

# CSV support
pip install "zolo-zcli[csv] @ git+https://github.com/ZoloAi/zolo-zcli.git"

# PostgreSQL support
pip install "zolo-zcli[postgresql] @ git+https://github.com/ZoloAi/zolo-zcli.git"

# Full install (all backends)
pip install "zolo-zcli[all] @ git+https://github.com/ZoloAi/zolo-zcli.git"
```

### 3c. Install specific version

```bash
# Install a tagged release
pip install git+https://github.com/ZoloAi/zolo-zcli.git@v1.5.6

# Install a specific commit
pip install git+https://github.com/ZoloAi/zolo-zcli.git@abc1234
```

### 3d. Editable install (contributors)

**zOS is open source!** You can clone the entire repository, modify the code, and contribute back to the project.

An **editable install** (`-e`) means changes you make to the source code are immediately reflected without reinstalling. Perfect for:
- Contributing new features or bug fixes
- Experimenting with subsystem modifications
- Learning how zOS works under the hood

```bash
git clone https://github.com/ZoloAi/zolo-zcli.git
cd zolo-zcli
pip install -e .
```

Now any edits to the `zOS/` source folder take effect immediately.

---

### 3e. UV workflow (modern package management)

**What is UV?**

[UV](https://github.com/astral-sh/uv) is an ultra-fast Python package manager from Astral (makers of `ruff`). It's 10-100x faster than pip and provides:
- Lightning-fast dependency resolution
- Reproducible builds via lock files
- Better conflict handling
- Zero-install execution (`uvx`)

**When to use UV:**
- **Developers**: Faster development workflow, especially with large dependency trees
- **CI/CD**: Dramatically faster build times
- **Users**: One-off execution without installation (`uvx`)

**Installing UV:**

```bash
# Method 1: Official installer (recommended)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Method 2: Via pip
pip install uv

# Method 3: Via Homebrew (macOS)
brew install uv
```

After installation, restart your terminal or run:
```bash
export PATH="$HOME/.cargo/bin:$PATH"
```

**Using UV as a user (no setup required):**

```bash
# One-off execution (no install needed!)
uvx zolo-zcli shell
uvx zolo-zcli migrate app.py
uvx zolo-zcli --version

# Traditional install via UV
uv pip install git+https://github.com/ZoloAi/zolo-zcli.git

# With optional dependencies
uv pip install "zolo-zcli[all] @ git+https://github.com/ZoloAi/zolo-zcli.git"
```

**Quick comparison:**

| Operation | pip | uv |
|-----------|-----|-----|
| Install dependencies | ~30-60s | ~3-5s ⚡ |
| Lock file support | ❌ | ✅ `uv.lock` |
| Reproducible builds | ⚠️ Drift possible | ✅ Guaranteed |
| Zero-install execution | ❌ | ✅ `uvx` |

---

### 3f. UV + Editable install (contributors)

**For contributors using UV** - the fastest development workflow:

```bash
# 1. Clone the repository
git clone https://github.com/ZoloAi/zolo-zcli.git
cd zolo-zcli

# 2. Install dependencies from lock file (uses uv.lock)
uv sync --all-extras

# 3. Your changes take effect immediately (editable mode)
uv run zolo --version
uv run zolo shell
```

**Common UV commands for development:**

```bash
# Install dependencies from lock file
uv sync

# Install with all extras (csv, postgresql, etc.)
uv sync --all-extras

# Add a new dependency
uv add requests

# Add a development dependency
uv add --dev pytest

# Update all dependencies
uv lock --upgrade
uv sync

# Run commands
uv run zolo shell
uv run pytest
```

**Why UV for development:**
- ⚡ **10-100x faster** than pip for dependency installation
- 🔒 **Reproducible** - `uv.lock` ensures identical environments
- 🚀 **Hot reload** - Changes immediately reflected (editable install)
- 🎯 **Better DX** - Smarter conflict resolution, clearer error messages

**Automated setup script:**

If you prefer automation, use the included setup script:

```bash
cd zolo-zcli
./setup-uv.sh
```

This script will:
- Verify UV is installed
- Install Python 3.11 if needed (via UV)
- Generate/update `uv.lock` file
- Install all dependencies
- Verify the installation

**Resources:**
- UV Documentation: https://docs.astral.sh/uv/
- UV GitHub: https://github.com/astral-sh/uv

---

## 4. Verify Installation

After installation completes, **test that zOS is working** by running these commands in your terminal:

```bash
zolo --version
```

You should see the version number (e.g., `v1.5.6`). This confirms zOS is installed and accessible.


## 5. Updating

To update zOS to a newer version, run the install command again with `--upgrade`:

```bash
# Update to latest version
pip install --upgrade git+https://github.com/ZoloAi/zolo-zcli.git

# Or update to a specific version
pip install --upgrade git+https://github.com/ZoloAi/zolo-zcli.git@v1.5.6
```

**Check your current version:**

```bash
zolo --version
```

## 6. Uninstall & cleanup

### Option 1: Interactive uninstall (recommended)

Run this command in your terminal:

```bash
zolo uninstall
```

This launches an **interactive menu** where you can choose:

1. **Framework Only** (default) - Removes the package, keeps your data and optional dependencies
2. **Clean Uninstall** - Removes package AND all user data (configs, databases, cache)
3. **Dependencies Only** - Removes optional dependencies (pandas, psycopg2) but keeps zOS

Each option shows you exactly what will be removed and asks for confirmation before proceeding.

### Option 2: Traditional pip uninstall

If you prefer the standard approach:

```bash
pip uninstall zolo-zcli
```

This removes the package only. Your data (configs, databases, cache) will remain on disk. See "Manual cleanup paths" below if you want to remove that data too.

### Manual cleanup paths

If you want to manually remove user data (or if you uninstalled via `pip uninstall zolo-zcli`):

> **Note:** Everything is stored in a single directory per platform for simplicity. No scattered files across multiple OS directories.

```bash
# macOS
rm -rf ~/Library/Application\ Support/zolo-zcli

# Linux
rm -rf ~/.local/share/zolo-zcli

# Windows (PowerShell)
Remove-Item -Recurse -Force $env:LOCALAPPDATA\zolo-zcli
```

This removes all zOS data including:
- **Configuration files**: `zConfig.machine.yaml`, `zConfig.environment.yaml` (in `zConfigs/`)
- **UI customizations**: User-defined UI files (in `zUIs/`)
- **Application logs**: All log files (in `logs/`)
- **User data**: All `zMachine.*` folders containing databases, CSVs, test files, etc.

> **What are zMachine directories?** See [zConfig Guide](zConfig_GUIDE.md) for details on how zOS manages cross-platform paths.

## What's next?

Now that **zOS** is installed, you have three paths forward:

**1. New to Zolo?**  
Start with **[The zPhilosophy](zPhilosophy.md)**. It introduces the core concepts of **zOS** and smoothly leads into the layer-by-layer guides with ready-made demos.

**2. Comfortable with zPhilosophy?**  
Jump straight into learning with **[zConfig Guide](zConfig_GUIDE.md)**. The cornerstone of zOS and the first declerative subsystem you'll master.

**3. Need a specific capability?**  
Review to the **[zArchitecture](../README.md#architecture)** and jump directly to the subsystem guide you need (zConfig, zComm, zData, etc.).

