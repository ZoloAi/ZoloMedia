# zBifrost Architecture

## Overview

zBifrost has been refactored to use an **event-driven architecture** that mirrors zDisplay's clean design pattern. This provides consistency across the framework and makes the codebase easier to understand and maintain.

---

## Architecture Comparison

### Before (Monolithic - REMOVED)
```
[OLD] bifrost_bridge.py (494 lines) - DELETED
├── Inline message handling (150+ lines of if/elif)
├── Mixed authentication logic
├── Hard-coded cache operations
└── No clear event registry
```

### After (Event-Driven - Current)
```
bifrost_bridge_modular.py (280 lines)
├── Event map registry
├── Modular event handlers
├── Single handle_message() entry point
└── Organized by domain

bridge_modules/events/
├── client_events.py      # Client-side events
├── cache_events.py        # Cache operations
├── discovery_events.py    # Auto-discovery API
└── dispatch_events.py     # Command execution
```

---

## Event-Driven Pattern

### Event Map (like zDisplay)
```python
self._event_map = {
    # Client events
    "input_response": self.events['client'].handle_input_response,
    "connection_info": self.events['client'].handle_connection_info,
    
    # Cache events
    "get_schema": self.events['cache'].handle_get_schema,
    "clear_cache": self.events['cache'].handle_clear_cache,
    "cache_stats": self.events['cache'].handle_cache_stats,
    "set_cache_ttl": self.events['cache'].handle_set_cache_ttl,
    
    # Discovery events
    "discover": self.events['discovery'].handle_discover,
    "introspect": self.events['discovery'].handle_introspect,
    
    # Dispatch events
    "dispatch": self.events['dispatch'].handle_dispatch,
}
```

### Single Handler Entry Point
```python
async def handle_message(self, ws, message):
    """Single entry point (mirrors zDisplay.handle)"""
    data = json.loads(message)
    event = data.get("event")
    
    # Backward compatibility
    if not event:
        event = self._infer_event_type(data)
    
    # Route via event map
    handler = self._event_map.get(event)
    if handler:
        await handler(ws, data)
```

---

## Module Organization

### Core Modules (bridge_modules/)

#### `authentication.py`
- Client authentication
- Origin validation (CSRF protection)
- Session management

#### `cache_manager.py`
- Query result caching with TTL
- Cache statistics
- Cache invalidation

#### `connection_info.py`
- Server information
- Schema discovery
- Introspection API

#### `message_handler.py`
- Legacy message routing (being phased out)
- Backward compatibility layer

### Event Modules (bridge_modules/events/)

#### `client_events.py`
**Events:**
- `input_response` - Route GUI input to zDisplay
- `connection_info` - Send server info to client

#### `cache_events.py`
**Events:**
- `get_schema` - Retrieve schema definitions
- `clear_cache` - Clear query cache
- `cache_stats` - Get cache statistics
- `set_cache_ttl` - Configure cache TTL

#### `discovery_events.py`
**Events:**
- `discover` - Auto-discovery API
- `introspect` - Schema introspection

#### `dispatch_events.py`
**Events:**
- `dispatch` - Execute zDispatch commands
- Handles caching for read operations
- Manages request correlation

---

## Benefits

### 1. Discoverability
All events visible in `_event_map` - no need to search through if/elif chains.

### 2. Maintainability
Each event type has a dedicated handler function with clear responsibility.

### 3. Extensibility
Adding new events is simple:
1. Add handler to appropriate event class
2. Register in `_event_map`
3. Done!

### 4. Testability
Event handlers can be tested independently without mocking WebSocket connections.

### 5. Consistency
Mirrors zDisplay's architecture - developers see familiar patterns throughout zCLI.

---

## Message Flow

```
Client Message
    ↓
[WebSocket Connection]
    ↓
handle_client()
    ↓
handle_message()  ← Single entry point
    ↓
_event_map lookup
    ↓
Event Handler (events/*.py)
    ↓
Response sent back
```

---

## Backward Compatibility

The architecture maintains full backward compatibility:

### Legacy Format Support
```python
def _infer_event_type(self, data):
    """Map old formats to new events"""
    if "action" in data:
        return data["action"]  # {"action": "get_schema"}
    if "zKey" in data:
        return "dispatch"      # {"zKey": "^List.users"}
    return None
```

### API Wrappers
```python
def validate_origin(self, ws):
    """Wrapper for backward compatibility"""
    return self.auth.validate_origin(ws)
```

All existing code continues to work without modification.

---

## Migration Path

### Phase 1: ✅ Completed
- Switch to modular implementation
- Create event packages
- Add event map

### Phase 2: ✅ Completed  
- Implement event handlers
- Add single entry point
- Maintain backward compatibility

### Phase 3: In Progress
- Update client-side code to use `event` field
- Document new protocol
- Create migration guide

### Phase 4: Future
- Deprecate legacy format support
- Remove old bifrost_bridge.py
- Clean up redundant code

---

## Comparison to zDisplay

| Feature | zDisplay | zBifrost |
|---------|----------|----------|
| Event Map | ✅ | ✅ |
| Single Handler | `handle()` | `handle_message()` |
| Event Packages | zEvents | bridge_modules/events |
| Registry | `_event_map` | `_event_map` |
| Backward Compat | N/A | ✅ Full support |

---

## Best Practices

### For Developers

1. **Add New Events**
   - Create handler in appropriate events/*.py
   - Register in `_event_map`
   - Document in MESSAGE_PROTOCOL.md

2. **Use Event Field**
   - Always use `{"event": "..."}` format
   - Don't rely on backward compatibility inference

3. **Handle Errors**
   - Use try/except in event handlers
   - Return proper error responses
   - Log errors with context

### For Users

1. **Send Messages**
   ```python
   ws.send(json.dumps({
       "event": "dispatch",
       "zKey": "^List.users"
   }))
   ```

2. **Handle Responses**
   ```python
   response = json.loads(message)
   if "error" in response:
       # Handle error
   else:
       result = response["result"]
   ```

---

## See Also

- `MESSAGE_PROTOCOL.md` - Complete protocol documentation
- `zDisplay/` - Frontend event system
- `HOOKS_GUIDE.md` - WebSocket hooks

