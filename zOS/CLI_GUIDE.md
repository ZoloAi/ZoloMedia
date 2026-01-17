# zolo CLI Guide

Complete reference for the `zolo` command-line interface.

---

## Overview

The `zolo` CLI provides system-level operations for the Zolo ecosystem, including machine configuration, file opening, and package information.

```bash
zolo <command> [options]
```

**Available Commands:**
- `(none)` - Show version and installed products
- `machine` - Display or edit machine configuration
- `open` - Open files or URLs

---

## Commands

### zolo

Display version information and installed Zolo products.

```bash
zolo                    # Show all info
zolo --version          # Show version only
zolo --verbose          # Show detailed bootstrap logs
```

**Output:**

```
╔════════════════════════════════════════════════════════════════╗
║                  Zolo Ecosystem Information                    ║
╚════════════════════════════════════════════════════════════════╝

📦 Installed Packages:
   zOS:     1.0.0  (editable)
   zlsp:    1.1.0  (editable)
   zKernel: 2.5.0  (pip)

🖥  Machine Configuration:
   OS:      macOS 14.6.0
   Browser: Chrome
   IDE:     Cursor

📍 Paths:
   Ecosystem Root: ~/Library/Application Support/Zolo
   Machine Config: ~/Library/Application Support/Zolo/zConfig.machine.zolo

💡 Quick Actions:
   zolo machine         View full machine configuration
   zolo machine --edit  Edit user preferences
   zolo open <path>     Open file or URL
```

**When to use:**
- Check installed Zolo packages
- Verify installation status (editable vs pip)
- Quick overview of system configuration

---

### zolo machine

Display machine configuration from `zConfig.machine.zolo`.

```bash
zolo machine              # Show full configuration
zolo machine --system     # Show system-detected values (locked)
zolo machine --user       # Show user preferences (editable)
zolo machine --open       # Open config file in IDE
zolo machine --edit       # Interactive editor for preferences
```

#### Basic Usage

**Show full configuration:**

```bash
zolo machine
```

**Output:**

```
╔════════════════════════════════════════════════════════════════╗
║                    Machine Configuration                       ║
╚════════════════════════════════════════════════════════════════╝

🔒 System Configuration (Detected, Locked)
   OS:              macOS
   Version:         14.6.0
   Architecture:    arm64
   CPU Cores:       10
   Memory:          16 GB
   GPU:             Apple M1 Pro
   Hostname:        MacBook-Pro.local

✏️  User Preferences (Editable)
   Browser:         Chrome
   IDE:             Cursor
   Terminal:        iTerm
   Shell:           zsh
   Image Viewer:    Preview
   Video Player:    VLC
   Audio Player:    Music

📍 Paths
   Home:            /Users/username
   Desktop:         /Users/username/Desktop
   Documents:       /Users/username/Documents
   Downloads:       /Users/username/Downloads

⚙️  Launch Commands
   Browser:         open -a "Google Chrome" "{url}"
   IDE:             cursor "{file}"
   Terminal:        open -a "iTerm"
   
💡 To edit preferences: zolo machine --edit
```

#### Filter by Category

**Show system configuration only:**

```bash
zolo machine --system
```

Shows only the locked system-detected values (OS, CPU, memory, etc.).

**Show user preferences only:**

```bash
zolo machine --user
```

Shows only editable user preferences (browser, IDE, terminal, etc.).

#### Open in IDE

```bash
zolo machine --open
```

Opens `zConfig.machine.zolo` in your configured IDE (from the `ide` preference).

**When to use:**
- Quick access to edit configuration
- Bypasses `zolo machine --edit` interactive mode
- Direct file editing with full IDE features

#### Interactive Editor

```bash
zolo machine --edit
```

Launches an interactive terminal editor to modify user preferences.

**Interactive Flow:**

```
╔════════════════════════════════════════════════════════════════╗
║              Edit Machine User Preferences                     ║
╚════════════════════════════════════════════════════════════════╝

Current Preferences:
  browser:       Chrome
  ide:           Cursor
  terminal:      iTerm
  shell:         zsh

Select preference to edit:
  1. browser
  2. ide
  3. terminal
  4. shell
  5. Save and exit
  
Enter choice [1-5]:
```

**Supported preferences:**
- `browser` - Chrome, Firefox, Safari, Arc, Brave
- `ide` - Cursor, VSCode, Vim, Neovim, Sublime
- `terminal` - iTerm, Terminal, Alacritty, Kitty
- `shell` - zsh, bash, fish
- `image_viewer` - Preview, Feh, Eye of GNOME
- `video_player` - VLC, QuickTime, MPV
- `audio_player` - Music, Spotify, VLC

**When to use:**
- Quick preference changes without leaving terminal
- Guided editing with validation
- Alternative to manual file editing

---

### zolo open

Open files or URLs using configured applications.

```bash
zolo open <target>           # Open file or URL
zolo open <target> --verbose # Show detailed logs
```

#### Open Files

```bash
zolo open ~/Documents/file.py
zolo open /path/to/zConfig.machine.zolo
```

Opens the file in your configured IDE (from `zConfig.machine.zolo`).

**Supported file types:**
- Code files (`.py`, `.js`, `.ts`, `.zolo`, etc.)
- Text files (`.txt`, `.md`, `.json`, etc.)
- Configuration files (`.yaml`, `.toml`, `.ini`, etc.)

**IDE Detection:**
1. Reads `ide` preference from `zConfig.machine.zolo`
2. Falls back to `code` (VSCode) if not configured
3. Uses OS-specific launch commands

**Example:**

```bash
$ zolo open ~/Documents/script.py

Opening script.py in Cursor...

✓ Opened in Cursor
```

#### Open URLs

```bash
zolo open https://example.com
zolo open www.google.com
```

Opens the URL in your configured browser (from `zConfig.machine.zolo`).

**Supported URL formats:**
- `https://example.com`
- `http://example.com`
- `www.example.com` (auto-adds `https://`)

**Browser Detection:**
1. Reads `browser` preference from `zConfig.machine.zolo`
2. Falls back to `chrome` if not configured
3. Uses OS-specific browser launch commands

**Example:**

```bash
$ zolo open https://github.com

✓ Opened https://github.com in Chrome
```

#### Expand Paths

```bash
zolo open ~/Library/Application\ Support/Zolo/zConfig.machine.zolo
```

Automatically expands `~` to home directory and handles spaces.

#### Error Handling

**File not found:**

```bash
$ zolo open /nonexistent/file.txt

✗ File not found: /nonexistent/file.txt
```

**Failed to open:**

```bash
$ zolo open file.py

✗ Failed to open file.py
  Try opening manually: /path/to/file.py
```

**When to use:**
- Quick file opening from terminal
- Open URLs without typing browser name
- Respects user preferences (no need to specify IDE/browser)

---

## Global Options

Options that work with any command:

```bash
--verbose    Show detailed bootstrap logs
--dev        Enable development mode (for debugging)
--help       Show help message
--version    Show version information
```

**Examples:**

```bash
zolo --verbose machine
zolo --dev open file.py
zolo --help
```

---

## Configuration File

### Location

The machine configuration is stored at:

```
~/Library/Application Support/Zolo/zConfig.machine.zolo    # macOS
~/.local/share/Zolo/zConfig.machine.zolo                   # Linux
C:\Users\<user>\AppData\Local\Zolo\zConfig.machine.zolo   # Windows
```

### Structure

```zolo
# zConfig.machine.zolo
# Auto-generated machine configuration

zMachine:
	machine_identity:
		hostname: MacBook-Pro.local
		os: macOS
		version: 14.6.0
		architecture: arm64
	
	user_preferences:
		browser: Chrome       #> editable <#
		ide: Cursor           #> editable <#
		terminal: iTerm       #> editable <#
		shell: zsh            #> editable <#
	
	launch_commands:
		browser: open -a "Google Chrome" "{url}"
		ide: cursor "{file}"
		terminal: open -a "iTerm"
```

**Key sections:**
- `machine_identity` - 🔒 Locked (auto-detected)
- `user_preferences` - ✏️ Editable (user choices)
- `launch_commands` - 🔒 Locked (OS-specific commands)

---

## Common Workflows

### Check Installation

```bash
# Quick check
zolo

# Detailed check with logs
zolo --verbose
```

### View Configuration

```bash
# Full config
zolo machine

# Just user preferences
zolo machine --user

# Just system info
zolo machine --system
```

### Edit Preferences

```bash
# Interactive editor (guided)
zolo machine --edit

# Open in IDE (full control)
zolo machine --open
```

### Open Files/URLs

```bash
# Open file in IDE
zolo open ~/Documents/script.py

# Open URL in browser
zolo open https://github.com

# Open config file
zolo open ~/Library/Application\ Support/Zolo/zConfig.machine.zolo
```

---

## Troubleshooting

### Config file not found

**Problem:**

```
⚠️  Configuration file not found: zConfig.machine.zolo
```

**Solution:**

Run `zolo` once to auto-generate the configuration:

```bash
zolo
```

### IDE not opening

**Problem:**

```
✗ Failed to open file.py in Cursor
```

**Solution:**

1. Check IDE is installed:
   ```bash
   which cursor
   ```

2. Verify IDE in config:
   ```bash
   zolo machine --user
   ```

3. Update IDE preference:
   ```bash
   zolo machine --edit
   ```

### Browser not opening URL

**Problem:**

```
✗ Failed to open https://example.com
```

**Solution:**

1. Check browser in config:
   ```bash
   zolo machine --user
   ```

2. Update browser preference:
   ```bash
   zolo machine --edit
   ```

3. Test with explicit browser:
   - Edit `zConfig.machine.zolo` manually
   - Set `browser: Safari` (or another installed browser)

---

## Advanced Usage

### Development Mode

Enable verbose logging for debugging:

```bash
zolo --verbose --dev machine
```

Shows:
- Bootstrap logger output
- File paths being accessed
- Config parsing details
- Command execution logs

### Scripting

Use `zolo open` in scripts:

```bash
#!/bin/bash
# Open project files quickly

zolo open ~/Projects/app/main.py
zolo open ~/Projects/app/README.md
zolo open https://docs.example.com
```

### CI/CD Integration

Check Zolo installation in CI pipelines:

```yaml
# .github/workflows/test.yml
- name: Verify Zolo installation
  run: |
    zolo --version
    zolo machine --system
```

---

## Exit Codes

- `0` - Success
- `1` - Error (file not found, failed to open, etc.)

---

## Related Documentation

- [README.md](README.md) - Package overview and API usage
- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture
- [zConfig File Format](../zlsp/Documentation/FILE_TYPES.md) - .zolo file syntax

---

**Version:** 1.0.0  
**Last Updated:** 2024

