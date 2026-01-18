# BifrostClient Coding Patterns
## Industry-Grade JavaScript Patterns for zCLI Frontend

**Version:** 2.0  
**Last Updated:** Dec 18, 2025  
**Philosophy:** Consistency over cleverness, patterns over perfection  

---

## 📋 Table of Contents

1. [File Structure](#file-structure)
2. [Naming Conventions](#naming-conventions)
3. [Import/Export Patterns](#importexport-patterns)
4. [Function Patterns](#function-patterns)
5. [Class Patterns](#class-patterns)
6. [Error Handling](#error-handling)
7. [Logging](#logging)
8. [Testing Patterns](#testing-patterns)
9. [JSDoc Standards](#jsdoc-standards)
10. [Anti-Patterns](#anti-patterns)

---

## 📁 File Structure

### **Every file follows this structure:**

```javascript
/**
 * ═══════════════════════════════════════════════════════════════
 * [File Name] - [One-line description]
 * ═══════════════════════════════════════════════════════════════
 * 
 * [Detailed description of purpose, 2-3 sentences]
 * 
 * @module [module_name]
 * @layer [0-6]
 * @pattern [Pattern name - e.g., Facade, Strategy, Adapter]
 * 
 * Dependencies:
 * - [Layer X]: file1.js, file2.js
 * - [Layer Y]: file3.js
 * 
 * Exports:
 * - [ClassName or functionName]: [Description]
 * 
 * Example:
 * ```javascript
 * // Brief usage example
 * ```
 */

// ─────────────────────────────────────────────────────────────────
// Imports (grouped by layer, alphabetical within groups)
// ─────────────────────────────────────────────────────────────────
import { lowerLayer1 } from './lower_layer1.js';
import { lowerLayer2 } from './lower_layer2.js';

// ─────────────────────────────────────────────────────────────────
// Constants
// ─────────────────────────────────────────────────────────────────
const DEFAULT_TIMEOUT = 5000;
const MAX_RETRIES = 3;

// ─────────────────────────────────────────────────────────────────
// Private Helpers (if needed)
// ─────────────────────────────────────────────────────────────────
function _privateHelper() {
  // Implementation
}

// ─────────────────────────────────────────────────────────────────
// Main Implementation
// ─────────────────────────────────────────────────────────────────
export class MyClass {
  // Implementation
}

// OR

export function myFunction() {
  // Implementation
}
```

---

## 🏷️ Naming Conventions

### **Files**
```
snake_case.js       ✅ GOOD: dom_utils.js, button_renderer.js
camelCase.js        ❌ BAD: domUtils.js, buttonRenderer.js
PascalCase.js       ❌ BAD: DomUtils.js
kebab-case.js       ❌ BAD: dom-utils.js
```

### **Classes**
```javascript
class PascalCase { }           ✅ GOOD: ButtonRenderer, DashboardManager
class camelCase { }            ❌ BAD
class snake_case { }           ❌ BAD
```

### **Functions**
```javascript
function camelCase() { }       ✅ GOOD: createElement, getButtonColor
function PascalCase() { }      ❌ BAD
function snake_case() { }      ❌ BAD
```

### **Constants**
```javascript
const SCREAMING_SNAKE_CASE     ✅ GOOD: MAX_RETRIES, DEFAULT_TIMEOUT
const camelCase                ❌ BAD
```

### **Private Methods**
```javascript
class MyClass {
  _privateThing() { }          ✅ GOOD: _handleClick, _fetchData
  privateThing() { }           ❌ BAD (no underscore prefix)
}
```

### **Boolean Variables**
```javascript
const isReady                  ✅ GOOD: isReady, hasError, canRetry
const ready                    ❌ BAD (unclear)
```

---

## 📦 Import/Export Patterns

### **Import Grouping**

```javascript
// 1. External libraries (if any)
import Swiper from 'swiper';

// 2. Layer 0 (Browser APIs - rarely imported directly)
// (none - use directly)

// 3. Layer 1 (Core primitives)
import { Logger } from '../core/logger.js';
import { StorageManager } from '../core/storage_manager.js';

// 4. Layer 2 (Utils)
import { createElement, appendChildren } from '../utils/dom_utils.js';
import { getButtonColorClass } from '../utils/ztheme_utils.js';

// 5. Layer 3 (Renderers) - only in managers
import { ButtonRenderer } from '../rendering/button_renderer.js';

// Blank line before code
```

### **Named Exports (Preferred)**

```javascript
// ✅ GOOD - Named exports
export function createElement(tag) { }
export function appendChildren(parent, children) { }

// Usage
import { createElement, appendChildren } from './dom_utils.js';
```

### **Default Exports (Classes Only)**

```javascript
// ✅ ACCEPTABLE - Default export for classes
export default class ButtonRenderer {
  // ...
}

// Usage
import ButtonRenderer from './button_renderer.js';
```

### **NO Wildcard Imports**

```javascript
// ❌ BAD - Unclear what's being imported
import * as DomUtils from './dom_utils.js';

// ✅ GOOD - Explicit imports
import { createElement, appendChildren } from './dom_utils.js';
```

---

## 🔧 Function Patterns

### **Pure Functions (Layer 2 - Utils)**

```javascript
/**
 * Get zTheme button color class from zCLI color name
 * @param {string} zColor - zCLI color (primary, danger, etc)
 * @returns {string} zTheme class (zBtnPrimary, etc)
 */
export function getButtonColorClass(zColor) {
  // 1. Use lookup tables, not if/else chains
  const BUTTON_COLOR_MAP = {
    'primary': 'zBtnPrimary',
    'secondary': 'zBtnSecondary',
    'success': 'zBtnSuccess',
    'danger': 'zBtnDanger',
    'warning': 'zBtnWarning',
    'info': 'zBtnInfo',
    'light': 'zBtnLight',
    'dark': 'zBtnDark'
  };
  
  // 2. Normalize input (case-insensitive)
  const normalized = zColor?.toLowerCase() || 'primary';
  
  // 3. Return with fallback
  return BUTTON_COLOR_MAP[normalized] || 'zBtnPrimary';
}

// ✅ Characteristics:
// - No side effects
// - Same input → same output
// - No external state
// - Highly testable
```

### **Function Parameters**

```javascript
// ✅ GOOD - Destructured with defaults
function createButton({ 
  label, 
  color = 'primary', 
  size = 'md',
  disabled = false 
}) {
  // ...
}

// ❌ BAD - Positional parameters with many args
function createButton(label, color, size, disabled, style, icon) {
  // Hard to remember order
}

// ✅ GOOD - Optional callback last
function fetchData(url, { timeout = 5000 } = {}, onSuccess = null) {
  // ...
}
```

---

## 🏗️ Class Patterns

### **Constructor Pattern**

```javascript
export class ButtonRenderer {
  /**
   * Create a button renderer
   * @param {Object} logger - Logger instance
   * @param {Object} options - Configuration options
   * @param {string} options.defaultColor - Default button color
   */
  constructor(logger, options = {}) {
    // 1. Validate required dependencies
    if (!logger) {
      throw new Error('[ButtonRenderer] Logger is required');
    }
    
    // 2. Store dependencies
    this.logger = logger;
    
    // 3. Initialize options with defaults
    this.options = {
      defaultColor: 'primary',
      defaultSize: 'md',
      ...options
    };
    
    // 4. Initialize state (if needed)
    this._cache = new Map();
    this._isInitialized = false;
    
    // 5. Log initialization
    this.logger.log('[ButtonRenderer] Initialized');
  }
  
  /**
   * Initialize renderer (async setup if needed)
   * @returns {Promise<void>}
   */
  async init() {
    if (this._isInitialized) {
      this.logger.warn('[ButtonRenderer] Already initialized');
      return;
    }
    
    // Async initialization work here
    
    this._isInitialized = true;
    this.logger.log('[ButtonRenderer] Initialization complete');
  }
  
  // Public methods
  render(data, zone) {
    // ...
  }
  
  // Private methods (underscore prefix)
  _validateData(data) {
    // ...
  }
}
```

### **Manager Pattern (Layer 5)**

```javascript
export class DashboardManager {
  constructor(client, logger) {
    this.client = client;
    this.logger = logger;
    
    // Lazy-load dependencies
    this._renderer = null;
    this._cache = null;
  }
  
  /**
   * Lazy-load renderer
   * @private
   * @returns {Promise<ZDisplayOrchestrator>}
   */
  async _getRenderer() {
    if (!this._renderer) {
      const module = await import('../rendering/zdisplay_orchestrator.js');
      this._renderer = new module.ZDisplayOrchestrator(this.logger);
    }
    return this._renderer;
  }
  
  /**
   * Render dashboard (public API)
   * @param {Object} config - Dashboard configuration
   * @returns {Promise<HTMLElement>}
   */
  async renderDashboard(config) {
    // 1. Validate input
    if (!config.folder || !config.sidebar) {
      throw new Error('[DashboardManager] Invalid config');
    }
    
    // 2. Business logic
    const shouldUseCache = this._shouldUseCache(config);
    
    // 3. Delegate to renderer
    const renderer = await this._getRenderer();
    return renderer.render(config);
  }
  
  /**
   * Business decision: should we use cache?
   * @private
   */
  _shouldUseCache(config) {
    // Business logic here
    return true;
  }
}
```

---

## ⚠️ Error Handling

### **Pattern 1: Validate Early**

```javascript
export function createButton(data, zone) {
  // 1. Validate inputs at the start
  if (!data) {
    throw new Error('[createButton] data is required');
  }
  if (!zone) {
    throw new Error('[createButton] zone is required');
  }
  if (!data.label) {
    throw new Error('[createButton] data.label is required');
  }
  
  // 2. Proceed with confidence
  const button = document.createElement('button');
  button.textContent = data.label;
  // ...
}
```

### **Pattern 2: Graceful Degradation**

```javascript
export function renderDashboard(config) {
  const container = document.getElementById(config.zone);
  
  // Graceful: Return null instead of throwing
  if (!container) {
    this.logger.error(`[renderDashboard] Zone not found: ${config.zone}`);
    return null;
  }
  
  // Continue normally
}
```

### **Pattern 3: Try-Catch for Async/External**

```javascript
async function fetchPanelMetadata(folder, sidebar) {
  try {
    const response = await fetch(`/api/dashboard/panel/meta?zPath=${folder}`);
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    return await response.json();
  } catch (error) {
    this.logger.error('[fetchPanelMetadata] Failed to fetch metadata:', error);
    
    // Return safe fallback
    return sidebar.map(panel => ({
      label: panel,
      icon: 'bi-file-text'
    }));
  }
}
```

### **Pattern 4: Error Boundaries for Renderers**

```javascript
// ✅ GOOD - Wrap renderer methods with error boundaries
import { withErrorBoundary } from '../utils/error_boundary.js';

export class TextRenderer {
  constructor(logger) {
    this.logger = logger || console;
    
    // Wrap render method with error boundary
    const originalRender = this.render.bind(this);
    this.render = withErrorBoundary(originalRender, {
      component: 'TextRenderer',
      logger: this.logger
    });
  }
  
  render(data, zone) {
    // If this throws, error boundary catches it
    // and displays graceful fallback UI
    const element = document.createElement('p');
    element.textContent = data.content;
    return element;
  }
}
```

**Benefits:**
- One renderer error doesn't break entire UI
- Users see error message instead of blank screen
- Stack traces available in collapsible details
- Consistent error UX across all renderers

**When to Use:**
- ✅ All renderer classes (Layer 3)
- ✅ Complex rendering logic
- ✅ User-facing components
- ❌ Simple utility functions (use try-catch instead)

### **Pattern 5: Error Messages**

```javascript
// ✅ GOOD - Descriptive error with context
throw new Error('[ButtonRenderer.render] data.label is required but was undefined');

// ❌ BAD - Vague error
throw new Error('Invalid data');

// ✅ GOOD - Include relevant data
throw new Error(`[DashboardManager] Panel not found: ${panelName} in folder ${folder}`);

// ❌ BAD - No context
throw new Error('Panel not found');
```

---

## 📝 Logging

### **Log Levels**

```javascript
// Use appropriate log level
this.logger.log('[Component] Normal operation');       // INFO
this.logger.warn('[Component] Recoverable issue');     // WARNING
this.logger.error('[Component] Critical error', err);  // ERROR
this.logger.debug('[Component] Debug info', data);     // DEBUG (dev only)
```

### **Log Format**

```javascript
// ✅ GOOD - Component prefix in brackets
this.logger.log('[ButtonRenderer] Button created:', button);

// ❌ BAD - No prefix
this.logger.log('Button created:', button);

// ✅ GOOD - Action + context
this.logger.log('[DashboardManager] Loading panel:', panelName, 'from', folder);

// ❌ BAD - Vague
this.logger.log('Loading panel');
```

### **NO console.log**

```javascript
// ❌ BAD - Direct console usage
console.log('Something happened');

// ✅ GOOD - Use logger
this.logger.log('[Component] Something happened');

// Exception: Only in standalone utilities with no logger
// (but prefer passing logger as parameter)
```

---

## 🧪 Testing Patterns

### **Unit Test Pattern (Utils)**

```javascript
// dom_utils.test.js
import { createElement, appendChildren } from './dom_utils.js';

describe('dom_utils', () => {
  describe('createElement', () => {
    it('should create element with tag', () => {
      const el = createElement('div');
      expect(el.tagName).toBe('DIV');
    });
    
    it('should add classes', () => {
      const el = createElement('div', ['class1', 'class2']);
      expect(el.classList.contains('class1')).toBe(true);
      expect(el.classList.contains('class2')).toBe(true);
    });
    
    it('should set attributes', () => {
      const el = createElement('input', [], { type: 'text', id: 'test' });
      expect(el.type).toBe('text');
      expect(el.id).toBe('test');
    });
    
    it('should handle empty inputs', () => {
      const el = createElement('div');
      expect(el.classList.length).toBe(0);
    });
  });
  
  describe('appendChildren', () => {
    it('should append multiple children', () => {
      const parent = createElement('div');
      const child1 = createElement('span');
      const child2 = createElement('span');
      
      appendChildren(parent, [child1, child2]);
      
      expect(parent.children.length).toBe(2);
      expect(parent.children[0]).toBe(child1);
      expect(parent.children[1]).toBe(child2);
    });
  });
});
```

### **Integration Test Pattern (Renderers)**

```javascript
// button_renderer.test.js
import ButtonRenderer from './button_renderer.js';

describe('ButtonRenderer', () => {
  let renderer;
  let mockLogger;
  let container;
  
  beforeEach(() => {
    // Setup
    mockLogger = {
      log: jest.fn(),
      error: jest.fn()
    };
    renderer = new ButtonRenderer(mockLogger);
    
    // Create DOM environment
    container = document.createElement('div');
    container.id = 'test-zone';
    document.body.appendChild(container);
  });
  
  afterEach(() => {
    // Cleanup
    document.body.removeChild(container);
  });
  
  it('should render button with label', () => {
    const data = { label: 'Click Me', action: 'test_action' };
    const button = renderer.render(data, 'test-zone');
    
    expect(button).toBeTruthy();
    expect(button.textContent).toContain('Click Me');
  });
  
  it('should handle click events', () => {
    const data = { label: 'Click Me', action: 'test_action', requestId: '123' };
    const button = renderer.render(data, 'test-zone');
    
    // Trigger click
    button.querySelector('button').click();
    
    // Verify response sent
    expect(mockLogger.log).toHaveBeenCalledWith(
      expect.stringContaining('Button clicked')
    );
  });
});
```

---

## 📚 JSDoc Standards

### **Function Documentation**

```javascript
/**
 * Create an HTML element with zTheme classes and attributes
 * 
 * @param {string} tag - HTML tag name (e.g., 'div', 'button', 'input')
 * @param {string[]} [classNames=[]] - Array of CSS class names to add
 * @param {Object} [attributes={}] - HTML attributes to set {id, type, disabled, etc}
 * @returns {HTMLElement} Created element
 * 
 * @example
 * const button = createElement('button', ['zBtn', 'zBtnPrimary'], { type: 'button' });
 * 
 * @throws {Error} If tag is empty or invalid
 */
export function createElement(tag, classNames = [], attributes = {}) {
  // Implementation
}
```

### **Class Documentation**

```javascript
/**
 * Renders button input events for zDisplay
 * 
 * Handles the 'button' event type from zCLI backend, creating
 * interactive button elements with zTheme styling and WebSocket
 * response handling.
 * 
 * @class
 * @example
 * const renderer = new ButtonRenderer(logger);
 * const button = renderer.render({
 *   label: 'Submit',
 *   action: 'process_form',
 *   color: 'primary',
 *   requestId: '123'
 * }, 'zVaF');
 */
export class ButtonRenderer {
  /**
   * Create a button renderer
   * @param {Object} logger - Logger instance for debugging
   */
  constructor(logger) {
    this.logger = logger;
  }
  
  /**
   * Render a button input request
   * 
   * @param {Object} data - Button configuration
   * @param {string} data.label - Button label text
   * @param {string} data.action - Action identifier (or '#' for placeholder)
   * @param {string} [data.color='primary'] - Button color
   * @param {string} [data.style='default'] - Button style variant
   * @param {string} [data.size='md'] - Button size
   * @param {string} data.requestId - Request ID for response correlation
   * @param {string} zone - Target DOM element ID
   * @returns {HTMLElement|null} Created button container, or null if zone not found
   */
  render(data, zone) {
    // Implementation
  }
}
```

### **Type Definitions**

```javascript
/**
 * @typedef {Object} DashboardConfig
 * @property {string} folder - Base folder path (@.UI.zAccount)
 * @property {string[]} sidebar - Panel names ['Overview', 'Settings']
 * @property {string} [default] - Default panel to load
 */

/**
 * Render dashboard with sidebar navigation
 * @param {DashboardConfig} config - Dashboard configuration
 * @returns {Promise<HTMLElement>}
 */
async renderDashboard(config) {
  // Implementation
}
```

---

## 🚫 Anti-Patterns

### **Anti-Pattern 1: God Objects**

```javascript
// ❌ BAD - Class doing too much
class UIManager {
  renderButton() { }
  renderTable() { }
  renderForm() { }
  handleNavigation() { }
  manageDarkMode() { }
  updateCache() { }
  // ... 50 more methods
}

// ✅ GOOD - Single responsibility
class ButtonRenderer {
  render() { }
}
class NavigationManager {
  navigate() { }
}
class ThemeManager {
  toggleDarkMode() { }
}
```

### **Anti-Pattern 2: Backward Imports**

```javascript
// ❌ BAD - Utils importing from managers
// utils/dom_utils.js
import { DashboardManager } from '../managers/dashboard_manager.js';

// ✅ GOOD - Managers import utils
// managers/dashboard_manager.js
import { createElement } from '../utils/dom_utils.js';
```

### **Anti-Pattern 3: Magic Numbers/Strings**

```javascript
// ❌ BAD - Magic values
if (status === 200) { }
setTimeout(callback, 5000);

// ✅ GOOD - Named constants
const HTTP_OK = 200;
const DEFAULT_TIMEOUT_MS = 5000;

if (status === HTTP_OK) { }
setTimeout(callback, DEFAULT_TIMEOUT_MS);
```

### **Anti-Pattern 4: Callback Hell**

```javascript
// ❌ BAD - Nested callbacks
fetchData(url, (data) => {
  processData(data, (result) => {
    saveResult(result, (saved) => {
      updateUI(saved, () => {
        // ...
      });
    });
  });
});

// ✅ GOOD - async/await
async function handleData(url) {
  const data = await fetchData(url);
  const result = await processData(data);
  const saved = await saveResult(result);
  await updateUI(saved);
}
```

### **Anti-Pattern 5: Mutating Parameters**

```javascript
// ❌ BAD - Mutating input
function addDefaults(config) {
  config.timeout = config.timeout || 5000;
  config.retries = config.retries || 3;
  return config;
}

// ✅ GOOD - Return new object
function addDefaults(config) {
  return {
    timeout: 5000,
    retries: 3,
    ...config
  };
}
```

### **Anti-Pattern 6: Stringly Typed**

```javascript
// ❌ BAD - Everything is a string
function setButtonState(state) {
  if (state === 'loading') { }
  else if (state === 'success') { }
  else if (state === 'eror') { } // Typo!
}

// ✅ GOOD - Constants
const BUTTON_STATE = {
  LOADING: 'loading',
  SUCCESS: 'success',
  ERROR: 'error'
};

function setButtonState(state) {
  if (state === BUTTON_STATE.LOADING) { }
  else if (state === BUTTON_STATE.SUCCESS) { }
  else if (state === BUTTON_STATE.ERROR) { }
}
```

---

## ✅ Code Review Checklist

Before committing:

- [ ] File follows structure template
- [ ] Imports grouped correctly (layer order)
- [ ] All functions have JSDoc comments
- [ ] No console.log (use logger)
- [ ] No magic numbers/strings
- [ ] Error messages include component name
- [ ] No backward imports (check layer rules)
- [ ] File size under limit
- [ ] Tests written and passing
- [ ] ESLint passing

---

## 🎓 Philosophy

These patterns exist for three reasons:

1. **Predictability** - Code looks the same everywhere
2. **Maintainability** - Easy to understand 6 months later
3. **AI-Friendliness** - Claude (Layer 7) can follow patterns

**When in doubt:**
- Follow existing patterns
- Simpler is better
- Delete code aggressively
- Ask: "Will this be obvious to AI?"

---

**Remember:** Good code is boring code. If you're being clever, you're probably being wrong.

