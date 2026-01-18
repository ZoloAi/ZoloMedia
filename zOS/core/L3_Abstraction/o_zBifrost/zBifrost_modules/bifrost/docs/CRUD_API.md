# BifrostClient CRUD API Documentation

**Version:** 1.5.5  
**Last Updated:** 2025-01-15

## Overview

The `BifrostClient` provides a simple, promise-based API for CRUD (Create, Read, Update, Delete) operations over WebSocket. All operations return promises that resolve with the server's response or reject with an error.

---

## Core Principles

1. **Promise-Based** - All CRUD methods return promises
2. **Automatic Correlation** - `_requestId` is automatically managed
3. **Type-Safe** - Clear request/response structures
4. **Error Handling** - Promises reject on errors, resolve on success

---

## API Reference

### `client.create(model, data, options)`

Create a new resource.

**Parameters:**
- `model` (string, required): Model/resource name (e.g., "User", "Post")
- `data` (object, required): Resource data to create
- `options` (object, optional): Additional options
  - `timeout` (number): Request timeout in milliseconds (default: 30000)

**Returns:** Promise<object> - Created resource with server-generated fields (id, timestamps, etc.)

**Example:**
```javascript
try {
  const user = await client.create('User', {
    name: 'John Doe',
    email: 'john@example.com'
  });
  console.log('Created user:', user);
  // { id: 42, name: 'John Doe', email: 'john@example.com', created_at: '2025-01-15T10:30:00Z' }
} catch (error) {
  console.error('Failed to create user:', error);
}
```

**Request Format:**
```json
{
  "event": "dispatch",
  "_requestId": 1,
  "zKey": "^Create User",
  "model": "User",
  "data": {
    "name": "John Doe",
    "email": "john@example.com"
  }
}
```

**Note:** CRUD operations use the `dispatch` event with zCLI command keys (`^Create`, `^List`, `^Update`, `^Delete`).

**Response Format:**
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

### `client.read(model, params, options)`

Read/query resources.

**Parameters:**
- `model` (string, required): Model/resource name
- `params` (object, optional): Query parameters
  - `id` (number/string): Specific resource ID
  - `limit` (number): Maximum number of results
  - `offset` (number): Pagination offset
  - `filters` (object): Filter conditions
- `options` (object, optional): Additional options
  - `timeout` (number): Request timeout in milliseconds
  - `cache_ttl` (number): Cache TTL override in seconds
  - `no_cache` (boolean): Disable caching for this request

**Returns:** Promise<object|array> - Single resource (if `id` provided) or array of resources

**Example (Single Resource):**
```javascript
const user = await client.read('User', { id: 42 });
console.log('User:', user);
// { id: 42, name: 'John Doe', email: 'john@example.com' }
```

**Example (List with Filters):**
```javascript
const users = await client.read('User', {
  limit: 10,
  offset: 0,
  filters: { role: 'admin' }
});
console.log('Admin users:', users);
// [{ id: 1, name: 'Alice' }, { id: 2, name: 'Bob' }]
```

**Example (Disable Cache):**
```javascript
const freshData = await client.read('User', { id: 42 }, { no_cache: true });
```

**Request Format:**
```json
{
  "event": "dispatch",
  "_requestId": 2,
  "zKey": "^List User",
  "model": "User",
  "where": {
    "id": 42
  }
}
```

**Response Format:**
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

**Response Format (Cached):**
```json
{
  "_requestId": 2,
  "result": {
    "id": 42,
    "name": "John Doe",
    "email": "john@example.com"
  },
  "_cached": true
}
```

---

### `client.update(model, params, data, options)`

Update an existing resource.

**Parameters:**
- `model` (string, required): Model/resource name
- `params` (object, required): Resource identifier (usually `{ id: ... }`)
- `data` (object, required): Fields to update
- `options` (object, optional): Additional options
  - `timeout` (number): Request timeout in milliseconds

**Returns:** Promise<object> - Updated resource

**Example:**
```javascript
const updatedUser = await client.update('User', 
  { id: 42 }, 
  { email: 'newemail@example.com' }
);
console.log('Updated user:', updatedUser);
// { id: 42, name: 'John Doe', email: 'newemail@example.com', updated_at: '2025-01-15T10:35:00Z' }
```

**Request Format:**
```json
{
  "event": "dispatch",
  "_requestId": 3,
  "zKey": "^Update User",
  "model": "User",
  "where": {
    "id": 42
  },
  "data": {
    "email": "newemail@example.com"
  }
}
```

**Response Format:**
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

### `client.delete(model, params, options)`

Delete a resource.

**Parameters:**
- `model` (string, required): Model/resource name
- `params` (object, required): Resource identifier (usually `{ id: ... }`)
- `options` (object, optional): Additional options
  - `timeout` (number): Request timeout in milliseconds

**Returns:** Promise<object> - Deletion confirmation

**Example:**
```javascript
const result = await client.delete('User', { id: 42 });
console.log('Deleted:', result);
// { deleted: true, id: 42 }
```

**Request Format:**
```json
{
  "event": "dispatch",
  "_requestId": 4,
  "zKey": "^Delete User",
  "model": "User",
  "where": {
    "id": 42
  }
}
```

**Response Format:**
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

## Error Handling

All CRUD methods reject their promises when an error occurs. The error message comes from the server's `error` field.

**Example:**
```javascript
try {
  await client.read('User', { id: 999 });
} catch (error) {
  console.error('Error:', error.message);
  // "User with id 999 not found"
}
```

**Error Response Format:**
```json
{
  "_requestId": 2,
  "error": "User with id 999 not found"
}
```

---

## Advanced Usage

### Custom Timeout

```javascript
// 5-second timeout instead of default 30 seconds
const user = await client.read('User', { id: 42 }, { timeout: 5000 });
```

### Cache Control

```javascript
// Disable cache for this request
const freshData = await client.read('User', { id: 42 }, { no_cache: true });

// Custom cache TTL (120 seconds)
const cachedData = await client.read('User', { id: 42 }, { cache_ttl: 120 });
```

### Batch Operations

```javascript
// Create multiple users in parallel
const users = await Promise.all([
  client.create('User', { name: 'Alice', email: 'alice@example.com' }),
  client.create('User', { name: 'Bob', email: 'bob@example.com' }),
  client.create('User', { name: 'Charlie', email: 'charlie@example.com' })
]);
console.log('Created users:', users);
```

### Error Recovery

```javascript
async function fetchUserWithRetry(id, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await client.read('User', { id });
    } catch (error) {
      if (i === maxRetries - 1) throw error;
      console.log(`Retry ${i + 1}/${maxRetries}...`);
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
  }
}
```

---

## Implementation Status

✅ **Implemented:**
- `create()` method with promise-based API
- `read()` method with filtering and caching
- `update()` method with partial updates
- `delete()` method with confirmation
- Automatic `_requestId` correlation
- Error handling with promise rejection
- Timeout support
- Cache control options

⏳ **Coming Soon:**
- Optimistic updates (update UI before server confirms)
- Batch operations helper (`client.batch()`)
- Real-time subscriptions (`client.subscribe()`)
- Offline queue (retry failed operations when reconnected)

---

## See Also

- [Message Protocol Documentation](./MESSAGE_PROTOCOL.md)
- [BifrostClient Core API](../client/README.md)
- [zBifrost Architecture](../README.md)


