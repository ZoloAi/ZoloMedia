# zServer Guide

> **Lightweight HTTP Static File Server**  
> Serves HTML, CSS, JavaScript using Python's built-in http.server. Zero dependencies.

---

## What It Does

**zServer** is an optional subsystem that adds HTTP static file serving to zOS applications:

- ✅ **Static file serving** - HTML, CSS, JavaScript, images
- ✅ **Background threading** - Non-blocking, runs alongside your app
- ✅ **CORS enabled** - Automatic headers for local development
- ✅ **Security built-in** - Directory listing disabled
- ✅ **Logger integration** - All requests logged via zOS
- ✅ **Works with zBifrost** - HTTP + WebSocket = full-stack

**Status:** ✅ Production-ready (100% test coverage, 35/35 tests passing)

---

## Why It Matters

### For Developers
- **Zero dependencies** - Uses Python's built-in `http.server`
- **Simple API** - 5 methods (start, stop, is_running, get_url, health_check)
- **Runs in background** - Daemon thread, non-blocking
- **Mock-friendly** - All tests run without network binding
- **Industry-grade** - 35 comprehensive tests, 8 categories

### For Executives
- **Reduces infrastructure costs** - No separate web server needed for dev
- **Fast prototyping** - Serve web UIs alongside CLI apps
- **Production-ready** - 35 tests ensure reliability
- **Optional feature** - Only use if needed, zero overhead otherwise
- **Works standalone or with WebSocket** - Flexible architecture

---

## Architecture (Simple View)

```
zServer (Optional HTTP Server)
│
├── Static File Serving
│   ├── HTML, CSS, JavaScript
│   ├── Images, fonts, JSON
│   └── Any static content
│
├── Background Thread (daemon=True)
│   ├── Non-blocking execution
│   └── Automatic cleanup
│
├── CORS Support
│   ├── Access-Control-Allow-Origin: *
│   └── OPTIONS preflight handling
│
└── Security
    ├── Directory listing disabled
    └── Localhost-only by default

Integration Points:
├── zComm.create_http_server() → Factory method
└── zConfig.http_server → Configuration
```

**Test Coverage:** 35 tests across 8 categories = 100% coverage

---

## How It Works

### 1. Create HTTP Server

```python
from zOS import zOS

z = zOS({"zWorkspace": "."})

# Create server via zComm
http_server = z.comm.create_http_server(
    port=8080,
    host="127.0.0.1",
    serve_path="./public"
)
```

### 2. Start Server

```python
# Start in background thread
http_server.start()

print(f"Server running at: {http_server.get_url()}")
# Output: Server running at: http://127.0.0.1:8080
```

### 3. Serve Files

Place files in `serve_path`:
```
public/
├── index.html
├── style.css
└── script.js
```

Access via: `http://127.0.0.1:8080/index.html`

### 4. Stop Server

```python
# Graceful shutdown
http_server.stop()
```

---

## API Reference

### Factory Method (via zComm)

#### `zComm.create_http_server(port=None, host=None, serve_path=None)`
Create HTTP server instance.

```python
http_server = z.comm.create_http_server(
    port=8080,
    host="127.0.0.1",
    serve_path="./public"
)
```

### Server Methods

#### `start()`
Start HTTP server in background thread.

```python
http_server.start()
# Raises OSError if port already in use
```

#### `stop()`
Stop HTTP server gracefully.

```python
http_server.stop()
# Shuts down thread, closes connections
```

#### `is_running()`
Check if server is running.

```python
if http_server.is_running():
    print("Server is active")
# Returns: bool
```

#### `get_url()`
Get server URL.

```python
url = http_server.get_url()
# Returns: "http://127.0.0.1:8080"
```

#### `health_check()`
Get comprehensive server status.

```python
status = http_server.health_check()
# Returns: {
#   "running": True,
#   "host": "127.0.0.1",
#   "port": 8080,
#   "url": "http://127.0.0.1:8080",
#   "serve_path": "/path/to/files"
# }
```

---

## Configuration

### Via zSpark (zOS init)

```python
z = zOS({
    "http_server": {
        "host": "127.0.0.1",
        "port": 8080,
        "serve_path": "./public",
        "enabled": True
    }
})
```

### Programmatic

```python
# Custom configuration
http_server = z.comm.create_http_server(
    host="0.0.0.0",           # All interfaces
    port=9090,                 # Custom port
    serve_path="/var/www"      # Specific path
)
```

---

## Common Patterns

### Pattern 1: Development Server

```python
#!/usr/bin/env python3
from zOS import zOS

z = zOS({"zWorkspace": "."})

# Start HTTP server
server = z.comm.create_http_server(port=8080, serve_path="./public")
server.start()

print(f"Dev server: {server.get_url()}")
input("Press Enter to stop...")

server.stop()
```

### Pattern 2: Full-Stack (HTTP + WebSocket)

```python
#!/usr/bin/env python3
from zOS import zOS

z = zOS({
    "zMode": "zBifrost",
    "websocket": {"port": 8765, "require_auth": False},
    "http_server": {"port": 8080, "serve_path": ".", "enabled": True}
})

# Start HTTP server
http_server = z.comm.create_http_server(port=8080)
http_server.start()

print(f"HTTP:      {http_server.get_url()}")
print(f"WebSocket: ws://127.0.0.1:8765")

# Start WebSocket server (blocking)
z.walker.run()
```

### Pattern 3: With Health Check

```python
# Start server
server = z.comm.create_http_server(port=8080)
server.start()

# Monitor status
while True:
    status = server.health_check()
    if not status["running"]:
        print("Server stopped unexpectedly!")
        break
    time.sleep(10)
```

---

## Relationship with zBifrost

**zServer** (HTTP) and **zBifrost** (WebSocket) are **independent systems**:

| Aspect | zServer | zBifrost |
|--------|---------|----------|
| Protocol | HTTP | WebSocket |
| Direction | One-way (request → response) | Bidirectional |
| Purpose | Static file delivery | Real-time messaging |
| Library | `http.server` | `websockets` |
| Port | 8080 (default) | 8765 (default) |
| Auth | ❌ No | ✅ Yes |

**Can Run:**
- ✅ **Standalone**: zServer only (no WebSocket)
- ✅ **Standalone**: zBifrost only (no HTTP)
- ✅ **Together**: Both systems (full-stack)

**Why Separate?**
- Different protocols (HTTP vs WebSocket)
- Different use cases (static vs real-time)
- Different security models
- Easier to maintain and update

---

## Testing

### Declarative Test Suite
**Location:** `zTestRunner/zUI.zServer_tests.yaml`  
**Plugin:** `zTestRunner/plugins/zserver_tests.py`  
**Total Tests:** 35 (100% passing)

### Test Categories (8)

| Category | Tests | Coverage |
|----------|-------|----------|
| A. Initialization & Configuration | 5 | Defaults, custom config, zOS integration |
| B. Lifecycle Management | 6 | Start/stop, status, warnings, threads |
| C. Static File Serving | 5 | HTML, CSS, JS, path config, security |
| D. CORS Support | 4 | Headers, OPTIONS, local dev |
| E. Error Handling | 5 | Port conflicts, paths, logging, shutdown |
| F. Health Check API | 4 | Status tracking, structure validation |
| G. URL Generation | 3 | Format, custom host/port |
| H. Integration & Handler | 3 | Logger, methods, attributes |

### Run Tests

```bash
# From zOS test menu
python main.py
# Select: zServer

# Or direct (option 17)
python main.py << 'EOF'
17
EOF
```

### Test Results

```
==========================================================================================
zServer Comprehensive Test Suite - 35 Tests
==========================================================================================

A. Initialization & Configuration (5 tests)
------------------------------------------------------------------------------------------
  [OK]  Init: Default Configuration                      Defaults: port=8080, host=127.0.0.1
  [OK]  Init: Custom Configuration                       Custom port=9090, host=0.0.0.0
  ...

[8 categories total]

==========================================================================================
SUMMARY: 35/35 passed (100.0%) | Errors: 0 | Warnings: 0
==========================================================================================
```

---

## Best Practices

### ✅ DO: Use High Ports
```python
server = z.comm.create_http_server(port=8080)  # No root needed
```

### ❌ DON'T: Use Low Ports
```python
server = z.comm.create_http_server(port=80)  # Requires root!
```

---

### ✅ DO: Bind to Localhost for Dev
```python
server = z.comm.create_http_server(host="127.0.0.1")  # Secure
```

### ❌ DON'T: Expose to Network Without Protection
```python
server = z.comm.create_http_server(host="0.0.0.0")  # Insecure!
```

---

### ✅ DO: Clean Shutdown in Handlers
```python
try:
    server.start()
    z.walker.run()
except KeyboardInterrupt:
    server.stop()  # Clean exit
```

### ❌ DON'T: Leave Server Running
```python
server.start()
# Forgot to stop() → resource leak
```

---

### ✅ DO: Check Status Before Actions
```python
if server.is_running():
    server.stop()
```

### ❌ DON'T: Assume Server State
```python
server.stop()  # May not be running, logs warning
```

---

## Security Considerations

### Localhost Only (Default)

```python
# Safe: Only accessible from same machine
server = z.comm.create_http_server()
```

### Network Exposure (Use Proxy)

```python
# ⚠️ Only in trusted networks or behind nginx/Apache
server = z.comm.create_http_server(host="0.0.0.0")
```

### Built-in Security Features

- ✅ **Directory listing disabled** - 403 error for directory browsing
- ✅ **CORS enabled** - For local development only
- ✅ **Localhost default** - Secure by default
- ❌ **No authentication** - Use reverse proxy for production

---

## Troubleshooting

### Issue: Port already in use

```python
OSError: [zServer] Port 8080 already in use
```

**Solution**: Change port or stop conflicting process
```python
server = z.comm.create_http_server(port=9090)
```

### Issue: Permission denied

```python
OSError: [Errno 13] Permission denied
```

**Solution**: Use ports 1024+ (no root required)
```python
server = z.comm.create_http_server(port=8080)  # Not 80
```

### Issue: Files not found

```
404 Error: File not found
```

**Solution**: Verify serve_path and file locations
```python
from pathlib import Path

serve_path = Path("./public").resolve()
print(f"Serving from: {serve_path}")
server = z.comm.create_http_server(serve_path=str(serve_path))
```

### Issue: Server won't stop

**Solution**: Force stop with timeout
```python
server.stop()  # Has 2-second thread join timeout
# Server automatically cleaned up
```

---

## Performance Tips

1. **Use appropriate serve_path** - Don't serve entire filesystem
2. **Separate ports** - HTTP and WebSocket on different ports
3. **Monitor health** - Use health_check() for production monitoring
4. **Clean shutdown** - Always call stop() in exception handlers

---

## Examples Directory

**Location:** `Demos/zBifost/`

Example applications showing:
- Static file serving
- HTTP + WebSocket integration
- Production deployment patterns
- Security best practices

---

## Summary

**zServer** is a lightweight HTTP static file server built into zOS:

- **Simple** - 5 methods, zero dependencies
- **Secure** - Directory listing disabled, localhost default
- **Fast** - Background thread, non-blocking
- **Tested** - 35 tests, 100% coverage
- **Optional** - Use only when needed

**Use Cases:**
- Serve web UI for CLI apps
- Development web server
- Full-stack apps (with zBifrost)
- Static asset hosting

**Test Coverage:** 35/35 tests passing (100%)  
**Status:** ✅ Production Ready  
**Version:** 1.5.4
