# BifrostClient Architecture
## 7-Layer Industry-Grade Frontend Architecture

**Version:** 2.0  
**Last Updated:** Dec 18, 2025  
**Philosophy:** Bottom-to-top, primitives first, zero technical debt  

---

## 📊 The 7 Layers

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 6: APPLICATION (bifrost_client.js)                   │
│  Role: Orchestration, lifecycle, module initialization      │
│  Size: ~500 lines                                           │
│  Pattern: Facade + Lazy Loading                            │
│  Imports: Managers (Layer 5), Core (Layer 1)               │
│  Exports: BifrostClient class                               │
└─────────────────────────────────────────────────────────────┘
                         ↓ delegates to
┌─────────────────────────────────────────────────────────────┐
│  Layer 5: FEATURE MANAGERS (managers/)                      │
│  Role: Domain-specific business logic                       │
│  Files: cache_manager.js, navigation_manager.js,            │
│         widget_hook_manager.js, zvaf_manager.js             │
│  Pattern: Manager pattern (one manager per domain)          │
│  Imports: Core (Layer 1), Utilities (Layer 2)              │
│  Exports: Manager classes                                   │
└─────────────────────────────────────────────────────────────┘
                         ↓ uses
┌─────────────────────────────────────────────────────────────┐
│  Layer 4: EVENT HANDLERS (core/)                            │
│  Role: Protocol handling, message routing                   │
│  Files: message_handler.js, hooks.js                        │
│  Pattern: Observer + Command                                │
│  Imports: Renderers (Layer 3), Core (Layer 1)              │
│  Exports: MessageHandler, HooksManager classes              │
└─────────────────────────────────────────────────────────────┘
                         ↓ uses
┌─────────────────────────────────────────────────────────────┐
│  Layer 3: RENDERERS (rendering/)                            │
│  Role: Presentation logic, DOM manipulation                 │
│  Files: zdisplay_orchestrator.js (router)                   │
│         + specialized renderers (button, input, table, etc) │
│  Pattern: Strategy + Facade                                 │
│  Imports: Utilities (Layer 2)                               │
│  Exports: Renderer classes with .render() method            │
└─────────────────────────────────────────────────────────────┘
                         ↓ uses
┌─────────────────────────────────────────────────────────────┐
│  Layer 2: UTILITIES (utils/)                                │
│  Role: Reusable helpers, zero business logic                │
│  Files: dom_utils.js, ztheme_utils.js, error_boundary.js,  │
│         color_utils.js, size_utils.js, spacing_utils.js,   │
│         container_utils.js, block_utils.js, validation.js  │
│  Pattern: Pure functions (stateless)                        │
│  Imports: NONE (only Layer 0 - Browser APIs)               │
│  Exports: Pure functions                                    │
└─────────────────────────────────────────────────────────────┘
                         ↓ uses
┌─────────────────────────────────────────────────────────────┐
│  Layer 1: CORE PRIMITIVES (core/)                           │
│  Role: System primitives, platform abstractions             │
│  Files: connection.js, storage_manager.js, hooks.js,        │
│         session_manager.js, cache_orchestrator.js, logger.js│
│  Pattern: Adapter + Singleton                               │
│  Imports: Utilities (Layer 2) only                          │
│  Exports: Core infrastructure classes                       │
└─────────────────────────────────────────────────────────────┘
                         ↓ uses
┌─────────────────────────────────────────────────────────────┐
│  Layer 0: BROWSER APIs                                      │
│  Role: Platform (DOM, WebSocket, IndexedDB, localStorage)   │
│  Provided by: Browser runtime                               │
└─────────────────────────────────────────────────────────────┘

         +------------------------------------------------+
         |  Layer 7: AI (Claude) - Pattern Recognition   |
         |  Role: Understand architecture, generate code |
         |  Context: This document + PATTERNS.md          |
         +------------------------------------------------+
```

---

## 🎯 Layer Responsibilities

### **Layer 0: Browser APIs**
**Provided by the platform - DO NOT WRAP unnecessarily**
- `document.querySelector()`, `createElement()`, etc
- `WebSocket`, `fetch()`, `XMLHttpRequest`
- `localStorage`, `sessionStorage`, `IndexedDB`
- `addEventListener()`, event bubbling
- Standard Web APIs

**Rule:** Use directly when simple, wrap in Layer 1 when complex state is needed.

---

### **Layer 1: Core Primitives** (`core/`)
**Purpose:** Abstract platform primitives with zCLI-specific concerns

| File | Purpose | Pattern | Exports |
|------|---------|---------|---------|
| `connection.js` | WebSocket lifecycle | Adapter | `Connection` class |
| `storage_manager.js` | IndexedDB + localStorage | Adapter | `StorageManager` class |
| `session_manager.js` | Session state management | Singleton | `SessionManager` class |
| `cache_orchestrator.js` | Multi-tier caching | Facade | `CacheOrchestrator` class |
| `hooks.js` | Event hook system | Observer | `HooksManager` class |
| `logger.js` | Centralized logging | Singleton | `Logger` class |
| `error_display.js` | Error UI handling | Utility | `ErrorDisplay` class |

**Key Principles:**
- ✅ Abstract platform complexity
- ✅ Provide zCLI-specific defaults
- ✅ Can import from Layer 2 (utils)
- ❌ NO business logic
- ❌ NO DOM rendering (except error_display)
- ❌ NO knowledge of zDisplay events

**Example:**
```javascript
// ✅ GOOD - Platform abstraction
class StorageManager {
  async get(key) {
    // Abstracts IndexedDB complexity
    const db = await this._openDB();
    return db.get(key);
  }
}

// ❌ BAD - Business logic in core
class StorageManager {
  async getCachedDashboard(panelName) {
    // This is business logic - belongs in managers/
  }
}
```

---

### **Layer 2: Utilities** (`utils/`)
**Purpose:** Pure functions with ZERO state or side effects

| File | Purpose | Exports |
|------|---------|---------|
| `dom_utils.js` | DOM manipulation helpers | 10+ pure functions |
| `ztheme_utils.js` | zTheme class mappings | 8+ pure functions |
| `validation_utils.js` | Input validation | 6+ pure functions |
| `error_boundary.js` | Error boundary wrappers | `withErrorBoundary`, `createErrorFallback` |
| `color_utils.js` | Color class utilities | Color mapping functions |
| `size_utils.js` | Size class utilities | Size mapping functions |
| `spacing_utils.js` | Spacing class utilities | Spacing mapping functions |
| `container_utils.js` | Container class utilities | Container helpers |
| `block_utils.js` | Block element utilities | Block element helpers |

**Key Principles:**
- ✅ Pure functions ONLY (same input → same output)
- ✅ Stateless
- ✅ No side effects (no DOM modification, no API calls)
- ✅ Highly testable (unit tests easy)
- ❌ NO imports from upper layers
- ❌ NO business logic
- ❌ NO rendering

**Example:**
```javascript
// ✅ GOOD - Pure function
export function getButtonColorClass(zColor) {
  const mapping = {
    'primary': 'zBtnPrimary',
    'danger': 'zBtnDanger',
    // ...
  };
  return mapping[zColor?.toLowerCase()] || 'zBtnPrimary';
}

// ❌ BAD - Side effects
export function applyButtonColor(button, zColor) {
  button.classList.add(getButtonColorClass(zColor)); // Mutates DOM!
}
```

---

### **Layer 3: Renderers** (`rendering/`)
**Purpose:** Presentation logic, DOM manipulation, event binding

| File | Purpose | Handles |
|------|---------|---------|
| `zdisplay_orchestrator.js` | Event routing | All zDisplay events |
| `button_renderer.js` | Button inputs | `button` event |
| `input_renderer.js` | Text/selection inputs | `selection`, `text_input` |
| `table_renderer.js` | Tables | `zTable` event |
| `alert_renderer.js` | Alerts/signals | `error`, `warning`, `success`, `info` |
| `form_renderer.js` | Forms | `zDialog` event |
| `typography_renderer.js` | Text elements | `text`, `header`, `divider` |
| `card_renderer.js` | Cards | `zCard` event |
| `navigation_renderer.js` | Navigation | `zMenu`, `zNavBar` events |

**Key Principles:**
- ✅ ONE event type per renderer (single responsibility)
- ✅ Use utilities from Layer 2
- ✅ Return created DOM element (testable)
- ✅ Handle own event listeners
- ❌ NO business logic (e.g., "should this button be disabled?")
- ❌ NO API calls (managers handle that)
- ❌ NO direct WebSocket usage

**Example:**
```javascript
// ✅ GOOD - Focused renderer
class ButtonRenderer {
  render(data, zone) {
    const button = createElement('button', ['zoloButton']);
    button.textContent = data.label;
    button.addEventListener('click', () => this._handleClick(data));
    document.getElementById(zone).appendChild(button);
    return button;
  }
}

// ❌ BAD - Too much responsibility
class ButtonRenderer {
  render(data, zone) {
    // Rendering button (OK)
    // + fetching user permissions (NO - manager's job)
    // + updating cache (NO - cache's job)
    // + logging analytics (NO - separate concern)
  }
}
```

---

### **Layer 4: Event Handlers** (`core/`)
**Purpose:** WebSocket message routing, hook orchestration

| File | Purpose | Pattern |
|------|---------|---------|
| `message_handler.js` | Route incoming messages | Command |
| `hooks.js` | Hook registration/execution | Observer |

**Key Principles:**
- ✅ Route messages to correct handlers
- ✅ Trigger hooks at lifecycle points
- ✅ NO rendering logic (delegate to Layer 3)
- ✅ NO business decisions (delegate to Layer 5)

---

### **Layer 5: Feature Managers** (`managers/`)
**Purpose:** Domain-specific business logic

| File | Purpose | Domain |
|------|---------|--------|
| `cache_manager.js` | Cache tier orchestration | Caching strategy |
| `navigation_manager.js` | Client-side routing | SPA navigation |
| `widget_hook_manager.js` | Widget lifecycle hooks | Widget integration |
| `zvaf_manager.js` | zVaF element management | zVaF framework |

**Key Principles:**
- ✅ ONE domain per manager
- ✅ Orchestrate multiple renderers
- ✅ Make business decisions
- ✅ Call APIs, update cache
- ❌ NO direct DOM manipulation (use renderers)

**Example:**
```javascript
// ✅ GOOD - Manager orchestrates
class CacheManager {
  async initCacheSystem(storage) {
    // Business logic: Initialize storage
    this.storage = new StorageManager(storage);
    await this.storage.init();
    
    // Business logic: Set up cache tiers
    this.systemCache = new SystemCache(this.storage);
    this.pinnedCache = new PinnedCache(this.storage);
    this.sessionCache = new SessionCache(null); // In-memory
    
    // Delegate cache operations to appropriate tiers
    return {
      system: this.systemCache,
      pinned: this.pinnedCache,
      session: this.sessionCache
    };
  }
}
```

---

### **Layer 6: Application** (`bifrost_client.js`)
**Purpose:** Orchestration, lifecycle, public API

**Key Principles:**
- ✅ Initialize all subsystems
- ✅ Expose public API (`connect()`, `send()`, `disconnect()`)
- ✅ Lazy-load managers (performance)
- ✅ Handle connection lifecycle
- ❌ NO business logic (delegate to managers)
- ❌ NO rendering (delegate to renderers)
- ❌ Keep < 500 lines

**Structure:**
```javascript
class BifrostClient {
  constructor(url, options) {
    // 1. Initialize Layer 1 (core primitives)
    this.connection = new Connection(url);
    this.storage = new StorageManager();
    this.logger = new Logger();
    
    // 2. Initialize Layer 4 (handlers)
    this.messageHandler = new MessageHandler(this);
    
    // 3. Lazy-load Layer 5 (managers)
    this.managers = {
      cache: null,
      navigation: null,
      widgetHook: null,
      zvaf: null
    };
    
    // 4. Register hooks
    this._registerHooks();
    
    // 5. Connect
    if (options.autoConnect) this.connect();
  }
  
  // Public API
  async connect() { /* Delegate to connection */ }
  async send(payload) { /* Delegate to connection */ }
  disconnect() { /* Delegate to connection */ }
  
  // Private - delegate to managers
  async _initCacheSystem() {
    if (!this.managers.cache) {
      this.managers.cache = new CacheManager(this);
    }
    return this.managers.cache.initCacheSystem(this.storage);
  }
}
```

---

## 🚫 Dependency Rules

### **The Cardinal Rule: Lower layers NEVER import upper layers**

```
Layer 6 ──→ Layer 5 ──→ Layer 4 ──→ Layer 3 ──→ Layer 2 ──→ Layer 1 ──→ Layer 0
   ↑          ↑          ↑          ↑          ↑          ↑
   └──────────┴──────────┴──────────┴──────────┴──────────┘
            ❌ NEVER import backwards
```

### **Valid Imports:**

| Layer | Can Import From |
|-------|-----------------|
| Layer 6 (Application) | Layer 5, 4, 1 |
| Layer 5 (Managers) | Layer 3, 2, 1 |
| Layer 4 (Handlers) | Layer 3, 2, 1 |
| Layer 3 (Renderers) | Layer 2 only |
| Layer 2 (Utils) | NOTHING (Layer 0 only) |
| Layer 1 (Core) | Layer 2 only |

### **Examples:**

```javascript
// ✅ GOOD - Upper imports lower
// managers/cache_manager.js
import { StorageManager } from '../core/storage_manager.js';
import { SystemCache } from '../core/caches/system_cache.js';

// ❌ BAD - Lower imports upper
// rendering/button_renderer.js
import { CacheManager } from '../managers/cache_manager.js';

// ❌ BAD - Circular dependency
// managers/cache_manager.js
import { NavigationManager } from './navigation_manager.js';
// managers/navigation_manager.js
import { CacheManager } from './cache_manager.js';
```

---

## 📏 File Size Limits

| Layer | Max Lines | Rationale |
|-------|-----------|-----------|
| Utils | 150 lines | Pure functions, minimal logic |
| Renderers | 300 lines | Single event type |
| Managers | 400 lines | Domain logic, but focused |
| Application | 500 lines | Orchestration only |

**If a file exceeds its limit:** Split it or refactor, don't justify.

---

## 🧪 Testing Strategy

### **Layer 2 (Utils):** Unit tests
- Test each function in isolation
- Mock NOTHING (pure functions)
- Aim for 100% coverage

### **Layer 3 (Renderers):** Unit + Integration tests
- Mock DOM (jsdom)
- Test rendering output
- Test event handlers

### **Layer 5 (Managers):** Integration tests
- Mock renderers
- Mock API calls
- Test business logic

### **Layer 6 (Application):** E2E tests
- Real browser
- Real WebSocket
- Test full flows

---

## 📝 AI Guidelines (Layer 7)

When generating code:

1. **Always identify the layer first**
   - Ask: "What layer does this belong to?"
   - Check import rules before writing

2. **Follow single responsibility**
   - One event type per renderer
   - One domain per manager
   - One concern per utility

3. **Use patterns from PATTERNS.md**
   - Constructor patterns
   - Error handling patterns
   - Logging patterns

4. **Write JSDoc comments**
   - Every exported function/class
   - Parameter types
   - Return types

5. **Test as you go**
   - Write unit tests for utils
   - Write integration tests for complex logic

---

## 🔄 Migration Strategy

When refactoring existing code:

1. **Identify the layer** - Where does this logic belong?
2. **Extract to new file** - Don't modify original yet
3. **Write tests** - Ensure behavior matches
4. **Update imports** - Wire up new architecture
5. **Delete old code** - Once tests pass
6. **Commit** - One layer at a time

---

## ✅ Quality Checklist

Before considering a layer "complete":

- [ ] All files follow layer rules
- [ ] No file exceeds size limit
- [ ] All imports valid (no backwards)
- [ ] 100% JSDoc coverage
- [ ] Tests passing (>90% coverage)
- [ ] No console.log (use logger)
- [ ] No magic numbers/strings (use constants)
- [ ] ESLint passing

---

## 📚 Further Reading

- `PATTERNS.md` - Coding patterns for each layer
- Backend architecture: `zCLI/ARCHITECTURE.md` (similar principles)
- zTheme documentation: `https://github.com/ZoloAi/zTheme`

---

**Remember:** This architecture is not about being clever. It's about being **predictable, maintainable, and AI-friendly**. Every file should have ONE clear job. Every layer should have ONE clear boundary.

**When in doubt:** Simpler is better. Delete code aggressively. Follow the patterns.

