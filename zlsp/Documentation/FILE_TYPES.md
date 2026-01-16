# Zolo File Types Reference

This guide covers the different `.zolo` file types and their specific purposes, syntax, and features.

---

## Overview

Zolo uses a **filename-based convention** to determine file type and provide specialized LSP features:

| Pattern | Purpose | Documentation |
|---------|---------|---------------|
| `zSpark.*.zolo` | Spark application configuration | [zSpark.md](./zSpark.md) |
| `zConfig.*.zolo` | Application settings | _Coming soon_ |
| `zEnv.*.zolo` | Environment variables | _Coming soon_ |
| `zUI.*.zolo` | UI components and layouts | _Coming soon_ |
| `zSchema.*.zolo` | Data schema definitions | _Coming soon_ |
| `zMachine.*.zolo` | Machine/system configuration | _Coming soon_ |
| `*.zolo` | Generic zolo files | Use any structure |

---

## File Type Detection

The LSP automatically detects file types based on filename patterns:

```python
FileType.ZSPARK   → zSpark.*.zolo
FileType.ZCONFIG  → zConfig.*.zolo
FileType.ZENV     → zEnv.*.zolo
FileType.ZUI      → zUI.*.zolo
FileType.ZSCHEMA  → zSchema.*.zolo
FileType.ZMACHINE → zMachine.*.zolo
FileType.GENERIC  → *.zolo (fallback)
```

### Examples

```
✅ zSpark.production.zolo    → FileType.ZSPARK
✅ zConfig.database.zolo     → FileType.ZCONFIG
✅ zUI.Navbar.zolo           → FileType.ZUI
✅ mydata.zolo               → FileType.GENERIC
❌ spark.config.zolo         → FileType.GENERIC (no prefix match)
```

---

## Documented File Types

### 1. zSpark Files

**Pattern:** `zSpark.*.zolo`  
**Purpose:** Spark application runtime configuration

📚 **[Full Documentation →](./zSpark.md)**

**Key Features:**
- Single root key: `zSpark:`
- Deployment & logging configuration
- Server and UI settings
- Snippet expansion with `zSpark>>`

**Quick Example:**

```zolo
zSpark:
    title: MyApp
    deployment: Production
    logger: INFO
    zMode: Terminal
```

---

## Upcoming Documentation

### 2. zConfig Files

**Pattern:** `zConfig.*.zolo`  
**Purpose:** Application-specific configuration settings

**Status:** 🚧 _Documentation coming soon_

---

### 3. zEnv Files

**Pattern:** `zEnv.*.zolo`  
**Purpose:** Environment variables and secrets management

**Status:** 🚧 _Documentation coming soon_

---

### 4. zUI Files

**Pattern:** `zUI.*.zolo`  
**Purpose:** User interface components and layouts

**Status:** 🚧 _Documentation coming soon_

**Quick Preview:**

```zolo
zImage: @.assets.logo.png
zText: Welcome to Zolo!
zH1: Main Heading
zURL: https://zolo.media
```

---

### 5. zSchema Files

**Pattern:** `zSchema.*.zolo`  
**Purpose:** Data schema and model definitions

**Status:** 🚧 _Documentation coming soon_

**Quick Preview:**

```zolo
users:
    username: (string)
    email: (string)
    age: (int)
```

---

### 6. zMachine Files

**Pattern:** `zMachine.*.zolo`  
**Purpose:** Machine and system configuration

**Status:** 🚧 _Documentation coming soon_

---

## Common Syntax Elements

### Indentation

All `.zolo` files use **4-space indentation** (Python-style):

```zolo
root_key:
    nested_key: value        ← 4 spaces
    deeper:
        nested: value        ← 8 spaces
```

### Type Hints

Use parentheses for explicit type hints:

```zolo
age: (int) 25
name: (string) John
active: (boolean) true
```

### zPath Syntax

Special path notation for Zolo-managed paths:

```zolo
logo: @.assets.logo.png
config: @.config.settings
logs: @.logs.production
```

### Comments

Standard `#` comments:

```zolo
# This is a comment
key: value  # Inline comment
```

---

## LSP Features by File Type

### All File Types

✅ **Semantic Highlighting** - Context-aware syntax coloring  
✅ **Diagnostics** - Real-time error/warning detection  
✅ **Hover Documentation** - Inline help on properties  
✅ **Indentation Validation** - 4-space enforcement

### File-Type-Specific Features

| Feature | zSpark | zConfig | zEnv | zUI | zSchema |
|---------|--------|---------|------|-----|---------|
| **Context Completions** | ✅ | 🚧 | 🚧 | 🚧 | 🚧 |
| **Snippet Expansion** | ✅ | 🚧 | 🚧 | 🚧 | 🚧 |
| **Value Validation** | ✅ | 🚧 | 🚧 | 🚧 | 🚧 |
| **Root Key Enforcement** | ✅ | 🚧 | 🚧 | ❌ | ❌ |
| **Code Actions** | ✅ | 🚧 | 🚧 | 🚧 | 🚧 |

_Legend: ✅ Implemented | 🚧 Coming Soon | ❌ Not Applicable_

---

## Best Practices

### Naming Conventions

Use descriptive middle segments in filenames:

```
✅ zSpark.production.zolo
✅ zSpark.development.zolo
✅ zConfig.database.zolo
✅ zUI.MainNavbar.zolo

❌ zSpark.zolo          (too generic)
❌ config.prod.zolo     (missing prefix)
```

### File Organization

Organize by file type in your project:

```
project/
├── zSpark.app.zolo
├── config/
│   ├── zConfig.database.zolo
│   └── zConfig.api.zolo
├── ui/
│   ├── zUI.Navbar.zolo
│   ├── zUI.Footer.zolo
│   └── zUI.Dashboard.zolo
└── schema/
    └── zSchema.users.zolo
```

### Consistency

- Use **4 spaces** for indentation (never tabs)
- Keep similar files in same directory
- Use consistent naming patterns
- Document complex configurations with comments

---

## Related Documentation

- **[Installation Guide](./INSTALLATION.md)** - Set up the LSP
- **[Quick Start](./QUICKSTART.md)** - Get started in 5 minutes
- **[Architecture](./ARCHITECTURE.md)** - How it all works
- **[Editor Integrations](./editors/)** - Editor-specific guides

---

## Contributing Documentation

Want to help document a file type? See our contribution guidelines:

1. Create `Documentation/<FileType>.md`
2. Follow the zSpark.md template structure
3. Include examples, best practices, and troubleshooting
4. Update this index (FILE_TYPES.md)

---

**Last Updated:** January 2026  
**Contact:** info@zolo.media
