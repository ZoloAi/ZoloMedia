# zBifrost Client (JavaScript)

Production-ready JavaScript WebSocket client for zCLI's zBifrost bridge.

## Structure

```
bifrost/
├── src/                       # Source files
│   ├── bifrost_client.js      # Main BifrostClient class (Layer 6: Application)
│   ├── managers/              # Feature managers (Layer 5: Business logic)
│   │   ├── cache_manager.js
│   │   ├── navigation_manager.js
│   │   ├── widget_hook_manager.js
│   │   └── zvaf_manager.js
│   ├── core/                  # Core primitives (Layer 1: Platform abstraction)
│   │   ├── connection.js
│   │   ├── hooks.js
│   │   ├── logger.js
│   │   ├── message_handler.js
│   │   ├── storage_manager.js
│   │   ├── session_manager.js
│   │   ├── cache_orchestrator.js
│   │   ├── error_display.js
│   │   └── caches/            # Cache implementations
│   ├── rendering/             # Renderers (Layer 3: Presentation logic)
│   │   ├── zdisplay_orchestrator.js
│   │   ├── *_renderer.js      # Specialized renderers
│   │   └── primitives/        # HTML primitive functions
│   └── utils/                 # Utilities (Layer 2: Pure functions)
│       ├── dom_utils.js
│       ├── ztheme_utils.js
│       ├── error_boundary.js
│       └── *_utils.js         # Various utility helpers
├── testing/                   # Test files
├── ARCHITECTURE.md            # 7-layer architecture guide
├── PATTERNS.md                # Coding patterns reference
└── README.md                  # This file
```

## Usage

### Swiper-Style Elegance (Recommended)

```html
<script src="https://cdn.jsdelivr.net/gh/ZoloAi/zolo-zcli@main/zCLI/subsystems/zComm/zComm_modules/bifrost/client/src/bifrost_client.js"></script>

<div id="zVaF"></div> <!-- Default zCLI container (zView and Function) -->

<script>
  // One declaration, everything happens automatically!
  const client = new BifrostClient('ws://localhost:8765', {
    autoConnect: true,              // Auto-connect on instantiation
    zTheme: true,                   // Enable zTheme CSS & rendering
    // targetElement: 'zVaF',       // Optional: default is 'zVaF'
    autoRequest: 'my_event',        // Auto-send on connect
    onConnected: (info) => console.log('✅ Connected!', info)
  });
</script>
```

### Traditional (More Control)

```html
<script>
  const client = new BifrostClient('ws://localhost:8765', {
    zTheme: true,
    hooks: {
      onConnected: (info) => console.log('Connected!', info),
      onDisconnected: (reason) => console.log('Disconnected:', reason),
      onMessage: (msg) => console.log('Message:', msg),
      onError: (error) => console.error('Error:', error)
    }
  });
  
  await client.connect();
  client.send({event: 'my_event'});
</script>
```

### Local Development

```html
<script src="../../../../zCLI/subsystems/zComm/zComm_modules/bifrost/client/src/bifrost_client.js"></script>
```

## Features

- **7-Layer Architecture**: Industry-grade separation of concerns (see ARCHITECTURE.md)
- **Swiper-Style Elegance**: `autoConnect`, `zTheme`, `autoRequest` for one-line initialization
- **Lazy Loading**: Modules load dynamically only when needed
- **Auto-Reconnect**: Automatic reconnection with exponential backoff
- **zTheme Integration**: Optional CSS loading & automatic rendering
- **Hooks System**: Lifecycle callbacks (onConnected, onDisconnected, onMessage, etc.)
- **Multi-Tier Caching**: 5-tier cache system (system, pinned, plugin, session, rendered)
- **Error Boundaries**: Graceful error handling with visual fallback UI
- **Auto-Rendering**: Renderers for all zDisplay events (text, table, form, menu, etc.)
- **Client-Side Routing**: Delta navigation without page reloads
- **zCLI Integration**: Full support for zDisplay, zDialog, zMenu, zDash events

## Documentation

- [`ARCHITECTURE.md`](./ARCHITECTURE.md) - 7-layer architecture guide
- [`PATTERNS.md`](./PATTERNS.md) - Coding patterns & best practices
- [`testing/README.md`](./testing/README.md) - Test suite documentation
- Backend integration: `Documentation/zBifrost_GUIDE.md` (in main repo)

## Demos

See [`../Demos/Layer_2/zBifrost_Demo/`](../Demos/Layer_2/zBifrost_Demo/) for progressive tutorials:
- Frontend demos showcasing BifrostClient features
- Progressive complexity (basic connection → full zDisplay integration)
- Test files available in [`testing/`](./testing/) directory (21 HTML test files)

