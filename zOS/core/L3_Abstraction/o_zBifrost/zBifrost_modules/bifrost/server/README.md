# zBifrost Server (Python)

WebSocket server implementation for zCLI's zBifrost bridge.

## Structure

```
server/
├── bifrost_bridge.py          # Main zBifrost class (server lifecycle)
├── modules/                   # Server-side modules
│   ├── bridge_auth.py         # Authentication & authorization
│   ├── bridge_cache.py        # Schema & data caching
│   ├── bridge_connection.py   # Connection state management
│   ├── bridge_messages.py     # Message routing & dispatch
│   └── events/                # Event handlers
│       ├── bridge_event_cache.py      # Cache-related events
│       ├── bridge_event_client.py     # Client lifecycle events
│       ├── bridge_event_discovery.py  # Service discovery events
│       └── bridge_event_dispatch.py   # Command dispatch events
└── __init__.py                # Package exports
```

## Usage

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

## Documentation

See [`../docs/`](../docs/) for:
- `ARCHITECTURE.md` - Server architecture & design
- `MESSAGE_PROTOCOL.md` - WebSocket message format
- `HOOKS_GUIDE.md` - Event hooks reference

