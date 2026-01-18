# BifrostClient Testing

Centralized location for all BifrostClient test files.

## Test Files

### 🏗️ Layer 0: Foundation Primitives (HTML Elements + Layout/Structure)

#### Micro-Step 0.0: HTML Element Primitives
- **`test_html_elements.html`** - **RAWEST PRIMITIVES (18 ELEMENT FACTORIES)**
  - Tests `createDiv()`, `createSpan()` - Generic containers
  - Tests `createParagraph()`, `createHeading(level)` - Text content (h1-h6)
  - Tests `createButton(type)`, `createLink(href)` - Interactive elements
  - Tests `createList(ordered)`, `createListItem()` - List structures
  - Tests `createInput(type)`, `createLabel(forId)`, `createForm()` - Form elements
  - Tests `createImage(src, alt)` - Media elements
  - Tests `createSection()`, `createArticle()`, `createHeader()`, `createFooter()`, `createNav()`, `createMain()` - Semantic HTML5
  - Tests composition (REBOOT philosophy: raw elements + zTheme utilities)
  - **Why FIRST?** Raw HTML building blocks for EVERYTHING. NO zTheme classes (pure HTML).
  - **Run:** Open in browser at `http://127.0.0.1:8080/bifrost/testing/test_html_elements.html`
  - **Expected:** ✅ All 18 element factories create valid semantic HTML with proper type enforcement
  - **Status:** ✅ Complete (7 test scenarios, 18 functions verified)

#### Micro-Step 0.1: Container Utilities
- **`test_container_utils.html`** - **FOUNDATIONAL LAYOUT PRIMITIVES**
  - Tests `createContainer()` - Main content containers (zContainer, zContainer-fluid)
  - Tests `createSection()` - Semantic section elements
  - Tests `createWrapper()` - Generic divs for grouping/layout
  - Tests `applyContainerStyles()` - Apply flex/grid/alignment via config
  - Tests nested container patterns (real-world structure)
  - **Why First?** Text needs a container. Containers need spacing. Everything needs structure.
  - **Run:** Open in browser at `http://127.0.0.1:8080/bifrost/testing/test_container_utils.html`
  - **Expected:** ✅ All container types render with proper zTheme classes
  - **Status:** ✅ Complete (all 5 tests passing)

#### Micro-Step 0.2: Spacing Utilities
- **`test_spacing_utils.html`** - **FOUNDATIONAL SPACING PRIMITIVES**
  - Tests `getMarginClass()` - Generate margin classes (zm-, zmt-, zmb-, zms-, zme-, zmx-, zmy-)
  - Tests `getPaddingClass()` - Generate padding classes (zp-, zpt-, zpb-, zps-, zpe-, zpx-, zpy-)
  - Tests `getGapClass()` - Generate gap classes (zGap-)
  - Tests `applySpacing()` - Apply margin/padding/gap via config
  - Tests negative margins (zm-n*, zmt-n*, zmb-n*, zmx-n*, zmy-n*)
  - **Why Second?** Layout rhythm and breathing room for all content.
  - **Run:** Open in browser at `http://127.0.0.1:8080/bifrost/testing/test_spacing_utils.html`
  - **Expected:** ✅ All spacing variations render with correct zTheme classes
  - **Status:** ✅ Complete (all 5 tests passing)

#### Micro-Step 0.3: Color Utilities
- **`test_color_utils.html`** - **FOUNDATIONAL COLOR PRIMITIVES**
  - Tests `getBackgroundClass()` - Generate background classes (zBg-primary, zBg-light, etc.)
  - Tests `getTextColorClass()` - Generate text color classes (zText-primary, zText-muted, etc.)
  - Tests `getBorderColorClass()` - Generate border color classes (zBorder-primary, etc.)
  - Tests `applyColorScheme()` - Apply background/text/border via config
  - Tests color combinations (alerts, cards, real-world patterns)
  - **Why Third?** Visual identity and semantic meaning for all content.
  - **Run:** Open in browser at `http://127.0.0.1:8080/bifrost/testing/test_color_utils.html`
  - **Expected:** ✅ All color variations render with correct zTheme classes

---

### ⚡ Core Primitives (Foundation)

#### Bootstrap Icons Auto-Load
- **`test_bootstrap_icons.html`** - **CRITICAL PRIMITIVE TEST**
  - Tests that Bootstrap Icons auto-load when BifrostClient initializes
  - Verifies icons render correctly (not empty squares)
  - NO manual import required - tests pure auto-load functionality
  - This is a **foundational feature** for ALL renderers
  - **Run:** Open in browser at `http://127.0.0.1:8080/bifrost/testing/test_bootstrap_icons.html`
  - **Expected:** ✅ Green success alert + 6 visible icons (check, x, heart, star, person, gear)

---

### Layer 2 Utilities
- **`test_utils_quick.html`** - Quick validation tests for all Layer 2 utilities
  - Tests `dom_utils.js` (createElement, appendChildren, etc.)
  - Tests `ztheme_utils.js` (getButtonColorClass, indentToHeaderTag, etc.)
  - Tests `validation_utils.js` (validateInput, isValidEmail, etc.)
  - **Run:** Open in browser at `http://127.0.0.1:8080/bifrost/testing/test_utils_quick.html`

### Layer 3 Renderers

#### Micro-Step 1: Text Renderer
- **`test_text_renderer.html`** - Tests plain text rendering (simplest primitive)
  - Tests basic text, colors, indent levels, custom classes, mixed features
  - **Run:** Open in browser at `http://127.0.0.1:8080/bifrost/testing/test_text_renderer.html`

#### Micro-Step 2: Header Renderer
- **`test_header_renderer.html`** - Tests semantic header rendering (h1-h6)
  - Tests all header levels (indent 1→h1, 6→h6)
  - Tests colors, custom classes, indent 0 warning
  - **Run:** Open in browser at `http://127.0.0.1:8080/bifrost/testing/test_header_renderer.html`

#### Micro-Step 3: Alert Renderer
- **`test_alert_renderer.html`** - Tests signal/alert rendering (zSignals)
  - Tests all 4 alert types (success, info, warning, error)
  - Tests indent levels, zTheme zSignal classes
  - **Run:** Open in browser at `http://127.0.0.1:8080/bifrost/testing/test_alert_renderer.html`

#### Micro-Step 4: List Renderer
- **`test_list_renderer.html`** - Tests list rendering (bullet and numbered)
  - Tests bullet lists (ul), numbered lists (ol)
  - Tests indent levels, empty lists, zTheme zList classes
  - **Run:** Open in browser at `http://127.0.0.1:8080/bifrost/testing/test_list_renderer.html`

#### Micro-Step 5: Table Renderer
- **`test_table_renderer.html`** - Tests zTable rendering (data tables with pagination)
  - Tests array rows, object rows (SQL-style)
  - Tests titles, empty tables, pagination metadata
  - Tests data type formatting (dates, booleans, nulls, numbers, objects)
  - **Run:** Open in browser at `http://127.0.0.1:8080/bifrost/testing/test_table_renderer.html`

#### Micro-Step 8: Button Renderer (OUT OF ORDER - revisit later)
- **`test_button_renderer.html`** - Tests interactive button rendering
  - ⚠️ Created out of order (should be after simpler renderers)
  - Will be revisited after Micro-Steps 4-7 complete
  - **Run:** Open in browser at `http://127.0.0.1:8080/bifrost/testing/test_button_renderer.html`

## Testing Philosophy

1. **Terminal First** - Start with simplest primitives (text, headers)
2. **Pure Rendering** - No WebSocket, no state, no side effects
3. **Layer 2 Utilities** - All renderers use utilities exclusively
4. **100% Testable** - Each renderer has isolated test file
5. **zTheme Only** - No custom CSS for components (only body background)

## Running Tests

All tests require ES6 module support, so they must be served via HTTP:

```bash
# From workspace root
# Tests are available at: http://127.0.0.1:8080/bifrost/testing/
# (zServer should already be running)
```

## Import Paths

Test files use relative imports from `bifrost/testing/` to `bifrost/src/`:

```javascript
// Example from test_text_renderer.html
import { TextRenderer } from '../src/rendering/text_renderer.js';

// Example from test_utils_quick.html
import { createElement } from '../src/utils/dom_utils.js';
```

## Next Tests to Add

As we complete more micro-steps:
- ~~`test_alert_renderer.html` (Micro-Step 3)~~ ✅ Complete
- ~~`test_list_renderer.html` (Micro-Step 4)~~ ✅ Complete
- ~~`test_table_renderer.html` (Micro-Step 5)~~ ✅ Complete
- `test_form_renderer.html` (Micro-Step 6)
- `test_input_renderer.html` (Micro-Step 7)

