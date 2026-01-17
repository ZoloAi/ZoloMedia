# File Type Detection

This document describes how zlsp detects and provides specialized LSP features for different `.zolo` file patterns.

---

## Overview

zlsp uses filename-based conventions to determine file types and provide context-aware LSP features. This detection happens automatically based on the filename pattern.

---

## Supported File Patterns

| Pattern | Detected Type | LSP Features |
|---------|---------------|--------------|
| `zSpark.*.zolo` | ZSPARK | Full support |
| `zConfig.*.zolo` | ZCONFIG | Full support |
| `zEnv.*.zolo` | ZENV | Basic support |
| `zUI.*.zolo` | ZUI | Basic support |
| `zSchema.*.zolo` | ZSCHEMA | Basic support |
| `zMachine.*.zolo` | ZMACHINE | Basic support |
| `*.zolo` | GENERIC | Basic support |

---

## Detection Logic

zlsp matches filenames against specific patterns:

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
zSpark.production.zolo    → ZSPARK
zConfig.database.zolo     → ZCONFIG
zUI.Navbar.zolo           → ZUI
mydata.zolo               → GENERIC
spark.config.zolo         → GENERIC (no prefix match)
```

**Note:** The pattern must start with the special prefix (e.g., `zSpark.`) to be detected as a special file type.

---

## LSP Features

### Universal Features (All File Types)

All `.zolo` files receive these LSP features:

- **Semantic Highlighting** - Context-aware syntax coloring
- **Diagnostics** - Real-time error and warning detection
- **Hover Documentation** - Inline help for keys and values
- **Indentation Validation** - Enforces tabs OR spaces (like Python)
- **Code Formatting** - Auto-formatting support
- **Symbol Navigation** - Jump to definitions

### File-Type-Specific Features

Some file types receive additional context-aware features:

| Feature | zSpark | zConfig | Others |
|---------|--------|---------|--------|
| Context-aware completions | Yes | Yes | No |
| Value validation | Yes | Yes | No |
| Snippet expansion | Yes | No | No |
| Root key enforcement | Yes | No | No |

**Note:** File-type-specific features are implemented in the LSP providers based on the detected file type.

---

## Common Syntax Elements

All `.zolo` files share these syntax rules:

### Indentation

Like Python, all `.zolo` files allow **tabs OR spaces** (but never mixed):

```zolo
# Valid: 4-space indentation (recommended)
root_key:
    nested_key: value
    deeper:
        nested: value

# Valid: Tab indentation
root_key:
	nested_key: value
	deeper:
		nested: value
```

**Forbidden:** Mixing tabs and spaces (Python 3 TabError style)

### Type Hints

Use parentheses for explicit type hints:

```zolo
age(int): 25
name(string): John
active(boolean): true
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

Inline documentation comments:

```zolo
key: value  #> This is an inline doc comment <#
```

---

## Naming Conventions

Use descriptive middle segments in filenames:

```
Good:
  zSpark.production.zolo
  zSpark.development.zolo
  zConfig.database.zolo
  zUI.MainNavbar.zolo

Avoid:
  zSpark.zolo          (too generic)
  config.prod.zolo     (missing prefix)
```

---

## File Organization

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

---

## Related Documentation

- [INSTALLATION.md](./INSTALLATION.md) - Set up the LSP
- [ARCHITECTURE.md](./ARCHITECTURE.md) - How it all works
- [Editor Integrations](../editors/) - Editor-specific guides

For detailed information about what these file types are used for in Zolo applications, see the zOS and zKernel documentation (coming when those packages are added to the monorepo).

---

**Last Updated:** January 2026
