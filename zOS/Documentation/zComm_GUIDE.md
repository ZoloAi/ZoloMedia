**[← Back to zConfig Guide](zConfig_GUIDE.md) | [Home](../README.md) | [Next: zBifrost Guide →](zBifrost_GUIDE.md)**

---

# zComm

**zComm** is the **second subsystem** initialized by **zOS**.
> See [**zArchitecture**](../README.md#the-zarchitecture) for full context.

It provides unified client-side communication - HTTP requests, port checking, and service management - through one simple interface.

You get:

- **Zero configuration**  
- **No requests library**
- **No websockets library**  
- **HTTP client** (GET, POST, PUT, PATCH, DELETE)
- **Service detection** (PostgreSQL, Redis, MongoDB)  
- **Port checking** (before binding servers)

> **Note:** zComm focuses on **client-side** communication. For HTTP servers (serving HTML/CSS/JS), see [zServer Guide](zServer_GUIDE.md). For WebSocket servers (real-time bidirectional), see [zBifrost Guide](zBifrost_GUIDE.md).

## Tutorials

**Learn by doing!** 

The tutorials below are organized in a bottom-up fashion. Every tutorial below has a working demo you can run and modify.

**A Note on Learning zOS:**  
Each tutorial (lvl1, lvl2, lvl3...) progressively introduces more complex features of **this subsystem**. The early tutorials start with familiar imperative patterns (think Django-style conventions) to meet you where you are as a developer.

As you progress through zOS's subsystems, you'll notice a gradual shift from imperative to declarative patterns. This intentional journey helps reshape your mental model from imperative to declarative thinking. Only when you reach **Layer 3 (Orchestration)** will you see subsystems used **fully declaratively** as intended in production. By then, the true magic of declarative coding will reveal itself, and you'll understand why we started this way.

Get the demos:

```bash
# Clone only the Demos folder
git clone --depth 1 --filter=blob:none --sparse https://github.com/ZoloAi/zolo-zcli.git
cd zolo-zcli
git sparse-checkout set Demos
```

> All zComm demos are in: `Demos/Layer_0/zComm_Demo/`

---

# **zComm - Level 0** (Hello zComm)

After mastering zConfig's 5-layer hierarchy, you're ready to explore zComm - zOS's communication layer. The good news? You already know everything you need!

**The same zSpark pattern** from zConfig demos unlocks zComm's capabilities:

```python
from zOS import zOS

# Familiar zSpark pattern from zConfig
zSpark = {
    "deployment": "Development",  # Show subsystem banners
    "title": "hello-comm",        # Session identifier
    "logger": "PROD",             # Silent console, file-only logging
    "logger_path": "./logs",      # Where logs go
}

# Watch the initialization order in the output:
# [zConfig Ready] → [zComm Ready]

z = zOS(zSpark)

# zComm is now ready to use!
```

**Key Discovery**: zComm auto-initializes immediately after zConfig when you call `zOS()`. Both are Layer 0 subsystems - the foundation of the framework.

**🎯 Try it yourself:**

Run the demo to see zComm in action:

```bash
python3 Demos/Layer_0/zComm_Demo/lvl0_hello/1_hello_comm.py
```

[View demo source →](../Demos/Layer_0/zComm_Demo/lvl0_hello/1_hello_comm.py)

**What you'll discover:**
- Watch the initialization order: [zConfig Ready] → [zComm Ready]
- Both are Layer 0 subsystems (foundation)
- Same zSpark pattern as zConfig demos
- Communication layer ready with zero configuration

---

# **zComm - Level 1** (Network Basics)

### **i. Port Checking**

In Level 0, you watched zComm initialize. Now let's actually **use** it.  
The simplest zComm action? Checking if a network port is available.

**Think of your computer as an apartment building**. It has one address (your IP), but thousands of apartments (1-65535). **Different services "live" at different apartment numbers (ports)**:
- **Port 80** → HTTP (websites)
- **Port 443** → HTTPS (secure websites)
- **Port 5432** → PostgreSQL
- **Port 8080** → Development servers

> **Why check ports?** If two services try to use the same port, one fails. Checking first prevents the dreaded "port already in use" error!

Let's check multiple ports at once and see which services use which numbers:

```python
from zOS import zOS

# Consistent zSpark pattern
zSpark = {
    "deployment": "Production",
    "title": "port-check",
    "logger": "INFO",
    "logger_path": "./logs",
}
z = zOS(zSpark)

# Check multiple ports
ports = {80: "HTTP", 443: "HTTPS", 5432: "PostgreSQL", 6379: "Redis"}

for port, service in ports.items():
    is_available = z.comm.check_port(port)
    status = "✓ available" if is_available else "✗ in use"
    print(f"Port {port:5} ({service:12}): {status}")
```

> **Returns:** `True` if port is available (not in use), `False` if port is already bound.

**🎯 Check which ports are available on your machine:**

```bash
python3 Demos/Layer_0/zComm_Demo/lvl1_network/1_port_check.py
```

[View demo source →](../Demos/Layer_0/zComm_Demo/lvl1_network/1_port_check.py)

**What you'll discover:**
- Check common service ports (HTTP, HTTPS, PostgreSQL, Redis, MongoDB)
- Cross-platform port detection
- No manual socket probing or cleanup
- Clean, scannable output

---

### **ii. HTTP/HTTPS Requests (GET)**

Remember our apartment building? Port 80 is HTTP, port 443 is HTTPS. But what's the difference?

**HTTP (Port 80):**
- Unencrypted conversation - anyone can eavesdrop
- Like shouting across a room - everyone hears
- ❌ Never use for passwords, personal data, or production APIs

**HTTPS (Port 443):**
- Encrypted with SSL/TLS - private conversation
- Like whispering in a soundproof room - nobody can listen in
- ✅ Always use for production, sensitive data, modern web APIs
- The "S" stands for "Secure"

> **Discovery:** zComm supports both `http://` and `https://` automatically. Just change the URL - no certificates to configure, no extra code needed!

**HTTP Request Methods:**

Whether using HTTP or HTTPS, the conversation types are the same:
- **GET** → "Can I see what you have?" ***(we are here)***
- **POST** → "Here's something new for you"
- **PUT** → "Replace everything with this"
- **PATCH** → "Update just this one thing"
- **DELETE** → "Remove this item"

Let's make a secure HTTPS GET request:

```python
from zOS import zOS

# Consistent zSpark pattern
zSpark = {
    "deployment": "Production",
    "title": "http-get",
    "logger": "INFO",
    "logger_path": "./logs",
}
z = zOS(zSpark)

# Notice the https:// - secure, encrypted connection
url = "https://httpbin.org/get"

# Make GET request with query parameters
response = z.comm.http_get(url, params={"demo": "zComm", "level": "1"})

if response:
    data = response.json()
    print(f"Server received: {data.get('args')}")
```

> One line to make requests. No `requests` library needed. HTTPS encryption handled automatically.

> **About httpbin.org:** This is a free, public testing service that "echoes" back whatever you send it. Perfect for learning HTTP without needing your own server. Think of it as a practice mirror - you send a message, it bounces back so you can see it worked!

**🎯 Try it yourself:**

```bash
python3 Demos/Layer_0/zComm_Demo/lvl1_network/2_http_get.py
```

[View demo source →](../Demos/Layer_0/zComm_Demo/lvl1_network/2_http_get.py)

**What you'll discover:**
- One line: `z.comm.http_get(url, params={...})`
- Both `http://` and `https://` work identically
- HTTPS encryption is automatic (no configuration needed)
- Built-in JSON parsing with `.json()`
- Returns `None` on failure (safe, no crashes)

---

### **iii. All HTTP Methods**

Now that you've made a GET request, let's see the complete RESTful toolkit.

```python
from zOS import zOS

# Consistent zSpark pattern
zSpark = {
    "deployment": "Production",
    "title": "http-methods",
    "logger": "INFO",
    "logger_path": "./logs",
}
z = zOS(zSpark)

# GET - Retrieve data
response = z.comm.http_get("https://httpbin.org/get", params={"key": "value"})

# POST - Create resource
response = z.comm.http_post("https://httpbin.org/post", data={"name": "Alice"})

# PUT - Update entire resource
response = z.comm.http_put("https://httpbin.org/put", data={"name": "Alice", "role": "Developer"})

# PATCH - Partial update
response = z.comm.http_patch("https://httpbin.org/patch", data={"role": "Tech Lead"})

# DELETE - Remove resource
response = z.comm.http_delete("https://httpbin.org/delete")
```

> Five methods, one simple pattern. Complete RESTful HTTP client.

**🎯 Try it yourself:**

```bash
python3 Demos/Layer_0/zComm_Demo/lvl1_network/3_http_methods.py
```

[View demo source →](../Demos/Layer_0/zComm_Demo/lvl1_network/3_http_methods.py)

**What you'll discover:**
- All RESTful HTTP methods (GET, POST, PUT, PATCH, DELETE)
- Consistent API across methods
- Built-in timeout handling
- Unified response format

---

**🎯 Level 1 Complete!**

You've learned the core communication fundamentals:
- ✅ **Port checking** - Verify ports are available before binding
- ✅ **HTTP GET** - Retrieve data from APIs
- ✅ **All HTTP methods** - Complete RESTful toolkit (GET, POST, PUT, PATCH, DELETE)

**These are the essentials. Most applications only need these.**

---

# **zComm - Level 2** (WebSockets)

> **Note:** Throughout Level 2, we're using WebSockets **imperatively** - raw infrastructure, step-by-step. This is Layer 0 basics. Later, in **zBifrost (Layer 2)**, you'll see the same WebSocket capabilities used **declaratively** with full orchestration. We're starting with the foundation!  
> → [**Jump to zBifrost Guide**](zBifrost_GUIDE.md) (Advanced!)

Remember our apartment building? **HTTP was like knocking on doors** - you knock, get a response, then walk away. But what if you want to have an ongoing conversation?

**WebSockets are like installing a telephone line** - you connect once, then you can talk back and forth as long as you want! Perfect for chat, live updates, and real-time collaboration.


### **i. WebSocket Server Basics**

Let's create your first WebSocket server - a persistent connection for real-time communication.

`z.comm.websocket.start()` creates a **persistent server** that stays running:
- **Respects zConfig's 5-layer hierarchy** - defaults come from zConfig if not specified!
- Or override explicitly: `start(host="...", port=...)` 
- Keeps connections alive for bidirectional communication
- Handles multiple clients simultaneously
- Manages all async complexity internally (no `asyncio` needed!)

Think of it like opening a phone line - waiting for incoming calls. Clients connect, stay connected, and you can exchange messages freely until someone hangs up.

> **zConfig Integration:** The `start()` method follows zOS's configuration philosophy. If you don't specify `host` or `port`, it pulls from the 5-layer hierarchy (defaults → machine → environment → .zEnv → zSpark). This means you can configure WebSocket settings once in your environment and never repeat them!


```python
from zOS import zOS

# Initialize zOS - gets WebSocket infrastructure
z = zOS({
    "deployment": "Production",
    "title": "websocket-server",
    "logger": "PROD",
    "logger_path": "./logs",
})

# Start WebSocket server - zOS handles async internally
z.comm.websocket.start(host="127.0.0.1", port=8765)
```

**🎯 Try it yourself:**

```bash
python3 Demos/Layer_0/zComm_Demo/lvl2_websocket/1_websocket_server.py
```

[View demo source →](../Demos/Layer_0/zComm_Demo/lvl2_websocket/1_websocket_server.py)

**What happens when you run this?**

Unlike HTTP requests (which finish immediately), this WebSocket server **stays running** - listening on port 8765, waiting for clients to connect. The connection stays open until you explicitly close it.

In traditional Python, stopping a server safely is tricky: Ctrl+C crashes immediately, leaving the port "stuck" - you'll get "port already in use" errors on restart.

**zOS handles this automatically.** Press Ctrl+C, and zOS gracefully closes all connections, releases the port, and exits cleanly. You'll see cleanup messages confirming everything shut down properly.

**What you'll discover:**
- Create WebSocket server with one method call
- zOS handles async complexity internally
- **Safe Ctrl+C shutdown** - zOS gracefully closes connections and releases ports
- Persistent connections (unlike HTTP)
- Foundation for real-time apps

---

### **ii. Bidirectional Communication**

In the previous demo you started a server with `z.comm.websocket.start()`. Now let's make it **respond** to messages by adding the `handler` parameter.

> WebSockets work for any client (backend-to-backend, IoT, etc.), but here we'll use a **browser client** as our use case.

**Server Side (Python - Imperative):**

```python
from zOS import zOS

# Define what happens when client sends a message
async def echo_handler(websocket, message):
    """Echo messages back to the client."""
    echo_msg = f"Echo: {message}"
    await websocket.send(echo_msg)

z = zOS({
    "deployment": "Production",
    "title": "websocket-echo",
    "logger": "INFO",
    "logger_path": "./logs",
})

# Pass the handler to start()
z.comm.websocket.start(host="127.0.0.1", port=8765, handler=echo_handler)
```

**Client Side (JavaScript):**

```javascript
// Connect to server
const ws = new WebSocket('ws://127.0.0.1:8765');

// Send message to server
ws.send('Hello from browser!');

// Receive echoed message
ws.onmessage = (event) => {
    console.log('Server echoed:', event.data);
};
```

**🎯 Try it yourself:**

> **Step 1**: Start the Python server:

```bash
python3 Demos/Layer_0/zComm_Demo/lvl2_websocket/2_websocket_echo.py
```

> **Step 2**: Open the HTML client in your browser:

```bash
# Just double-click 2_client_echo.html in Finder/Explorer
```

[View demo source →](../Demos/Layer_0/zComm_Demo/lvl2_websocket/2_websocket_echo.py) | [View client →](../Demos/Layer_0/zComm_Demo/lvl2_websocket/2_client_echo.html)

**What you'll discover:**
- Add `handler` parameter to process incoming messages
- Use `websocket.send()` to reply to client
- Connect from JavaScript browser client
- Complete bidirectional communication (server ↔ client)

**About Security:** Did you notice? Any client could connect to your server - no password, no token, nothing. That's because zOS's WebSocket has `require_auth: false` by default. This makes development easy, but in production you'll want to lock it down—as you'll see in the next section.

---

### **iii. Secure Connections (Authentication)**

In Level 2.ii, any client could connect to our websocket and echo messages. But what if you want to **restrict access to authorized clients** only?

**Security is OFF by default - you turn it ON when ready**

Remember from Level 2.ii, where the connection was open (`require_auth: false`) for easy development. Now let's flip that security switch.

**Enabling Authentication**: Set `require_auth: True` in your zSpark configuration, and for our **browser use case**, we also need to specify `allowed_origins` - this controls **which web pages can connect**.

> **Note**: Backend-to-backend connections don't send origin headers, so they rely on token authentication alone.

```python
from zOS import zOS

zSpark = {
    "deployment": "Production",
    "title": "websocket-secure",
    "logger": "INFO",
    "logger_path": "./logs",
    "websocket": {
        "require_auth": True,  # 🔒 Enable authentication
        "allowed_origins": [   # 🌐 Which sites can connect?
            "http://localhost",
            "http://127.0.0.1",
            "file://",  # Local HTML files (for this demo)
        ],
    }
}

z = zOS(zSpark)

async def secure_echo_handler(websocket, message):
    """Only authenticated clients reach this handler."""
    await websocket.send(f"[Secure Echo]: {message}")

# Start secured server - requires token to connect
z.comm.websocket.start(host="127.0.0.1", port=8765, handler=secure_echo_handler)
```

**Storing Tokens Securely with `.zEnv`**

Never hardcode authentication tokens! Instead, store them in a `.zEnv` file (automatically loaded by zOS):

```bash
# .zEnv file in your project directory
WEBSOCKET_TOKEN=demo_secure_token_123
```

> **Security Best Practice:** Add `.zEnv` to your `.gitignore` file to prevent committing secrets to version control.

**Client-Side Authentication**

Clients pass the token as a query parameter in the WebSocket URL:

```javascript
// Get token from user input (in production: from login API)
const token = document.getElementById('tokenInput').value;

// Build WebSocket URL with token
const url = `ws://127.0.0.1:8765?token=${token}`;

// Create WebSocket connection
let ws = new WebSocket(url);

// Connection opened - token was valid!
ws.onopen = function() {
    console.log('✓ Connected and authenticated!');
};

// Connection closed - check if auth failed
ws.onclose = function(event) {
    if (event.code === 1008) {
        // Code 1008 = authentication failed
        console.log('❌ Authentication failed');
    }
};
```

That's it. Origin validation, token checking, connection limits - all handled by zOS. You just pass `?token=xxx` in the URL.

**Testing the Secure Demo**

```bash
# Step 1: Start the secure Python server
python3 Demos/Layer_0/zComm_Demo/lvl2_websocket/3_websocket_secure.py

# Step 2: Open the secure HTML client
# Double-click: Demos/Layer_0/zComm_Demo/lvl2_websocket/3_client_secure.html

# Step 3: Test authentication rejection
# Click "Test Wrong Token" button to see rejection in action
```

[View demo source →](../Demos/Layer_0/zComm_Demo/lvl2_websocket/3_websocket_secure.py) | [View client →](../Demos/Layer_0/zComm_Demo/lvl2_websocket/3_client_secure.html)

**What you'll discover:**
- Enable security with `require_auth: True`
- Store tokens in `.zEnv` (never hardcode!)
- Validate origin headers (CORS/CSRF protection)
- Reject unauthorized connections automatically
- Access client auth info via `z.comm.websocket.auth.get_client_info(websocket)`

**Security Features Implemented:**

| Feature | Purpose | Configuration |
|---------|---------|---------------|
| **Token Authentication** | Verify client identity | `WEBSOCKET_TOKEN` in `.zEnv` |
| **Origin Validation** | Prevent CORS/CSRF attacks | `allowed_origins` in zSpark |
| **Connection Limits** | Prevent resource exhaustion | `max_connections` in zConfig |
| **Automatic Rejection** | Close unauthorized connections | WebSocket close code 1008 |

> **Note:** For advanced three-tier authentication (zSession, Application, Dual), see [zBifrost Guide](zBifrost_GUIDE.md).

---

### **iv. Encrypted Connections (WSS - WebSocket Secure)**

So far we've used `ws://` (unencrypted WebSocket). Just like HTTP vs HTTPS, production WebSocket connections should use `wss://` (WebSocket Secure) with SSL/TLS encryption.

**Why WSS Matters:**
- **Encryption** - All data encrypted in transit (like HTTPS)
- **Industry standard** - Required for production deployments
- **Browser security** - Modern browsers require WSS for secure contexts
- **Prevents eavesdropping** - Man-in-the-middle attacks blocked

zOS makes SSL/TLS simple - it's **opt-in** via zSpark:

**Server Configuration (SSL is opt-in):**

```python
from zOS import zOS

zSpark = {
    "websocket": {
        "port": 8766,
        "require_auth": True,  # Token auth from .zEnv
        "ssl_enabled": True,  # 🔒 Opt-in to SSL/TLS
        "ssl_cert": "certs/demo.cert",
        "ssl_key": "certs/demo.key",
        "allowed_origins": [
            "https://localhost",  # Note: https (not http)
            "https://127.0.0.1",
            "file://",
        ],
    }
}

z = zOS(zSpark)
z.comm.websocket.start(host="127.0.0.1", port=8766, handler=my_handler)
```

**Why Opt-In?**
- **Development ease:** `ws://` works without certificates by default
- **Explicit security:** You consciously enable `wss://` when ready
- **Same pattern as authentication:** `require_auth: True` is also opt-in

**Production:** Store certificate paths in environment variables or `.zEnv`:
```bash
# .zEnv (production)
WEBSOCKET_TOKEN=your_secure_token
WEBSOCKET_SSL_CERT=/etc/ssl/certs/yourdomain.crt
WEBSOCKET_SSL_KEY=/etc/ssl/private/yourdomain.key
```

Then reference them in zSpark:
```python
import os
zSpark = {
    "websocket": {
        "ssl_enabled": True,
        "ssl_cert": os.getenv("WEBSOCKET_SSL_CERT"),
        "ssl_key": os.getenv("WEBSOCKET_SSL_KEY"),
    }
}
```

**Client Connection (JavaScript):**

```javascript
// Use wss:// protocol instead of ws://
const token = document.getElementById('tokenInput').value;
const ws = new WebSocket(`wss://127.0.0.1:8766?token=${token}`);

ws.onopen = function() {
    console.log('✓ Secure connection established (SSL/TLS)');
};
```

**Try it yourself:**

```bash
# Step 1: Start the WSS server
python3 Demos/Layer_0/zComm_Demo/lvl2_websocket/4_websocket_wss.py

# Step 2: Trust the certificate first (self-signed cert requirement)
# Open browser and navigate to: https://127.0.0.1:8766
# Click "Advanced" → "Proceed to 127.0.0.1 (unsafe)"
# You'll see an error page (expected - you're just teaching browser to trust cert)

# Step 3: Now open the HTML client
open Demos/Layer_0/zComm_Demo/lvl2_websocket/4_client_wss.html
```

**Why the Manual Step?**

Self-signed certificates aren't trusted by browsers by default. For WSS connections, you must explicitly trust the certificate **before** the WebSocket can connect. Navigate to `https://127.0.0.1:8766` first, accept the warning, then the HTML client will work.

In production with proper certificates from:
- **Let's Encrypt** (free, automated, recommended)
- Your organization's Certificate Authority
- Commercial SSL providers (DigiCert, Comodo, etc.)

[View demo source →](../Demos/Layer_0/zComm_Demo/lvl2_websocket/4_websocket_wss.py) | [View client →](../Demos/Layer_0/zComm_Demo/lvl2_websocket/4_client_wss.html)

**What you'll discover:**
- Configure SSL in `.zEnv` - no hardcoded paths!
- zConfig loads SSL settings via 5-layer hierarchy
- Client connects with `wss://` instead of `ws://`
- Connection is encrypted end-to-end (like HTTPS)
- Industry-standard security for production WebSockets

**zConfig Integration:**

SSL settings follow the 5-layer hierarchy:
1. **Defaults** - `ssl_enabled: false` (code)
2. **Machine Config** - System-wide YAML config
3. **Environment Variables** - `WEBSOCKET_SSL_ENABLED`, `WEBSOCKET_SSL_CERT`, `WEBSOCKET_SSL_KEY`
4. **`.zEnv` file** - Project-specific (what the demo uses)
5. **zSpark** - Runtime override

**Production Certificates:**

Never commit SSL certificates to version control! For production:
- Use `.zEnv` for local development (add to `.gitignore`)
- Use environment variables in production: `WEBSOCKET_SSL_CERT=/etc/ssl/certs/cert.pem`
- Store in secure vaults: AWS Secrets Manager, Azure Key Vault, HashiCorp Vault
- Use Let's Encrypt for free, automated certificates

**WebSocket Security Best Practices:**

| Practice | Development | Production |
|----------|-------------|------------|
| **Protocol** | `ws://` OK | `wss://` required |
| **Certificates** | Self-signed OK | CA-signed required |
| **Token Storage** | `.zEnv` file | Environment variables + secrets manager |
| **Origins** | `file://` OK | Whitelist specific domains |
| **Authentication** | Optional | Always required |

---

### **v. Broadcast to Multiple Clients (Secured)**

In previous demos, you secured connections with authentication (Level 2.iii) and encryption (Level 2.iv). Now let's apply security to **multi-client scenarios** using `z.comm.websocket.broadcast()` to send messages to all authenticated clients at once.

**Secure Broadcasting**

Combine authentication (from Level 2.iii) with broadcasting to create secure one-to-many communication:

```python
from zOS import zOS

zSpark = {
    "deployment": "Production",
    "title": "websocket-broadcast",
    "logger": "INFO",
    "logger_path": "./logs",
    "websocket": {
        "require_auth": True,  # 🔒 All clients must authenticate
        "allowed_origins": [
            "file://",  # Allow local HTML files
        ],
    }
}

z = zOS(zSpark)

# Define broadcast handler
async def broadcast_handler(websocket, message):
    """Broadcast messages to all connected clients."""
    client_addr = websocket.remote_address
    broadcast_msg = f"{client_addr[0]} says: {message}"
    
    # Use zComm broadcast primitive (excludes sender)
    count = await z.comm.websocket.broadcast(broadcast_msg, exclude=websocket)
    print(f"Broadcasted to {count} client(s)")

# Start with broadcast handler - zOS handles async internally
z.comm.websocket.start(
    host="127.0.0.1",
    port=8765,
    handler=broadcast_handler
)
```

**🎯 Try it yourself:**

```bash
# Step 1: Start the secure broadcast server
python3 Demos/Layer_0/zComm_Demo/lvl2_websocket/5_websocket_broadcast.py

# Step 2: Open the HTML client in MULTIPLE windows
# Double-click 2-3 times: Demos/Layer_0/zComm_Demo/lvl2_websocket/5_client_broadcast.html
# (Each window authenticates independently with the same token)
```

[View demo source →](../Demos/Layer_0/zComm_Demo/lvl2_websocket/5_websocket_broadcast.py) | [View client →](../Demos/Layer_0/zComm_Demo/lvl2_websocket/5_client_broadcast.html)

**What you'll discover:**
- Apply security to multi-client broadcasting
- All clients must authenticate with the same token
- Use `z.comm.websocket.broadcast()` to send to authenticated clients
- Exclude sender with `exclude=websocket` parameter
- See message count returned (how many clients received it)
- zOS tracks authenticated clients automatically

> **Note:** This is Layer 0 WebSocket infrastructure with basic token authentication. For advanced three-tier authentication (zSession, Application, Dual), caching, and Terminal↔Web orchestration, see [zBifrost Guide](zBifrost_GUIDE.md)!

---

**🎯 Level 2 Complete!**

You've mastered real-time secure bidirectional communication using **imperative primitives**:
- ✅ **WebSocket Server** - Persistent connections with `z.comm.websocket.start()`
- ✅ **Echo Messages** - Custom handlers to process messages
- ✅ **Secure Connections** - Token authentication and origin validation  
- ✅ **Encrypted Connections** - SSL/TLS with WSS protocol (production-ready)
- ✅ **Broadcast** - One-to-many messaging with authentication

**This is raw infrastructure - the building blocks.** You wrote Python code to handle each message (imperative). As you progress through zOS, you'll see how **zBifrost (Layer 2)** transforms this into declarative configuration!

---

## **What's Next?**

**Levels 3 and 4 cover advanced topics** - service management (PostgreSQL, Redis, MongoDB detection and lifecycle). These are optional for most applications.

**Choose your path:**

### **Path A: Continue to Advanced zComm** (Service Management)
If you need database/service detection → **Continue below to Level 3**

### **Path B: Skip to Next Subsystem** (zDisplay)
If you have what you need → **[Jump to zDisplay Guide](zDisplay_GUIDE.md)**

> **Recommendation:** Skip to zDisplay. Come back to Levels 3/4 when you need service management!

---

# **zComm - Level 3** (Service Management)

### **i. Service Status Check**

```python
from zOS import zOS

z = zOS({"logger": "PROD"})

# Check if PostgreSQL is running
status = z.comm.service_status("postgresql")

if status.get("running"):
    info = z.comm.get_service_connection_info("postgresql")
    print(f"✓ PostgreSQL: {info['host']}:{info['port']}")
else:
    print("✗ PostgreSQL not running")
```

Auto-detect services without OS-specific commands. Safe to run even if service isn't installed. Works across macOS, Linux, and Windows.

**Returns:** Dict with `"running"` (bool), `"port"` (int), `"os"` (str), and optional `"connection_info"` or `"error"`.

**Supported Services:** `postgresql`, `redis`, `mongodb`

**🎯 Try it yourself:**

```bash
python3 Demos/Layer_0/zComm_Demo/lvl3_services/1_service_check.py
```

[View demo source →](../Demos/Layer_0/zComm_Demo/lvl3_services/1_service_check.py)

**What you'll discover:**
- Detect if services are running
- Cross-platform service detection
- Get connection info automatically
- Safe execution (won't crash if service not installed)

> **Installation Requirements:**
> 
> **zOS PostgreSQL Support:**
> ```bash
> pip install git+ssh://git@github.com/ZoloAi/zolo-zcli.git[postgresql]
> ```
> 
> **PostgreSQL Database:**
> - **macOS:** `brew install postgresql`
> - **Linux:** `sudo apt-get install postgresql` or `sudo yum install postgresql-server`
> - **Windows:** Download from [postgresql.org/download/windows](https://www.postgresql.org/download/windows/) and run the installer
> 
> See [Installation Guide](INSTALL.md) for complete setup instructions.

### **ii. Check Multiple Services**

```python
from zOS import zOS

z = zOS({"logger": "PROD"})

# Check multiple services
services = {
    "postgresql": "PostgreSQL Database",
    "redis": "Redis Cache",
    "mongodb": "MongoDB Database"
}

for service_name, description in services.items():
    status = z.comm.service_status(service_name)
    
    if status.get("running"):
        info = z.comm.get_service_connection_info(service_name)
        print(f"✓ {description}: {info['host']}:{info['port']}")
    else:
        print(f"✗ {description}: Not running")
```

Check your entire development stack with one script. Practical for environment setup.

**Status Returns:** `{"running": True/False, "port": int, "error": str}` per service.

**Connection Returns:** `{"host": str, "port": int, "user": str}` if service is running.

**🎯 Try it yourself:**

```bash
python3 Demos/Layer_0/zComm_Demo/lvl3_services/2_service_multi.py
```

[View demo source →](../Demos/Layer_0/zComm_Demo/lvl3_services/2_service_multi.py)

**What you'll discover:**
- Check multiple services in one script
- Unified API across different services
- Practical for environment validation
- Clean, scannable output

### **iii. HTTP Error Handling**

```python
from zOS import zOS

z = zOS({"logger": "PROD"})

# Test various error conditions
test_cases = [
    ("https://httpbin.org/status/404", "404 Not Found"),
    ("https://httpbin.org/status/500", "500 Server Error"),
    ("https://invalid-domain-12345.com", "Invalid URL"),
    ("https://httpbin.org/delay/10", "Timeout (2s limit)")
]

for url, description in test_cases:
    print(f"Testing {description}...")
    response = z.comm.http_post(url, data={}, timeout=2)
    
    if response is None:
        print(f"  ✓ Handled gracefully")
    else:
        print(f"  Status: {response.status_code}")
```

All errors return `None` instead of crashing. Always check for `None` before using response.

**Error Handling:**
- ❌ Connection timeouts → `None`
- ❌ Invalid URLs/DNS failures → `None`
- ❌ Network errors → `None`
- ✅ HTTP error codes (404, 500) → Response object (check `.status_code`)

**🎯 Try it yourself:**

```bash
python3 Demos/Layer_0/zComm_Demo/lvl3_services/3_http_errors.py
```

[View demo source →](../Demos/Layer_0/zComm_Demo/lvl3_services/3_http_errors.py)

**What you'll discover:**
- Graceful error handling
- No try/except boilerplate needed
- Consistent `None` returns for failures
- HTTP status codes still accessible

---

# **zComm - Level 4** (Service Lifecycle)

### **i. Start Services Programmatically**

```python
from zOS import zOS

z = zOS({"logger": "PROD"})

# Declare: Start PostgreSQL
success = z.comm.start_service("postgresql")

if success:
    # Declare: Get connection info
    info = z.comm.get_service_connection_info("postgresql")
    print(f"✓ Ready: {info['host']}:{info['port']}")
else:
    print("✗ Failed to start")
```

Declare desired state—zComm handles orchestration. No `brew services start`, no manual checks, no waiting.

**Returns:** `True` if service started successfully, `False` if failed (not installed, insufficient permissions, port in use).

**Available Methods:** `start_service()`, `stop_service()`, `restart_service()`, `service_status()`, `get_service_connection_info()`

**🎯 Try it yourself:**

```bash
python3 Demos/Layer_0/zComm_Demo/lvl4_lifecycle/1_service_start.py
```

[View demo source →](../Demos/Layer_0/zComm_Demo/lvl4_lifecycle/1_service_start.py)

**What you'll discover:**
- Start services programmatically
- Cross-platform service management
- Automatic connection info retrieval
- Declarative service orchestration

> **Requirements:** PostgreSQL must be installed with appropriate system permissions.
> - **macOS:** Homebrew (`brew install postgresql`)
> - **Linux:** systemd/apt (`sudo apt-get install postgresql`)
> - **Windows:** Windows Services ([Download Installer](https://www.postgresql.org/download/windows/))

---

**🎯 Level 4 Complete!**

You've completed the zComm tutorial journey:
- ✅ **Level 0**: Hello zComm (Initialize zOS)
- ✅ **Level 1**: Network basics (Port checking, HTTP GET, All HTTP methods)
- ✅ **Level 2**: WebSocket communication (Server, Echo, Broadcast)
- ✅ **Level 3**: Service management (Service status, Multiple services, HTTP errors)
- ✅ **Level 4**: Service lifecycle (Start services programmatically)

**You now understand the complete zComm subsystem for communication infrastructure!**

---

## What's Next?

You've mastered **zComm** (client-side communication). Now you have two paths:

### **Path 1: Continue to zBifrost** (WebSocket Server)

Learn **zBifrost** - zComm's WebSocket **server** counterpart for real-time bidirectional Terminal ↔ Web communication:

```python
z = zOS({"zMode": "zBifrost"})
z.walker.run()  # One-line WebSocket server
```

Features: Authentication, caching, CRUD operations, real-time messaging.

**→ Continue to [zBifrost Guide](zBifrost_GUIDE.md)**

### **Path 2: Continue to Layer 1** (Display & Interaction)

Continue the natural layer progression with **Layer 1 subsystems** - zDisplay (rendering), zAuth (security), zDispatch (events):

**→ Continue to [zDisplay Guide](zDisplay_GUIDE.md)**

> **Note:** Both paths work together. zBifrost showcases the subsystems you'll learn in Layer 1. You're not choosing one over the other - zBifrost is there when you need WebSocket orchestration for production apps.

---

**[← Back to zConfig Guide](zConfig_GUIDE.md) | [Home](../README.md) | [Next: zBifrost Guide →](zBifrost_GUIDE.md)**

