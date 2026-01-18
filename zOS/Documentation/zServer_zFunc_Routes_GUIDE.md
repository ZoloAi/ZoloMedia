# zServer zFunc Routes - Schema-Aware API Endpoints

**Version**: v1.5.8  
**Status**: ✅ Complete  
**Pattern**: Declarative API routing with schema integration

---

## Overview

`type: zFunc` routes enable **declarative API endpoints** that call plugin functions directly, with automatic schema resolution and context injection.

### Philosophy
- **Routes are data, not code** - Define API endpoints declaratively in YAML
- **Schema-first design** - Link routes to zSchemas for auto-validation
- **Plugin-based handlers** - Keep business logic in plugins, routing in YAML

---

## Basic Pattern

### Route Definition
```yaml
# zServer.api.yaml
meta:
  base_path: "/api"
  schema: "@.zSchema.users"  # Default schema (optional)

routes:
  "/api/users/:user_id/avatar":
    type: zFunc                              # Route type
    method: POST                              # HTTP method
    handler: "&file_operations.upload_avatar" # Plugin function reference
    zRBAC:
      public: true                            # RBAC config
    context:
      max_size_mb: 5                          # Route-specific config
```

### Plugin Handler
```python
# plugins/file_operations.py
def upload_avatar(request_context):
    """
    Handle avatar upload request.
    
    Args:
        request_context: {
            'method': 'POST',
            'path': '/api/users/1/avatar',
            'headers': {...},
            'route': {...},                   # Full route definition
            'route_params': {'user_id': '1'}, # Extracted URL params
            'schema': {                       # Auto-injected schema context
                'schema_name': 'users',
                'schema_ref': '@.zSchema.users',
                'table_name': 'users'
            },
            'body': b'...',                   # Request body (for POST/PUT)
            'content_type': 'multipart/form-data'
        }
    
    Returns:
        dict: JSON response with status_code
        str: Plain text response
        bytes: Binary response
        None: 204 No Content
    """
    user_id = request_context['route_params']['user_id']
    schema_name = request_context['schema']['schema_name']
    
    # Business logic here...
    
    return {
        'status_code': 200,
        'success': True,
        'avatar_url': '/storage/avatars/123.jpg'
    }
```

---

## Schema Resolution Hierarchy

zFunc routes support **two-level schema resolution** (same pattern as zOS's config hierarchy):

### Level 1: Meta-Level Schema (Default)
```yaml
meta:
  schema: "@.zSchema.users"  # Default for ALL routes in this file

routes:
  "/api/users/:user_id/avatar":
    type: zFunc
    handler: "&file_operations.upload_avatar"
    # Inherits schema: "@.zSchema.users" from meta
```

### Level 2: Route-Level Model (Override)
```yaml
meta:
  schema: "@.zSchema.users"  # Default

routes:
  "/api/users/:user_id/avatar":
    type: zFunc
    handler: "&file_operations.upload_avatar"
    # Uses meta.schema

  "/api/services/:service_id/logo":
    type: zFunc
    handler: "&service_operations.upload_logo"
    model: "@.zSchema.services"  # OVERRIDES meta.schema
```

**Resolution Order**:
1. Check route-level `model`
2. Fall back to meta-level `schema`
3. If neither exists, `schema: null` in context

---

## Parametrized Routes

### Syntax
Use `:param_name` for dynamic URL segments:

```yaml
"/api/users/:user_id/files/:file_id":
  type: zFunc
  handler: "&file_operations.delete_file"
```

### Matching
- `/api/users/123/files/456` ✅ Matches → `{user_id: "123", file_id: "456"}`
- `/api/users/123/avatar` ❌ No match (different number of segments)

### Access in Handler
```python
def delete_file(request_context):
    user_id = request_context['route_params']['user_id']      # "123"
    file_id = request_context['route_params']['file_id']      # "456"
    schema = request_context['schema']['table_name']          # "users"
```

---

## HTTP Methods

zFunc routes support all HTTP methods:

```yaml
routes:
  "/api/users/:user_id":
    type: zFunc
    method: GET                    # Read user
    handler: "&user_ops.get_user"
  
  "/api/users/:user_id":
    type: zFunc
    method: PUT                    # Update user
    handler: "&user_ops.update_user"
  
  "/api/users/:user_id":
    type: zFunc
    method: DELETE                 # Delete user
    handler: "&user_ops.delete_user"
```

**Note**: For POST/PUT/PATCH, `request_context['body']` contains raw request body.

---

## Response Formats

Handlers can return multiple formats:

### 1. JSON (dict)
```python
return {
    'status_code': 200,  # Optional, defaults to 200
    'success': True,
    'data': {...}
}
# → HTTP 200, Content-Type: application/json
```

### 2. Plain Text (str)
```python
return "Upload successful"
# → HTTP 200, Content-Type: text/plain
```

### 3. Binary (bytes)
```python
return file_bytes
# → HTTP 200, Content-Type: application/octet-stream
```

### 4. No Content (None)
```python
return None
# → HTTP 204 No Content
```

---

## RBAC Integration

zFunc routes fully support zAuth RBAC:

```yaml
"/api/users/:user_id/avatar":
  type: zFunc
  handler: "&file_operations.upload_avatar"
  zRBAC:
    require_auth: true              # Must be logged in
    require_role: "user"            # Must have 'user' role
    require_permission: "upload"    # Must have 'upload' permission
```

Access is checked **before** calling the handler function.

---

## Context Field

Use `context:` for route-specific configuration:

```yaml
"/api/users/:user_id/avatar":
  type: zFunc
  handler: "&file_operations.upload_avatar"
  context:
    max_size_mb: 5
    allowed_types: ["image/jpeg", "image/png"]
    file_type: "avatar"
```

Access in handler:
```python
def upload_avatar(request_context):
    max_size = request_context['route']['context']['max_size_mb']
    allowed = request_context['route']['context']['allowed_types']
```

---

## Complete Example: Avatar Upload

### Route Definition
```yaml
# zCloud/routes/zServer.api.yaml
meta:
  base_path: "/api"
  schema: "@.zSchema.users"

routes:
  "/api/users/:user_id/avatar":
    type: zFunc
    method: POST
    handler: "&file_operations.upload_avatar"
    zRBAC:
      public: true
    context:
      max_size_mb: 5
      allowed_types: ["image/jpeg", "image/png", "image/webp"]
```

### Plugin Handler
```python
# zCloud/plugins/file_operations.py
def upload_avatar(request_context):
    # Extract route params
    user_id = request_context['route_params']['user_id']
    
    # Get schema context
    table_name = request_context['schema']['table_name']  # 'users'
    
    # Parse multipart form data
    body = request_context['body']
    content_type = request_context['content_type']
    
    # Validate file
    max_size = request_context['route']['context']['max_size_mb'] * 1024 * 1024
    if len(body) > max_size:
        return {
            'status_code': 413,
            'error': 'File too large'
        }
    
    # Save file (using zcli.comm.storage)
    storage_key = f"users/{user_id}/avatar.jpg"
    zcli.comm.storage.upload(storage_key, body)
    
    # Update database (using zcli.data)
    zcli.data.update(
        table=table_name,
        where={'id': user_id},
        data={
            'avatar_url': storage_key,
            'avatar_updated_at': zcli.zfunc.zNow()
        }
    )
    
    return {
        'status_code': 200,
        'success': True,
        'avatar_url': storage_key
    }
```

---

## Comparison with Other Route Types

| Feature | `type: zFunc` | `type: form` | `type: json` | `type: template` |
|---------|---------------|--------------|--------------|------------------|
| **Use Case** | API endpoints, file uploads | HTML form submission | Static JSON responses | Server-rendered HTML |
| **Handler** | Plugin function | onSubmit dispatch | Declarative data | Jinja2 template |
| **Schema Integration** | ✅ Auto-inject | ✅ Validation | ❌ | ✅ Template context |
| **Parametrized Routes** | ✅ Yes | ❌ No | ❌ No | ✅ Yes |
| **Request Body** | ✅ Full access | ✅ Parsed form data | ❌ N/A | ❌ N/A |
| **Response Format** | JSON/Text/Binary | Redirect | JSON only | HTML only |

---

## Best Practices

### ✅ DO
- Link routes to schemas using `model:` or `meta.schema:`
- Use descriptive handler names (`upload_avatar`, not `handle_upload`)
- Return structured JSON with `status_code` for errors
- Validate inputs in handler functions
- Use `zcli.zfunc.zNow()` for timestamps

### ❌ DON'T
- Don't hardcode table names - use `request_context['schema']`
- Don't use `datetime.now()` - use `zcli.zfunc.zNow()`
- Don't return 200 for errors - use appropriate status codes
- Don't bypass RBAC - use `zRBAC` configuration
- Don't duplicate route definitions - use parametrized routes

---

## Error Handling

Handlers should return appropriate HTTP status codes:

```python
def upload_avatar(request_context):
    # Validate user exists
    user_id = request_context['route_params']['user_id']
    user = zcli.data.get('users', user_id)
    
    if not user:
        return {
            'status_code': 404,
            'error': 'User not found'
        }
    
    # Validate file type
    content_type = request_context['content_type']
    if 'image/' not in content_type:
        return {
            'status_code': 415,
            'error': 'Invalid file type'
        }
    
    # Success
    return {
        'status_code': 200,
        'success': True
    }
```

---

## Testing zFunc Routes

### Terminal-First Testing
```python
# zTest_avatar.py
zSpark = {
    "title": "Avatar Upload Test",
    "zMode": "Terminal",
    "http_server": {
        "enabled": True,
        "zShell": True  # Concurrent server + REPL
    },
    "zVaFile": "@.UI.zUI.test_avatar"
}
```

### Declarative Test (zUI.test_avatar.yaml)
```yaml
Test_Avatar_Upload:
  Generate_Image:
    - zFunc: "&test_operations.generate_test_avatar()"
  
  Upload_Image:
    - zFunc: "&test_operations.test_avatar_upload(user_id=1)"
  
  Verify_Database:
    - zFunc: "&test_operations.verify_avatar_database(user_id=1)"
```

### Run Test
```bash
cd zCloud
python3 zTest_avatar.py
# In zShell:
walker run
```

---

## See Also

- [zServer Guide](./zServer_GUIDE.md) - Complete zServer documentation
- [zMigration Guide](./zMigration_GUIDE.md) - Schema migration system
- [zComm Storage](./zComm_Storage_GUIDE.md) - File storage abstraction
- [zFunc Guide](./zFunc_GUIDE.md) - Plugin system documentation

---

**Next Steps**:
1. Add automatic parameter validation against schema
2. Implement multipart/form-data parsing in `request_context`
3. Add request/response middleware hooks
4. Support async handlers for long-running operations

