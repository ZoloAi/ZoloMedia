# zSpark Configuration Files

**File Pattern:** `zSpark.*.zolo`  
**Purpose:** Spark application configuration and runtime settings

---

## Overview

zSpark files configure the core runtime behavior of Zolo Spark applications. They define application metadata, deployment settings, logging configuration, UI rendering, and server options.

### Key Characteristics

- **Single Root Key:** `zSpark:` is the ONLY valid root key
- **Indentation:** Like Python - either tabs OR spaces (4 spaces recommended)
- **File Naming:** Must match `zSpark.*.zolo` pattern (e.g., `zSpark.myapp.zolo`, `zSpark.production.zolo`)
- **LSP Features:** Full autocomplete, diagnostics, hover documentation, and snippet expansion

---

## Quick Start

### Using the Snippet Expansion

Type `zSpark>>` at the root level to expand a full template with tab stops:

```zolo
zSpark:
    title: MyApp              ← Tab stop 1
    deployment: Development   ← Tab stop 2
    logger: INFO              ← Tab stop 3
    logger_path: @.logs       ← Tab stop 4
    zMode: Terminal           ← Tab stop 5
    zServer:
        enabled: True         ← Tab stop 6
        zShell: True          ← Tab stop 7
    app_storage: True         ← Tab stop 8
    zVaFolder: @.UI           ← Tab stop 9
    zVaFile: zUI.Component    ← Tab stop 10
    zBlock: MainLayout        ← Tab stop 11
```

Press **Tab** to jump between fields and customize values.

---

## Structure Reference

### Root Key

```zolo
zSpark:
```

**Required.** This is the only valid root-level key for zSpark files.

---

## Properties

### `title`

**Type:** `string`  
**Description:** Application name or title  
**Example:**

```zolo
zSpark:
    title: MyAwesomeApp
```

---

### `deployment`

**Type:** `enum`  
**Values:** `Production` | `Development`  
**Description:** Deployment environment setting  
**Example:**

```zolo
zSpark:
    deployment: Production
```

**Notes:**
- `Production` - Optimized for live/production environments
- `Development` - Enables debug features and verbose logging

---

### `logger`

**Type:** `enum`  
**Values:** `PROD` | `DEV` | `INFO` | `DEBUG` | `WARNING` | `ERROR`  
**Description:** Logging level for application output  
**Example:**

```zolo
zSpark:
    logger: INFO
```

**Levels:**
- `PROD` - Production logging (errors only)
- `DEV` - Development logging (verbose)
- `INFO` - Informational messages
- `DEBUG` - Detailed debugging output
- `WARNING` - Warning messages only
- `ERROR` - Error messages only

---

### `logger_path`

**Type:** `zPath`  
**Description:** Directory path for log file storage  
**Example:**

```zolo
zSpark:
    logger_path: @.logs
```

**zPath Syntax:**
- `@.logs` - Relative to project root
- `@.logs.app` - Nested directory
- Supports Zolo's special path resolution

---

### `zMode`

**Type:** `enum`  
**Values:** `Terminal` | `zBifrost`  
**Description:** Application execution mode  
**Example:**

```zolo
zSpark:
    zMode: Terminal
```

**Modes:**
- `Terminal` - Command-line/console execution
- `zBifrost` - Bridge mode for web/GUI rendering

---

### `zServer`

**Type:** `object`  
**Description:** Server configuration block  
**Example:**

```zolo
zSpark:
    zServer:
        enabled: True
        zShell: True
```

#### `zServer.enabled`

**Type:** `boolean`  
**Description:** Enable or disable the server component  
**Values:** `True` | `False`

#### `zServer.zShell`

**Type:** `boolean`  
**Description:** Enable zShell interactive shell access  
**Values:** `True` | `False`

---

### `app_storage`

**Type:** `boolean`  
**Values:** `True` | `False`  
**Description:** Enable application storage layer  
**Example:**

```zolo
zSpark:
    app_storage: True
```

---

### `zVaFolder`

**Type:** `zPath`  
**Description:** Path to theme/styling folder  
**Example:**

```zolo
zSpark:
    zVaFolder: @.UI
    zVaFolder: @.UI.zProducts.zTheme
```

**Usage:**
- Points to a directory containing UI configuration and styling
- Uses zPath syntax for flexible path resolution

---

### `zVaFile`

**Type:** `reference`  
**Description:** Reference to a zUI file for component styling  
**Example:**

```zolo
zSpark:
    zVaFile: zUI.Component
    zVaFile: zUI.zBreakpoints
```

**Format:** `zUI.<filename>` (without `.zolo` extension)

---

### `zBlock`

**Type:** `string`  
**Description:** Reference to a reusable zBlock component  
**Example:**

```zolo
zSpark:
    zBlock: MainLayout
    zBlock: Navbar
    zBlock: zBreakpoints_Details
```

**Notes:**
- Free-form string naming
- No `zBlock.` prefix required (this was removed in recent updates)
- Used for modular UI composition

---

## Complete Example

```zolo
zSpark:
    title: ProductionApp
    deployment: Production
    logger: PROD
    logger_path: @.logs.production
    zMode: zBifrost
    zServer:
        enabled: True
        zShell: False
    app_storage: True
    zVaFolder: @.UI.zProducts.zTheme
    zVaFile: zUI.ProductTheme
    zBlock: MainDashboard
```

---

## LSP Features

### Autocompletion

- **Context-aware** - Only shows valid properties based on indentation and parent keys
- **Value suggestions** - Enum values auto-suggested after typing `:`
- **Snippet expansion** - `zSpark>>` expands full template

### Diagnostics

- **Indentation validation** - Like Python 3: allows tabs OR spaces, but forbids mixing
- **Invalid root keys** - Warns if keys other than `zSpark:` are at root level
- **Type validation** - Checks boolean, enum, and path values

### Hover Documentation

Hover over any property to see:
- **Description** - What the property does
- **Type** - Expected value type
- **Valid values** - For enums/booleans

---

## Best Practices

### File Naming

✅ **Good:**
- `zSpark.production.zolo`
- `zSpark.myapp.zolo`
- `zSpark.config.zolo`

❌ **Bad:**
- `spark.config.zolo` (missing `zSpark` prefix)
- `zSpark.zolo` (missing middle identifier)

### Indentation

Like Python, Zolo allows **either tabs OR spaces** (but never mixed):

**Recommended: 4 spaces**
```zolo
zSpark:
    title: MyApp        ← 4 spaces
    zServer:
        enabled: True   ← 8 spaces (nested)
```

**Allowed: Consistent tabs**
```zolo
zSpark:
	title: MyApp        ← 1 tab
	zServer:
		enabled: True   ← 2 tabs (nested)
```

**Forbidden: Mixed tabs and spaces** ❌
```zolo
zSpark:
    title: MyApp        ← spaces
	zServer:            ← tab (ERROR!)
```

### Deployment Separation

Consider separate files for different environments:

```
zSpark.development.zolo
zSpark.staging.zolo
zSpark.production.zolo
```

### Logging Configuration

**Development:**
```zolo
logger: DEV
logger_path: @.logs.dev
```

**Production:**
```zolo
logger: PROD
logger_path: @.logs.production
```

---

## Related Files

- **zUI Files** - Referenced by `zVaFile` for styling
- **zConfig Files** - Application-specific configuration
- **zEnv Files** - Environment variables and secrets
- **zSchema Files** - Data schema definitions

---

## Troubleshooting

### "Invalid root key" error

**Problem:** Root-level key is not `zSpark:`

**Solution:** zSpark files MUST have `zSpark:` as the only root key:

```zolo
# ❌ Wrong
config:
    title: MyApp

# ✅ Correct
zSpark:
    title: MyApp
```

### "Inconsistent indentation" error

**Problem:** Mixing tabs and spaces (like Python 3's TabError)

**Solution:** Use EITHER tabs OR spaces consistently throughout the file:

```zolo
# ❌ Wrong (mixing tabs and spaces)
zSpark:
    title: MyApp        ← spaces
	logger: INFO        ← tab (ERROR!)

# ✅ Correct (consistent spaces - recommended)
zSpark:
    title: MyApp
    logger: INFO

# ✅ Also correct (consistent tabs)
zSpark:
	title: MyApp
	logger: INFO
```

**Note:** If using spaces, they must be in multiples of 4 (like Python's PEP 8).

### Autocomplete not showing

**Problem:** File not named with `zSpark.*.zolo` pattern

**Solution:** Ensure filename matches the pattern:

```bash
mv myconfig.zolo zSpark.myconfig.zolo
```

---

## Version History

- **v1.0.3** - Added `zSpark>>` snippet expansion
- **v1.0.2** - Removed `zBlock.` prefix requirement
- **v1.0.1** - Changed indentation standard from 2 to 4 spaces
- **v1.0.0** - Initial zSpark file type support

---

## Support

For questions, issues, or contributions:
- **Email:** info@zolo.media
- **Repository:** [GitHub](https://github.com/zolomedia/zlsp)
- **Documentation:** `Documentation/` directory
