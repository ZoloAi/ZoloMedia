# zDisplay Refactoring & Validation Plan

**Date:** January 19, 2026  
**Status:** Phase 0 - Audit Complete  
**Goal:** Decompose monolithic files, enforce DRY, achieve industry-grade architecture

---

## Executive Summary

The `zDisplay_modules` system has grown organically and now contains several monolithic files that violate zOS fundamentals (DRY, single responsibility, modularity). The largest offender is `display_event_system.py` (2,386 lines) which contains 6 distinct system events that should be separate modules.

### Critical Issues Identified

1. **Monolithic Files (5 files >800 lines)**
   - `display_event_system.py`: 2,386 lines → Target: 6 modules @ ~200-300 lines each
   - `display_event_timebased.py`: 1,219 lines → Target: 3 modules @ ~300-400 lines each
   - `display_event_advanced.py`: 1,049 lines → Target: 3 modules @ ~300-350 lines each
   - `display_event_inputs.py`: 941 lines → Target: 2 modules @ ~400-500 lines each
   - `display_event_data.py`: 878 lines → Target: 2 modules @ ~400-450 lines each

2. **Architectural Pollution**
   - Duplicate `display_primitives.py` (root AND `b_primitives/`)
   - Test files in production code (`c_basic/test_*.py`)
   - Backup files in production (`display_event_timebased.py.bak`)
   - Incomplete delegate pattern (delegates/ vs display_delegates.py)

3. **DRY Violations** (Partially Fixed)
   - ✅ Mode detection unified (`is_bifrost_mode`)
   - ✅ Event ID generation centralized (`generate_event_id`)
   - ✅ WebSocket emission unified (`emit_websocket_event`)
   - ⚠️ Logging patterns still duplicated across files
   - ⚠️ Field display helpers duplicated
   - ⚠️ Color code lookups duplicated

4. **Missing Infrastructure**
   - No centralized field rendering helpers
   - No centralized section rendering helpers
   - No centralized logger integration utilities
   - Constants could be decomposed by domain (system, data, time-based, etc.)

---

## Phase 0: Pre-Refactoring Audit ✅ COMPLETE

**Objective:** Understand current structure, identify issues, document dependencies

---

## Phase 1: Clean Up Pollution ✅ COMPLETE

**Objective:** Remove duplicate, test, and backup files  
**Duration:** 15 minutes  
**Status:** ✅ COMPLETE  
**Details:** See `PHASE1_COMPLETE.md`

**Results:**
- ✅ Removed duplicate `display_primitives.py` (-709 lines)
- ✅ Moved 5 test files to `tests/markdown_parser/`
- ✅ Deleted backup file `display_event_timebased.py.bak`
- ✅ Updated import in `zDisplay.py`
- ✅ Validated with `zTest.py` - all systems operational

**Impact:** -5 files, cleaner architecture, no functionality changes

### 0.1 File Size Analysis ✅

```
Monolithic (>800 lines - CRITICAL):
  2386  display_event_system.py       [f_orchestration/]
  1219  display_event_timebased.py    [e_advanced/]
  1049  display_event_advanced.py     [e_advanced/]
   941  display_event_inputs.py       [d_interaction/]
   878  display_event_data.py         [d_interaction/]

Large (500-800 lines - WARNING):
   832  markdown_terminal_parser.py   [c_basic/]
   772  display_event_outputs.py      [c_basic/]
   709  display_primitives.py         [root + b_primitives/] (DUPLICATE!)
   575  display_event_media.py        [d_interaction/]

Acceptable (<500 lines):
   462  display_event_signals.py      [c_basic/]
   418  display_constants.py          [root]
   417  display_semantic_primitives.py [b_primitives/]
   332  display_event_links.py        [d_interaction/]
   298  display_rendering_helpers.py  [b_primitives/]
   297  display_utilities.py          [b_primitives/]
   242  display_delegates.py          [root]
   242  display_event_helpers.py      [a_infrastructure/]
```

### 0.2 Architectural Issues ✅

1. **Duplicate Files:**
   - `display_primitives.py` exists at root AND `b_primitives/`
   - Decision: Keep `b_primitives/display_primitives.py`, deprecate root version

2. **Misplaced Files:**
   - Test files in production: `c_basic/test_*.py` (5 files)
   - Decision: Move to `tests/` directory at zDisplay root

3. **Pollution:**
   - Backup file: `e_advanced/display_event_timebased.py.bak`
   - Decision: Delete (git has history)

4. **Incomplete Abstractions:**
   - `delegates/` folder with 5 delegate modules
   - Root `display_delegates.py` (different purpose?)
   - Decision: Clarify roles - keep both if different responsibilities

### 0.3 Dependency Graph ✅

```
Layer 0: Infrastructure
  ├── a_infrastructure/display_event_helpers.py (242 lines)
  └── display_constants.py (418 lines)

Layer 1: Primitives (Foundation)
  ├── b_primitives/display_primitives.py (709 lines)
  ├── b_primitives/display_semantic_primitives.py (417 lines)
  ├── b_primitives/display_rendering_helpers.py (298 lines)
  └── b_primitives/display_utilities.py (297 lines)

Layer 2: Basic Events
  ├── c_basic/display_event_outputs.py (772 lines)
  ├── c_basic/display_event_signals.py (462 lines)
  └── c_basic/markdown_terminal_parser.py (832 lines)

Layer 3: Interaction Events
  ├── d_interaction/display_event_inputs.py (941 lines) [REFACTOR]
  ├── d_interaction/display_event_data.py (878 lines) [REFACTOR]
  ├── d_interaction/display_event_media.py (575 lines)
  └── d_interaction/display_event_links.py (332 lines)

Layer 4: Advanced Events
  ├── e_advanced/display_event_advanced.py (1049 lines) [REFACTOR]
  └── e_advanced/display_event_timebased.py (1219 lines) [REFACTOR]

Layer 5: Orchestration (CRITICAL REFACTOR)
  └── f_orchestration/display_event_system.py (2386 lines) [CRITICAL]

Layer 6: Coordinator
  └── display_events.py (865 lines)
```

### 0.4 display_event_system.py Deep Dive ✅

**Current Structure:** Monolithic 2,386-line file with 6 distinct system events

**Identified Modules (Target Decomposition):**

1. **system_event_session.py** (~300 lines)
   - `zSession()` - Display session state
   - `zConfig()` - Display config state
   - `_display_zmachine()` - Machine section
   - `_display_zauth()` - Auth section
   - `_display_zcache()` - Cache section
   - `_display_zshortcuts()` - Shortcuts section
   - `_format_path_as_zpath()` - Path formatting

2. **system_event_navigation.py** (~200 lines)
   - `zCrumbs()` - Display breadcrumbs
   - `zMenu()` - Display menu
   - Breadcrumb formatting helpers

3. **system_event_dashboard.py** (~600 lines)
   - `zDash()` - Dashboard orchestration
   - RBAC filtering logic
   - Panel loading and navigation
   - Context management

4. **system_event_dialog.py** (~500 lines)
   - `zDialog()` - Form dialog orchestration
   - Field collection with validation
   - Schema integration
   - 10 helper methods for dialog workflow

5. **system_event_declare.py** (~150 lines)
   - `zDeclare()` - System message display
   - `_should_show_sysmsg()` - Log-level conditioning

6. **system_display_helpers.py** (~400 lines)
   - `_display_field()` - Field rendering
   - `_display_section()` - Section rendering
   - `_display_zmachine()` - Machine display
   - `_display_zauth()` - Auth display (+ 8 zAuth helpers)
   - `_display_zcache()` - Cache display
   - `_display_zshortcuts()` - Shortcuts display
   - `_get_color()` - Color lookup
   - `_output_text()` - Text output wrapper

**Remaining Core:** ~200 lines
   - Class definition and `__init__`
   - Constants and imports
   - `_try_gui_event()` (delegates to infrastructure)

---

## Phase 1: Clean Up Pollution (Quick Wins)

**Objective:** Remove duplicate, test, and backup files
**Estimated Impact:** -500 lines of pollution
**Risk:** Low (no functionality changes)

### 1.1 Remove Duplicate Primitives File

**Action:**
```bash
# Verify root display_primitives.py is identical or outdated
diff display_primitives.py b_primitives/display_primitives.py

# If outdated/identical, delete root version
rm display_primitives.py

# Update imports in display_events.py and display_delegates.py
# OLD: from .display_primitives import ...
# NEW: from .b_primitives.display_primitives import ...
```

**Files to Update:**
- `display_events.py`: Update primitive imports
- `display_delegates.py`: Update primitive imports
- Any other files importing from root `display_primitives`

**Validation:**
- Run `python3 zTest.py` to ensure no import errors
- Check LSP for any broken references

### 1.2 Move Test Files to Tests Directory

**Action:**
```bash
# Create tests directory at zDisplay root
mkdir -p ../../../tests/zDisplay/markdown_parser

# Move test files
mv c_basic/test_*.py ../../../tests/zDisplay/markdown_parser/

# Update test imports (if needed)
```

**Files to Move:**
- `c_basic/test_markdown_parser.py`
- `c_basic/test_phase2_html_mapping.py`
- `c_basic/test_phase3_list_extraction.py`
- `c_basic/test_phase4_block_parsing.py`
- `c_basic/test_phase5_integration.py`

**Validation:**
- Tests should still run from new location
- Update any CI/CD scripts if needed

### 1.3 Delete Backup Files

**Action:**
```bash
# Remove .bak files (git has history)
rm e_advanced/display_event_timebased.py.bak
```

**Validation:**
- Verify git history contains the backup content
- No references to .bak file anywhere

---

## Phase 2: Extract Infrastructure Helpers (Foundation)

**Objective:** Create reusable helpers for logging, field rendering, section display
**Estimated Impact:** -200 lines from monoliths, +300 lines in new helpers (net +100, but DRY++)
**Risk:** Medium (refactoring existing code, but isolated utilities)

### 2.1 Create Centralized Display Helpers

**New File:** `a_infrastructure/display_rendering_utilities.py` (~150 lines)

**Functions to Extract:**
```python
# From display_event_system.py and others:
def render_field(label: str, value: Any, indent: int, color: str, display: Any) -> None:
    """Render a labeled field with color formatting."""

def render_section_title(title: str, indent: int, color: str, display: Any) -> None:
    """Render a section title with color formatting."""

def get_color_code(color_name: str, zColors: Any) -> str:
    """Get ANSI color code with fallback to RESET."""

def output_text_via_basics(content: str, indent: int, break_after: bool, display: Any) -> None:
    """Output text via BasicOutputs if available."""
```

**Extract From:**
- `display_event_system.py`: `_display_field`, `_display_section`, `_get_color`, `_output_text`
- Similar patterns in `display_event_advanced.py`, `display_event_data.py`

**Benefits:**
- DRY: One implementation for all field/section rendering
- Testable: Unit tests for formatting logic
- Consistent: Same rendering across all events

### 2.2 Create Centralized Logger Integration

**New File:** `a_infrastructure/display_logging_helpers.py` (~100 lines)

**Functions to Extract:**
```python
def should_show_system_message(display: Any) -> bool:
    """Check if system messages should be displayed (deployment/logging aware)."""

def log_event_start(logger: Optional[Any], event_name: str, context: Dict[str, Any]) -> None:
    """Log event start with context (if logger available and debug mode)."""

def log_event_end(logger: Optional[Any], event_name: str, duration: float) -> None:
    """Log event completion with duration."""

def get_display_logger(display: Any) -> Optional[Any]:
    """Get logger instance from display hierarchy (display.zcli.logger or display.logger)."""
```

**Extract From:**
- `display_event_system.py`: `_should_show_sysmsg`
- `display_event_system.py` (zDialog): Logger access patterns
- Similar patterns in `display_event_timebased.py`

**Benefits:**
- DRY: One logging integration point
- Consistent: Same logging behavior everywhere
- Testable: Mock logger in tests

### 2.3 Update display_event_helpers.py

**Add to Existing File:** `a_infrastructure/display_event_helpers.py`

**New Functions:**
```python
def safe_get_nested(obj: Any, *keys: str, default: Any = None) -> Any:
    """Safely get nested attribute/dict value with fallback."""

def format_value_for_display(value: Any, max_length: int = 60) -> str:
    """Format value for display (handle bool, None, dict, list, long strings)."""
```

**Benefits:**
- Common patterns used across multiple event files
- Safe navigation of nested structures

---

## Phase 3: Decompose display_event_system.py (CRITICAL)

**Objective:** Break 2,386-line monolith into 6 focused modules
**Estimated Impact:** -2,386 lines from monolith, +1,800 lines in new modules (net -586 lines due to DRY)
**Risk:** High (core system events, extensive testing required)

### 3.1 Create system_event_session.py

**New File:** `f_orchestration/system_event_session.py` (~350 lines)

**Contents:**
```python
class SessionEvents:
    """Session and configuration display events."""
    
    def __init__(self, display_instance: Any):
        self.display = display_instance
        # ... setup
    
    # PUBLIC METHODS
    def zSession(self, session_data, break_after=True, break_message=None):
        """Display complete zCLI session state."""
    
    def zConfig(self, config_data=None, break_after=True, break_message=None):
        """Display zConfig machine and environment configuration."""
    
    # PRIVATE HELPERS
    def _display_zmachine(self, zMachine: Dict[str, Any]):
        """Display complete zMachine section."""
    
    def _display_zauth(self, zAuth: Dict[str, Any]):
        """Display complete zAuth section (three-tier aware)."""
    
    def _display_zcache(self, zCache: Dict[str, Any]):
        """Display complete zCache section (4-tier caching)."""
    
    def _display_zshortcuts(self, zvars, zshortcuts):
        """Display zVars and file shortcuts section."""
    
    def _format_path_as_zpath(self, path_value: str, session_data: Dict) -> str:
        """Convert absolute path to zPath notation."""
    
    # ... + 8 zAuth display helpers
```

**Extract From:** `display_event_system.py` lines 825-1067, 2021-2319

**Dependencies:**
- Import: `display_rendering_utilities` (field/section rendering)
- Import: `display_event_helpers` (try_gui_event)
- Import: `display_constants` (SESSION_KEY_*, ZAUTH_KEY_*)

**Validation:**
- Unit tests for zSession display
- Unit tests for zConfig display
- Unit tests for path formatting
- Integration test: `python3 zTest.py` (check zSession command)

### 3.2 Create system_event_navigation.py

**New File:** `f_orchestration/system_event_navigation.py` (~200 lines)

**Contents:**
```python
class NavigationEvents:
    """Navigation UI events (breadcrumbs, menus)."""
    
    def __init__(self, display_instance: Any):
        self.display = display_instance
        # ... setup
    
    # PUBLIC METHODS
    def zCrumbs(self, session_data: Optional[Dict[str, Any]]):
        """Display breadcrumb navigation trail."""
    
    def zMenu(self, menu_items, prompt=DEFAULT_MENU_PROMPT, return_selection=False):
        """Display menu options and optionally collect user selection."""
```

**Extract From:** `display_event_system.py` lines 1068-1226

**Dependencies:**
- Import: `display_rendering_utilities` (text output)
- Import: `display_event_helpers` (try_gui_event)
- Import: `display_constants` (SESSION_KEY_ZCRUMBS, format strings)

**Validation:**
- Unit tests for zCrumbs display
- Unit tests for zMenu display
- Integration test: Load file with `zCrumbs: true` in zUI

### 3.3 Create system_event_dashboard.py

**New File:** `f_orchestration/system_event_dashboard.py` (~650 lines)

**Contents:**
```python
class DashboardEvents:
    """Dashboard orchestration with RBAC-aware panel navigation."""
    
    def __init__(self, display_instance: Any):
        self.display = display_instance
        # ... setup
    
    # PUBLIC METHODS
    def zDash(self, folder, sidebar, default=None, _zcli=None, **kwargs):
        """Display dashboard with interactive panel navigation."""
    
    # PRIVATE HELPERS (10+ methods for dashboard workflow)
    def _filter_panels_by_rbac(self, sidebar, folder, _zcli, logger):
        """RBAC filter panels before display."""
    
    def _load_panel_metadata(self, panel_name, folder, _zcli):
        """Load panel metadata for menu display."""
    
    def _execute_panel(self, current_panel, folder, _zcli, logger):
        """Execute panel block via zDispatch."""
    
    def _build_dashboard_menu(self, sidebar, current_panel, panel_metadata):
        """Build and display dashboard navigation menu."""
    
    # ... more helpers
```

**Extract From:** `display_event_system.py` lines 1227-1594

**Dependencies:**
- Import: `display_rendering_utilities` (text output)
- Import: `display_event_helpers` (try_gui_event)
- Import: `zWizard.wizardzRBAC` (checkzRBAC_access)
- Import: `display_constants` (SESSION_KEY_*)

**Validation:**
- Unit tests for RBAC filtering
- Unit tests for panel loading
- Integration test: Navigate dashboard in Terminal mode
- Integration test: Dashboard in Bifrost mode

### 3.4 Create system_event_dialog.py

**New File:** `f_orchestration/system_event_dialog.py` (~550 lines)

**Contents:**
```python
class DialogEvents:
    """Form dialog with field-by-field validation."""
    
    def __init__(self, display_instance: Any):
        self.display = display_instance
        # ... setup
    
    # PUBLIC METHODS
    def zDialog(self, context, _zcli=None, _walker=None):
        """Display form dialog and collect validated input."""
    
    # PRIVATE HELPERS (10 methods for dialog workflow)
    def _log_zdialog_start(self, context, _zcli):
        """Log zDialog start (debug mode only)."""
    
    def _try_zdialog_gui_mode(self, context, _zcli):
        """Try to send zDialog event to Bifrost."""
    
    def _setup_zdialog_validator(self, context, _zcli):
        """Setup schema validator for field-by-field validation."""
    
    def _collect_zdialog_fields(self, fields, validator, table_name, logger):
        """Collect all form fields with validation."""
    
    # ... 6 more helpers
```

**Extract From:** `display_event_system.py` lines 1596-1953

**Dependencies:**
- Import: `display_rendering_utilities` (text output)
- Import: `display_event_helpers` (try_gui_event)
- Import: `display_logging_helpers` (logger access)
- Import: `zData.DataValidator` (schema validation)

**Validation:**
- Unit tests for field collection
- Unit tests for validation retry loop
- Integration test: Dialog with schema validation
- Integration test: Dialog without schema (simple mode)

### 3.5 Create system_event_declare.py

**New File:** `f_orchestration/system_event_declare.py` (~150 lines)

**Contents:**
```python
class DeclareEvents:
    """System declaration/message display with log-level conditioning."""
    
    def __init__(self, display_instance: Any):
        self.display = display_instance
        # ... setup
    
    # PUBLIC METHODS
    def zDeclare(self, label, color=None, indent=DEFAULT_INDENT, style=DEFAULT_STYLE):
        """Display system declaration/message with log-level conditioning."""
```

**Extract From:** `display_event_system.py` lines 685-757, 2323-2386 (logging helper)

**Dependencies:**
- Import: `display_logging_helpers` (should_show_system_message)
- Import: `display_constants` (COLOR_*, STYLE_*)

**Validation:**
- Unit tests for auto-style selection
- Unit tests for log-level conditioning
- Integration test: zDeclare in dev vs prod modes

### 3.6 Update display_event_system.py (Slim Coordinator)

**Remaining:** ~250 lines

**New Role:** **Coordinator class that composes the 5 event sub-classes**

**Contents:**
```python
class zSystem:
    """
    zCLI System Introspection & Navigation UI Events (Coordinator).
    
    Composes 5 specialized event classes:
    - SessionEvents: zSession, zConfig
    - NavigationEvents: zCrumbs, zMenu
    - DashboardEvents: zDash
    - DialogEvents: zDialog
    - DeclareEvents: zDeclare
    """
    
    def __init__(self, display_instance: Any):
        self.display = display_instance
        self.zPrimitives = display_instance.zPrimitives
        self.zColors = display_instance.zColors
        
        # Compose specialized event classes
        self._session = SessionEvents(display_instance)
        self._navigation = NavigationEvents(display_instance)
        self._dashboard = DashboardEvents(display_instance)
        self._dialog = DialogEvents(display_instance)
        self._declare = DeclareEvents(display_instance)
        
        # Cross-reference setup (set after zEvents init)
        self.BasicOutputs = None
        self.Signals = None
        self.BasicInputs = None
    
    # DELEGATION METHODS (forward to specialized classes)
    def zSession(self, *args, **kwargs):
        """Display complete zCLI session state."""
        return self._session.zSession(*args, **kwargs)
    
    def zConfig(self, *args, **kwargs):
        """Display zConfig machine and environment configuration."""
        return self._session.zConfig(*args, **kwargs)
    
    def zCrumbs(self, *args, **kwargs):
        """Display breadcrumb navigation trail."""
        return self._navigation.zCrumbs(*args, **kwargs)
    
    def zMenu(self, *args, **kwargs):
        """Display menu options."""
        return self._navigation.zMenu(*args, **kwargs)
    
    def zDash(self, *args, **kwargs):
        """Display dashboard with panel navigation."""
        return self._dashboard.zDash(*args, **kwargs)
    
    def zDialog(self, *args, **kwargs):
        """Display form dialog."""
        return self._dialog.zDialog(*args, **kwargs)
    
    def zDeclare(self, *args, **kwargs):
        """Display system declaration."""
        return self._declare.zDeclare(*args, **kwargs)
    
    # BACKWARD COMPATIBILITY (deprecated helper)
    def _try_gui_event(self, event_name: str, data: Dict[str, Any]) -> bool:
        """DEPRECATED: Use try_gui_event from display_event_helpers."""
        from ..a_infrastructure.display_event_helpers import try_gui_event
        return try_gui_event(self.display, event_name, data)
```

**Benefits:**
- Public API unchanged (delegation methods forward to sub-classes)
- Each sub-class focused on single responsibility
- Easier testing (test each sub-class independently)
- Easier maintenance (find bugs/features in ~200-350 line files, not 2,386 line monolith)

**Validation:**
- All existing integration tests must pass
- No changes to external API (delegation ensures backward compatibility)

### 3.7 Refactoring Steps (Execution Order)

**Step 1:** Create infrastructure helpers (Phase 2)
**Step 2:** Create `system_event_declare.py` (smallest, least dependencies)
**Step 3:** Create `system_event_navigation.py` (small, simple)
**Step 4:** Create `system_event_session.py` (medium, uses new helpers)
**Step 5:** Create `system_event_dialog.py` (medium-large, complex)
**Step 6:** Create `system_event_dashboard.py` (largest, most complex)
**Step 7:** Update `display_event_system.py` to coordinator
**Step 8:** Run full integration test suite

---

## Phase 4: Decompose display_event_timebased.py

**Objective:** Break 1,219-line time-based events into 3 focused modules
**Estimated Impact:** -1,219 lines, +900 lines in new modules (net -319 lines due to DRY)
**Risk:** Medium (active event state management)

### 4.1 Create timebased_progress.py

**New File:** `e_advanced/timebased_progress.py` (~400 lines)

**Contents:**
```python
class ProgressEvents:
    """Progress bar events with active state management."""
    
    def progress_bar(self, label, current, total, ...):
        """Display progress bar (Terminal) or send WebSocket event (Bifrost)."""
    
    def progress_start(self, label, total):
        """Start a progress bar."""
    
    def progress_update(self, progress_id, current, label=None):
        """Update progress bar."""
    
    def progress_complete(self, progress_id):
        """Complete and remove progress bar."""
```

### 4.2 Create timebased_spinner.py

**New File:** `e_advanced/timebased_spinner.py` (~300 lines)

**Contents:**
```python
class SpinnerEvents:
    """Spinner events for indefinite operations."""
    
    def spinner(self, label, active=True):
        """Display spinner (Terminal) or send WebSocket event (Bifrost)."""
```

### 4.3 Create timebased_swiper.py

**New File:** `e_advanced/timebased_swiper.py` (~400 lines)

**Contents:**
```python
class SwiperEvents:
    """Swiper/carousel events for multi-item display."""
    
    def swiper(self, items, config=None):
        """Display swiper/carousel in Bifrost."""
```

### 4.4 Update display_event_timebased.py (Coordinator)

**Remaining:** ~150 lines (coordinator + active state management)

---

## Phase 5: Decompose display_event_advanced.py

**Objective:** Break 1,049-line advanced events into 3 focused modules
**Estimated Impact:** -1,049 lines, +800 lines in new modules (net -249 lines due to DRY)
**Risk:** Medium (complex table rendering logic)

### 5.1 Create advanced_table.py

**New File:** `e_advanced/advanced_table.py` (~450 lines)

**Contents:**
```python
class TableEvents:
    """Advanced table rendering with pagination and sorting."""
    
    def zTable(self, data, headers, config):
        """Render table with advanced features."""
```

### 5.2 Create advanced_cards.py

**New File:** `e_advanced/advanced_cards.py` (~250 lines)

**Contents:**
```python
class CardEvents:
    """Card layout events."""
    
    def zCards(self, items, layout):
        """Render cards in grid layout."""
```

### 5.3 Create advanced_charts.py

**New File:** `e_advanced/advanced_charts.py` (~250 lines)

**Contents:**
```python
class ChartEvents:
    """Chart visualization events."""
    
    def zChart(self, data, chart_type):
        """Render chart visualization."""
```

### 5.4 Update display_event_advanced.py (Coordinator)

**Remaining:** ~150 lines (coordinator)

---

## Phase 6: Decompose Interaction Events

**Objective:** Break large interaction event files into focused modules
**Estimated Impact:** -1,819 lines, +1,400 lines in new modules (net -419 lines due to DRY)
**Risk:** Low (simpler event types)

### 6.1 Decompose display_event_inputs.py (941 lines)

**Split Into:**
- `d_interaction/inputs_selection.py` (~400 lines) - `selection()` event
- `d_interaction/inputs_text.py` (~300 lines) - Text input events
- `d_interaction/inputs_file.py` (~200 lines) - File selection events
- Coordinator: ~100 lines

### 6.2 Decompose display_event_data.py (878 lines)

**Split Into:**
- `d_interaction/data_list.py` (~350 lines) - `list()` event
- `d_interaction/data_json.py` (~300 lines) - `json()` event
- `d_interaction/data_tree.py` (~200 lines) - Tree view events
- Coordinator: ~100 lines

---

## Phase 7: Extract Constants by Domain

**Objective:** Decompose `display_constants.py` into domain-specific constant modules
**Estimated Impact:** -418 lines, +500 lines in new modules (net +82, but better organization)
**Risk:** Low (pure constant extraction)

### 7.1 Create Constant Modules

**New Files:**
```
display_constants/
├── __init__.py (re-exports all constants)
├── system_constants.py (~100 lines) - zSession, zAuth, zMachine keys
├── data_constants.py (~80 lines) - zTable, zList, zJSON keys
├── interaction_constants.py (~60 lines) - Input/selection constants
├── timebased_constants.py (~50 lines) - Progress/spinner constants
├── color_constants.py (~40 lines) - Color definitions
├── style_constants.py (~40 lines) - Style definitions
└── message_constants.py (~100 lines) - User-facing messages
```

**Benefits:**
- Easier to find constants (domain-based organization)
- Reduces import time (only import needed constants)
- Better documentation (constants grouped by purpose)

---

## Phase 8: Final Validation & Documentation

**Objective:** Ensure all refactoring is complete, tested, and documented
**Estimated Impact:** Quality assurance phase
**Risk:** Low (validation only)

### 8.1 Integration Testing

**Test Coverage:**
- All public methods have integration tests
- All event types tested in Terminal mode
- All event types tested in Bifrost mode
- Error handling tested
- Edge cases tested

**Test Commands:**
```bash
# Run full test suite
cd zCloud && python3 zTest.py

# Test specific event types
spark --ui zUI.zContainers.zolo  # Test zCrumbs
spark --dash @.UI.zAccount       # Test zDash
spark --session                  # Test zSession
```

### 8.2 Update Documentation

**Files to Update:**
- Module docstrings (all new files)
- `zDisplay/README.md` (architecture overview)
- `zOS/Documentation/zDisplay.md` (event reference)
- CHANGELOG.md (note refactoring completion)

### 8.3 Performance Validation

**Metrics to Check:**
- Import time (should be same or faster)
- Event rendering time (should be same)
- Memory usage (should be same or lower)

---

## Estimated Impact Summary

| Phase | Files Changed | Lines Before | Lines After | Net Change | Risk Level |
|-------|---------------|--------------|-------------|------------|------------|
| 1. Cleanup | 3 | +500 (pollution) | 0 | -500 | Low |
| 2. Infrastructure | 3 new | 0 | +300 | +300 | Medium |
| 3. system refactor | 6 new + 1 update | 2,386 | 1,800 | -586 | High |
| 4. timebased refactor | 3 new + 1 update | 1,219 | 900 | -319 | Medium |
| 5. advanced refactor | 3 new + 1 update | 1,049 | 800 | -249 | Medium |
| 6. interaction refactor | 6 new + 2 update | 1,819 | 1,400 | -419 | Low |
| 7. constants refactor | 7 new + 1 update | 418 | 500 | +82 | Low |
| **TOTAL** | **31 files** | **7,391 lines** | **5,700 lines** | **-1,691 lines** | **Medium** |

**DRY Savings:** ~1,691 lines removed due to:
- Eliminated duplication (mode detection, event IDs, WebSocket emission)
- Extracted common helpers (field rendering, section display, logging)
- Removed pollution (tests, backups, duplicates)

**Maintainability Gain:**
- Average file size: 2,386 lines → 250 lines (9.5x improvement)
- Single responsibility per module
- Easier testing (unit tests per module)
- Easier debugging (smaller surface area)

---

## Success Criteria

### Phase 1 Success:
- ✅ No duplicate files
- ✅ No test files in production code
- ✅ No backup files in production
- ✅ All imports updated and working

### Phase 2 Success:
- ✅ Infrastructure helpers created and tested
- ✅ At least 3 event files using new helpers
- ✅ DRY violations eliminated

### Phase 3 Success:
- ✅ `display_event_system.py` reduced to <300 lines
- ✅ 5 new focused modules created
- ✅ All integration tests passing
- ✅ No changes to public API

### Phases 4-7 Success:
- ✅ All monolithic files (<500 lines)
- ✅ Coordinator pattern applied consistently
- ✅ All integration tests passing

### Final Success:
- ✅ All phases complete
- ✅ Total lines reduced by >1,500
- ✅ No file >500 lines
- ✅ 100% test coverage maintained
- ✅ Documentation updated
- ✅ Performance benchmarks met

---

## Risk Mitigation

### High-Risk Phase (Phase 3 - system refactor)

**Risks:**
1. Breaking public API
2. Breaking cross-references (BasicOutputs, Signals, BasicInputs)
3. Breaking session access patterns
4. Breaking logger integration

**Mitigation:**
1. Keep all public method signatures identical (delegation)
2. Test cross-references after each sub-class creation
3. Use SESSION_KEY_* constants (already done)
4. Extract logging helpers first (Phase 2)

**Rollback Plan:**
- Git branch for each phase
- Keep old file until all tests pass
- Gradual deprecation (old → new over 2 weeks)

---

## Timeline Estimate

| Phase | Duration | Complexity |
|-------|----------|------------|
| Phase 1: Cleanup | 1 hour | Simple |
| Phase 2: Infrastructure | 2 hours | Medium |
| Phase 3: system refactor | 8 hours | High |
| Phase 4: timebased refactor | 4 hours | Medium |
| Phase 5: advanced refactor | 4 hours | Medium |
| Phase 6: interaction refactor | 4 hours | Low |
| Phase 7: constants refactor | 2 hours | Low |
| Phase 8: Validation | 3 hours | Medium |
| **TOTAL** | **28 hours** | **3-4 days** |

---

## Approval & Next Steps

**Status:** ⏸️ Awaiting User Approval

**Next Step:** User reviews plan and approves Phase 1 execution

**Questions for User:**
1. Approve overall approach?
2. Approve phase order?
3. Any concerns with estimated timeline?
4. Ready to begin Phase 1?

---

**Document Version:** 1.0  
**Last Updated:** January 19, 2026  
**Author:** Codex AI (Claude Sonnet 4.5)  
**Reviewed By:** [Pending User Review]
