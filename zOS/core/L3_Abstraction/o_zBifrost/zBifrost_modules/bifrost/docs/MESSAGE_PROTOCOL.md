# zBifrost Message Protocol

**Version:** 1.5.5  
**Last Updated:** 2025-01-15

## Overview

This document defines the standard message protocol for communication between the `BifrostClient` (JavaScript frontend) and `zBifrost` server (Python backend) over WebSocket.

---

## Core Principles

1. **All messages are JSON** - Both client→server and server→client
2. **Request-Response Correlation** - Every request includes `_requestId`, server echoes it back
3. **Event-Driven** - Messages use `event` field to specify the action type
4. **Structured Responses** - Responses include either `result` (success) or `error` (failure)

---

## Message Structure

### Client → Server (Request)

```json
{
  "event": "string",        // Required: Event type (e.g., "create", "read", "update", "delete")
  "_requestId": 123,        // Required: Unique request ID for correlation
  "model": "string",        // Optional: Model/resource name
  "zKey": "string",         // Optional: zCLI command key
  "zHorizontal": "string",  // Optional: zCLI horizontal routing
  "data": {},               // Optional: Payload data
  "params": {}              // Optional: Query parameters
}
```

### Server → Client (Response)

```json
{
  "_requestId": 123,        // Required: Echoed from request
  "result": {},             // Present on success
  "error": "string"         // Present on failure
}
```

### Server → Client (Broadcast)

```json
{
  "event": "string",        // Event type (e.g., "display", "broadcast")
  "data": {}                // Event payload
}
```

---

## Standard Events

### CRUD Operations

#### `create` - Create a new resource

**Request:**
```json
{
  "event": "create",
  "_requestId": 1,
  "model": "User",
  "data": {
    "name": "John Doe",
    "email": "john@example.com"
  }
}
```

**Response:**
```json
{
  "_requestId": 1,
  "result": {
    "id": 42,
    "name": "John Doe",
    "email": "john@example.com",
    "created_at": "2025-01-15T10:30:00Z"
  }
}
```

---

#### `read` - Read/query resources

**Request:**
```json
{
  "event": "read",
  "_requestId": 2,
  "model": "User",
  "params": {
    "id": 42
  }
}
```

**Response:**
```json
{
  "_requestId": 2,
  "result": {
    "id": 42,
    "name": "John Doe",
    "email": "john@example.com"
  }
}
```

---

#### `update` - Update an existing resource

**Request:**
```json
{
  "event": "update",
  "_requestId": 3,
  "model": "User",
  "params": {
    "id": 42
  },
  "data": {
    "email": "newemail@example.com"
  }
}
```

**Response:**
```json
{
  "_requestId": 3,
  "result": {
    "id": 42,
    "name": "John Doe",
    "email": "newemail@example.com",
    "updated_at": "2025-01-15T10:35:00Z"
  }
}
```

---

#### `delete` - Delete a resource

**Request:**
```json
{
  "event": "delete",
  "_requestId": 4,
  "model": "User",
  "params": {
    "id": 42
  }
}
```

**Response:**
```json
{
  "_requestId": 4,
  "result": {
    "deleted": true,
    "id": 42
  }
}
```

---

### Cache Management

#### `clear_cache` - Clear all cached data

**Request:**
```json
{
  "event": "clear_cache",
  "_requestId": 5
}
```

**Response:**
```json
{
  "_requestId": 5,
  "result": "Cache cleared successfully",
  "stats": {
    "queries_cleared": 42,
    "schemas_cleared": 5
  }
}
```

---

#### `cache_stats` - Get cache statistics

**Request:**
```json
{
  "event": "cache_stats",
  "_requestId": 6
}
```

**Response:**
```json
{
  "_requestId": 6,
  "result": {
    "query_cache": {
      "hits": 150,
      "misses": 30,
      "hit_rate": 0.833
    },
    "schema_cache": {
      "entries": 5
    }
  }
}
```

---

#### `set_query_cache_ttl` - Set cache TTL

**Request:**
```json
{
  "event": "set_query_cache_ttl",
  "_requestId": 7,
  "ttl": 120
}
```

**Response:**
```json
{
  "_requestId": 7,
  "result": "Query cache TTL set to 120 seconds"
}
```

---

### Schema & Discovery

#### `get_schema` - Load model schema

**Request:**
```json
{
  "event": "get_schema",
  "_requestId": 8,
  "model": "User"
}
```

**Response:**
```json
{
  "_requestId": 8,
  "result": {
    "model": "User",
    "fields": {
      "id": {"type": "integer", "primary_key": true},
      "name": {"type": "string", "required": true},
      "email": {"type": "string", "unique": true}
    }
  }
}
```

---

#### `discover` - Auto-discover available models

**Request:**
```json
{
  "event": "discover",
  "_requestId": 9
}
```

**Response:**
```json
{
  "_requestId": 9,
  "result": {
    "models": ["User", "Post", "Comment", "Tag"]
  }
}
```

---

#### `introspect` - Introspect model structure

**Request:**
```json
{
  "event": "introspect",
  "_requestId": 10,
  "model": "User"
}
```

**Response:**
```json
{
  "_requestId": 10,
  "result": {
    "model": "User",
    "table": "users",
    "columns": ["id", "name", "email", "created_at"],
    "relationships": {
      "posts": {"type": "has_many", "model": "Post"}
    }
  }
}
```

---

### zCLI Command Dispatch

#### zDispatch Command Execution

**Request:**
```json
{
  "event": "dispatch",
  "_requestId": 11,
  "zKey": "User.List",
  "zHorizontal": "User.List",
  "params": {
    "limit": 10,
    "offset": 0
  }
}
```

**Response (Success):**
```json
{
  "_requestId": 11,
  "result": [
    {"id": 1, "name": "Alice"},
    {"id": 2, "name": "Bob"}
  ]
}
```

**Response (Cached):**
```json
{
  "_requestId": 11,
  "result": [
    {"id": 1, "name": "Alice"},
    {"id": 2, "name": "Bob"}
  ],
  "_cached": true
}
```

---

### Broadcast Events (Server → Client)

#### `display` - zDisplay event for UI rendering

**Broadcast:**
```json
{
  "event": "display",
  "type": "text",
  "content": "Hello from backend!",
  "target": "zui-content"
}
```

---

#### `broadcast` - General broadcast message

**Broadcast:**
```json
{
  "event": "broadcast",
  "data": {
    "message": "Server notification",
    "timestamp": "2025-01-15T10:40:00Z"
  }
}
```

---

#### `input_request` - Request user input

**Broadcast:**
```json
{
  "event": "input_request",
  "requestId": "input_123",
  "prompt": "Enter your name:",
  "type": "text"
}
```

**Client Response:**
```json
{
  "event": "input_response",
  "requestId": "input_123",
  "value": "John Doe"
}
```

---

#### Progress & Spinner Events

**Progress Bar:**
```json
{
  "event": "progress_bar",
  "id": "upload_1",
  "total": 100,
  "label": "Uploading..."
}
```

**Progress Update:**
```json
{
  "event": "progress_update",
  "id": "upload_1",
  "current": 45
}
```

**Progress Complete:**
```json
{
  "event": "progress_complete",
  "id": "upload_1"
}
```

**Spinner Start:**
```json
{
  "event": "spinner_start",
  "id": "loading_1",
  "message": "Loading data..."
}
```

**Spinner Stop:**
```json
{
  "event": "spinner_stop",
  "id": "loading_1"
}
```

---

## Error Handling

### Error Response Format

```json
{
  "_requestId": 123,
  "error": "User with id 42 not found"
}
```

### Common Error Scenarios

1. **Missing `_requestId`** - Client logs error, does not correlate
2. **Invalid JSON** - Message is broadcast as-is (fallback)
3. **Unknown event** - Treated as broadcast
4. **Backend exception** - Returns `error` field with exception message

---

## Migration Notes

### Deprecated Fields (v1.5.5)

- `action` field → Use `event` instead
- `cmd` field → Use `zKey` instead

### Backward Compatibility

The backend currently supports both `action` and `event` fields during the transition period. However, **all new code should use `event`**.

---

## Implementation Checklist

- [x] Request-Response correlation with `_requestId`
- [x] Backend echoes `_requestId` in all responses
- [x] Standardize all messages to use `event` field (v1.5.5)
- [x] Backend supports both `event` and `action` for backward compatibility
- [x] Protocol fully documented with examples
- [ ] Remove `action` field support (planned for v1.6.0)
- [ ] Update all demos to use `event` field
- [ ] Add protocol validation in `message_handler.js`

---

## See Also

- [BifrostClient API Documentation](./API.md) *(coming soon)*
- [zDisplay Event Reference](../../zDisplay/README.md)
- [zBifrost Architecture](../README.md)
