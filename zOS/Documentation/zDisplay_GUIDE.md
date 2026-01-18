<div style="display: flex; flex-direction: column; align-items: stretch; margin-bottom: 1rem; font-weight: 500;">
  <div style="display:flex; justify-content:space-between; align-items:center;">
    <span><a style="color:#FFFBCC;" href="zComm_GUIDE.md">← Back to zComm</a></span>
    <span><a style="color:#FFFBCC;" href="../README.md">Home</a></span>
    <span><a style="color:#FFFBCC;" href="zAuth_GUIDE.md">Next: zAuth Guide →</a></span>
  </div>
  <div style="display: flex; justify-content: center; align-items: center; margin-top: 0.85rem;">
    <h1 style="margin: 0; font-size: 2.15rem; font-weight: 700;">
      <span style="color:#FFFBCC;">zDisplay Guide</span>
    </h1>
  </div>
</div>

> **<span style="color:#F8961F">Professional terminal output</span>** — progress bars, tables, menus, and more through one clean API.

**<span style="color:#8FBE6D">Every application needs output.</span>** Tables, progress bars, menus, user input—you either write mode-specific code (terminal vs web) or duplicate everything.

<span style="color:#8FBE6D">**zDisplay**</span> is zOS's **<span style="color:#F8961F">Layer 1 rendering engine</span>**, initialized after zConfig/zComm to provide **<span style="color:#8FBE6D">30+ display events</span>** for professional Terminal output. Get **<span style="color:#8FBE6D">progress bars</span>**, **<span style="color:#F8961F">interactive tables</span>**, and **<span style="color:#F8961F">structured data display</span>** through one facade.<br>**No curses library, no ANSI escape sequences, no manual formatting.**

> **Need GUI rendering?** All these display methods also work in Browser mode. See [zBifrost Guide](zBifrost_GUIDE.md) for real-time Terminal ↔ Web rendering.

## Best Practices & Import Patterns

### <span style="color:#8FBE6D">Centralized Imports</span>

zOS provides a **unified import namespace** for all standard library modules and typing helpers. Instead of importing directly from `typing`, `asyncio`, `json`, etc., use the centralized pattern:

**✅ Recommended (Centralized):**
```python
from zOS import zOS, Any, Dict, Optional, asyncio, json, uuid
```

**❌ Avoid (Direct Imports):**
```python
import asyncio
import json
import uuid
from typing import Any, Dict, Optional
```

**Why Centralized Imports?**
- **Single source of truth** - All imports defined in `zOS/__init__.py`
- **Consistency** - All modules use the same pattern
- **Future-proof** - Easy to add polyfills or compatibility layers
- **Type safety** - Centralized typing helpers ensure consistency
- **Cleaner code** - One import line instead of multiple

**Available Centralized Imports:**
- **Standard Library**: `asyncio`, `json`, `logging`, `os`, `re`, `sys`, `traceback`, `uuid`, `datetime`, `Path`, and more
- **Typing Helpers**: `Any`, `Callable`, `Dict`, `List`, `Optional`, `Tuple`, `Union`
- **Third-Party**: `yaml`, `requests`, `websockets`
- **Utils**: `Colors`, `safe_json_dumps`

**Example:**
```python
from zOS import zOS, Dict, List, json

z = zOS()

# Use centralized imports throughout your code
data: Dict[str, List[str]] = {"users": ["alice", "bob"]}
json_str = json.dumps(data)
z.display.text(f"Data: {json_str}", color="CYAN")
```

> **Note:** This pattern is used internally by all zDisplay modules for consistency and maintainability.

---

## zDisplay Tutorials

### <span style="color:#8FBE6D">Level 1A: raw() - No Newline</span>

```python
from zOS import zOS

z = zOS({"logger": "PROD"})

# All on one line - raw() never adds newlines
z.display.raw("First")
z.display.raw(" + ")
z.display.raw("Second")
z.display.raw(" + ")
z.display.raw("Third")
z.display.raw("\n")  # You control when to break

# Use case: Building status messages
z.display.raw("Status: ")
z.display.raw("✓ Connected")
z.display.raw("\n")
```

The most primitive display operation—**write text with no automatic newline**. You get complete control over when lines break. Perfect for building output piece by piece: progress indicators, inline status updates, or combining text fragments. `raw()` is the foundation—all other display methods build on this.

> **Try it:** [`output/Level_1_Primitives/write_raw.py`](../Demos/Layer_1/zDisplay_Demo/output/Level_1_Primitives/write_raw.py)

### <span style="color:#8FBE6D">Level 1B: line() - Automatic Newline</span>

```python
from zOS import zOS

z = zOS({"logger": "PROD"})

# Each call becomes its own line
z.display.line("1) Each call becomes its own line")
z.display.line("2) No need to append \\n manually")
z.display.line("3) Perfect for log-style output")
```

Single-line output with automatic newline handling. No need to manually add `\n`—`line()` does it for you. Perfect for log-style output, simple messages, or any content where each call should start on a new line. Cleaner than `raw()` when you want the newline every time.

> **Try it:** [`output/Level_1_Primitives/write_line.py`](../Demos/Layer_1/zDisplay_Demo/output/Level_1_Primitives/write_line.py)

### <span style="color:#8FBE6D">Level 1C: block() - Multi-Line Output</span>

```python
from zOS import zOS

z = zOS({"logger": "PROD"})

# Multi-line string, formatting preserved
block = """Deployment Summary
- Host: localhost
- Mode: Terminal
- Status: Ready to render"""

z.display.block(block)
```

Send multiple lines at once while preserving your formatting. `block()` handles the trailing newline automatically. Great for banners, status summaries, or any preformatted text. Your line breaks stay intact, terminal spacing stays clean.

> **Try it:** [`output/Level_1_Primitives/write_block.py`](../Demos/Layer_1/zDisplay_Demo/output/Level_1_Primitives/write_block.py)

### <span style="color:#8FBE6D">Level 1D: read_string() - Collect Text Input</span>

```python
from zOS import zOS

z = zOS({"logger": "PROD"})

# Simple prompt
name = z.display.read_string("What's your name? ")
z.display.line(f"Hello, {name}!")

# Configuration input with defaults
host = z.display.read_string("Database host [localhost]: ")
if not host:
    host = "localhost"
port = z.display.read_string("Database port [5432]: ")
if not port:
    port = "5432"

z.display.line(f"✓ Configuration: {host}:{port}")
```

The most basic input primitive—**collect user text input**. Prompts the user, waits for their response, and returns what they typed (without the newline). Perfect for interactive CLIs, configuration wizards, or any situation where you need to ask the user a question.

> **Try it:** [`input/Level_1_Primitives/read_string.py`](../Demos/Layer_1/zDisplay_Demo/input/Level_1_Primitives/read_string.py)

### <span style="color:#8FBE6D">Level 1E: read_password() - Masked Input</span>

```python
from zOS import zOS

z = zOS({"logger": "PROD"})

# Secure password input
password = z.display.read_password("Password: ")
z.display.line(f"✓ Password captured ({len(password)} characters)")

# Login flow
username = z.display.read_string("Username: ")
password = z.display.read_password("Password: ")

if username and password:
    z.display.line(f"✓ Credentials collected for: {username}")
```

Secure input collection with **masked typing**—just like `read_string()`, but the user's input is hidden from view. Essential for passwords, API keys, tokens, or any sensitive data. The terminal shows nothing (or asterisks) while the user types, preventing shoulder-surfing and accidental exposure.

> **Try it:** [`input/Level_1_Primitives/read_password.py`](../Demos/Layer_1/zDisplay_Demo/input/Level_1_Primitives/read_password.py)

---

### <span style="color:#8FBE6D">Level 2A: header() - Formatted Headers</span>

```python
from zOS import zOS

z = zOS({"logger": "PROD"})

# Style: full (═══)
z.display.header("System Initialization", color="CYAN", style="full")

# Style: single (───)
z.display.header("Loading Configuration", color="GREEN", style="single")

# Style: wave (~~~)
z.display.header("Processing Data", color="YELLOW", style="wave")

# With indentation
z.display.header("Main Section", color="MAGENTA", indent=0, style="full")
z.display.header("Subsection", color="BLUE", indent=1, style="single")
```

Create **visual structure** with formatted section headers. Three styles: `full` (═), `single` (─), `wave` (~). Multiple colors (CYAN, GREEN, YELLOW, MAGENTA, BLUE, RED). Use indentation to show hierarchy. Headers organize your output into clear sections.

> **Try it:** [`output/Level_2_Foundation/header.py`](../Demos/Layer_1/zDisplay_Demo/output/Level_2_Foundation/header.py)

### <span style="color:#8FBE6D">Level 2B: text() - Display with Control</span>

```python
from zOS import zOS

z = zOS({"logger": "PROD"})

# Simple text output
z.display.text("Configuration loaded successfully")

# With indentation (each level = 2 spaces)
z.display.text("Configuration:", indent=0)
z.display.text("Database: PostgreSQL", indent=1)
z.display.text("Host: localhost", indent=2)

# With pause for user acknowledgment
z.display.text("⚠️  About to delete data...", pause=True)
z.display.text("Data deleted", indent=1)
```

Display text with **indent and pause control**. Indent creates hierarchy (0-3+ levels, 2 spaces each). Pause waits for user to press Enter before continuing. Perfect for nested content, step-by-step workflows, or confirmations. Builds on `line()` by adding control features.

> **Try it:** [`output/Level_2_Foundation/text.py`](../Demos/Layer_1/zDisplay_Demo/output/Level_2_Foundation/text.py)

### <span style="color:#8FBE6D">Level 2C: signals() - Color-Coded Feedback</span>

```python
from zOS import zOS

z = zOS({"logger": "PROD"})

# Success (green ✓)
z.display.success("Operation completed successfully")

# Error (red ✗)
z.display.error("Connection failed")

# Warning (yellow ⚠)
z.display.warning("Deprecated feature in use")

# Info (cyan ℹ)
z.display.info("Processing 10 records...")

# With indentation
z.display.success("Database connected", indent=0)
z.display.info("Host: localhost", indent=1)
z.display.info("Port: 5432", indent=1)

# zMarker - visual separator for workflow stages
z.display.zMarker("Checkpoint 1")
z.display.info("Stage 1 complete")
z.display.zMarker("Checkpoint 2", color="CYAN")
```

**Semantic feedback with automatic colors.** Four core signals (success=green, error=red, warning=yellow, info=cyan) plus `zMarker()` for workflow separators. Colors and icons apply automatically based on message type. Perfect for operation feedback, validation results, and user notifications. All signals support indentation for hierarchical feedback.

> **Try it:** [`output/Level_2_Foundation/signals.py`](../Demos/Layer_1/zDisplay_Demo/output/Level_2_Foundation/signals.py)

### <span style="color:#8FBE6D">Level 2D: system() - System Display Events</span>

> **💡 Note:** These system display events build on concepts from **[zConfig Guide](zConfig_GUIDE.md)**. If you've worked through the early zConfig demos, you've already seen `z.session`, `z.config.get_machine()`, and `z.config.get_environment()`. This tutorial shows how to **display** that configuration data professionally. For more on reading and managing config values, see the [zConfig Guide](zConfig_GUIDE.md).

```python
from zOS import zOS

z = zOS({"logger": "PROD"})

# System announcements with zDeclare()
z.display.zDeclare("System Initialization")
z.display.zDeclare("Loading Configuration", indent=1)
z.display.zDeclare("Services Ready", color="GREEN")

# Display session state
z.display.zSession(z.session)

# Display configuration info
config_data = {
    "machine": {
        "os": z.config.get_machine("os"),
        "hostname": z.config.get_machine("hostname")
    },
    "environment": {
        "deployment": "Debug",
        "mode": "Terminal"
    }
}
z.display.zConfig(config_data)

# Real-world startup sequence
z.display.zDeclare("Application Starting", color="CYAN")
z.display.info("Loading environment", indent=1)
z.display.success("Configuration complete", indent=1)
z.display.zDeclare("Application Ready", color="GREEN")
```

**Professional system status reporting.** Three specialized methods: `zDeclare()` for system announcements with colors (GREEN/YELLOW/RED/BLUE), `zSession()` for displaying current session state, and `zConfig()` for machine/environment configuration. Perfect for startup sequences, system monitoring, and professional status displays. All support indentation for hierarchical output.

> **Try it:** [`output/Level_2_Foundation/system.py`](../Demos/Layer_1/zDisplay_Demo/output/Level_2_Foundation/system.py)

### <span style="color:#8FBE6D">Level 2E: button() - Action Confirmation</span>

```python
from zOS import zOS

z = zOS({"logger": "PROD"})

# Safe action confirmation
if z.display.button("Save Profile", color="success"):
    z.display.success("✅ Profile saved!")
else:
    z.display.info("Profile not saved")

# Dangerous action warning
if z.display.button("Delete Account", color="danger"):
    z.display.warning("⚠️ Account marked for deletion!")
else:
    z.display.info("Account deletion cancelled")

# Multi-step workflow
if z.display.button("Start Backup", color="info"):
    z.display.info("Preparing backup...", indent=1)
    if z.display.button("Confirm Backup", color="success"):
        z.display.success("✓ Backup completed!", indent=1)
```

**Action confirmation with yes/no prompts.** Requires explicit user confirmation (y/n) to prevent accidental actions. Color-coded by action type: `success` (green), `danger` (red), `warning` (yellow), `info` (blue). Returns `True` (confirmed) or `False` (cancelled). Perfect for destructive operations, important decisions, or multi-step workflows requiring validation.

> **Try it:** [`input/Level_2_Foundation/button.py`](../Demos/Layer_1/zDisplay_Demo/input/Level_2_Foundation/button.py)

### <span style="color:#8FBE6D">Level 2F: selection() - Choose from List</span>

```python
from zOS import zOS

z = zOS({"logger": "PROD"})

# Single selection
role = z.display.selection(
    "Select your role:",
    ["Developer", "Designer", "Manager"]
)
z.display.success(f"Selected: {role}")

# Multiple selections
skills = z.display.selection(
    "Select your skills:",
    ["Python", "JavaScript", "React", "Django"],
    multi=True
)
z.display.success(f"Selected: {', '.join(skills)}")

# Selection with default
theme = z.display.selection(
    "Choose theme:",
    ["Light", "Dark", "Auto"],
    default="Dark"
)
z.display.success(f"Selected: {theme}")
```

**User choice from numbered list.** Displays options with numbers (1, 2, 3...), user types number(s) to select. Single selection returns one item, multi-selection (`multi=True`) returns a list. Optional `default` parameter for pre-selected values. Perfect for menus, configuration wizards, or any scenario where users need to choose from predefined options.

> **Try it:** [`input/Level_2_Foundation/selection.py`](../Demos/Layer_1/zDisplay_Demo/input/Level_2_Foundation/selection.py)

---

### <span style="color:#8FBE6D">Level 3: Data - Structured Data Display</span>

```python
from zOS import zOS

z = zOS({"logger": "PROD"})

# List - Bullet/Number/Letter styles
z.display.list(["Fast", "Simple", "Multi-mode"], style="bullet")
z.display.list(["Initialize", "Configure", "Deploy"], style="number")
z.display.list(["Option A", "Option B", "Option C"], style="letter")

# Outline - Hierarchical multi-level (1→a→i→•)
z.display.outline([
    {
        "content": "Backend Architecture",
        "children": [
            {
                "content": "Python Runtime",
                "children": ["zOS initialization", "Event handling"]
            },
            "Data Processing Layer"
        ]
    },
    {
        "content": "Frontend Architecture",
        "children": ["Rendering Engine", "User Interaction"]
    }
])

# JSON Data - With syntax coloring
config = {"version": "1.5.5", "mode": "Terminal", "ready": True}
z.display.json_data(config, color=True)
```

**Professional structured data display.** Three display types: `list()` for bullet/number/letter lists, `outline()` for hierarchical multi-level documents (1→a→i→• pattern), and `json_data()` for pretty-printed JSON with optional syntax coloring. Perfect for options, menu items, config display, and nested structures.

> **Try it:** [`output/Level_3_Data/data.py`](../Demos/Layer_1/zDisplay_Demo/output/Level_3_Data/data.py)

### <span style="color:#8FBE6D">Level 3: Data - Tables (zTable)</span>

```python
from zOS import zOS

z = zOS({"logger": "PROD"})

users = [
    {"ID": 1, "Name": "Alice", "Email": "alice@example.com"},
    {"ID": 2, "Name": "Bob", "Email": "bob@example.com"},
    {"ID": 3, "Name": "Charlie", "Email": "charlie@example.com"},
    {"ID": 4, "Name": "Diana", "Email": "diana@example.com"},
    {"ID": 5, "Name": "Eve", "Email": "eve@example.com"},
]

# Type 1: Basic - No Pagination (all rows)
z.display.zTable(
    title="All Users",
    columns=["ID", "Name", "Email"],
    rows=users
)

# Type 2: Simple Truncation (limit only → "... N more rows" footer)
z.display.zTable(
    title="Users (Limited to 3)",
    columns=["ID", "Name", "Email"],
    rows=users,
    limit=3  # Shows first 3 with footer
)

# Type 3: Interactive Navigation (limit + interactive=True)
z.display.zTable(
    title="Users - Interactive",
    columns=["ID", "Name", "Email"],
    rows=users,
    limit=2,
    offset=0,
    interactive=True  # Keyboard navigation: [n]ext, [p]revious, [f]irst, [l]ast, [#] jump, [q]uit
)
```

**Advanced table display with THREE pagination modes.** Type 1: Basic (no pagination, shows all rows). Type 2: Simple truncation (limit only, shows "... N more rows" footer). Type 3: Interactive navigation (limit + interactive=True, full keyboard controls). Perfect for database query results from `zData`. Automatic column alignment and mixed data type support (strings, numbers, booleans).

> **Try it:** [`output/Level_3_Data/table.py`](../Demos/Layer_1/zDisplay_Demo/output/Level_3_Data/table.py)

---

## Level 4: Progress Tracking

> **💡 Consolidated Demos:** Level 4 uses a streamlined demo structure where related methods are combined into single files. Each demo shows both automatic and manual modes for the same visual output, helping you choose the right control level for your use case.

### <span style="color:#8FBE6D">Level 4A: progress_bar() & progress_iterator() - Deterministic Progress</span>

```python
import time
from zOS import zOS

z = zOS({"logger": "PROD"})

# Manual mode: Full control over progress
total = 50
start_time = time.time()

for i in range(total + 1):
    z.display.progress_bar(
        current=i,
        total=total,
        label="Processing files",
        show_percentage=True,
        show_eta=True,
        start_time=start_time,
        color="GREEN"
    )
    time.sleep(0.05)  # Simulate work

# Automatic mode: Zero manual updates
files = [f"file_{i}.txt" for i in range(1, 26)]

for filename in z.display.progress_iterator(files, "Processing files"):
    time.sleep(0.08)  # progress_iterator() manages current/total/start_time
```

**Visual progress tracking with TWO modes.** Manual mode (`progress_bar`) gives full control over current/total/start_time. Automatic mode (`progress_iterator`) wraps iterables for zero-config progress tracking. Both display identical visual output with percentage completion and ETA. Choose based on your use case: manual for flexibility, automatic for simplicity.

> **💡 Cross-Terminal Support:** Progress bars automatically adapt to your terminal's capabilities. Modern terminals (iTerm2, Alacritty, Kitty, Cursor) use smooth in-place updates with `\r`. macOS Terminal.app uses cursor-up rendering for the same visual effect. Same code, optimized rendering everywhere.

> **Try it:** [`output/Level_4_Progress/bar.py`](../Demos/Layer_1/zDisplay_Demo/output/Level_4_Progress/bar.py)

### <span style="color:#8FBE6D">Level 4B: spinner() & indeterminate_progress() - Unknown Duration</span>

```python
import time
from zOS import zOS

z = zOS({"logger": "PROD"})

# Automatic mode: Context manager with auto-animation
with z.display.spinner("Loading data", style="dots"):
    time.sleep(2)  # Animates automatically in background

with z.display.spinner("Processing", style="arc"):
    time.sleep(2)

# Manual mode: Fine-grained control over updates
update_progress = z.display.indeterminate_progress("Processing data")
for i in range(30):
    update_progress()  # You control when frames update
    time.sleep(0.1)
z.display.raw("\n")  # Add newline when done
```

**Animated loading indicator with TWO control modes.** Automatic mode (`spinner`) uses context manager for background animation and auto-cleanup. Manual mode (`indeterminate_progress`) returns an update function you call in your loop for fine-grained control. Both produce identical visual output (animated spinner frames). Perfect for API calls, database queries, file I/O, or any operation where duration is unpredictable.

> **Try it:** [`output/Level_4_Progress/spinner.py`](../Demos/Layer_1/zDisplay_Demo/output/Level_4_Progress/spinner.py)

### <span style="color:#8FBE6D">Level 4C: swiper() - Interactive Slideshow</span>

```python
from zOS import zOS

z = zOS({"logger": "PROD"})

# Simple auto-advancing slideshow
intro_slides = [
    "Welcome to zOS!",
    "zOS is a declarative CLI framework",
    "Professional terminal UI with one API",
    "Let's explore the features..."
]

z.display.zEvents.TimeBased.swiper(
    intro_slides, 
    "Introduction", 
    auto_advance=True, 
    delay=3
)

# Manual navigation tutorial
tutorial_slides = [
    "Step 1: Initialize zOS\n\n  from zOS import zOS\n  z = zOS()",
    "Step 2: Display Progress\n\n  z.display.progress_bar(50, 100)",
    "Step 3: Show Spinners\n\n  with z.display.spinner('Loading'):\n      time.sleep(2)"
]

z.display.zEvents.TimeBased.swiper(
    tutorial_slides, 
    "Tutorial", 
    auto_advance=False  # User navigates with arrow keys
)
```

**Interactive content carousel with beautiful box-drawn UI.** Auto-advancing slides with configurable delay, or manual navigation with arrow keys (◀ ▶), number keys (1-N jump to slide), pause/resume ('p' key), and quit ('q' key). Multi-line content support with proper formatting. Perfect for tutorials, onboarding flows, feature showcases, and presentations.

> **💡 Note:** Swiper is accessed via `z.display.zEvents.TimeBased.swiper()` - a powerful interactive component for guided experiences.

> **Try it:** [`output/Level_4_Progress/swiper.py`](../Demos/Layer_1/zDisplay_Demo/output/Level_4_Progress/swiper.py)

---

## Summary

You've learned zDisplay's **<span style="color:#8FBE6D">complete rendering capabilities</span>**:

✅ **Primitives (Layer 1)**
- `raw()` - Write without newline (full control)
- `line()` - Write with automatic newline
- `block()` - Multi-line output with preserved formatting
- `read_string()` - Collect text input from user
- `read_password()` - Masked password input

✅ **Foundation (Layer 2)**
- `header()` - Formatted section headers (═/─/~) with colors
- `text()` - Display text with indentation control and pause support
- `success()` - Green ✓ confirmations
- `error()` - Red ✗ failures
- `warning()` - Yellow ⚠ cautions
- `info()` - Cyan ℹ information
- `zMarker()` - Magenta workflow separators
- `zDeclare()` - System announcements with colors
- `zSession()` - Session state display
- `zConfig()` - Configuration display
- `button()` - Action confirmation with yes/no prompts
- `selection()` - Choose from numbered list (single or multi-select)

✅ **Data (Layer 3)**
- `list()` - Bullet/number/letter lists
- `outline()` - Hierarchical multi-level (1→a→i→•)
- `json_data()` - Pretty-printed JSON with syntax coloring
- `zTable()` - Tables with THREE pagination modes:
  - Type 1: Basic (no pagination, all rows)
  - Type 2: Simple truncation (limit only, "... N more rows" footer)
  - Type 3: Interactive navigation (limit + interactive=True, keyboard controls)

✅ **Progress Tracking (Layer 4)**
- `progress_bar()` + `progress_iterator()` - Deterministic progress (manual + automatic modes)
- `spinner()` + `indeterminate_progress()` - Indeterminate loading (automatic + manual modes)
- `swiper()` - Interactive slideshow carousel with navigation

**<span style="color:#F8961F">16 micro-step demos</span>** organized by function:

**Output Demos** (`output/` folder):
- Level 1: Primitives (3) - `raw`, `line`, `block`
- Level 2: Foundation (4) - `header`, `text`, `signals`, `system`
- Level 3: Data (2) - `data` (list/outline/json), `table`
- Level 4: Progress (3) - `bar`, `spinner`, `swiper`

**Input Demos** (`input/` folder):
- Level 1: Primitives (2) - `read_string`, `read_password`
- Level 2: Foundation (2) - `button`, `selection`

## You've Mastered Dual-Mode Display

You now have the complete **<span style="color:#F8961F">rendering toolkit</span>**:
- ✅ Output primitives (raw, line, block) for full control
- ✅ Input primitives (read_string, read_password) for user interaction
- ✅ Foundation events (header, text, signals, system, button, selection)
- ✅ Data display (list, outline, json_data, zTable with pagination)
- ✅ Progress tracking (bar, spinner, swiper with auto/manual modes)

**<span style="color:#8FBE6D">zDisplay gives you professional UI for Terminal and Browser—same code, automatic adaptation.</span>**

---

## Event Composition

Complex methods build on primitives—everything composes from the foundation:

```
zTable() → header() → text() → line() → raw()
```

When you call `z.display.zTable()`, it internally uses headers and text formatting, which ultimately call `raw()` or `line()`. **Everything builds on the primitives.**

## Quick Reference

**Primitives (Layer 1):**

```python
# Raw output - you control newlines
z.display.raw("Loading")
z.display.raw("...")
z.display.raw("\n")

# Line output - automatic newline
z.display.line("Processing complete")

# Block output - multi-line with preserved formatting
z.display.block("Line 1\nLine 2\nLine 3")

# Input collection
name = z.display.read_string("What's your name? ")
password = z.display.read_password("Password: ")

# Legacy aliases (backward compatible)
z.display.write_raw("text")   # → raw()
z.display.write_line("text")  # → line()
z.display.write_block("text") # → block()
```

**Foundation (Layer 2):**

```python
# Formatted headers - visual structure
z.display.header("Section Title", color="CYAN", style="full")   # ═══
z.display.header("Subsection", color="GREEN", style="single")   # ───
z.display.header("Note", color="YELLOW", style="wave")          # ~~~

# Text with indentation - hierarchy
z.display.text("Main content", indent=0)
z.display.text("Nested content", indent=1)
z.display.text("Deeper content", indent=2)

# Optional pause for user acknowledgment
z.display.text("Press Enter to continue", pause=True)

# Legacy parameter still works (backward compatible)
z.display.text("Old API", break_after=False)

# Feedback signals - automatic color coding
z.display.success("✅ Done!")        # Green
z.display.error("❌ Failed!")        # Red
z.display.warning("⚠️  Watch out!")  # Yellow
z.display.info("ℹ️  FYI...")         # Cyan

# Visual workflow separator
z.display.zMarker("Stage 1")         # Magenta separator
z.display.zMarker("Stage 2", color="CYAN")  # Custom color

# System events - professional status reporting
z.display.zDeclare("System Initialization", color="GREEN")
z.display.zDeclare("Loading Configuration", indent=1)
z.display.zSession(z.session)        # Display session state
z.display.zConfig(config_data)       # Display configuration

# User input - action confirmation
if z.display.button("Save Profile", color="success"):
    z.display.success("Profile saved!")

# User input - selection
role = z.display.selection("Choose role:", ["Developer", "Designer", "Manager"])
skills = z.display.selection("Choose skills:", ["Python", "React"], multi=True)
```

**Data (Layer 3):**

```python
# Lists - bullet/number/letter styles
z.display.list(["Apple", "Banana", "Cherry"], style="bullet")
z.display.list(["Step 1", "Step 2", "Step 3"], style="number")
z.display.list(["Option A", "Option B", "Option C"], style="letter")

# Outline - hierarchical (1→a→i→•)
z.display.outline([
    {
        "content": "Backend",
        "children": ["Python", "Database"]
    },
    "Frontend"
])

# JSON - with syntax coloring
z.display.json_data({"version": "1.5.5", "ready": True}, color=True)

# Tables with THREE pagination modes
# Type 1: Basic (no pagination)
z.display.zTable(
    title="Users",
    columns=["id", "name", "email"],
    rows=user_data
)

# Type 2: Simple truncation (limit only)
z.display.zTable(
    title="Users (Limited)",
    columns=["id", "name", "email"],
    rows=user_data,
    limit=3  # Shows "... N more rows" footer
)

# Type 3: Interactive navigation (limit + interactive=True)
z.display.zTable(
    title="Users - Interactive",
    columns=["id", "name", "email"],
    rows=user_data,
    limit=2,
    offset=0,
    interactive=True  # Keyboard controls: [n]ext, [p]revious, [f]irst, [l]ast, [#] jump, [q]uit
)
```

**Progress Tracking (Layer 4):**

```python
import time

# Deterministic progress - Manual mode (full control)
for i in range(100):
    z.display.progress_bar(
        current=i,
        total=100,
        label="Processing",
        show_percentage=True,
        show_eta=True,
        start_time=time.time()
    )

# Deterministic progress - Automatic mode (wrapper)
files = ["file1.txt", "file2.txt", "file3.txt"]
for file in z.display.progress_iterator(files, "Processing files"):
    process(file)  # progress_iterator manages counters automatically

# Indeterminate spinner - Automatic mode (context manager)
with z.display.spinner("Loading data", style="dots"):
    time.sleep(2)  # Background animation

# Indeterminate spinner - Manual mode (fine control)
update = z.display.indeterminate_progress("Building index")
for i in range(30):
    update()  # You control frame updates
    time.sleep(0.1)
z.display.raw("\n")

# Interactive slideshow carousel
slides = ["Welcome!", "Feature 1", "Feature 2", "Thank you!"]
z.display.zEvents.TimeBased.swiper(slides, "Tutorial", auto_advance=True, delay=3)
```

---

## What's Next

**<span style="color:#8FBE6D">Continue the Layer Journey</span>**

zDisplay is **<span style="color:#F8961F">Layer 1</span>**—the rendering engine that powers user interfaces. The natural progression continues with other **<span style="color:#8FBE6D">Layer 1 subsystems</span>** that build on this foundation:

- **[zAuth Guide →](zAuth_GUIDE.md)** - Authentication and user management
- **zDialog Guide** - Forms and validation
- **zDispatch Guide** - Event handling and routing

**<span style="color:#8FBE6D">Want Browser Rendering?</span>**

All these display methods also work in real-time web browser mode. For Terminal ↔ Web rendering, see:

- **[zBifrost Guide](zBifrost_GUIDE.md)** - WebSocket server with GUI rendering support

