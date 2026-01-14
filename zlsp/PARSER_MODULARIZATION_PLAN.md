# Parser Modularization Plan

**Goal:** Break parser.py (3,420 lines) into clean, focused modules (<500 lines each)

**Status:** Planning Phase  
**Estimated Time:** 2-3 hours  
**Risk:** High (big refactor, must preserve all functionality)

---

## 📊 Current State

**File:** `core/parser/parser.py` = **3,420 lines**

**Problems:**
- ❌ Monolithic (impossible to navigate)
- ❌ 17+ block tracking lists (DRY violation)
- ❌ Mixed concerns (parsing + tokenization + validation + emission)
- ❌ Hard to test (must test everything together)
- ❌ Difficult for new contributors

---

## 🎯 Target Architecture

**Inspired by:** `~/Projects/Zolo/zKernel` subsystem structure

```
core/parser/
├── parser.py (~200 lines)          # Public API + main orchestration
├── parser_modules/
│   ├── __init__.py                  # Module exports
│   ├── token_emitter.py            # TokenEmitter class (~500 lines)
│   ├── comment_processors.py       # Comment handling (~300 lines)
│   ├── multiline_collectors.py     # Multi-line collection (~400 lines)
│   ├── line_parsers.py             # Line parsing logic (~500 lines)
│   ├── value_processors.py         # Value type detection (~400 lines)
│   ├── token_emitters.py           # Token emission (~400 lines)
│   ├── validators.py               # Validation helpers (~200 lines)
│   └── escape_processors.py        # Escape sequences (~200 lines)
├── block_tracker.py (✅ done)
├── type_hints.py (✅ exists)
└── constants.py (✅ exists)
```

**Total:** 8 focused modules + main parser = 9 files

---

## 📋 Module Breakdown

### **1. token_emitter.py** (~500 lines)

**Purpose:** TokenEmitter class with block tracking

**Contents:**
- `class TokenEmitter` (lines 40-454)
  - `__init__()` - File type detection, BlockTracker init
  - `add_comment_range()`
  - `emit()` - Core token emission
  - `split_modifiers()` - Key modifier parsing
  - **REPLACE**: 17+ individual block tracking lists → `self.block_tracker = BlockTracker()`
  - **REMOVE**: All `enter_X_block()`, `update_X_blocks()`, `is_in_X_block()` methods

**Dependencies:**
- `BlockTracker` from `..block_tracker`
- `TokenType`, `SemanticToken` from `...lsp_types`

**Testing:** Existing tests should pass

---

### **2. comment_processors.py** (~300 lines)

**Purpose:** Handle comment stripping and preprocessing

**Contents:**
- `strip_comments_and_prepare_lines(content: str)` → `(lines, line_mapping)`
- `strip_comments_and_prepare_lines_with_tokens(content: str, emitter)` → `(lines, line_mapping)`
- Helper: `_char_to_utf16_offset()` (utility)

**Current lines:** 726-1014 (without tokens), 848-1014 (with tokens)

**Dependencies:**
- `TokenEmitter` (for tokenized version)
- `TokenType` (for comment tokens)

**Testing:** Comment handling tests

---

### **3. multiline_collectors.py** (~400 lines)

**Purpose:** Collect multi-line values (strings, lists, etc.)

**Contents:**
- `collect_str_hint_multiline()` (lines 1945-2017)
- `collect_dash_list()` (lines 2018-2098)
- `collect_bracket_array()` (lines 2099-2166)
- `collect_pipe_multiline()` (lines 2167-2210)
- `collect_triple_quote_multiline()` (lines 2211-2275)

**Dependencies:** None (pure string processing)

**Testing:** Multi-line value tests

---

### **4. line_parsers.py** (~500 lines)

**Purpose:** Core line parsing and structure building

**Contents:**
- `parse_lines_with_tokens()` (lines 1015-1812) - **HUGE function**
- `parse_lines()` (lines 1813-1944)
- `build_nested_dict()` (lines 2276-2394)
- `parse_root_key_value_pairs()` (lines 2395-2440)
- `check_indentation_consistency()` (lines 659-725)

**Dependencies:**
- `TokenEmitter`
- `multiline_collectors`
- `value_processors`

**Testing:** Core parsing tests (most critical!)

---

### **5. value_processors.py** (~400 lines)

**Purpose:** Value type detection and parsing

**Contents:**
- `detect_value_type()` (lines 2878-2959)
- `parse_brace_object()` (lines 2960-3030)
- `parse_bracket_array()` (lines 3267-3314)
- `split_on_comma()` (lines 3031-3072)

**Dependencies:**
- `escape_processors` (for Unicode handling)

**Testing:** Value parsing tests

---

### **6. token_emitters.py** (~400 lines)

**Purpose:** Emit semantic tokens for values

**Contents:**
- `emit_value_tokens()` (lines 2441-2637) - **HUGE function**
- `emit_string_with_escapes()` (lines 2638-2679)
- `emit_array_tokens()` (lines 2680-2719)
- `emit_object_tokens()` (lines 2720-2812)

**Dependencies:**
- `TokenEmitter`
- `validators` (for zPath/env detection)

**Testing:** Token emission tests

---

### **7. validators.py** (~200 lines)

**Purpose:** Validation helpers and type checking

**Contents:**
- `validate_ascii_only()` (lines 2813-2877)
- `is_zpath_value()` (lines 3148-3180)
- `is_env_config_value()` (lines 3181-3230)
- `is_valid_number()` (lines 3231-3266)

**Dependencies:** None (pure validation)

**Testing:** Validation tests

---

### **8. escape_processors.py** (~200 lines)

**Purpose:** Handle escape sequences

**Contents:**
- `decode_unicode_escapes()` (lines 3073-3109)
- `process_escape_sequences()` (lines 3110-3147)

**Dependencies:** None (pure string processing)

**Testing:** Escape sequence tests

---

### **9. parser.py** (main, ~200 lines)

**Purpose:** Public API and orchestration

**Contents:**
- **Public API** (keep these):
  - `tokenize(content, filename)` → `ParseResult`
  - `load(fp, file_extension)` → `Any`
  - `loads(s, file_extension)` → `Any`
  - `dump(data, fp, file_extension)` → `None`
  - `dumps(data, file_extension)` → `str`

- **Private orchestration** (keep these):
  - `_parse_zolo_content(content)` → `Any`
  - `_parse_zolo_content_with_tokens(content, emitter)` → `Any`

- **Imports:**
  ```python
  from .parser_modules.token_emitter import TokenEmitter
  from .parser_modules.comment_processors import (
      strip_comments_and_prepare_lines,
      strip_comments_and_prepare_lines_with_tokens,
  )
  from .parser_modules.line_parsers import parse_lines_with_tokens, parse_lines
  # ... etc
  ```

**Dependencies:** All modules

**Testing:** Integration tests (public API)

---

## 🔄 Migration Strategy

### **Phase 1: Create Module Skeletons** (30 min)
1. Create `parser_modules/__init__.py`
2. Create all 8 module files with headers
3. Copy function signatures (no implementation yet)
4. Add TODO comments for each function

### **Phase 2: Extract Modules One-by-One** (90 min)
Order of extraction (least to most dependencies):

1. ✅ **validators.py** - No dependencies, pure functions
2. ✅ **escape_processors.py** - No dependencies
3. ✅ **value_processors.py** - Depends on escape_processors
4. ✅ **multiline_collectors.py** - No dependencies
5. ✅ **comment_processors.py** - Depends on TokenEmitter
6. ✅ **token_emitter.py** - Integrate BlockTracker here
7. ✅ **token_emitters.py** - Depends on TokenEmitter, validators
8. ✅ **line_parsers.py** - Depends on most others (do last!)

### **Phase 3: Update Main Parser** (30 min)
1. Add imports from all modules
2. Remove extracted code
3. Keep only public API + orchestration

### **Phase 4: Testing & Validation** (30 min)
1. Run all existing unit tests
2. Run integration tests
3. Run E2E tests
4. Fix any import issues

---

## ✅ Success Criteria

1. **All tests pass** - No functionality broken
2. **No file > 500 lines** - Clean, focused modules
3. **Clear dependencies** - No circular imports
4. **Easy to navigate** - New contributors can find code
5. **BlockTracker integrated** - 17+ lists → 1 unified system

---

## 🚨 Risks & Mitigation

### **Risk 1: Breaking existing imports**
**Mitigation:** 
- Keep old imports working via `__init__.py` re-exports
- Add deprecation warnings if needed

### **Risk 2: Circular dependencies**
**Mitigation:**
- Extract in dependency order (bottom-up)
- Use forward type hints where needed

### **Risk 3: Tests break**
**Mitigation:**
- Run tests after each module extraction
- Keep integration tests as smoke tests

---

## 📊 Before/After Comparison

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| **Largest file** | 3,420 lines | ~500 lines | -85% |
| **Avg file size** | 3,420 lines | ~350 lines | -90% |
| **Block tracking** | 17+ lists | 1 BlockTracker | DRY ✅ |
| **Testability** | Integration only | Unit + Integration | ✅ |
| **Onboarding time** | 2-4 days | 1 day | -60% |
| **Add new feature** | 2-4 days | 4-8 hours | -75% |

---

## 🎯 Execution Order

1. ✅ Create `parser_modules/` directory
2. ✅ Create this plan document
3. **Commit plan** (before making changes)
4. Execute Phase 1 (skeletons)
5. Execute Phase 2 (extraction)
6. Execute Phase 3 (main parser)
7. Execute Phase 4 (testing)
8. **Commit completed refactor**

---

**Status:** Ready to execute  
**Next:** Commit this plan, then start Phase 1  
**ETA:** 2-3 hours total
