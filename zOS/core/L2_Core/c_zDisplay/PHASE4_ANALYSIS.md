# Phase 4: display_event_timebased.py Decomposition Analysis

**Date:** January 19, 2026  
**Status:** ⏳ ANALYZED - Ready for Implementation

## Current Structure (1,219 lines)

**Class:** `TimeBased` (single monolithic class)

**Public Methods:**
1. `progress_bar()` (lines 565-729) - 164 lines - Visual progress indicator
2. `spinner()` (lines 730-852) - 122 lines - Animated loading spinner
3. `progress_iterator()` (lines 853-900) - 47 lines - Iterator wrapper with auto-progress
4. `indeterminate_progress()` (lines 901-958) - 57 lines - Indefinite progress feedback
5. `swiper()` (lines 959-1219) - 260 lines - Interactive content carousel

**Total Public Methods:** 650 lines  
**Infrastructure:** ~569 lines (imports, constants, helpers, `__init__`)

## Decomposition Strategy

### Module 1: timebased_progress.py (~450 lines)

**Purpose:** Progress tracking and visualization

**Methods:**
- `progress_bar()` - Main progress bar with percentage/ETA
- `progress_iterator()` - Wrap any iterable with progress tracking
- `indeterminate_progress()` - Progress without known total

**Shared Infrastructure:**
- Progress rendering helpers
- ETA calculation
- Terminal progress bar drawing
- WebSocket progress events

**Lines:** 164 + 47 + 57 + ~180 infrastructure = ~450 lines

### Module 2: timebased_spinner.py (~250 lines)

**Purpose:** Animated loading indicators

**Methods:**
- `spinner()` - Context manager for indefinite operations

**Shared Infrastructure:**
- Spinner frame styles (dots, line, arc, arrow, bouncingBall)
- Animation thread management
- Terminal animation loop
- WebSocket spinner events

**Lines:** 122 + ~130 infrastructure = ~250 lines

### Module 3: timebased_swiper.py (~350 lines)

**Purpose:** Interactive content carousel

**Methods:**
- `swiper()` - Multi-slide carousel with navigation

**Shared Infrastructure:**
- Keyboard input handling (termios)
- Auto-advance threading
- Box-drawing UI
- Slide navigation
- WebSocket swiper events

**Lines:** 260 + ~90 infrastructure = ~350 lines

### Module 4: display_event_timebased.py (Coordinator, ~170 lines)

**Purpose:** Compose all 3 specialized modules

**New Structure:**
```python
class TimeBased:
    """TimeBased Events Coordinator (v2.0 - Refactored)."""
    
    def __init__(self, display_instance):
        self.display = display_instance
        
        # Compose specialized modules
        self._progress = ProgressEvents(display_instance)
        self._spinner = SpinnerEvents(display_instance)
        self._swiper = SwiperEvents(display_instance)
    
    # Delegation methods
    def progress_bar(self, *args, **kwargs):
        return self._progress.progress_bar(*args, **kwargs)
    
    def spinner(self, *args, **kwargs):
        return self._spinner.spinner(*args, **kwargs)
    
    def progress_iterator(self, *args, **kwargs):
        return self._progress.progress_iterator(*args, **kwargs)
    
    def indeterminate_progress(self, *args, **kwargs):
        return self._progress.indeterminate_progress(*args, **kwargs)
    
    def swiper(self, *args, **kwargs):
        return self._swiper.swiper(*args, **kwargs)
```

**Lines:** ~170 lines (imports, class, delegation)

## Impact Metrics

- **Before:** 1,219 lines (monolithic)
- **After:** ~1,220 lines (coordinator + 3 modules)
- **Change:** +1 line (minimal overhead)
- **Files:** 1 → 4 (modular architecture)
- **Largest module:** 450 lines (vs. 1,219 lines original)

## Benefits

1. **Single Responsibility:** Each module focused on one type of temporal feedback
2. **Easier Testing:** Test progress, spinner, swiper independently
3. **Clearer Organization:** Related methods grouped together
4. **Maintainability:** Find bugs in ~250-450 line files, not 1,219-line monolith
5. **Parallel Development:** Different developers can work on different modules

## Implementation Steps

1. ✅ **Analyze structure** - Understand method boundaries and dependencies
2. ⏳ **Create timebased_progress.py** - Extract progress-related methods
3. ⏳ **Create timebased_spinner.py** - Extract spinner method
4. ⏳ **Create timebased_swiper.py** - Extract swiper method
5. ⏳ **Update display_event_timebased.py** - Transform to coordinator
6. ⏳ **Validate with zTest.py** - Ensure no regressions

## Risk Assessment

**Risk Level:** Medium

**Challenges:**
- **Threading complexity:** Spinner and swiper use background threads
- **State management:** Active state tracking for WebSocket events
- **Terminal capabilities:** Carriage return support detection
- **Context managers:** Proper cleanup in finally blocks

**Mitigation:**
- Careful extraction of shared threading helpers
- Preserve exact context manager behavior
- Test in both Terminal and Bifrost modes
- Validate thread cleanup (no resource leaks)

## Next Steps

After Phase 4 completion, continue to:
- **Phase 5:** Decompose remaining event modules
- **Phase 6:** Extract shared constants
- **Phase 7:** Comprehensive testing
- **Phase 8:** Documentation update
