# zConfig 5-Layer Hierarchy

**[← Back to zConfig Guide](zConfig_GUIDE.md) | [Home](../README.md)**

---

## Overview

zConfig uses a **5-layer configuration hierarchy** where each layer can override the previous one. Understanding this hierarchy is crucial for effective zOS configuration.

## The 5 Layers (Lowest to Highest Priority)

```
┌─────────────────────────────────────────────────────────────┐
│ Layer 5: zSpark (Runtime Dict)          ← HIGHEST PRIORITY │
├─────────────────────────────────────────────────────────────┤
│ Layer 4: Environment Variables (.zEnv, shell exports)       │
├─────────────────────────────────────────────────────────────┤
│ Layer 3: Config Files (zConfig.environment.yaml)            │
├─────────────────────────────────────────────────────────────┤
│ Layer 2: System Environment Variables (ZOLO_*)              │
├─────────────────────────────────────────────────────────────┤
│ Layer 1: Hardcoded Defaults              ← LOWEST PRIORITY  │
└─────────────────────────────────────────────────────────────┘
```

---

## Layer 1: Hardcoded Defaults

**Priority:** Lowest  
**Location:** Built into zOS code  
**Purpose:** Fallback values when nothing else is configured

```python
# Defaults (you never need to set these)
deployment: "Debug"
role: "development"
logger: "INFO"
```

**When used:** First run, before any configuration exists.

---

## Layer 2: System Environment Variables

**Priority:** Low  
**Location:** Operating system environment  
**Purpose:** System-wide settings across all projects

```bash
# Set in your shell profile (.bashrc, .zshrc, etc.)
export ZOLO_DEPLOYMENT="Production"
export ZOLO_LOGGER="ERROR"
```

**When used:** When you want consistent settings across ALL zOS projects on your machine.

---

## Layer 3: Config Files

**Priority:** Medium  
**Location:** `~/Library/Application Support/zolo-zcli/zConfigs/zConfig.environment.yaml`  
**Purpose:** Persistent user preferences

```yaml
zEnv:
  deployment: "Production"
  role: "staging"
  logging:
    level: "WARNING"
```

**When used:** For persistent settings you want across restarts but can edit in one place.

**Edit via:**
- File: Manually edit the YAML file
- Code: `z.config.persistence.persist_environment("deployment", "Production")`
- Shell: `zcli config environment deployment Production`

---

## Layer 4: Environment Variables (.zEnv files)

**Priority:** High  
**Location:** `.zEnv` or `.env` file in your workspace  
**Purpose:** Project-specific secrets and settings

```bash
# .zEnv in your project directory
ZOLO_DEPLOYMENT=Debug
ZOLO_LOGGER=DEBUG
APP_API_KEY=secret123
DATABASE_URL=postgresql://localhost/mydb
```

**When used:** Project-specific overrides that shouldn't be committed to version control.

**Access via:**
```python
z.config.environment.get_env_var("APP_API_KEY")
```

---

## Layer 5: zSpark (Runtime Dict)

**Priority:** **HIGHEST**  
**Location:** Passed to `zOS()` constructor  
**Purpose:** Runtime overrides, experimentation, programmatic control

```python
z = zOS({
    "deployment": "Production",  # Overrides everything
    "logger": "ERROR",           # Highest priority
    "zTraceback": True,          # Runtime behavior
})
```

**When used:**
- Quick experimentation
- Programmatic configuration
- Testing different settings
- Override everything else

**Key benefit:** No files to edit, immediate effect, perfect for testing.

---

## Examples: How the Hierarchy Works

### Example 1: Logger Level

```python
# Layer 1: Default
# logger = "INFO"

# Layer 2: System env
export ZOLO_LOGGER="WARNING"
# → logger = "WARNING"

# Layer 3: Config file
# zConfig.environment.yaml: logging.level: "ERROR"
# → logger = "ERROR"

# Layer 4: .zEnv file
# .zEnv: ZOLO_LOGGER=DEBUG
# → logger = "DEBUG"

# Layer 5: zSpark
z = zOS({"logger": "CRITICAL"})
# → logger = "CRITICAL" ✅ WINS!
```

### Example 2: Deployment Mode

```python
# Layer 1: Default
# deployment = "Debug"

# Layer 3: Config file
# zConfig.environment.yaml: deployment: "Production"
# → deployment = "Production"

# Layer 5: zSpark
z = zOS({"deployment": "Debug"})
# → deployment = "Debug" ✅ WINS!
```

---

## Quick Reference

| Setting | Layer 1 | Layer 2 | Layer 3 | Layer 4 | Layer 5 |
|---------|---------|---------|---------|---------|---------|
| **deployment** | ✓ | `ZOLO_DEPLOYMENT` | `zEnv.deployment` | `.zEnv` | `zSpark` |
| **logger** | ✓ | `ZOLO_LOGGER` | `logging.level` | `.zEnv` | `zSpark` |
| **Custom vars** | - | - | `zEnv.custom_*` | `.zEnv` | - |
| **Secrets** | - | - | - | `.zEnv` ✓ | - |

---

## Best Practices

### Use Layer 3 (Config Files) For:
- Persistent user preferences
- Machine-specific defaults
- Settings you edit occasionally

### Use Layer 4 (.zEnv) For:
- Project-specific secrets
- API keys and credentials
- Database URLs
- Per-project overrides

### Use Layer 5 (zSpark) For:
- Quick testing
- Experimentation
- Programmatic control
- Runtime overrides

### Don't Use Layer 2 (System Env) Unless:
- You want the same setting across ALL projects
- You're setting up a new machine
- You have organization-wide defaults

---

## Case-Insensitive Keys in zSpark

zSpark accepts deployment in any case:

```python
# All work the same:
z = zOS({"deployment": "Production"})
z = zOS({"Deployment": "Production"})
z = zOS({"DEPLOYMENT": "Production"})
```

**Why?** Flexibility for different coding styles.

---

## Debugging the Hierarchy

Want to see which layer won?

```python
z = zOS({"deployment": "Production", "logger": "DEBUG"})

# Check what's active
print(f"Deployment: {z.config.get_environment('deployment')}")
print(f"Logger: {z.session.get('zLogger')}")
print(f"zSpark stored: {z.session.get('zSpark')}")

# Check production status
print(f"Is production? {z.config.is_production()}")
```

**Look for these messages in console:**
```
[EnvironmentConfig] Deployment overridden by zSpark: Production
[SessionConfig] Logger level from zSpark: DEBUG
```

---

**[← Back to zConfig Guide](zConfig_GUIDE.md) | [Home](../README.md)**

