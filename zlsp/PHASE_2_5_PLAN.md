# Phase 2.5: KeyDetector Integration

## Goal
Integrate the KeyDetector module (created in Phase 2.4) into `line_parsers.py` to replace 100+ lines of scattered key detection logic with clean, maintainable calls to KeyDetector methods.

## Current State
`line_parsers.py` has extensive if-elif chains for key detection:
- **Root keys** (lines 149-207): 58 lines of complex conditionals
- **Nested keys** (lines 238-411): 173+ lines of detection logic
- **Total:** ~230+ lines of key detection that can be simplified

## Integration Strategy

### Step 1: Import KeyDetector
```python
from .key_detector import KeyDetector, detect_key_type
```

### Step 2: Replace Root Key Detection
**Before (58 lines):**
```python
if (emitter.is_zui_file and (core_key == 'zMeta' or ...)) or \
   (emitter.is_zschema_file and core_key == 'zMeta'):
    emitter.emit(..., TokenType.ZMETA_KEY)
elif emitter.is_zspark_file and core_key == 'zSpark':
    emitter.emit(..., TokenType.ZSPARK_KEY)
# ... 50+ more lines
else:
    emitter.emit(..., TokenType.ROOT_KEY)
```

**After (~10 lines):**
```python
# Detect token type using KeyDetector
token_type = KeyDetector.detect_root_key(core_key, emitter, indent)
emitter.emit(original_line_num, current_pos, len(core_key), token_type)

# Check for block entry
block_type = KeyDetector.should_enter_block(core_key, emitter)
if block_type:
    # Enter appropriate block
```

### Step 3: Replace Nested Key Detection
**Before (173+ lines):**
```python
if core_key == 'zRBAC':
    if emitter.is_zenv_file or emitter.is_zui_file:
        emitter.emit(..., TokenType.ZRBAC_KEY)
    emitter.enter_zrbac_block(...)
elif emitter.is_znavbar_first_level(indent) and emitter.is_zenv_file:
    emitter.emit(..., TokenType.ZNAVBAR_NESTED_KEY)
# ... 160+ more lines
```

**After (~10 lines):**
```python
# Detect token type using KeyDetector
token_type = KeyDetector.detect_nested_key(core_key, emitter, indent)
emitter.emit(original_line_num, current_pos, len(core_key), token_type)

# Check for block entry
block_type = KeyDetector.should_enter_block(core_key, emitter)
if block_type:
    # Enter appropriate block
```

## Expected Impact
- **Remove:** ~230 lines of complex conditionals
- **Add:** ~20 lines of clean KeyDetector calls
- **Net reduction:** ~210 lines from line_parsers.py
- **Maintainability:** 10x improvement
- **Test coverage:** Already at 98% for KeyDetector

## Validation
- All 162 existing tests must pass
- No regressions in semantic highlighting
- LSP functionality preserved

## Success Criteria
- ✅ line_parsers.py reduced by ~210 lines
- ✅ All tests passing
- ✅ KeyDetector fully integrated
- ✅ Code more maintainable and readable
