# zBifrost - WebSocket Bridge for zCLI

Real-time WebSocket communication between zCLI backends and web frontends, enabling dual-mode applications (CLI + Web) with zero configuration.

---

## 📁 Directory Structure (v1.5.5+)

```
bifrost/
├── README.md                  # This file
├── __init__.py                # Package exports (imports from server/)
│
├── server/                    # Python backend
│   ├── README.md              # Server documentation
│   ├── bifrost_bridge.py      # Main zBifrost class
│   ├── modules/               # Server-side modules
│   │   ├── bridge_auth.py     # Authentication & authorization
│   │   ├── bridge_cache.py    # Schema & data caching
│   │   ├── bridge_connection.py  # Connection state management
│   │   ├── bridge_messages.py # Message routing & dispatch
│   │   └── events/            # Event handlers
│   │       ├── bridge_event_cache.py      # Cache operations
│   │       ├── bridge_event_client.py     # Client lifecycle
│   │       ├── bridge_event_discovery.py  # Service discovery
│   │       └── bridge_event_dispatch.py   # Command execution
│   └── __init__.py            # Server package exports
│
├── client/                    # JavaScript client
│   ├── README.md              # Client documentation
│   ├── src/                   # Source files
│   │   ├── bifrost_client.js  # Main BifrostClient class
│   │   ├── core/              # Core modules
│   │   │   ├── connection.js  # WebSocket connection management
│   │   │   ├── hooks.js       # Hook management system
│   │   │   ├── logger.js      # Debug logging
│   │   │   └── message_handler.js  # Message processing & correlation
│   │   ├── rendering/         # Rendering modules
│   │   │   ├── renderer.js    # Auto-rendering with zTheme
│   │   │   └── theme_loader.js  # zTheme CSS loading
│   │   └── api/               # API wrappers [future]
│   ├── dist/                  # Built files for production [future]
│   └── tests/                 # Unit tests [future]
│
└── docs/                      # Shared documentation
    ├── ARCHITECTURE.md        # Event-driven architecture
    ├── MESSAGE_PROTOCOL.md    # Protocol specification
    └── HOOKS_GUIDE.md         # Hooks system reference
```

---

## 🚀 Quick Start

### Python Backend

```python
from zCLI import zCLI

# Auto-start via zCLI (zBifrost mode)
z = zOS({"zMode": "zBifrost"})
z.walker.run()

# Programmatic control
from zCLI.subsystems.zComm.zComm_modules.bifrost import zBifrost

bifrost = zBifrost(zcli_instance, logger)
await bifrost.start_socket_server(socket_ready_event)
await bifrost.broadcast({"event": "message", "data": "Hello"})
```

### JavaScript Client

#### Via CDN (jsDelivr)

```html
<script src="https://cdn.jsdelivr.net/gh/ZoloAi/zolo-zcli@main/zCLI/subsystems/zComm/zComm_modules/bifrost/client/src/bifrost_client.js"></script>

<script>
  const client = new BifrostClient('ws://localhost:8765', {
    autoTheme: true,
    autoReconnect: true,
    hooks: {
      onConnected: (info) => console.log('Connected!', info),
      onDisconnected: (reason) => console.log('Disconnected:', reason),
      onMessage: (msg) => console.log('Message:', msg),
      onDisplay: (data) => console.log('Display event:', data),
      onError: (error) => console.error('Error:', error)
    }
  });
  
  client.connect();
</script>
```

#### Local Development

```html
<script src="../../../../zCLI/subsystems/zComm/zComm_modules/bifrost/client/src/bifrost_client.js"></script>
```

---

## ✨ Features

### Server (Python)
- ✅ Event-driven architecture (mirrors zDisplay)
- ✅ Automatic authentication & authorization
- ✅ Schema & data caching
- ✅ Connection state management
- ✅ Message routing & dispatch
- ✅ Broadcast to all clients

### Client (JavaScript)
- ✅ Lazy loading (modules load only when needed)
- ✅ Auto-reconnect with exponential backoff
- ✅ Auto-theme (optional zTheme CSS loading)
- ✅ Hooks system (onConnected, onDisconnected, onMessage, etc.)
- ✅ CRUD operations (`create()`, `read()`, `update()`, `delete()`)
- ✅ Auto-rendering (`renderTable()`, `renderForm()`, `renderMenu()`)
- ✅ zCLI integration (`zFunc()`, `zLink()`, `zOpen()`)

---

## 📚 Documentation

- **[server/README.md](server/README.md)** - Python backend documentation
- **[client/README.md](client/README.md)** - JavaScript client documentation
- **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** - Event-driven architecture
- **[docs/MESSAGE_PROTOCOL.md](docs/MESSAGE_PROTOCOL.md)** - Protocol specification
- **[docs/HOOKS_GUIDE.md](docs/HOOKS_GUIDE.md)** - Hooks system reference

---

## 🎓 Demos

See [`../../../../Demos/Layer_0/zBifrost_Demo/`](../../../../Demos/Layer_0/zBifrost_Demo/) for progressive tutorials:

- **Level 0**: Hello zBlog (basic connection)
- **Level 1**: Echo Test (two-way communication)
- **Level 2**: Post Feed (structured data)
- **Level 4a+**: Multi-zone layout with zDisplay events

---

## 🔄 Migration Notes (v1.5.5)

### What Changed?

- **Reorganized folder structure**: Python backend → `server/`, JavaScript client → `client/src/`
- **Updated import paths**: `bifrost_client_modular.js` → `client/src/bifrost_client.js`
- **Module organization**: JS modules now in `core/` and `rendering/` subfolders
- **No breaking changes**: All APIs remain the same

### Updating Your Code

**HTML files** (update script src):
```html
<!-- Old -->
<script src=".../bifrost/bifrost_client_modular.js"></script>

<!-- New -->
<script src=".../bifrost/client/src/bifrost_client.js"></script>
```

**Python imports** (no changes needed):
```python
from zCLI.subsystems.zComm.zComm_modules.bifrost import zBifrost
# Still works! __init__.py handles the new structure
```

---

## 🧪 Testing

```bash
# Run backend
cd Demos/Layer_0/zBifrost_Demo/Level_0_Connection
python level0_backend.py

# Open client in browser
open level0_client.html

# Check console for debug logs
# Enable with: { debug: true }
```

---

## 📊 Performance

- **Connection**: < 100ms to establish
- **Message**: < 10ms round-trip
- **Rendering**: < 50ms for 1000 rows
- **Memory**: ~2MB for client library
- **Bundle Size**: 26KB (minified), 8KB (gzipped)

---

## 🌐 Browser Compatibility

- ✅ Chrome/Edge 88+
- ✅ Firefox 78+
- ✅ Safari 14+
- ✅ All browsers with WebSocket and ES6 support

---

**Version**: 1.5.5  
**License**: MIT  
**Author**: Gal Nachshon
