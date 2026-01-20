# zDispatch Layer Refactoring Plan

**Status**: DRAFT  
**Created**: 2026-01-20  
**Goal**: Decompose 2749-line monolith into focused, testable modules (300-400 LOC each)  
**Philosophy**: "Linux from scratch" - clean separation of concerns, minimal dependencies

---

## 🔴 Current Problems

### dispatch_launcher.py (2749 lines)
**God Object Anti-Pattern**:
- ✗ Command routing (string + dict + list)
- ✗ Shorthand syntax expansion (800+ lines!)
- ✗ Organizational structure handling
- ✗ Implicit wizard detection
- ✗ Subsystem routing (zFunc, zDialog, zLink, zDelta, zRead, zData, zLogin, zLogout)
- ✗ CRUD fallback logic
- ✗ Data resolution (_data block queries)
- ✗ Session interpolation
- ✗ Bifrost vs Terminal mode branching everywhere

**Consequences**:
1. **Debugging nightmare** - Current `zCrumbs` bug is hard to trace through 2749 lines
2. **Testing impossible** - Can't unit test individual concerns
3. **Performance unclear** - Repeated string checks, redundant dict traversals
4. **Merge conflicts** - Everyone touches this file
5. **Onboarding pain** - New contributors can't understand the flow

---

## ✅ Proposed Architecture

### File Structure (13 focused modules)

```
zOS/core/L2_Core/e_zDispatch/
├── dispatch_modules/
│   ├── dispatch_constants.py          [EXISTS - 203 lines] ✓
│   ├── dispatch_helpers.py            [EXISTS - minimal] ✓
│   │
│   ├── command_router.py              [NEW - 350 lines]
│   │   └── CommandRouter: Main entry point, type detection
│   │
│   ├── string_commands.py             [NEW - 280 lines]
│   │   └── StringCommandHandler: zFunc(), zLink(), zOpen(), zWizard(), zRead()
│   │
│   ├── dict_commands.py               [NEW - 320 lines]
│   │   └── DictCommandHandler: {zFunc:, zLink:, zDialog:, etc.}
│   │
│   ├── list_commands.py               [NEW - 180 lines]
│   │   └── ListCommandHandler: Sequential execution of command arrays
│   │
│   ├── shorthand_expander.py          [NEW - 400 lines] ⚠️ CRITICAL
│   │   ├── ShorthandExpander: zH1-zH6, zText, zImage, zURL, zCrumbs, zMD, etc.
│   │   ├── expand_ui_elements()
│   │   ├── expand_plurals()
│   │   └── expand_nested_shorthands()
│   │
│   ├── organizational_handler.py      [NEW - 380 lines]
│   │   ├── OrganizationalHandler: Nested dicts/lists recursion
│   │   ├── detect_implicit_sequence()
│   │   └── recurse_nested_structure()
│   │
│   ├── subsystem_router.py            [NEW - 350 lines]
│   │   ├── SubsystemRouter: Route to zFunc, zDialog, zLink, zDelta, etc.
│   │   └── route_to_*() methods for each subsystem
│   │
│   ├── navigation_handler.py          [NEW - 340 lines]
│   │   ├── NavigationHandler: zLink, zDelta logic
│   │   ├── resolve_delta_target_block()
│   │   └── initialize_breadcrumb_scope()
│   │
│   ├── auth_handler.py                [NEW - 260 lines]
│   │   ├── AuthHandler: zLogin, zLogout
│   │   └── build_auth_context()
│   │
│   ├── data_resolver.py               [NEW - 380 lines]
│   │   ├── DataResolver: _data block queries
│   │   ├── resolve_block_data()
│   │   ├── interpolate_session_values()
│   │   ├── build_declarative_query()
│   │   └── execute_data_query()
│   │
│   ├── wizard_detector.py             [NEW - 220 lines]
│   │   ├── WizardDetector: Implicit wizard pattern detection
│   │   └── detect_implicit_wizard()
│   │
│   └── crud_handler.py                [NEW - 240 lines]
│       ├── CRUDHandler: Generic CRUD fallback
│       └── detect_crud_pattern()
│
└── dispatch_launcher.py               [DEPRECATED - to be removed]
```

**Total**: ~3,700 lines across 13 files (avg 285 LOC/file) ✓

---

## 📦 Module Responsibilities

### 1. command_router.py (350 lines)
**Responsibility**: Main entry point, type detection, orchestration  
**Public API**:
```python
class CommandRouter:
    def __init__(self, dispatch)
    def route(self, zHorizontal, context, walker) -> Optional[Any]
    
    # Private orchestration
    def _route_string(self, cmd, context, walker)
    def _route_dict(self, cmd, context, walker)
    def _route_list(self, cmd, context, walker)
```

**Dependencies**: All other modules (facade pattern)

---

### 2. string_commands.py (280 lines)
**Responsibility**: Parse and route string-based commands  
**Public API**:
```python
class StringCommandHandler:
    def handle(self, cmd: str, context, walker) -> Optional[Any]
    
    # Private handlers (one per command type)
    def _handle_zfunc(self, cmd: str, context) -> Any
    def _handle_zlink(self, cmd: str, walker) -> Any
    def _handle_zopen(self, cmd: str, context) -> Any
    def _handle_zwizard(self, cmd: str, walker, context) -> Any
    def _handle_zread(self, cmd: str, context) -> Any
    def _handle_plain_string(self, cmd: str, context, walker) -> Any
```

**Dependencies**: SubsystemRouter, dispatch_constants

---

### 3. dict_commands.py (320 lines)
**Responsibility**: Route dict-based commands  
**Public API**:
```python
class DictCommandHandler:
    def handle(self, cmd: Dict, context, walker) -> Optional[Any]
    
    # Preprocessing
    def _unwrap_content_wrapper(self, cmd: Dict) -> Optional[Dict]
    def _resolve_data_block(self, cmd: Dict, context)
    
    # Detection & routing
    def _detect_command_type(self, cmd: Dict) -> str  # 'subsystem', 'crud', 'organizational', 'wizard'
    def _route_to_handler(self, cmd_type: str, cmd: Dict, context, walker)
```

**Dependencies**: ShorthandExpander, OrganizationalHandler, WizardDetector, SubsystemRouter, CRUDHandler

---

### 4. list_commands.py (180 lines)
**Responsibility**: Sequential execution of command arrays  
**Public API**:
```python
class ListCommandHandler:
    def handle(self, cmd_list: List, context, walker) -> Optional[Any]
    
    # Private
    def _execute_sequential(self, cmd_list: List, context, walker)
    def _check_navigation_signal(self, result: Any) -> bool
```

**Dependencies**: CommandRouter (recursive)

---

### 5. shorthand_expander.py (400 lines) ⚠️ CRITICAL
**Responsibility**: Expand all shorthand syntax to full zDisplay format  
**Public API**:
```python
class ShorthandExpander:
    def expand(self, zHorizontal: Dict, context) -> Dict
    
    # Top-level expansion
    def _expand_ui_elements(self, zh: Dict) -> Dict  # zH1-zH6, zText, zImage, zURL, zCrumbs, zMD
    def _expand_lists(self, zh: Dict) -> Dict        # zUL, zOL
    def _expand_tables(self, zh: Dict) -> Dict       # zTable
    
    # Plural shorthand (zURLs, zTexts, zH1s-zH6s, etc.)
    def _expand_plurals(self, zh: Dict) -> Dict
    
    # Nested expansion (within organizational structures)
    def _expand_nested_shorthands(self, zh: Dict) -> Dict
    
    # Individual element handlers
    def _expand_zcrumbs(self, key: str, value: Dict) -> Optional[Dict]
    def _expand_zimage(self, key: str, value: Dict) -> Optional[Dict]
    def _expand_zurl(self, key: str, value: Union[Dict, List]) -> Optional[Union[Dict, List]]
    def _expand_zheader(self, key: str, value: Dict, indent: int) -> Optional[Dict]
    def _expand_ztext(self, key: str, value: Dict) -> Optional[Dict]
    def _expand_zmd(self, key: str, value: Dict) -> Optional[Dict]
```

**Design Notes**:
- **Single responsibility**: Transform shorthand → full zDisplay
- **Mode-agnostic**: Works for both Terminal and Bifrost
- **Recursive**: Handles nested structures
- **Testable**: Pure functions, no side effects
- **Performance**: Single-pass expansion, no redundant checks

**Dependencies**: dispatch_constants

---

### 6. organizational_handler.py (380 lines)
**Responsibility**: Handle nested organizational structures (recursion)  
**Public API**:
```python
class OrganizationalHandler:
    def handle(self, zHorizontal: Dict, context, walker) -> Optional[Any]
    
    # Detection
    def _is_organizational(self, zh: Dict) -> bool
    def _detect_implicit_sequence(self, zh: Dict) -> bool
    
    # Recursion
    def _recurse_nested_structure(self, zh: Dict, context, walker)
    def _process_nested_key(self, key: str, value: Any, context, walker)
```

**Dependencies**: ShorthandExpander, CommandRouter (recursive)

---

### 7. subsystem_router.py (350 lines)
**Responsibility**: Route to subsystems (zFunc, zDialog, zDisplay, etc.)  
**Public API**:
```python
class SubsystemRouter:
    def route(self, cmd: Dict, context, walker) -> Optional[Any]
    
    # Routing methods (one per subsystem)
    def _route_zdisplay(self, cmd: Dict, context) -> Any
    def _route_zfunc(self, cmd: Dict, context) -> Any
    def _route_zdialog(self, cmd: Dict, context, walker) -> Any
    def _route_zlink(self, cmd: Dict, walker) -> Any
    def _route_zdelta(self, cmd: Dict, walker) -> Any
    def _route_zwizard(self, cmd: Dict, walker, context) -> Any
    def _route_zread(self, cmd: Dict, context) -> Any
    def _route_zdata(self, cmd: Dict, context) -> Any
```

**Dependencies**: NavigationHandler, AuthHandler, dispatch_constants

---

### 8. navigation_handler.py (340 lines)
**Responsibility**: zLink and zDelta navigation logic  
**Public API**:
```python
class NavigationHandler:
    def handle_zlink(self, cmd: Union[str, Dict], walker) -> Any
    def handle_zdelta(self, cmd: Dict, walker) -> Any
    
    # zDelta helpers
    def _resolve_delta_target_block(self, target: str, raw_file: Dict, current_file: str, walker)
    def _construct_fallback_zpath(self, target: str, current_file: str) -> str
    def _initialize_breadcrumb_scope(self, target: str, current_file: str, walker)
```

**Dependencies**: dispatch_constants

---

### 9. auth_handler.py (260 lines)
**Responsibility**: zLogin and zLogout operations  
**Public API**:
```python
class AuthHandler:
    def handle_zlogin(self, cmd: Dict, context) -> Any
    def handle_zlogout(self, cmd: Dict) -> Any
    
    # Context building
    def _build_auth_context(self, cmd: Dict, context: Dict) -> Dict
```

**Dependencies**: zAuth subsystem

---

### 10. data_resolver.py (380 lines)
**Responsibility**: _data block query execution  
**Public API**:
```python
class DataResolver:
    def resolve_block_data(self, data_block: Dict, context: Dict) -> Dict
    
    # Query building
    def _build_declarative_query(self, query_def: Dict) -> Dict
    def _build_shorthand_query(self, key: str, model_path: str) -> Dict
    
    # Execution
    def _execute_data_query(self, key: str, query_def: Dict, context: Dict) -> Any
    
    # Session interpolation
    def _interpolate_session_values(self, where_clause: Dict) -> Dict
```

**Dependencies**: zData subsystem

---

### 11. wizard_detector.py (220 lines)
**Responsibility**: Detect implicit wizard patterns  
**Public API**:
```python
class WizardDetector:
    def detect(self, zHorizontal: Dict) -> bool
    
    # Detection logic
    def _is_implicit_wizard(self, zh: Dict) -> bool
    def _count_content_keys(self, zh: Dict) -> int
```

**Dependencies**: dispatch_constants

---

### 12. crud_handler.py (240 lines)
**Responsibility**: Generic CRUD operation fallback  
**Public API**:
```python
class CRUDHandler:
    def handle(self, cmd: Dict, context) -> Optional[Any]
    
    # Detection
    def _is_crud_pattern(self, cmd: Dict) -> bool
    def _extract_crud_request(self, cmd: Dict) -> Dict
```

**Dependencies**: zData subsystem

---

## 🔄 Migration Strategy

### Phase 1: Extract Leaf Modules (Week 1)
**Goal**: Extract modules with no internal dependencies first

1. **data_resolver.py** (380 lines)
   - Extract from lines 2490-2748
   - No dependencies on other dispatch logic
   - ✓ Already has focused helpers

2. **auth_handler.py** (260 lines)
   - Extract from lines 2094-2184
   - Isolated auth logic
   - ✓ Clear boundaries

3. **crud_handler.py** (240 lines)
   - Extract from lines 1476-1521
   - Simple CRUD detection + routing
   - ✓ Minimal dependencies

**Test**: Each module in isolation with mock subsystems

---

### Phase 2: Extract Navigation & Subsystem Routing (Week 2)
**Goal**: Extract modules with subsystem dependencies

4. **navigation_handler.py** (340 lines)
   - Extract from lines 2186-2398
   - zLink + zDelta logic
   - ✓ Clear interface

5. **subsystem_router.py** (350 lines)
   - Extract from lines 2010-2184
   - Route to all subsystems
   - ✓ Simple dispatch table

**Test**: Integration tests with real subsystems

---

### Phase 3: Extract Core Logic (Week 3)
**Goal**: Extract the transformation and detection logic

6. **shorthand_expander.py** (400 lines) ⚠️ CRITICAL
   - Extract from lines 598-1175 + 1626-1979
   - **THIS IS WHERE zCrumbs BUG IS HIDING**
   - ✓ Make it mode-agnostic
   - ✓ Single-pass expansion
   - ✓ Recursive nested handling

7. **organizational_handler.py** (380 lines)
   - Extract from lines 1626-1979
   - Nested recursion logic
   - ✓ Depends on ShorthandExpander

8. **wizard_detector.py** (220 lines)
   - Extract from lines 1980-2009
   - Implicit wizard detection
   - ✓ Simple pattern matching

**Test**: Unit tests for each transformation, mode-specific integration tests

---

### Phase 4: Extract Command Handlers (Week 4)
**Goal**: Extract the command type handlers

9. **string_commands.py** (280 lines)
   - Extract from lines 405-531
   - String parsing + routing
   - ✓ Depends on SubsystemRouter

10. **dict_commands.py** (320 lines)
    - Extract from lines 537-1241
    - Dict routing orchestrator
    - ✓ Depends on all Phase 3 modules

11. **list_commands.py** (180 lines)
    - Extract from lines 343-399
    - Sequential execution
    - ✓ Depends on CommandRouter (circular - needs interface)

**Test**: Command-level integration tests

---

### Phase 5: Incremental In-Place Integration (Week 5)
**Goal**: Replace monolith code piece-by-piece, testing after EACH micro-step

**Strategy**: NO new facades. Directly modify existing `dispatch_launcher.py` 
by replacing small chunks with delegation calls. Keep system working at all times.

#### Micro-Step 5.1: Initialize Extracted Modules
- Add `__init__()` lines to create module instances
- **Lines to add**: ~15 lines in `__init__()` method
- **Test**: Import test only

#### Micro-Step 5.2: Replace ONE Method in `_launch_dict()`
- Find simplest delegation: `_data` block resolution
- Replace inline code with `self.data_resolver.resolve_block_data(...)`
- **Lines to replace**: ~30 lines (around line 550-580)
- **Test**: Run zTest.py, verify no breakage

#### Micro-Step 5.3: Replace Shorthand Expansion
- Replace `_expand_ui_elements()` call with `self.shorthand_expander.expand(...)`
- **Lines to replace**: ~5 lines (the call site)
- **Test**: Run zTest.py, verify breadcrumbs render

#### Micro-Step 5.4: Replace CRUD Detection
- Replace `_handle_crud_dict()` with `self.crud_handler.handle(...)`
- **Lines to replace**: ~20 lines
- **Test**: Run CRUD operation test

#### Micro-Step 5.5: Replace Auth Routing (zLogin/zLogout)
- Replace `_route_zlogin()` with `self.auth_handler.handle_zlogin(...)`
- Replace `_route_zlogout()` with `self.auth_handler.handle_zlogout(...)`
- **Lines to replace**: ~15 lines each
- **Test**: Test login/logout flow

#### Micro-Step 5.6: Replace Navigation (zLink/zDelta)
- Replace `_route_zlink()` with `self.navigation_handler.handle_zlink(...)`
- Replace `_route_zdelta()` with `self.navigation_handler.handle_zdelta(...)`
- **Lines to replace**: ~40 lines each
- **Test**: Test navigation between blocks

#### Micro-Step 5.7: Replace Organizational Handler
- Replace organizational detection logic with `self.organizational_handler.handle(...)`
- **Lines to replace**: ~50 lines
- **Test**: Test nested dict structures

#### Micro-Step 5.8: Replace Wizard Detection
- Replace implicit wizard detection with `self.wizard_detector.is_implicit_wizard(...)`
- **Lines to replace**: ~25 lines
- **Test**: Test multi-step wizard

#### Micro-Step 5.9: Replace `_launch_string()`
- Replace entire method body with `return self.string_handler.handle(...)`
- **Lines to replace**: ~80 lines
- **Test**: Test string commands (zFunc, zLink strings)

#### Micro-Step 5.10: Replace `_launch_list()`
- Replace entire method body with `return self.list_handler.handle(...)`
- **Lines to replace**: ~25 lines
- **Test**: Test list execution

#### Micro-Step 5.11: Delete Replaced Helper Methods
- Remove now-unused private methods one at a time
- **Methods to delete**: `_expand_ui_elements`, `_handle_crud_dict`, etc.
- **Test**: Verify no references remain

**Total**: 11 micro-steps, each tested independently
**Test**: Run full zTest.py after EACH micro-step

---

## 🐛 How This Fixes Current Bug

### Current Problem: zCrumbs Not Rendering in Bifrost
**Root cause**: Shorthand expansion scattered across 3 locations
1. dispatch_launcher.py lines 1022-1063 (Terminal only)
2. dispatch_launcher.py lines 1691-1768 (nested, Terminal only)
3. dispatch_launcher.py lines 1889-1907 (recursive, Terminal only)

**Why it fails**:
- Bifrost mode skips Terminal-only expansion (line 657: `if not is_bifrost_mode()`)
- Nested `zCrumbs` inside `Page_Header` never gets expanded
- zWizard receives raw `zCrumbs` dict, doesn't know how to process it

### After Refactor: Single Expansion Point
**shorthand_expander.py** becomes the **ONLY** place for expansion:
```python
class ShorthandExpander:
    def expand(self, zh: Dict, context: Dict) -> Dict:
        """
        Expand ALL shorthand syntax, for BOTH Terminal and Bifrost.
        Mode-specific rendering happens LATER in zDisplay/zWizard.
        """
        # Single-pass expansion
        zh = self._expand_ui_elements(zh)
        zh = self._expand_lists(zh)
        zh = self._expand_tables(zh)
        zh = self._expand_plurals(zh)
        zh = self._expand_nested_shorthands(zh)  # Recursive
        return zh
```

**Benefits**:
1. ✓ Works for both Terminal and Bifrost (mode-agnostic)
2. ✓ Handles nested structures recursively
3. ✓ Single source of truth
4. ✓ Testable in isolation
5. ✓ Easy to debug (one file, clear flow)

---

## 📊 Metrics

### Before Refactor
- **Files**: 1 (dispatch_launcher.py)
- **Lines**: 2749
- **Cyclomatic Complexity**: ~85 (unmaintainable)
- **Test Coverage**: ~30% (can't test monolith)
- **Bug Fix Time**: 4+ hours (current zCrumbs bug)

### After Refactor
- **Files**: 13
- **Lines**: ~3700 (distributed)
- **Avg Lines/File**: 285 ✓
- **Cyclomatic Complexity**: ~8-12 per file (maintainable)
- **Test Coverage**: 80%+ target (unit testable)
- **Bug Fix Time**: <30 min (clear module boundaries)

---

## 🚀 Next Steps

### Immediate (Today)
1. **Create shorthand_expander.py** - Extract all expansion logic
2. **Fix zCrumbs bug** - Make expansion mode-agnostic
3. **Test in Terminal + Bifrost** - Validate both modes

### Short-term (This Week)
4. Create REFACTORING_PLAN.md (this document) ✓
5. Extract leaf modules (data_resolver, auth_handler, crud_handler)
6. Write unit tests for extracted modules

### Medium-term (This Month)
7. Extract core logic (shorthand_expander, organizational_handler, wizard_detector)
8. Extract command handlers (string, dict, list)
9. Create command_router facade
10. Deprecate dispatch_launcher.py

---

## 📝 Design Principles

### 1. Single Responsibility
Each module has ONE clear purpose. If you can't describe it in one sentence, it's too big.

### 2. Dependency Inversion
High-level modules (CommandRouter) depend on abstractions, not implementations.

### 3. Interface Segregation
Small, focused interfaces. No god objects.

### 4. Open/Closed
Open for extension (add new shorthand), closed for modification (don't touch core logic).

### 5. DRY (Don't Repeat Yourself)
Current code has 3x copies of zCrumbs expansion. Refactor to 1x.

### 6. Mode-Agnostic Transformation
Shorthand expansion should work for Terminal AND Bifrost. Mode-specific rendering happens downstream.

---

## 🎯 Success Criteria

✅ **All modules < 400 lines**  
✅ **zCrumbs bug fixed** (works in both Terminal and Bifrost)  
✅ **Test coverage > 80%**  
✅ **No code duplication** (DRY)  
✅ **Clear dependency graph** (no circular deps)  
✅ **Performance maintained** (or improved)  
✅ **Backward compatible** (existing YAML works unchanged)

---

## 🔗 Related Documents

- `dispatch_constants.py` - Centralized constants ✓
- `PHASE1_COMPLETE.md` - Navigation system
- `PHASE2_COMPLETE.md` - Display system
- `BIFROST_ZOLO_SYNTAX.md` - Syntax reference

---

**END OF PLAN**
