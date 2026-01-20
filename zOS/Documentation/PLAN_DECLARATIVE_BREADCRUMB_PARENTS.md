# Declarative Breadcrumb Parents - Implementation Plan

**Feature**: Add `_parent` parameter to `zCrumbs` display event for stateless breadcrumb generation  
**Primary Use Case**: Bifrost/GUI direct URL access (no session state)  
**Status**: Planning  
**Created**: 2026-01-20

---

## Executive Summary

### Problem Statement
- **Current**: Breadcrumbs rely on session state (user navigation history)
- **Issue**: Bifrost users accessing pages via direct URL see no breadcrumbs (empty session)
- **Impact**: Poor UX for bookmarked pages, search engine links, shared URLs

### Proposed Solution
Allow declarative parent hierarchy in `.zolo` files:

```yaml
Show_Breadcrumbs:
    zDisplay:
        event: zCrumbs
        _parent: @.UI.zProducts.zUI.zTheme
```

**Behavior:**
- Session crumbs exist → Use session (actual user path) ✅
- Session empty + `_parent` → Build synthetic trail from parent hierarchy ✅
- Both empty → Skip display (graceful degradation) ✅

---

## Design Checkpoints

### 🔴 **Checkpoint 1: Path Syntax Decision**

**Options:**

**A. Absolute Only** (MVP)
```yaml
_parent: @.UI.zProducts.zUI.zTheme
```
- ✅ Simple, unambiguous
- ✅ Familiar `@` syntax
- ❌ Verbose, not portable

**B. Relative with `;` Modifier**
```yaml
_parent: ;.zUI.zTheme         # One level up (..)
_parent: ;.;.zUI.zTheme       # Two levels up (../..)
```
- ✅ Cleaner, portable
- ✅ Semantic (`;` = up one level)
- ⚠️ Requires current path resolution

**C. Filename Shorthand**
```yaml
_parent: zUI.zTheme   # Same directory assumed
```
- ✅ Ultra-clean for siblings
- ⚠️ Ambiguous if filename matches folder name

**Decision Point**: Start with **A (Absolute)**, add **B (Relative)** in Phase 3, add **C (Shorthand)** in Phase 4

---

### 🔴 **Checkpoint 2: Block Scope Decision**

**Question**: Should `_parent` reference files or blocks?

**Option 1: File-Level Only** (Recommended)
```yaml
_parent: @.UI.zProducts.zUI.zTheme
# Resolves to: Home → Products → zTheme → [Current]
```
- ✅ Clean breadcrumb hierarchy
- ✅ Matches typical website navigation
- ❌ Can't reference specific blocks

**Option 2: Block-Level Allowed**
```yaml
_parent: @.UI.zProducts.zUI.zTheme.zTheme_Details
# Resolves to: Home → Products → zTheme → Theme Details → [Current]
```
- ✅ Granular control
- ⚠️ More complex, less common use case

**Decision Point**: Support **file-level** by default, allow **optional block suffix** for granularity

---

### 🔴 **Checkpoint 3: Priority/Conflict Resolution**

**Scenario**: Both session crumbs AND `_parent` exist

**Option A: Session Wins** (Recommended)
- Session trail = actual user path (higher fidelity)
- `_parent` = fallback for cold starts only

**Option B: Merge**
- Session trail + parent context
- Complex, might create misleading paths

**Option C: `_parent` Wins**
- Override session with declared hierarchy
- Use case: Force canonical breadcrumb structure

**Decision Point**: **Option A** for MVP, add `_parent_mode` parameter in Phase 5 for options B/C

---

### 🔴 **Checkpoint 4: Display Name Resolution**

**Question**: How to get human-readable names for breadcrumb segments?

**Option 1: Use `zMeta.zTitle` from Files**
```python
# Load @.UI.zProducts.zUI.zTheme
# Extract: zMeta.zTitle = "zTheme Framework"
# Display: "zTheme Framework"
```
- ✅ Semantic, uses existing metadata
- ⚠️ Requires file loading (performance)

**Option 2: Use Filename Transform**
```python
# Path: @.UI.zProducts.zUI.zTheme
# Transform: "zUI.zTheme" → "zTheme"
# Display: "zTheme"
```
- ✅ Fast, no I/O
- ❌ Less semantic

**Option 3: Hybrid with Caching**
```python
# 1. Check cache for @.UI.zProducts.zUI.zTheme
# 2. If miss: Load file, extract zMeta.zTitle, cache
# 3. Fallback to filename transform if no zTitle
```
- ✅ Best UX, performant after warmup
- ✅ Graceful degradation

**Decision Point**: **Option 3 (Hybrid)** with LRU cache (100 entries)

---

## Phase Breakdown

### **Phase 0: Foundation - Bifrost Rendering Support**
**Goal**: Get basic `zCrumbs` display event working in Bifrost (GUI mode)

**Current Issue**: Backend sends `zCrumbs` event, but Bifrost frontend shows `[zCrumbs]` placeholder

#### **Step 0.1: Backend Audit**
**Tasks:**
1. ✅ Confirm `_parent` parameter syntax is valid (underscore-prefixed metadata)
2. ✅ Verify `zDisplay` event handler supports optional parameters
3. ✅ Verify backend sends `_EVENT_ZCRUMBS` event with proper structure
4. ⚠️ Audit `zNavigation.linking` for path resolution utilities (Phase 2)
5. ⚠️ Audit `zLoader` for `zMeta` extraction capabilities (Phase 2)
6. ⚠️ Check `zServer` routing for file-to-URL mapping (Phase 2)

**Backend Event Structure** (from `system_event_navigation.py`):
```python
# Event sent to Bifrost
event_type = "_EVENT_ZCRUMBS"
event_data = {
    "_KEY_CRUMBS": {
        "trails": {
            "file": ["Main", "Setup", "Config"],
            "vafile": ["App", "Database"],
            "block": ["^Root*", "User Management"]
        },
        "_context": {...},  # Internal metadata
        "_depth_map": {...}  # Internal metadata
    }
}
```

#### **Step 0.2: Frontend Event Handler**
**File**: `zOS/zTheme/js/zdisplay.js` (or similar Bifrost client file)

**Task**: Add event handler for `zCrumbs` display event

**Implementation**:
```javascript
// Add to event handler registry
eventHandlers['zCrumbs'] = function(eventData) {
    const crumbsData = eventData._KEY_CRUMBS || eventData.crumbs || {};
    const trails = crumbsData.trails || {};
    
    // Build Bootstrap breadcrumb HTML
    const breadcrumbHtml = buildBreadcrumbHtml(trails);
    
    // Insert into current block or create new element
    return createDOMElement('nav', {
        'aria-label': 'breadcrumb',
        'class': 'breadcrumb-nav',
        innerHTML: breadcrumbHtml
    });
};
```

#### **Step 0.3: Bootstrap Breadcrumb Renderer**
**File**: `zOS/zTheme/js/zdisplay.js` (helper function)

**Task**: Create HTML renderer for breadcrumb trails using Bootstrap classes

**Implementation**:
```javascript
function buildBreadcrumbHtml(trails) {
    // Skip internal metadata keys
    const visibleTrails = Object.entries(trails).filter(([key]) => !key.startsWith('_'));
    
    if (visibleTrails.length === 0) return '';
    
    let html = '<nav aria-label="breadcrumb">';
    
    // Render each trail (file, vafile, block)
    visibleTrails.forEach(([scope, trail]) => {
        if (!Array.isArray(trail) || trail.length === 0) return;
        
        html += `<ol class="breadcrumb">`;
        
        // Add scope label (optional, can be styled differently)
        // html += `<li class="breadcrumb-item text-muted">${scope}</li>`;
        
        trail.forEach((item, index) => {
            const isLast = (index === trail.length - 1);
            const itemClass = isLast ? 'breadcrumb-item active' : 'breadcrumb-item';
            const ariaAttr = isLast ? ' aria-current="page"' : '';
            
            if (isLast) {
                html += `<li class="${itemClass}"${ariaAttr}>${escapeHtml(item)}</li>`;
            } else {
                // Non-active items could be links (Phase 2: add routing)
                html += `<li class="${itemClass}"><a href="#" data-breadcrumb-segment="${escapeHtml(item)}">${escapeHtml(item)}</a></li>`;
            }
        });
        
        html += `</ol>`;
    });
    
    html += '</nav>';
    return html;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
```

#### **Step 0.4: CSS Styling (Bootstrap Integration)**
**File**: `zOS/zTheme/css/ztheme.css` or inline in component

**Task**: Ensure Bootstrap breadcrumb styles are loaded/available

**Check**:
```css
/* Bootstrap breadcrumb styles should already exist in zTheme */
.breadcrumb {
    display: flex;
    flex-wrap: wrap;
    padding: 0.75rem 1rem;
    margin-bottom: 1rem;
    list-style: none;
    background-color: #e9ecef;
    border-radius: 0.25rem;
}

.breadcrumb-item + .breadcrumb-item::before {
    content: "›"; /* or "/" */
    padding-right: 0.5rem;
    padding-left: 0.5rem;
    color: #6c757d;
}

.breadcrumb-item.active {
    color: #6c757d;
}
```

**Action**: Verify zTheme has these styles, add if missing

#### **Step 0.5: Integration Testing**
**Test File**: `zCloud/UI/zProducts/zTheme/zUI.zContainers.zolo`

**Test Case**:
```yaml
Show_Breadcrumbs:
    zDisplay:
        event: zCrumbs
```

**Expected Behavior**:
- **Terminal**: Displays text-based breadcrumb banner (already works)
- **Bifrost**: Displays Bootstrap breadcrumb component (NEW)
- **Session with trails**: Shows actual navigation path
- **Empty session**: Shows nothing (graceful degradation) or minimal "Home" breadcrumb

#### **Step 0.6: Actual Implementation (Files Located)**
**Task**: Add `zCrumbs` event handler to Bifrost client

**✅ Confirmed Architecture**:
- **Backend**: `system_event_navigation.py` sends `_EVENT_ZCRUMBS` event
- **Bifrost Client**: 
  - `zOS/bifrost/src/rendering/zdisplay_orchestrator.js` - Routes zDisplay events
  - `zOS/bifrost/src/rendering/zdisplay_renderer.js` - Renders display primitives

**Current Issue**: 
- `zdisplay_orchestrator.js:renderZDisplayEvent()` has NO `case 'zCrumbs':` handler
- Unknown events fall through to default case (line 811-818) which shows `[zCrumbs]`

**Implementation Steps**:

**A. Add zCrumbs Case to Orchestrator**
**File**: `zOS/bifrost/src/rendering/zdisplay_orchestrator.js:714-822`

**Insert new case** (after line 808, before `case 'zDash':`):
```javascript
case 'zCrumbs': {
  // Use modular NavigationRenderer for breadcrumbs (Bootstrap compatible)
  const navRenderer = await this.client._ensureNavigationRenderer();
  element = navRenderer.renderBreadcrumbs(eventData);
  this.logger.log('[renderZDisplayEvent] Rendered breadcrumbs element');
  break;
}
```

**B. Add Breadcrumb Event Handler to NavigationRenderer**
**File**: `zOS/bifrost/src/rendering/navigation_renderer.js:365-424`

**✅ Found**: `renderBreadcrumb(trail, options)` method already exists (renders single trail)

**Add new wrapper method** (after existing `renderBreadcrumb` at line 424):
```javascript
/**
 * Render breadcrumbs from zCrumbs display event (handles multiple trails)
 * @param {Object} eventData - Event data from backend zCrumbs event
 * @returns {HTMLElement} - Container with all breadcrumb trails
 */
renderBreadcrumbs(eventData) {
  // Extract crumbs data from event (backend sends in _KEY_CRUMBS or crumbs)
  const crumbsData = eventData.crumbs || eventData._KEY_CRUMBS || {};
  const trails = crumbsData.trails || {};
  
  // Filter out internal metadata (_context, _depth_map)
  const visibleTrails = Object.entries(trails).filter(([key]) => !key.startsWith('_'));
  
  if (visibleTrails.length === 0) {
    this.logger.log('[NavigationRenderer] No visible breadcrumb trails');
    return null; // No breadcrumbs to display
  }
  
  this.logger.log(`[NavigationRenderer] Rendering ${visibleTrails.length} breadcrumb trails`);
  
  // Create container for all trails (using primitive)
  const container = createDiv({ class: 'zBreadcrumbs-container zmb-3' });
  
  // Render each trail (file, vafile, block) using existing renderBreadcrumb method
  visibleTrails.forEach(([scope, trail]) => {
    if (!Array.isArray(trail) || trail.length === 0) return;
    
    // Add scope label (optional, for multi-trail displays)
    if (visibleTrails.length > 1) {
      const scopeLabel = createSpan({ class: 'zText-muted zSmall zFw-bold' });
      scopeLabel.textContent = `${scope}: `;
      container.appendChild(scopeLabel);
    }
    
    // Use existing renderBreadcrumb method for single trail
    const breadcrumbNav = this.renderBreadcrumb(trail, {
      className: `zBreadcrumb-${scope}`
    });
    
    if (breadcrumbNav) {
      container.appendChild(breadcrumbNav);
    }
  });
  
  return container;
}
```

**Note**: This reuses the existing `renderBreadcrumb` method, maintaining DRY principles

**C. Verify Breadcrumb CSS Styles**
**File**: `zOS/zTheme/src/css/zBreadcrumb.css`

**✅ Confirmed**: zTheme already has Bootstrap-compatible breadcrumb styles
- `.zBreadcrumb` - Base breadcrumb container
- `.zBreadcrumb-item` - Individual breadcrumb items
- `.zBreadcrumb-item.zActive` - Active (current page) item
- Auto-generated dividers using `::before` pseudo-element
- Responsive design for mobile
- Customizable dividers via CSS variables

**No changes needed** - existing styles are production-ready

**Deliverable**: 
- ✅ Bifrost renders breadcrumbs as Bootstrap component
- ✅ Terminal rendering still works (no regression)
- ✅ Test passes in both modes
- ✅ Foundation ready for `_parent` parameter (Phase 1)

---

### **Phase 1: Core Parser & Absolute Path Support**
**Goal**: Handle `_parent: @.UI.zProducts.zUI.zTheme` (absolute paths only)

#### **Step 1.1: Update Event Signature**
**File**: `zOS/core/L2_Core/c_zDisplay/zDisplay_modules/f_orchestration/system_event_navigation.py`

**Change**:
```python
def zCrumbs(
    self, 
    session_data: Optional[Dict[str, Any]] = None,
    _parent: Optional[str] = None  # NEW
) -> None:
```

**Propagate to**:
- `display_event_system.py:zCrumbs()`
- `display_events.py:zCrumbs()`

#### **Step 1.2: Create Path Parser Module**
**File**: `zOS/core/L2_Core/c_zDisplay/zDisplay_modules/a_infrastructure/breadcrumb_path_parser.py` (NEW)

**Functions**:
```python
def parse_parent_path(parent_path: str, current_file: str) -> ParsedPath:
    """
    Parse _parent path string into structured format.
    
    Phase 1: Only absolute paths (@.UI.zProducts...)
    Phase 3: Add relative (;.UI.zProducts...)
    Phase 4: Add shorthand (zUI.zTheme)
    
    Returns:
        ParsedPath(type='absolute', segments=['UI', 'zProducts', 'zUI.zTheme'], block=None)
    """
    pass

def validate_parent_path(parent_path: str) -> Tuple[bool, Optional[str]]:
    """Validate path syntax, return (is_valid, error_message)."""
    pass
```

**Tests**: Unit tests for valid/invalid paths

#### **Step 1.3: Integrate Parser into zCrumbs**
**File**: `system_event_navigation.py:zCrumbs()`

**Logic**:
```python
def zCrumbs(self, session_data=None, _parent=None):
    # Auto-inject session
    if session_data is None and hasattr(self.display, 'zcli'):
        session_data = self.display.zcli.session
    
    # Priority 1: Session crumbs (actual user path)
    z_crumbs = session_data.get(SESSION_KEY_ZCRUMBS, {}) if session_data else {}
    
    # Priority 2: Declarative parent (fallback for cold starts)
    if not z_crumbs and _parent:
        from .a_infrastructure.breadcrumb_path_parser import parse_parent_path
        parsed = parse_parent_path(_parent, session_data.get('zVaFile'))
        z_crumbs = self._build_crumbs_from_parent(parsed, session_data)
    
    # Rest of existing logic...
```

#### **Step 1.4: Build Synthetic Crumbs**
**File**: `system_event_navigation.py` (NEW METHOD)

**Method**:
```python
def _build_crumbs_from_parent(
    self, 
    parsed_path: ParsedPath, 
    session: Dict
) -> Dict[str, Any]:
    """
    Generate breadcrumb trail from parsed parent path.
    
    Phase 1: Simple segment list (no display name resolution)
    Phase 2: Add display name resolution with caching
    
    Returns:
        Enhanced breadcrumb dict: {'trails': {...}, '_context': {...}}
    """
    # Phase 1 MVP: Use raw segments
    current_file = session.get('zVaFile', 'unknown')
    trail = parsed_path.segments + [current_file.split('.')[-1]]
    
    return {
        'trails': {current_file: trail},
        '_context': {
            'last_operation': 'SYNTHETIC',
            'source': 'declarative_parent',
            'parent_path': parsed_path.full_path
        }
    }
```

**Deliverable**: Absolute paths work, display raw segment names

---

### **Phase 2: Display Name Resolution & Caching**
**Goal**: Resolve segments to human-readable names using `zMeta.zTitle`

#### **Step 2.1: Create Display Name Resolver**
**File**: `zOS/core/L2_Core/c_zDisplay/zDisplay_modules/a_infrastructure/breadcrumb_name_resolver.py` (NEW)

**Class**:
```python
class BreadcrumbNameResolver:
    """
    Resolve zPath segments to display names with caching.
    
    Resolution Strategy:
    1. Check LRU cache (100 entries, TTL 5min)
    2. Try zMeta.zTitle from zLoader
    3. Fallback to filename transform
    """
    def __init__(self, zcli):
        self.zcli = zcli
        self._cache = {}  # LRU cache
        self._max_cache_size = 100
    
    def resolve(self, zpath: str) -> str:
        """Resolve @.UI.zProducts.zUI.zTheme → "zTheme Framework"."""
        pass
    
    def _load_title_from_file(self, zpath: str) -> Optional[str]:
        """Load zMeta.zTitle using zLoader."""
        pass
    
    def _transform_filename(self, segment: str) -> str:
        """zUI.zTheme → zTheme (fallback)."""
        pass
```

#### **Step 2.2: Integrate Resolver**
**File**: `system_event_navigation.py:_build_crumbs_from_parent()`

**Update**:
```python
def _build_crumbs_from_parent(self, parsed_path, session):
    resolver = BreadcrumbNameResolver(self.display.zcli)
    
    # Resolve each segment to display name
    trail = []
    for segment in parsed_path.segments:
        full_path = '@.' + '.'.join(parsed_path.segments[:parsed_path.segments.index(segment)+1])
        display_name = resolver.resolve(full_path)
        trail.append(display_name)
    
    # Add current page
    current_display = resolver.resolve(session.get('zVaFile'))
    trail.append(current_display)
    
    return {'trails': {session.get('zVaFile'): trail}, ...}
```

**Deliverable**: Breadcrumbs show "Products → zTheme" instead of "zProducts → zUI.zTheme"

---

### **Phase 3: Relative Path Support (`;` Modifier)**
**Goal**: Support `_parent: ;.zUI.zTheme` (one level up)

#### **Step 3.1: Design Checkpoint - `;` Syntax**
**Decision**: `;` = one level up (like `..` in file systems)

**Examples**:
```yaml
# Current file: @.UI.zProducts.zTheme.zUI.zContainers
_parent: ;.zUI.zTheme               # → @.UI.zProducts.zUI.zTheme
_parent: ;.;.zUI.zProducts          # → @.UI.zUI.zProducts
_parent: ;.;.;.UI                   # → @.UI
```

**Edge Case**: `;` at root (`@`) should error or resolve to `@` (application root)

#### **Step 3.2: Update Parser**
**File**: `breadcrumb_path_parser.py:parse_parent_path()`

**Logic**:
```python
def parse_parent_path(parent_path: str, current_file: str) -> ParsedPath:
    # Absolute path (existing)
    if parent_path.startswith('@.'):
        return ParsedPath(type='absolute', ...)
    
    # Relative path (NEW)
    if parent_path.startswith(';'):
        return _parse_relative_path(parent_path, current_file)
    
    # Shorthand (Phase 4)
    return _parse_shorthand(parent_path, current_file)

def _parse_relative_path(parent_path: str, current_file: str) -> ParsedPath:
    """
    Parse relative path with ; modifiers.
    
    Example:
        parent_path = ';.zUI.zTheme'
        current_file = '@.UI.zProducts.zTheme.zUI.zContainers'
        
        Steps:
        1. Count ; prefixes → 1 (one level up)
        2. Split current_file → ['UI', 'zProducts', 'zTheme', 'zUI', 'zContainers']
        3. Go up 1 level → ['UI', 'zProducts', 'zTheme', 'zUI']
        4. Append rest of parent_path → ['UI', 'zProducts', 'zTheme', 'zUI', 'zUI.zTheme']
        5. Deduplicate → ['UI', 'zProducts', 'zUI.zTheme']
    """
    pass
```

#### **Step 3.3: Validation**
**File**: `breadcrumb_path_parser.py:validate_parent_path()`

**Checks**:
- Too many `;` (exceeds current depth) → Error
- `;` at root → Warning or resolve to `@`
- Mixed syntax (`@.;.UI`) → Error

**Deliverable**: Relative paths work, portable across file moves

---

### **Phase 4: Shorthand Support**
**Goal**: Support `_parent: zUI.zTheme` (same directory)

#### **Step 4.1: Design Checkpoint - Ambiguity**
**Question**: `zUI.zTheme` could be:
- Same directory: `@.UI.zProducts.zUI.zTheme`
- Subdirectory: `@.UI.zProducts.zTheme.zUI.zTheme`

**Decision**: **Same directory** (sibling file), users can use absolute for subdirectories

#### **Step 4.2: Update Parser**
**File**: `breadcrumb_path_parser.py:_parse_shorthand()`

**Logic**:
```python
def _parse_shorthand(parent_path: str, current_file: str) -> ParsedPath:
    """
    Shorthand: zUI.zTheme → same directory as current file.
    
    current_file = '@.UI.zProducts.zTheme.zUI.zContainers'
    parent_path = 'zUI.zTheme'
    
    Result: '@.UI.zProducts.zTheme.zUI.zTheme'
    """
    current_segments = current_file.split('.')[1:-1]  # Drop @ and filename
    return ParsedPath(
        type='shorthand',
        segments=current_segments + [parent_path],
        full_path='@.' + '.'.join(current_segments + [parent_path])
    )
```

**Deliverable**: Shorthand works for sibling files

---

### **Phase 5: Advanced Features (Optional)**
**Goal**: Power-user features for edge cases

#### **Feature 5.1: Parent Mode Parameter**
**Syntax**:
```yaml
Show_Breadcrumbs:
    zDisplay:
        event: zCrumbs
        _parent: @.UI.zProducts.zUI.zTheme
        _parent_mode: override  # Options: fallback, override, merge
```

**Modes**:
- `fallback` (default): Use session if available, else `_parent`
- `override`: Always use `_parent`, ignore session
- `merge`: Combine session trail + parent hierarchy

#### **Feature 5.2: Circular Reference Detection**
**File**: `breadcrumb_path_parser.py`

**Logic**:
```python
def detect_circular_reference(parent_path: str, current_file: str, visited: Set[str] = None) -> bool:
    """
    Detect circular parent references.
    
    Example:
        A._parent → B
        B._parent → C
        C._parent → A  ← CIRCULAR
    """
    pass
```

**Action**: Log error, skip breadcrumb display

#### **Feature 5.3: Multi-Path Support**
**Syntax**:
```yaml
Show_Breadcrumbs:
    zDisplay:
        event: zCrumbs
        _parents:  # Multiple parent paths
            - @.UI.zProducts.zUI.zTheme
            - @.UI.zDocs.zGuides.zTheme
```

**Use Case**: Pages with multiple navigation contexts (e.g., search results)

**Deliverable**: Edge cases handled, power users happy

---

## Testing Strategy

### **Unit Tests**
**File**: `tests/test_breadcrumb_path_parser.py`

```python
def test_parse_absolute_path():
    result = parse_parent_path('@.UI.zProducts.zUI.zTheme', '@.UI.zProducts.zTheme.zUI.zContainers')
    assert result.type == 'absolute'
    assert result.segments == ['UI', 'zProducts', 'zUI.zTheme']

def test_parse_relative_path_one_level():
    result = parse_parent_path(';.zUI.zTheme', '@.UI.zProducts.zTheme.zUI.zContainers')
    assert result.full_path == '@.UI.zProducts.zTheme.zUI.zTheme'

def test_parse_relative_path_two_levels():
    result = parse_parent_path(';.;.zUI.zProducts', '@.UI.zProducts.zTheme.zUI.zContainers')
    assert result.full_path == '@.UI.zProducts.zUI.zProducts'

def test_parse_shorthand():
    result = parse_parent_path('zUI.zTheme', '@.UI.zProducts.zTheme.zUI.zContainers')
    assert result.full_path == '@.UI.zProducts.zTheme.zUI.zTheme'

def test_validate_too_many_levels_up():
    valid, error = validate_parent_path(';.;.;.;.;.UI')  # 5 levels but file only 3 deep
    assert not valid
    assert 'exceeds current depth' in error
```

### **Integration Tests**
**File**: `zCloud/zTest_breadcrumb_parents.py`

**Scenarios**:
1. Cold start (no session) + `_parent` → Breadcrumbs show
2. Warm session + `_parent` → Session wins
3. Invalid `_parent` path → Graceful skip with log
4. Relative path across file move → Still works
5. Bifrost direct URL → Breadcrumbs render

### **Manual Testing**
**Files to Test**:
- `zCloud/UI/zProducts/zTheme/zUI.zContainers.zolo` (add `_parent`)
- Test in Terminal: `python3 zTest.py`
- Test in Bifrost: Direct URL `http://localhost:5000/zTheme/zContainers`

---

## Performance Considerations

### **Caching Strategy**
**Cache Key**: `zpath` (e.g., `@.UI.zProducts.zUI.zTheme`)  
**Cache Value**: Display name (e.g., "zTheme Framework")  
**TTL**: 5 minutes (invalidate on file changes)  
**Size**: 100 entries (LRU eviction)

**Expected Improvement**: 95% cache hit rate after warmup → <1ms lookup

### **Lazy Resolution**
- Don't resolve display names until breadcrumbs are actually displayed
- Skip resolution in Terminal if breadcrumbs are suppressed

---

## Rollout Plan

### **Phase 0-1** (Week 1)
- Audit foundation (Phase 0)
- Implement absolute path support (Phase 1)
- Test in Terminal only

### **Phase 2** (Week 2)
- Add display name resolution
- Test in Bifrost with direct URLs
- Validate caching performance

### **Phase 3-4** (Week 3)
- Add relative path support
- Add shorthand support
- Update documentation

### **Phase 5** (Optional, Week 4+)
- Advanced features (as needed)
- Community feedback integration

---

## Documentation Updates

### **Files to Update**:
1. `zOS/Documentation/zCrumbs_GUIDE.md` - Add `_parent` syntax examples
2. `AGENT.md` - Add pattern for declarative breadcrumbs
3. `zCloud/UI/zProducts/zTheme/README.md` - Add usage examples

### **New Documentation**:
- `DECLARATIVE_BREADCRUMBS_GUIDE.md` - Complete guide with all path types

---

## Success Metrics

### **Functional**
- ✅ Bifrost users see breadcrumbs on direct URL access
- ✅ Session-based crumbs still work (no regression)
- ✅ Relative paths survive file moves (portable)

### **Performance**
- ✅ <1ms breadcrumb generation (with cache)
- ✅ <50ms first load (cache miss)
- ✅ No impact on Terminal mode performance

### **Adoption**
- Target: 80% of zTheme pages use `_parent` within 1 month
- Target: 0 circular reference errors in production

---

## Risk Assessment

### **High Risk**
- **Path resolution complexity**: Many edge cases, needs thorough testing
- **Mitigation**: Extensive unit tests, Phase 0 audit

### **Medium Risk**
- **Performance impact**: Loading files for display names might be slow
- **Mitigation**: Aggressive caching, lazy evaluation

### **Low Risk**
- **Syntax confusion**: Users might mix `;` and `@` incorrectly
- **Mitigation**: Clear error messages, comprehensive docs

---

## Open Questions

1. **Should `;` work in absolute paths?** (e.g., `@.UI.;.zProducts`)
   - **Decision**: No, error. Use relative OR absolute, not both.

2. **Cache invalidation on file changes?**
   - **Decision**: Phase 6 feature, watch `.zolo` files for changes

3. **Support for external URLs as parents?**
   - **Decision**: No, breadcrumbs are internal navigation only

4. **Should `_parent` be inheritable?**
   - **Decision**: No, each file declares its own parent (explicit > implicit)

---

## Appendix: Syntax Cheat Sheet

```yaml
# Absolute path (Phase 1)
_parent: @.UI.zProducts.zUI.zTheme

# Relative - one level up (Phase 3)
_parent: ;.zUI.zTheme

# Relative - two levels up (Phase 3)
_parent: ;.;.zUI.zProducts

# Shorthand - sibling file (Phase 4)
_parent: zUI.zTheme

# With block (optional)
_parent: @.UI.zProducts.zUI.zTheme.zTheme_Details

# Override mode (Phase 5)
_parent: @.UI.zProducts.zUI.zTheme
_parent_mode: override
```

---

**Next Steps**: Approve plan → Begin Phase 0 audit → Implement Phase 1
