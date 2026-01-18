# zFunc Subsystem Guide

## Overview

**zFunc** is zOS's **Function Execution & Python Integration** subsystem. It enables dynamic loading and execution of Python functions from plugins, external files, or inline code, with intelligent argument parsing, automatic dependency injection, and context-aware parameter resolution.

### Executive Summary
zFunc is the bridge between zOS's declarative YAML configuration and Python's imperative code. It allows developers to call any Python function using a simple path syntax, while automatically injecting framework dependencies (like `zcli`, `session`) and context data (like `zHat`, `zConv`) based on function signatures. This eliminates boilerplate and makes extending zOS applications seamless.

**Key Value**: Write Python functions naturally, call them from YAML, and let zFunc handle all the wiring automatically.

---

## Architecture

### 4-Tier Design

```
┌─────────────────────────────────────────┐
│  Root (__init__.py)                     │  ← Public entry point
│  • zFunc() constructor                  │
└─────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│  Facade (zFunc.py)                      │  ← Main orchestration
│  • handle(zHorizontal, zContext)        │
│  • Delegates to modules below           │
└─────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│  Aggregator (zFunc_modules/__init__)    │  ← Module coordination
│  • Imports & exposes all modules        │
└─────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│  Foundation (Individual Modules)        │  ← Core logic
│  • func_resolver.py                     │
│  • func_args.py                         │
└─────────────────────────────────────────┘
```

**Design Principle**: Each tier has a single responsibility, making the system modular, testable, and maintainable.

---

## Core Features

### 1. Dynamic Function Loading
Load and execute Python functions from anywhere:
- **Plugins**: `&my_plugin.my_function()`
- **zPaths**: `@.utils.helpers:calculate()`
- **Absolute paths**: `/path/to/file.py:process()`

```yaml
# In zUI file
calculate_total:
  zFunc: "&invoice_plugin.calculate_total(invoice_id, tax_rate=0.08)"
```

### 2. Intelligent Argument Parsing
Handles complex argument structures:
- **Nested brackets**: `func([1, 2], {"key": "val"})`
- **String literals**: `func("hello", 'world')`
- **JSON expressions**: Safely evaluates JSON via zParser
- **Bracket matching**: Respects parentheses, square, curly braces

### 3. Auto-Injection
Automatically injects framework dependencies based on function signature:

```python
# Your function
def my_function(zcli, session, value):
    return zcli.config.get_setting(value)

# In YAML - zcli and session auto-injected
my_key:
  zFunc: "&my_plugin.my_function(42)"
```

**Supported Parameters**:
- `zcli` - Full zOS instance
- `session` - Session dictionary
- `context` - Current execution context

### 4. Context Injection (5 Special Types)
Access wizard/dialog data using special argument notation:

#### zContext - Full context dictionary
```python
def process(zContext):
    return zContext.get("user_id")
```

#### zHat - Accumulated wizard results
```python
def display_results(zHat):
    all_results = [zHat[i] for i in range(len(zHat))]
    return format_summary(all_results)
```

#### zConv - Dialog conversation data
```python
def greet_user(zConv):
    return f"Hello, {zConv.get('username')}!"
```

#### zConv.field - Specific dialog field
```python
def validate_email(email):  # email = context['zConv']['email']
    return is_valid_email(email)

# In YAML
validate:
  zFunc: "&validators.validate_email(zConv.email)"
```

#### this.key - Context field value
```python
def double_value(value):
    return value * 2

# In YAML (context has user_id: 21)
process:
  zFunc: "&math_utils.double_value(this.user_id)"  # Passes 21
```

### 5. Async Support
Automatically detects and executes async functions:

```python
async def fetch_data(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()
```

**Execution**:
- **Terminal mode**: Uses `asyncio.run()`
- **Bifrost mode**: Uses `run_coroutine_threadsafe()`

### 6. Result Display
Formats and displays function results with colored JSON output:
- Dictionaries → Pretty-printed JSON
- Lists → Formatted arrays
- Primitives → Direct display
- None → Silent (no output)

---

## Public API

### Main Method: `handle(zHorizontal, zContext=None)`

The only public method you need.

**Parameters**:
- `zHorizontal` (str): Function path with optional arguments
  - Format: `path/to/file.py:function_name(arg1, arg2, key=val)`
  - Or: `&plugin.function(args)`
  - Or: `@.module:function(args)`
- `zContext` (dict, optional): Execution context for injection

**Returns**: Function result (any type)

**Example**:
```python
zcli = zOS({'zWorkspace': '.'})

# Simple call
result = zcli.zfunc.handle("&calculator.add(5, 3)")

# With context
context = {"user_id": 123, "zConv": {"name": "Alice"}}
greeting = zcli.zfunc.handle("&greeter.greet(zConv.name)", context)
```

---

## Usage Examples

### Example 1: Simple Plugin Function
```python
# plugins/calculator.py
def add(a, b):
    return a + b

def multiply(a, b):
    return a * b
```

```yaml
# zUI file
calculations:
  add_numbers:
    zFunc: "&calculator.add(10, 20)"
  multiply_numbers:
    zFunc: "&calculator.multiply(5, 6)"
```

### Example 2: Auto-Injection
```python
# plugins/user_manager.py
def get_user_setting(setting_name, zcli):
    """zcli is auto-injected"""
    return zcli.config.get(setting_name)
```

```yaml
# zUI file
fetch_setting:
  zFunc: "&user_manager.get_user_setting('theme')"
  # zcli automatically injected - no need to pass it!
```

### Example 3: Context Injection in zWizard
```python
# plugins/report_generator.py
def generate_report(zHat):
    """Receives accumulated wizard results"""
    all_steps = [zHat[i] for i in range(len(zHat))]
    return {"total_items": len(all_steps), "data": all_steps}
```

```yaml
# zUI file
zVaF:
  zWizard:
    step1:
      zFunc: "&data_collector.collect_item1()"
    step2:
      zFunc: "&data_collector.collect_item2()"
    step3:
      zFunc: "&data_collector.collect_item3()"
    generate_summary:
      zFunc: "&report_generator.generate_report()"
      # zHat automatically contains results from step1, step2, step3
```

### Example 4: Dialog Field Extraction
```python
# plugins/validators.py
def validate_age(age):
    """age is extracted from zConv.age"""
    return age >= 18 and age <= 120
```

```yaml
# zUI file with zDialog
collect_info:
  zDialog:
    age_input:
      zInput: "Enter your age"
  
  validate:
    zFunc: "&validators.validate_age(zConv.age)"
    # Passes the age value from dialog
```

### Example 5: Async Function
```python
# plugins/api_client.py
import aiohttp

async def fetch_user(user_id):
    """Async function - automatically detected"""
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://api.example.com/users/{user_id}") as resp:
            return await resp.json()
```

```yaml
# zUI file
get_user:
  zFunc: "&api_client.fetch_user(123)"
  # zFunc detects async and uses asyncio.run() automatically
```

---

## Integration with Other Subsystems

### zParser Integration
- **Path Resolution**: Uses `parse_function_path()` to resolve zPaths and plugin names
- **Argument Evaluation**: Uses `parse_json_expr()` for safe JSON evaluation
- **Smart Parsing**: Delegates complex path and argument parsing to zParser

### zDispatch Integration
- **Automatic Routing**: zDispatch detects `zFunc` keys and routes to zFunc handler
- **Modifier Support**: Works with dispatch modifiers (`^`, `~`, etc.)
- **Context Passing**: Receives context from dispatch pipeline

### zLoader Integration
- **Plugin Discovery**: Uses zLoader's plugin paths for function discovery
- **Module Caching**: Benefits from zLoader's module import caching

### zWizard/zWalker Integration
- **zHat Access**: Functions can receive `zHat` with accumulated wizard results
- **Step Execution**: Each wizard step can be a `zFunc` call
- **Context Flow**: Context flows through wizard steps to functions

### zDialog Integration
- **zConv Access**: Functions can access dialog data via `zConv` or `zConv.field`
- **Field Extraction**: Automatic extraction of specific dialog fields
- **Validation**: Functions can validate dialog input

### zDisplay Integration
- **Result Formatting**: Uses zDisplay for colored JSON output
- **Type-Aware**: Different display logic for dict, list, primitive types

---

## Error Handling

### Common Errors

**1. FileNotFoundError**
```
Error: No such file: /path/to/file.py
```
- **Cause**: Function file doesn't exist
- **Fix**: Verify file path or use plugin syntax (`&plugin.func`)

**2. ImportError / ModuleNotFoundError**
```
Error: Cannot import module: my_module
```
- **Cause**: Missing dependencies or import errors in target file
- **Fix**: Install required packages, check import statements

**3. AttributeError**
```
Error: Function 'func_name' not found in module
```
- **Cause**: Function doesn't exist in specified file
- **Fix**: Check function name spelling, ensure it's defined

**4. ValueError**
```
Error: Invalid argument format
```
- **Cause**: Malformed arguments in function call
- **Fix**: Check bracket matching, quote strings properly

**5. TypeError**
```
Error: Missing required positional argument
```
- **Cause**: Function signature doesn't match provided arguments
- **Fix**: Check function signature, provide all required args

---

## Testing Results

### Comprehensive Test Suite: 86 Tests (100% Pass Rate ✅)

**Test Coverage by Category**:
- **A. Facade** (6 tests): Initialization, attributes, dependencies
- **B. Path Parsing** (8 tests): zParser delegation, plugin detection
- **C. Argument Parsing** (14 tests): Bracket matching, JSON evaluation
- **D. Function Resolution** (10 tests): File loading, error handling
- **E. Function Execution** (12 tests): Sync, async, return types
- **F. Auto-Injection** (10 tests): zcli, session, context injection
- **G. Context Injection** (12 tests): zContext, zHat, zConv, field notation
- **H. Result Display** (6 tests): Type-specific formatting
- **I. Integration** (8 tests): End-to-end workflows

**Key Validations**:
- ✅ All 5 special argument types work correctly
- ✅ Async detection and execution verified
- ✅ Auto-injection correctly detects function signatures
- ✅ Bracket matching handles nested structures
- ✅ Error propagation works as expected
- ✅ zParser delegation functions properly

**Test Location**: `zTestRunner/zUI.zFunc_tests.yaml` + `zTestRunner/plugins/zfunc_tests.py`

---

## Best Practices

### 1. Use Plugins for Reusable Functions
```python
# ✅ Good: plugins/calculations.py
def calculate_tax(amount, rate):
    return amount * rate
```

```yaml
# ✅ Good: Use plugin syntax
calculate:
  zFunc: "&calculations.calculate_tax(100, 0.08)"
```

### 2. Leverage Auto-Injection
```python
# ✅ Good: Let zFunc inject dependencies
def get_config(key, zcli):
    return zcli.config.get(key)

# ❌ Bad: Manually passing zcli
```

### 3. Use Context Injection for Wizard Data
```python
# ✅ Good: Use zHat for wizard results
def summarize(zHat):
    return sum(zHat[i]["value"] for i in range(len(zHat)))

# ❌ Bad: Manually tracking results
```

### 4. Use Field Notation for Dialog Data
```yaml
# ✅ Good: Extract specific fields
validate:
  zFunc: "&validators.check_email(zConv.email)"

# ❌ Bad: Pass entire zConv and extract manually
```

### 5. Keep Functions Focused
```python
# ✅ Good: Single responsibility
def calculate_total(items):
    return sum(item["price"] for item in items)

# ❌ Bad: Function does too many things
def do_everything(data, config, session, context, ...):
    # Too many concerns mixed together
```

### 6. Handle Async Naturally
```python
# ✅ Good: Write async when needed
async def fetch_data(url):
    async with aiohttp.ClientSession() as session:
        return await (await session.get(url)).json()

# No special handling needed - zFunc detects async automatically
```

---

## Performance Considerations

### Module Caching
- **First Load**: Module is imported and cached
- **Subsequent Calls**: Uses cached module (faster)
- **Impact**: ~10x speedup for repeated function calls

### Async Optimization
- **Terminal Mode**: Single async operation per call
- **Bifrost Mode**: Concurrent execution in event loop
- **Best Practice**: Use async for I/O-bound operations (API calls, DB queries)

### Argument Parsing
- **Simple Args**: Fast (direct split)
- **Complex Args**: Moderate (bracket matching)
- **JSON Evaluation**: Uses zParser's safe eval (secure)

---

## Troubleshooting

### Function Not Found
**Symptom**: `ValueError: Plugin not found: my_plugin`

**Solution**:
1. Check plugin file exists in `plugins/` directory
2. Verify plugin name matches filename (`my_plugin.py`)
3. Ensure file has `.py` extension
4. Check zWorkspace path is correct

### Auto-Injection Not Working
**Symptom**: `TypeError: missing required positional argument: 'zcli'`

**Solution**:
1. Verify parameter name is exactly `zcli`, `session`, or `context`
2. Check function signature uses correct spelling
3. Ensure auto-injection is enabled (default)

### zHat Returns Empty
**Symptom**: `zHat` has no accumulated results

**Solution**:
1. Verify function is called within `zWizard` block
2. Check previous wizard steps returned values
3. Ensure context is passed through wizard steps

### Async Not Executing
**Symptom**: Function returns coroutine object instead of result

**Solution**:
1. Verify function is declared with `async def`
2. Check asyncio is available
3. Ensure zOS mode supports async (Terminal/Bifrost)

---

## Summary

**zFunc** transforms Python function execution in zOS from manual wiring to automatic orchestration. By intelligently injecting dependencies and extracting context data based on function signatures, it eliminates boilerplate and lets developers focus on business logic.

**When to Use zFunc**:
- ✅ Extending zOS with custom Python logic
- ✅ Processing wizard or dialog results
- ✅ Calling external APIs or services
- ✅ Complex calculations or transformations
- ✅ Integration with third-party libraries

**Key Takeaway**: Write Python functions naturally, declare them in YAML with `zFunc`, and let the framework handle all the complexity.

---

*For more details on related subsystems, see: [zParser_GUIDE.md](zParser_GUIDE.md), [zWizard_GUIDE.md](zWizard_GUIDE.md), [zDialog_GUIDE.md](zDialog_GUIDE.md)*

