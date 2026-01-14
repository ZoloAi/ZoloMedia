# line_parsers.py Refactoring Plan

## Current State: CRITICAL Issues 🚨

**File Size:** 1,172 lines (Target: <500 lines)  
**Duplication:** ~350 lines of identical nested key detection (appears 2x)  
**Complexity:** 775-line function (`parse_lines_with_tokens`)

## Problem Analysis

### 1. Massive Code Duplication (346 lines × 2)
**Lines 219-392 and 514-687:** Nearly identical nested key detection logic

```python
# DUPLICATED SECTION 1 (with type hints) - lines 219-392
if core_key == 'zRBAC':
    ...
elif emitter.is_zspark_file:
    ...
# ... 173 lines of conditionals ...

# DUPLICATED SECTION 2 (without type hints) - lines 514-687
if core_key == 'zRBAC':
    ...
elif emitter.is_zspark_file:
    ...
# ... 173 lines of IDENTICAL conditionals ...
```

**Impact:** 173 lines of duplication = massive maintenance burden

### 2. KeyDetector Not Fully Integrated
- Root keys use KeyDetector ✅ (Phase 2.5)
- **Nested keys still use manual if-elif chains** ❌ (173 lines each!)

### 3. Monolithic Functions
- `parse_lines_with_tokens`: 775 lines (97-872)
- `parse_lines`: 130 lines (875-1005)
- `build_nested_dict`: 118 lines (1007-1124)

## Solution: Phase 2.6 - Complete KeyDetector Integration + Function Extraction

### Step 1: Integrate KeyDetector for Nested Keys (HIGH IMPACT)
**Target:** Lines 219-392 and 514-687 (173 lines each = 346 total)

**BEFORE (173 lines of nested if-elif):**
```python
if core_key == 'zRBAC':
    if emitter.is_zenv_file or emitter.is_zui_file:
        emitter.emit(..., TokenType.ZRBAC_KEY)
    ...
elif emitter.is_zspark_file:
    emitter.emit(..., TokenType.ZSPARK_NESTED_KEY)
elif emitter.is_znavbar_first_level(indent) and emitter.is_zenv_file:
    ...
# ... 165+ more lines ...
else:
    emitter.emit(..., TokenType.NESTED_KEY)
```

**AFTER (~10 lines using KeyDetector):**
```python
# Detect token type using KeyDetector
token_type = KeyDetector.detect_nested_key(core_key, emitter, indent)
emitter.emit(original_line_num, current_pos, len(core_key), token_type)

# Check for block entry
block_type = KeyDetector.should_enter_block(core_key, emitter)
if block_type:
    # Enter appropriate block (already implemented in KeyDetector)
```

**Expected Savings:** 346 lines → ~20 lines = **-326 lines (-94%)**

### Step 2: Extract Key Processing Helper Function
Create `_process_key_with_modifiers()` to handle the repeated pattern:

**Pattern appears 4 times in file:**
```python
prefix_mods, core_key, suffix_mods = emitter.split_modifiers(clean_key)
current_pos = key_start

# Emit prefix modifiers
for mod in prefix_mods:
    if emitter.is_zenv_file or emitter.is_zui_file:
        emitter.emit(..., TokenType.ZRBAC_OPTION_KEY)
    current_pos += 1

# ... detect and emit key ...

# Emit suffix modifiers
for mod in suffix_mods:
    if emitter.is_zenv_file or emitter.is_zui_file:
        emitter.emit(..., TokenType.ZRBAC_OPTION_KEY)
    current_pos += 1
```

**Extract to:**
```python
def _process_key_with_modifiers(
    key: str,
    line: int,
    key_start: int,
    emitter: 'TokenEmitter',
    is_root: bool,
    indent: int
) -> None:
    """Process key with modifiers (^~!*) and emit tokens."""
    prefix_mods, core_key, suffix_mods = emitter.split_modifiers(key)
    current_pos = key_start
    
    # Emit prefix modifiers
    for mod in prefix_mods:
        if emitter.is_zenv_file or emitter.is_zui_file:
            emitter.emit(line, current_pos, 1, TokenType.ZRBAC_OPTION_KEY)
        current_pos += 1
    
    # Detect and emit key using KeyDetector
    if is_root:
        token_type = KeyDetector.detect_root_key(core_key, emitter, indent)
        # Handle root-level diagnostics (zSub, zRBAC errors)
    else:
        token_type = KeyDetector.detect_nested_key(core_key, emitter, indent)
    
    emitter.emit(line, current_pos, len(core_key), token_type)
    current_pos += len(core_key)
    
    # Emit suffix modifiers
    for mod in suffix_mods:
        if emitter.is_zenv_file or emitter.is_zui_file:
            emitter.emit(line, current_pos, 1, TokenType.ZRBAC_OPTION_KEY)
        current_pos += 1
    
    # Handle block entry
    block_type = KeyDetector.should_enter_block(core_key, emitter)
    if block_type:
        # Enter blocks (already implemented)
```

**Expected Savings:** ~80 lines (4 occurrences of ~20 lines each)

### Step 3: Extract Value Handling Logic (OPTIONAL)
The value handling logic (lines 698-866) could be extracted to `_handle_value_emission()`:
- Multi-line (str) values
- Multi-line arrays
- Dash lists
- Regular values

**Expected Savings:** ~170 lines

## Implementation Plan

### Phase 2.6.1: Integrate KeyDetector for Nested Keys (CRITICAL)
**Impact:** -326 lines (-94% complexity reduction)

1. Replace lines 219-392 with KeyDetector.detect_nested_key()
2. Replace lines 514-687 with KeyDetector.detect_nested_key()
3. Update block entry logic to use KeyDetector.should_enter_block()
4. Test all 162 tests still pass

### Phase 2.6.2: Extract Key Processing Helper (HIGH)
**Impact:** -80 lines

1. Create `_process_key_with_modifiers()` function
2. Replace 4 occurrences with function call
3. Test all 162 tests still pass

### Phase 2.6.3: Extract Value Handling (OPTIONAL)
**Impact:** -170 lines

1. Create `_handle_value_emission()` function
2. Simplify parse_lines_with_tokens()
3. Test all 162 tests still pass

## ✅ ACTUAL RESULTS - Phase 2.6.1 COMPLETE!

**Before:** 1,172 lines  
**After:** 842 lines  
**Reduction:** -330 lines (-28%)  
**Status:** KeyDetector fully integrated for nested keys!

**All 162 tests passing** ✅  
**Coverage:** 52% (up from 42%, +10%!)

## Benefits

1. ✅ **Eliminates massive duplication** (-346 lines)
2. ✅ **Single source of truth** (KeyDetector)
3. ✅ **Maintainable code** (easy to extend)
4. ✅ **Consistent behavior** (no drift between sections)
5. ✅ **Testable** (KeyDetector already has 98% coverage)

## Risk Mitigation

- **Run tests after each step** (all 162 must pass)
- **Keep old code in comments temporarily** (for reference)
- **Incremental commits** (2.6.1, 2.6.2, 2.6.3)
- **Verify semantic highlighting still works**
