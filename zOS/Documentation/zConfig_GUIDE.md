**[← Back to zInstall Guide](zInstall_GUIDE.md) | [Home](../README.md) | [Next: zComm Guide →](zComm_GUIDE.md)**

---

# zConfig

**zConfig** is the **first sub-system** initialized by **zOS**.
> See [**zArchitecture**](../README.md#the-zarchitecture) for full context.

It auto detects **machine context**, **environment**, and manages **in-memory zSessions**.  
All **other subsystems** rely on **zConfig** for the delerative nature of **zOS**.

You get: 

- **Zero boilerplate**  
- **No dotenv sprawl**
- **No reinventing the wheel**
- **Hierarchical settings** (machine → environment → session)  
- **Cross-platform** paths  
- and **persistent preferences**.

## Tutorials

**Learn by doing!** 

The tutorials below are organized in a bottom-up fashion. Every tutorial below has a working demo you can run and modify.

**A Note on Learning zOS:**  
Each tutorial (lvl1, lvl2, lvl3...) progressively introduces more complex features of **this subsystem**. The early tutorials start with familiar imperative patterns (think Django-style conventions) to meet you where you are as a developer.

As you progress through zOS's subsystems, you'll notice a gradual shift from imperative to declarative patterns. This intentional journey helps reshape your mental model from imperative to declarative thinking. Only when you reach **Layer 3 (Orchestration)** will you see subsystems used **fully declaratively** as intended in production. By then, the true magic of declarative coding will reveal itself, and you'll understand why we started this way.

Get the demos:

```bash
# Clone only the Demos folder
git clone --depth 1 --filter=blob:none --sparse https://github.com/ZoloAi/zolo-zcli.git
cd zolo-zcli
git sparse-checkout set Demos
```

> All zConfig demos are in: `Demos/Layer_0/zConfig_Demo/`

---

# **zConfig - Level 1** (Initialization)

### **i. Initialize zOS**

One line does everything. When you call `zOS()`, it automatically:
- **Detects your machine** (OS, CPU, browser, IDE, terminal)
- **Creates config folders** in your OS-native application support directory (first run)
- **Loads configs** from multiple sources (system defaults, config files, environment variables)
- **Sets up deployment mode**, logger, and session ready for immediate use

No setup files. No configuration needed. **Just import and go**.

```python
from zOS import zOS

z = zOS()  # That's it!
```

**🎯 Run the demo to see for yourself**

```bash
python3 Demos/Layer_0/zConfig_Demo/lvl1_initialize/1_initialize.py
```

[View demo source →](../Demos/Layer_0/zConfig_Demo/lvl1_initialize/1_initialize.py)

When you run `z = zOS()`, you see colorful banners like "zConfig Ready", "zComm Ready", etc. These are **system messages** - visual feedback showing that internal subsystems are loading successfully.

In addition, between those banners, you'll see the **framework logger** outputting initialization details:

```
════════════════════ zConfig Ready ════════════════════
zConfig - DEBUG - Logger initialized at level: INFO
════════════════════ zComm Ready ══════════════════════
zComm - DEBUG - Communication subsystem ready
```

This is the **framework logger** - it captures DEBUG-level details of all internal zOS operations automatically. You never need to touch it, but it's invaluable for debugging!

**What are logs?** Logs are like a detailed history book of everything that happens in your application. While those banners display on your screen, zOS is *also* recording detailed framework operations to a file.

**The distinction:**
- **Banners** = what you *see*
- **Framework logs** = what's *recorded*

**Where are logs stored?** When you initialize zOS for the first time, it creates a designated directory in your OS-native application support folder.

**This is where all zOS configurations, logs, and default data live.** Located at:

- **macOS**: `~/Library/Application Support/zolo-zcli/`
- **Linux**: `~/.local/share/zolo-zcli/`
- **Windows**: `%APPDATA%/zolo-zcli/`

Inside this directory, zOS creates:
- `zConfigs/` - Machine and environment configuration files
- `zUIs/` - Custom UI definitions
- `logs/` - Application logs (both framework and app logs, kept separate)

> **Note:** This OS-native folder structure is what makes zOS truly cross-platform - your code works identically on macOS, Linux, and Windows without any path changes!
>
> Behind the scenes, zOS uses **zParser** (subsystem #8) to handle all path operations decleratively. For **advanced** path manipulation and file operations, see [**zParser Guide**](zParser_GUIDE.md).


---

### **ii. zSpark** - The Simplest Entry Point

**zSpark** is a dictionary you pass `zOS()` to override any presistent and/or enviornment settings. It has **the highest priority** — whatever you put in zSpark wins over everything else (config files, environment variables, system defaults).

**How zConfig resolves configuration** (5 sources, bottom to top priority):

| Priority | Source | What | Where |
|-------|--------|------|-------|
| **1 (lowest)** | **System Defaults** | Package defaults | Read-only |
| **2** | **zMachine** | Hardware + tools | Config file |
| **3** | **zEnvironment** | Deployment + logging | Config file |
| **4** | **dotenv** | Secrets + exports | .zEnv / shell |
| **5 (highest)** | **zSpark** | Runtime overrides | Your code |

> **Note:** Sources 2-3 are persistent config files in your OS-native application support folder (mentioned in the Initialize demo above).

**How priority works:** Higher number = higher priority. If the same setting exists in multiple sources, the highest priority wins. For example, if `deployment: "Debug"` is in zEnvironment (3) and `deployment: "Production"` is in zSpark (5), zSpark wins → Production mode. 

**Example:**

```python
# Production mode (silent)
zSpark = {"deployment": "Production"}  # Development, Testing, Production
z = zOS(zSpark)
```

**🎯 Try zSpark yourself:**

Run the demo to see zSpark and deployment modes in action:

```bash
python3 Demos/Layer_0/zConfig_Demo/lvl1_initialize/2_zspark.py
```

[View demo source →](../Demos/Layer_0/zConfig_Demo/lvl1_initialize/2_zspark.py)

---

### What is `deployment`?

In the previous demo, you saw `deployment: "Production"` in the zSpark dictionary. Now let's understand what deployment modes actually do!

The deployment setting controls **how zOS behaves** in different environments:

| Mode | Behavior | Default Logger | Use Case |
|------|----------|----------------|----------|
| **Development** | Full output: banners, system messages, detailed logs | INFO | Local development - see everything |
| **Testing** | Clean logs only: no banners/sysmsg, verbose logging | INFO | Staging/QA - logs for debugging, no noise |
| **Production** | Minimal: silent console, no banners, errors only | ERROR | Production - minimal output |

> **Note:** The `logger` column shows **default** levels when not explicitly set. You can override: `{"deployment": "Production", "logger": "DEBUG"}` for troubleshooting.

**Default behavior:** If you don't specify a deployment mode (like in the basic `zOS()` initialization from Level 1.i), zOS defaults to **Development** mode. This means full output with banners and INFO-level logging - perfect for getting started and seeing everything work!

### iii. Deployment Modes - All Three Options

Compare all three deployment modes in one place. This demo focuses purely on **deployment behavior** - how each mode affects system output, banners, and logging defaults:

```python
zSpark = {
    # "deployment": "Development",  # Full output
    # "deployment": "Testing",      # Clean logs
    "deployment": "Production",    # Minimal (active)
}
z = zOS(zSpark)
```

**What you'll discover by running each mode:**
- **Production**: Clean, silent output - no banners appear during initialization
- **Testing**: No banners but you'll see framework logs - perfect for staging/QA
- **Development**: Full banners + framework logs - ideal for local development

**Observe the behavior:** Run the demo with each deployment mode and watch how the initialization output changes!

**🎯 Try it yourself:**

Run the demo to see Production mode, then uncomment other modes to compare:

```bash
python3 Demos/Layer_0/zConfig_Demo/lvl1_initialize/3_deployment.py
```

[View demo source →](../Demos/Layer_0/zConfig_Demo/lvl1_initialize/3_deployment.py)

---

# **zConfig - Level 2** (zSettings)

Now that you understand deployment modes, let's explore **logging in detail**. You saw framework logs during initialization, but zOS also provides a powerful application logger for your code!

### **i. Logger Basics - Your First Logs**

Start using the built-in logger. No configuration, no imports beyond zOS itself!

```python
from zOS import zOS

z = zOS()  # That's it! Logger is ready

# Five log levels, from most to least verbose:
z.logger.debug("DEBUG: Detailed diagnostic information")
z.logger.info("INFO: Application status update")
z.logger.warning("WARNING: Something needs attention")
z.logger.error("ERROR: Something failed")
z.logger.critical("CRITICAL: System failure!")
```

**What you discover:**
- `z.logger` is built-in and ready to use
- Six log levels available (we'll cover the 6th in a moment)
- In Development mode (the default), INFO and above are shown
- Logs appear in both console AND log file automatically

**Where are your logs stored?**

Remember the zOS support folder from Level 1? Your logs live in the `logs/` directory, but with a smart twist: **each script gets its own log file**:

```
~/Library/Application Support/zolo-zcli/logs/
├── my_app.log           # Your app (my_app.py)
├── api_server.log       # Another app (api_server.py)
├── 1_logger_basics.log  # This demo
└── zcli-framework.log   # Internal zOS (automatic, separate)
```

**🎯 Try it yourself:**

Run the demo to see logging in action:

```bash
python3 Demos/Layer_0/zConfig_Demo/lvl2_settings/1_logger_basics.py
```

Check the log file created: `~/Library/.../logs/1_logger_basics.log`

[View demo source →](../Demos/Layer_0/zConfig_Demo/lvl2_settings/1_logger_basics.py)

---

**How it works:**
- Script name auto-detected: `my_app.py` → `my_app.log`
- Same script = same log file (appended across runs)
- Custom via zSpark: `{"title": "api"}` → `api.log`
- Framework logs always separate in `zcli-framework.log`

**Two completely separate logging streams:**

1. **`z.logger`** - Your application logs
   - Controlled by `logger` setting
   - Goes to `{script_name}.log`
   
2. **`z.logger.framework`** - Internal zOS logs
   - Controlled by `deployment` setting
   - Goes to `zcli-framework.log`
   - Automatic, transparent (you never touch it)


---

### ii. Advanced Logger - Custom Directory & Name

Take full control of your logging: custom log directory, custom filename, and override deployment defaults.

```python
zSpark = {
    "deployment": "Production",  # No banners/sysmsg
    "title": "api-server",  # Log filename (without .log)
    "logger": "INFO",  # Override Production default (ERROR)
    "logger_path": "./logs",  # Custom directory (relative to cwd)
}
z = zOS(zSpark)

z.logger.info("API started")  # Goes to ./logs/api-server.log
```

**Separation of Concerns:**

1. **Logger Path** (`"logger_path"`) - WHERE (directory):
   - Default: System folder (`~/Library/.../logs/`)
   - Relative: `"./logs"` (relative to current working directory)
   - Absolute: `"/var/log/myapp"` (full directory path)
   - Tilde: `"~/my_logs"` (expands to home directory)
   
2. **Session Title** (`"title"`) - WHAT (filename):
   - Default: Script filename (`my_app.py` → `my_app.log`)
   - Custom: `{"title": "api"}` → `api.log`
   - Always used (whether logger_path is custom or default)
   
3. **Logger Level** (`"logger"`):
   - Default: Based on deployment (Production→ERROR, others→INFO)
   - Override: DEBUG, INFO, WARNING, ERROR, CRITICAL, PROD

**Result:** `logger_path/title.log`

**Framework logs remain separate:**
- Always in: `~/Library/Application Support/zolo-zcli/logs/zcli-framework.log`
- Never customizable (by design - keeps framework transparent and predictable)

**🎯 Try it yourself:**

Run the demo to see full customization:

```bash
python3 Demos/Layer_0/zConfig_Demo/lvl2_settings/2_logger_advanced.py
```

Check both log files: custom location AND framework location!

[View demo source →](../Demos/Layer_0/zConfig_Demo/lvl2_settings/2_logger_advanced.py)

---

### iii. PROD Logger Level - Silent 

Now discover zOS's unique 6th logger level that doesn't exist in standard Python logging.

**Standard Python logging levels:**
- DEBUG, INFO, WARNING, ERROR, CRITICAL (5 levels)

**zOS adds a 6th level:**
- **PROD** = Silent console + DEBUG file logging

```python
zSpark = {
    "deployment": "Production",
    "logger": "PROD",  # The special 6th level!
}
z = zOS(zSpark)

z.logger.info("API started")  # Silent in console, DEBUG in file
```

**What makes PROD special:**
- Console: **Completely silent** (zero output)
- File: **DEBUG level** (captures everything)
- Perfect for: Production APIs, microservices, daemons, background services

**Why it exists:**
Production environments often need full debug logs for troubleshooting, but absolutely no console noise. PROD gives you both: silent operation with comprehensive file logging.

**🎯 Try it yourself:**

Experience the silence:

```bash
python3 Demos/Layer_0/zConfig_Demo/lvl2_settings/3_logger_prod.py
```

Notice: Your console stays silent, but check the log file - all messages are there!

[View demo source →](../Demos/Layer_0/zConfig_Demo/lvl2_settings/3_logger_prod.py)

---

### iv. zTraceback - Automatic Exception Handling

Enable automatic exception handling - no try/except blocks needed!

```python
zSpark = {
    "deployment": "Production",  # Clean zTraceback UI
    "title": "my-production-api",
    "logger": "INFO",
    "logger_path": "./logs",
    "zTraceback": True,  # Automatic exception handling
}
z = zOS(zSpark)

# Just write your code - errors are handled automatically
result = handle_request()  # If error occurs, interactive menu launches
```
**🎯 Try Experience automatic exception handling yourself:**

```bash
python3 Demos/Layer_0/zConfig_Demo/lvl2_settings/4_ztraceback.py
```

Watch the interactive menu launch when the error occurs!

[View demo source →](../Demos/Layer_0/zConfig_Demo/lvl2_settings/4_ztraceback.py)

**What you discover:**
- **No try/except blocks needed in your code**
- Unhandled exceptions intercepted automatically
- Interactive menu shows error details and full traceback
- Clean debugging experience with nested call stacks

**How it works:**
1. `zTraceback: True` installs `sys.excepthook`
2. Any unhandled exception triggers the menu
3. Interactive options: View Details, Full Traceback, Exit
4. Production deployment keeps the UI clean (no framework noise)

> **Note:** zTraceback is orchestrated by the `zWalker` subsystem, which provides the interactive menu infrastructure. For advanced customization and understanding the orchestration layer, see the [zWalker Guide](./zWalker_GUIDE.md).

---

**🎯 Level 2 Complete!**

You've mastered the development-critical settings: **logging** and **error handling**. zOS has many more configuration options (network, security, performance), but these two are essential for every project. In Level 3, you'll learn how to **read** all configuration values—from machine detection to environment settings.

---

# zConfig - Level 3 (Get)

### i. Read Machine Values

Now that you understand configuration basics (Level 1) and settings (Level 2), it's time to **read** configuration values.

Remember from Level 1: zOS auto-detects your hardware, OS, Python runtime, and tools during initialization. This **zMachine** configuration persists in your zOS support folder, shared across all projects:

- **macOS**: `~/Library/Application Support/zolo-zcli/zConfigs/zConfig.machine.yaml`
- **Linux**: `~/.local/share/zolo-zcli/zConfigs/zConfig.machine.yaml`
- **Windows**: `%APPDATA%/zolo-zcli/zConfigs/zConfig.machine.yaml`

This machine configuration is detected once and stored persistently. You can manually edit tool preferences (browser, IDE, terminal, shell) and resource limits (cpu_cores_limit, memory_gb_limit) directly in this file. For details on editing configuration, see the [Persist Configuration Changes](#persist-configuration-changes) section in the Appendix.

**Access machine configuration:**

```python
zSpark = {
    "deployment": "Production",
    "title": "machine-demo",
    "logger": "INFO",
    "logger_path": "./logs",
}
z = zOS(zSpark)

# Get all machine values at once
machine = z.config.get_machine()
print(f"OS: {machine.get('os')}")
print(f"CPU cores: {machine.get('cpu_cores')}")
print(f"Python: {machine.get('python_version')}")

# Or get a single value directly
hostname = z.config.get_machine("hostname")
```

**🎯 Try it yourself:**

See all 42 machine properties organized by category:

```bash
python3 Demos/Layer_0/zConfig_Demo/lvl3_get/1_zmachine.py
```

[View demo source →](../Demos/Layer_0/zConfig_Demo/lvl3_get/1_zmachine.py)

**What you'll discover:**
- **10 logical categories**: Hardware (System, CPU, Memory, GPU, Network) → Environment (User, Tools) → Software (Python, zOS) → Settings
- **Metal-aware detection**: P-cores vs E-cores on Apple Silicon
- **GPU capabilities**: Type, vendor, VRAM, compute APIs (Metal, CUDA, ROCm)
- **Network awareness**: 6 essential properties (interfaces, primary, local IP, MAC, gateway, public IP)
- **Resource limits**: Optional cpu_cores_limit and memory_gb_limit for containers/VMs
- **Production-ready** for ML, compute, and network-intensive applications
- **Copy-paste ready** accessor patterns for any property

Below are **all zMachine properties** available via `z.config.get_machine()`:

| Category | Property | Description |
|----------|----------|-------------|
| **System Identity** | os | macOS (Darwin), Linux, Windows |
| | os_name | Full OS name with version |
| | os_version | Kernel release (e.g., 24.5.0) |
| | hostname | Machine name |
| | architecture | x86_64, arm64, aarch64 |
| | processor | CPU model/type |
| **CPU Architecture** | cpu_cores | Total CPU cores (backward compatibility) |
| | cpu_physical | Physical CPU cores |
| | cpu_logical | Logical cores (with hyperthreading) |
| | cpu_performance | P-cores (Performance, Apple Silicon only) |
| | cpu_efficiency | E-cores (Efficiency, Apple Silicon only) |
| **Memory** | memory_gb | Total RAM via psutil or OS-specific methods |
| **GPU Capabilities** | gpu_available | GPU detected (true/false) |
| | gpu_type | GPU model name (e.g., Apple M1, NVIDIA RTX 3090) |
| | gpu_vendor | GPU vendor (Apple, NVIDIA, AMD, Intel) |
| | gpu_memory_gb | GPU memory (VRAM) in GB |
| | gpu_compute | Supported compute APIs (e.g., Metal, CUDA) |
| **Network** | network_interfaces | List of all network interface names |
| | network_primary | Active/primary network interface |
| | network_ip_local | Local IP address (primary interface) |
| | network_mac_address | MAC address (primary interface) |
| | network_gateway | Default gateway/router IP address |
| | network_ip_public | Public IP address (optional, may be None) |
| **User & Paths** | username | From USER or USERNAME env var |
| | home | User's home path |
| | cwd | Current directory (safe) |
| | user_data_dir | OS-native zOS support folder path |
| | path | Full PATH environment variable |
| **Development Tools** | ✏️ browser | Chrome, Firefox, Arc, Safari, Brave, Edge, Opera |
| | ✏️ ide | Cursor, VS Code, Sublime, Vim, Nano, Fleet, Zed, PyCharm, WebStorm |
| | ✏️ terminal | From TERM environment variable |
| | ✏️ shell | bash, zsh, fish, sh |
| **Python Runtime** | python_version | 3.12.0, 3.11.5, etc. |
| | python_impl | CPython, PyPy, Jython |
| | python_build | Build identifier |
| | python_compiler | Compiler used to build Python |
| | python_executable | Path to Python executable |
| | libc_ver | System C library version |
| **zOS Installation** | zcli_install_path | Where zOS package is installed |
| | zcli_install_type | editable (development) or standard |
| **System Settings** | lang | System locale (en_US.UTF-8, etc.) |
| | timezone | From TZ or system default |
| **Resource Limits** | ✏️ cpu_cores_limit | Limit CPU cores for pools/threads (soft limits, all platforms) |
| | ✏️ memory_gb_limit | Limit RAM for caches/buffers (soft limits, Linux hard enforcement) |

> ✏️ = Editable (user preferences or resource limits) | All others are auto-detected facts

**Note on editing zMachine values:**  
Editable zMachine values (tool preferences and resource limits) can be modified in three ways:
1. **zShell commands** (recommended) - See [zShell Guide](zShell_GUIDE.md) for `config set` and related commands
2. **Manual YAML editing** - Edit `zConfig.machine.yaml` directly
3. **Programmatic API** (advanced) - See [Persist Configuration Changes](#persist-configuration-changes) in the Appendix

The recommended approach is using **zShell commands** for interactive changes or **manual editing** for batch modifications.

---

### ii. Read Environment Values

While **zMachine** identifies your hardware and tools, **zEnvironment** defines your working context.  
Are you in Development mode? Testing? Production? What logging level do you need?  

Your environment settings persist across all projects, stored alongside zMachine:

- **macOS**: `~/Library/Application Support/zolo-zcli/zConfigs/zConfig.environment.yaml`
- **Linux**: `~/.local/share/zolo-zcli/zConfigs/zConfig.environment.yaml`
- **Windows**: `%APPDATA%/zolo-zcli/zConfigs/zConfig.environment.yaml`

This means you set your deployment mode once (e.g., "Production") and every zOS project respects it by default.

**Access environment configuration:**

```python
zSpark = {
    "deployment": "Production",
    "title": "environment-demo",
    "logger": "INFO",
    "logger_path": "./logs",
}
z = zOS(zSpark)

# Get all environment values at once
env = z.config.get_environment()

# Access top-level values directly
deployment = env.get('deployment')

# Access nested/grouped values (two methods):
# Method 1: Step by step
logging_dict = env.get('logging', {})
log_level = logging_dict.get('level')

# Method 2: Chained access (one line)
log_level = env.get('logging', {}).get('level')

# Or get a single top-level value directly (shortcut)
deployment = z.config.get_environment("deployment")
```

**Note:** This example demonstrates the **5-layer configuration hierarchy** in action! By setting `deployment: "Production"` in zSpark, we override whatever is stored in `zConfig.environment.yaml` for this session only. This is the highest priority layer, giving you programmatic control without modifying persistent configuration files.

**🎯 Try it yourself:**

See all environment properties organized by category:

```bash
python3 Demos/Layer_0/zConfig_Demo/lvl3_get/2_environment.py
```

[View demo source →](../Demos/Layer_0/zConfig_Demo/lvl3_get/2_environment.py)

**What you'll discover:**
- **6 categories**: Deployment, Logging, Network, Security, Performance, WebSocket
- **Deployment modes**: Development, Testing, Production (controls app behavior)
- **5-layer hierarchy in action**: See zSpark override environment.yaml (highest priority!)
- **Settings persistence**: Shared across all projects
- **Custom fields**: Add your own (datacenter, cluster, node_id, etc.)
- **Copy-paste ready** accessor patterns for any property

Below are **all zEnvironment properties** available via `z.config.get_environment()`:

| Category | Property | Description |
|----------|----------|-------------|
| **Deployment Context** | deployment | Development, Testing, Production |
| | datacenter | local, us-west-2, eu-central-1, etc. |
| | cluster | single-node, multi-node, k8s-cluster |
| | node_id | Unique identifier for this node |
| | role | development, staging, production |
| **Network** | network.host | Bind address (default: 127.0.0.1) |
| | network.port | Service port (default: 56891) |
| | network.external_host | External access hostname |
| | network.external_port | External access port |
| **WebSocket** | websocket.host | WebSocket bind address |
| | websocket.port | WebSocket port |
| | websocket.require_auth | Require authentication (true/false) |
| | websocket.allowed_origins | List of allowed CORS origins |
| | websocket.max_connections | Maximum concurrent connections |
| | websocket.ping_interval | Ping interval in seconds |
| | websocket.ping_timeout | Ping timeout in seconds |
| **Security** | security.require_auth | Require authentication |
| | security.allow_anonymous | Allow anonymous access |
| | security.ssl_enabled | Enable SSL/TLS |
| | security.ssl_cert_path | Path to SSL certificate |
| | security.ssl_key_path | Path to SSL private key |
| **Logging** | logging.level | DEBUG, INFO, WARNING, ERROR, CRITICAL |
| | logging.format | simple, detailed, json |
| | logging.file_enabled | Enable file logging (true/false) |
| | logging.file_path | Log file path |
| | logging.max_file_size | Max log file size (e.g., 10MB) |
| | logging.backup_count | Number of backup log files |
| **Performance** | performance.max_workers | Max concurrent workers |
| | performance.cache_size | Cache size limit |
| | performance.cache_ttl | Cache time-to-live in seconds |
| | performance.timeout | Default timeout in seconds |
| **Custom Fields** | custom_field_1 | User-defined value |
| | custom_field_2 | User-defined value |
| | custom_field_3 | User-defined value (can be list/dict)

**Note:** All environment settings are user-configurable

---

### iii. Read Workspace Variables (Dotenv)

So far you've learned about **zMachine** (Layer 2: hardware) and **zEnvironment** (Layer 3: global context). Now let's explore **Layer 4** in the configuration hierarchy.

**Quick reminder - The 5 Configuration Layers:**

| Priority | Layer | Source | What |
|----------|-------|--------|------|
| 1 (lowest) | Defaults | Package | Fallback values |
| 2 | zMachine | Config file | Auto-detected hardware |
| 3 | zEnvironment | Config file | Global deployment settings |
| **4** | **Dotenv** | **.env/.zEnv** | **Workspace-specific variables** |
| 5 (highest) | zSpark | Your code | Runtime overrides |

**Layer 4** is where workspace-specific variables live. These come from **dotenv files** (`.env` / `.zEnv`) that zOS automatically loads from your project folder.

This is a standard **computer science convention** - without the need to import `python-dotenv`!

**Perfect for:** API keys, secrets, feature flags, project-specific settings.

**Access workspace variables:**

```python
# .zEnv or .env file in your project folder (auto-loaded by zOS)
# APP_NAME=My Application
# API_KEY=secret_key_123
# DEBUG_MODE=true

zSpark = {
    "deployment": "Production",
    "title": "dotenv-demo",
    "logger": "INFO",
    "logger_path": "./logs",
}
z = zOS(zSpark)

# Get values with fallback defaults
app_name = z.config.environment.get_env_var("APP_NAME", "Unknown")
api_key = z.config.environment.get_env_var("API_KEY")
debug_mode = z.config.environment.get_env_var("DEBUG_MODE", "false").lower() == "true"
```

**🎯 Try it yourself:**

See dotenv loading in action:

```bash
cd Demos/Layer_0/zConfig_Demo/lvl3_get
python3 3_dotenv.py
```

[View demo source →](../Demos/Layer_0/zConfig_Demo/lvl3_get/3_dotenv.py)

**What you'll discover:**
- **Dotenv convention** - Standard `.env` / `.zEnv` files auto-load
- **No imports needed** - No `python-dotenv` import required
- **Workspace-specific** - Different projects = different dotenv files
- **Fallback defaults** - Provide default values if key doesn't exist
- **Perfect for secrets** - Add dotenv files to `.gitignore` for API keys
- **Layer 4 priority** - Overrides global config, overridden by zSpark

**Important:**
- zOS looks for `.zEnv` (preferred) or `.env` in your current working directory
- `.zEnv` wins if both files exist
- **Always add these files to `.gitignore` if they contain secrets!**
- Use for project-specific values that shouldn't be hardcoded

---

### iv. Read Session Values

**zMachine** is your hardware, **zEnvironment** is your context, **Dotenv** is your workspace, and **zSession** is your runtime.

**zSession** holds ephemeral state created during initialization - values like `zMode`, `zSpace`, `zLogger`, and your `zSpark` dictionary. Unlike zMachine and zEnvironment configs, **zSession exists only in memory during your program's runtime**.

**Access session configuration:**

```python
zSpark = {
    "deployment": "Production",
    "title": "session-demo",
    "logger": "INFO",
    "logger_path": "./logs",
    "zTraceback": True,
}
z = zOS(zSpark)

# Get session dictionary
session = z.session

# Access runtime values
session_id = session.get('zS_id')
mode = session.get('zMode')
logger_level = session.get('zLogger')

# Access your original zSpark dictionary
zspark_stored = session.get('zSpark')
```

**What's in session:**
- **Identity**: `zS_id`, `title` (runtime identifiers)
- **Configuration**: `zMode`, `zSpace`, `zLogger`, `logger_path`, `zTraceback`
- **Your zSpark**: Original dictionary stored for reference
- **Environment**: `virtual_env`, `system_env` (OS environment variables)
- **Custom vars**: `zVars` (user-defined runtime variables)

**🎯 Try it yourself:**

See all session properties organized by category:

```bash
python3 Demos/Layer_0/zConfig_Demo/lvl3_get/4_zsession.py
```

[View demo source →](../Demos/Layer_0/zConfig_Demo/lvl3_get/4_zsession.py)

**What you'll discover:**
- **Runtime state**: Values created during initialization
- **Ephemeral**: Exists only in memory (not persisted)
- **zSpark reference**: Your original configuration dictionary stored
- **System integration**: Access to virtual environments and system env vars
- **Copy-paste ready** accessor patterns for any value

Below are **all zSession properties** available via `z.session`:

| Category | Property | Description |
|----------|----------|-------------|
| **Session Identity** | zS_id | Unique session identifier (auto-generated) |
| | title | Session title (from zSpark or script filename) |
| **Runtime Configuration** | zMode | Execution mode (Terminal, Bifrost, etc.) |
| | zSpace | Workspace path (current working directory) |
| | zLogger | Active logger level (DEBUG, INFO, etc.) |
| | logger_path | Directory where application logs are stored |
| | zTraceback | Exception handling enabled (True/False) |
| **zSpark Reference** | zSpark | Original zSpark dictionary as provided |
| **Environment Integration** | virtual_env | Virtual environment path (if active, else None) |
| | system_env | Full system environment variables (dict) |
| **Custom Variables** | zVars | User-defined runtime variables (dict) |

**Note:** All session values are read-only runtime state. They exist only in memory and are not persisted to disk.

---

**🎯 Level 3 Complete!**

You've learned to **read** all three configuration sources: **zMachine** (hardware), **zEnvironment** (context), and **zSession** (runtime). In Level 4, you'll master the **5-layer hierarchy** and understand how these sources interact, including workspace-specific `.zEnv` files and configuration persistence.

---

# **zConfig - Level 4** (Use Case)

### **System Requirements Checker - The 5-Layer Hierarchy in Action**

Time to put everything together! Let's build a **real app** that every developer needs: a system requirements checker.

**What it does:**  
Checks if your computer meets the minimum requirements for a project. Think ML training, game development, or any compute-intensive application - they all need to validate your hardware before letting you proceed.

**The problem it solves:**  
Instead of hardcoding requirements like "needs 8GB RAM" directly in your code, you define them in a `.zEnv` file. The app then:
1. Reads requirements from `.zEnv` (what you need)
2. Gets actual specs from zMachine (what you have)
3. Compares them and tells you if you're ready to go

**Why this is a perfect demo:**  
Every configuration layer has a role - **Layer 2** provides hardware specs, **Layer 3** sets deployment mode, **Layer 4** defines project requirements, and **Layer 5** allows runtime overrides.

---

**The 5-Layer Hierarchy** (highest priority wins):

| Priority | Source | What | Where | Example |
|----------|--------|------|-------|---------|
| **5 (highest)** | **zSpark** | Runtime overrides | Your code | `zOS({"deployment": "Production"})` |
| **4** | **.zEnv** | Workspace secrets | Project folder | `MIN_CPU_CORES=4` |
| **3** | **zEnvironment** | Global settings | Config file | `deployment: Development` |
| **2** | **zMachine** | Hardware specs | Config file | `cpu_cores: 8` (auto-detected) |
| **1 (lowest)** | **Defaults** | Fallback values | Package | `deployment: Development` |

### **The App: System Requirements Checker**

Now let's see all 5 layers working together in a real app!

```python
zSpark = {
    "deployment": "Production",  # Layer 5: Override global deployment
    "title": "system-checker",
    "logger": "INFO",
    "logger_path": "./logs",
}
z = zOS(zSpark)

# Get requirements from .zEnv (Layer 4 - workspace-specific)
min_cores = int(z.config.environment.get_env_var("MIN_CPU_CORES", "2"))
min_memory = int(z.config.environment.get_env_var("MIN_MEMORY_GB", "4"))
project_name = z.config.environment.get_env_var("PROJECT_NAME", "Unknown")

# Get actual hardware from zMachine (Layer 2 - auto-detected)
machine = z.config.get_machine()
actual_cores = machine.get('cpu_cores')
actual_memory = machine.get('memory_gb')

# Compare and report
print(f"Checking {project_name}...")
print(f"CPU: {actual_cores} cores (need {min_cores}) - {'✅ PASS' if actual_cores >= min_cores else '❌ FAIL'}")
print(f"RAM: {actual_memory}GB (need {min_memory}GB) - {'✅ PASS' if actual_memory >= min_memory else '❌ FAIL'}")
```

**🎯 Try it yourself:**

Run the complete system checker:

```bash
python3 Demos/Layer_0/zConfig_Demo/lvl4_usecase/1_system_checker.py
```

[View demo source →](../Demos/Layer_0/zConfig_Demo/lvl4_usecase/1_system_checker.py)

**What you'll discover:**
- **Layer 5 (zSpark)**: Runtime override for deployment mode
- **Layer 4 (.zEnv)**: Project-specific requirements (CPU, RAM, Python, GPU)
- **Layer 3 (zEnvironment)**: Global deployment settings
- **Layer 2 (zMachine)**: Auto-detected hardware specs
- **Real-world use**: System validation, environment checks, deployment readiness

**Try modifying `.zEnv`:**
- Change `MIN_CPU_CORES=16` to fail the check
- Change `REQUIRED_GPU=false` to remove GPU requirement
- Add your own requirements

**The `.zEnv` file:**
```bash
# Project: ML Training Pipeline
PROJECT_NAME=ML Training Pipeline
PROJECT_VERSION=2.1.0

# Hardware Requirements
MIN_CPU_CORES=4
MIN_MEMORY_GB=8
REQUIRED_GPU=true

# Software Requirements
MIN_PYTHON_VERSION=3.11
```

This is **Layer 4** - workspace-specific configuration that travels with your project. Perfect for:
- System requirements
- API keys and secrets (add to `.gitignore`!)
- Environment-specific settings
- Team-shared defaults

---

**🎯 Level 4 Complete!**

You've completed the entire zConfig tutorial journey:
- ✅ **Level 1**: Initialization and deployment modes
- ✅ **Level 2**: Logging and error handling
- ✅ **Level 3**: Reading configuration (machine, environment, workspace, session)
- ✅ **Level 4**: Real-world app using all 5 layers

**You now understand the complete zConfig subsystem and the 5-layer configuration hierarchy!**

---

### So Why Use zOS? 
Declarative vs Imperative - Let's compare what you just **built decleratively** to the **traditional imperative approach**.

### **Your zOS App (Level 4 Demo)**

**Files:** 1 Python file + 1 .zEnv file  
**Lines of code:** ~130 lines total (heavily commented for learning)  
**Actual logic:** ~60 lines

```python
from zOS import zOS

z = zOS({"deployment": "Production", "logger": "INFO"})

# Everything just works:
# ✓ Hardware detection (42 properties)
# ✓ Dotenv loading (.env/.zEnv)
# ✓ Logger configured (console + file)
# ✓ Cross-platform paths
# ✓ Configuration hierarchy (5 layers)

min_cores = int(z.config.environment.get_env_var("MIN_CPU_CORES", "2"))
actual_cores = z.config.get_machine("cpu_cores")
```

### **Traditional Imperative Approach**

To achieve the same functionality without zOS:

**Files needed:** 8+ files  
**Lines of code:** ~800-1000+ lines  
**External dependencies:** 6+ packages

```
project/
├── config_loader.py         # ~150 lines - YAML/JSON parsing
├── env_loader.py            # ~80 lines - dotenv implementation
├── machine_detector.py      # ~300 lines - CPU, GPU, network detection
├── logger_setup.py          # ~120 lines - logging configuration
├── path_manager.py          # ~100 lines - cross-platform paths
├── config_hierarchy.py      # ~150 lines - layer resolution logic
├── requirements.txt         # python-dotenv, psutil, pyyaml, etc.
└── main.py                  # Your actual app logic
```

**What you'd need to manually implement:**

1. **Machine Detection** (~300 lines)
   - CPU detection (cores, architecture, P-cores, E-cores)
   - GPU detection (vendor, VRAM, compute APIs)
   - Network detection (interfaces, IPs, MAC, gateway)
   - Python runtime detection
   - Cross-platform compatibility

2. **Configuration Management** (~150 lines)
   - YAML file parsing
   - Config file discovery (OS-specific paths)
   - 5-layer hierarchy resolution
   - Defaults → Machine → Environment → Dotenv → Runtime

3. **Dotenv Loading** (~80 lines)
   - File discovery (.env vs .zEnv)
   - Parsing key=value pairs
   - Type conversion (strings → int/bool)
   - Or install `python-dotenv` dependency

4. **Logging Setup** (~120 lines)
   - Console handler configuration
   - File handler with rotation
   - Separate app vs framework logs
   - Deployment-aware log levels
   - Custom log file naming per script

5. **Path Management** (~100 lines)
   - OS detection (macOS, Linux, Windows)
   - Application support folder detection
   - Cross-platform path resolution
   - Directory creation with permissions

6. **Error Handling** (~50 lines)
   - sys.excepthook installation
   - Traceback formatting
   - Interactive error menus

**Total:** ~800-1000 lines of infrastructure code **before** you write your app logic.

### **The zOS Advantage**

| Aspect | zOS (Declarative) | Traditional (Imperative) |
|--------|-------------------|--------------------------|
| **Lines of code** | ~60 lines | ~800-1000 lines |
| **Files** | 1-2 files | 8+ files |
| **Dependencies** | `zolo-zcli` (1 package) | 6+ packages |
| **Maintenance** | Framework handles it | You maintain all of it |
| **Cross-platform** | Automatic | Manual OS detection |
| **Learning curve** | 4 tutorial levels | Weeks of docs/Stack Overflow |
| **Time to first app** | Minutes | Days/weeks |

### **Key Benefits**

1. **Declarative Magic**: `z = zOS()` - everything is ready
2. **Zero Boilerplate**: No config file parsing, no path handling, no logger setup
3. **Production-Ready**: Metal-aware detection, resource limits, dual loggers
4. **Maintained**: Framework updates benefit all apps automatically
5. **Consistent**: Same patterns across all subsystems (18 total!)

### **From Imperative to Declarative**

This is just **subsystem #1 of 18**. As you progress through zOS's architecture:
- **Layer 0** (zConfig, zComm) - Configuration and communication
- **Layer 1** (zDisplay, zAuth, zDispatch) - Display, auth, and command dispatch  
- **Layer 2** (zParser, zLoader, zUtils, zFunc) - Parsing and utilities
- **Layer 3** (zDialog, zOpen, zWizard, zData, zShell, zWalker, zServer) - Orchestration

You'll see the imperative-to-declarative shift become even more powerful. What traditionally takes thousands of lines becomes a few declarative configurations.

**That's the zOS philosophy: Focus on WHAT you want, not HOW to build it.**

---

## What's Next?

You've mastered **zConfig** (configuration and machine context). Now it's time to learn **zComm** - the communications hub that handles WebSocket connections and HTTP clients, enabling real-time data flow and API interactions with the same declarative simplicity.

**→ Continue to [zComm Guide](zComm_GUIDE.md)**

---

# Appendix: Advanced Configuration

### Persist Configuration Changes

> **Note:** The programmatic persistence API shown below is **not the recommended way** to modify configuration. Use **[zShell commands](zShell_GUIDE.md)** (interactive CLI) or **manual YAML editing** instead. This API exists for advanced use cases and backward compatibility.

Values from zMachine and zEnvironment can be saved permanently using the persistence API. These changes survive across all projects and sessions.

```python
# Save to ~/Library/.../zConfig.machine.yaml
z.config.persistence.persist_machine("browser", "Firefox")
z.config.persistence.persist_machine("ide", "cursor")

# Save to ~/Library/.../zConfig.environment.yaml
z.config.persistence.persist_environment("deployment", "Production")
z.config.persistence.persist_environment("custom_field_1", "my_value")
```

**Which Keys Are Editable?**

Machine config:
- ✅ **Editable**: 
  - browser, ide, terminal, shell (user tool preferences)
  - cpu_cores_limit, memory_gb_limit (resource allocation limits)
- 🔒 **Locked**: os, hostname, architecture, cpu_cores, memory_gb, python_version, processor, gpu_type, etc. (auto-detected hardware facts)

Environment config:
- ✅ **All keys editable**: `deployment`, `role`, `custom_field_1/2/3`, etc.

**Recommended Methods for Configuration Changes:**

1. **zShell Commands (Recommended):**
   ```bash
   # Interactive command-line interface
   zcli config set browser Firefox
   zcli config set deployment Production
   ```
   See [zShell Guide](zShell_GUIDE.md) for full command reference.

2. **Manual YAML Editing:**
   Edit the files directly in your text editor:
- `~/Library/Application Support/zolo-zcli/zConfigs/zConfig.machine.yaml`
- `~/Library/Application Support/zolo-zcli/zConfigs/zConfig.environment.yaml`

⚠️ **Warning:** Only edit the **editable** keys listed above. Modifying locked machine values (like `os`, `python_version`, `architecture`) may cause crashes or unexpected behavior.

3. **Programmatic API (Advanced):**
   Use the persistence API shown above for scripting or automation scenarios only.



---

**Resource Limits Implementation:**

Resource limits (`cpu_cores_limit`, `memory_gb_limit`) are **fully implemented** and work cross-platform:

- **Soft Limits (All Platforms)**: Application code can query limits via `z.config.get_cpu_limit()` and `z.config.get_memory_limit_gb()` to voluntarily respect resource constraints
- **Hard Limits (Linux Only)**: OS enforces limits - process is killed if exceeded (uses `resource.setrlimit()` and `os.sched_setaffinity()`)
- **Use Cases**: Multiprocessing pool sizing, cache management, Docker/K8s hints, shared systems

**Example usage:**
```python
# Query limits
cpu_limit = z.config.get_cpu_limit()
memory_limit_gb = z.config.get_memory_limit_gb()

# Apply to multiprocessing
import multiprocessing
pool = multiprocessing.Pool(processes=cpu_limit)

# Apply to cache sizing
cache_size = int(memory_limit_gb * 0.25 * 1024**3)  # 25% of limit
```

**To set limits**, edit `zConfig.machine.yaml` and uncomment:
```yaml
cpu_cores_limit: 4      # Limit to 4 cores
memory_gb_limit: 8      # Limit to 8 GB
```

---

**[← Back to zInstall Guide](zInstall_GUIDE.md) | [Home](../README.md) | [Next: zComm Guide →](zComm_GUIDE.md)**
