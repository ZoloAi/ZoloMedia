# BifrostClient Hooks Guide

## Overview

BifrostClient provides a **primitive hooks system** that allows you to customize behavior without modifying the core library. Hooks are callbacks that fire at specific points in the WebSocket lifecycle.

## Hook Philosophy

**Primitive & Composable**: Hooks are intentionally simple building blocks. You can compose complex behavior by combining multiple hooks.

**Non-Invasive**: Hooks don't modify internal state. They're observers that let you react to events.

**Optional**: All hooks are optional. BifrostClient works without any hooks defined.

---

## Available Hooks

### Connection Lifecycle Hooks

#### `onConnecting(url: string)`
Called when a connection attempt starts.

```javascript
onConnecting: (url) => {
  console.log('Connecting to:', url);
  showLoadingSpinner();
}
```

#### `onConnected(info: Object)`
Called when WebSocket connection is established.

**Parameters:**
- `info.url` - WebSocket URL
- `info.protocol` - WebSocket protocol
- `info.readyState` - Connection state

```javascript
onConnected: (info) => {
  console.log('✅ Connected:', info);
  hideLoadingSpinner();
  showSuccessMessage('Connected to server');
}
```

#### `onDisconnected(reason: Object)`
Called when WebSocket connection is lost.

**Parameters:**
- `reason.code` - Close code
- `reason.reason` - Close reason string
- `reason.wasClean` - Whether close was clean

```javascript
onDisconnected: (reason) => {
  console.log('Disconnected:', reason);
  if (!reason.wasClean) {
    showErrorMessage('Connection lost unexpectedly');
  }
}
```

---

### Message Hooks

#### `onMessage(message: Object)`
Called for **every** message received (before any processing).

```javascript
onMessage: (msg) => {
  // Log all messages
  console.log('📨 Message:', msg);
  
  // Track metrics
  messageCounter++;
  
  // Custom routing
  if (msg.type === 'analytics') {
    sendToAnalytics(msg.data);
  }
}
```

#### `onBroadcast(message: Object)`
Called for server-initiated broadcast messages (not responses to requests).

```javascript
onBroadcast: (msg) => {
  // Handle real-time updates
  if (msg.type === 'user_joined') {
    updateUserList(msg.user);
  }
  
  if (msg.type === 'notification') {
    showNotification(msg.text);
  }
}
```

---

### zDisplay Hooks

#### `onDisplay(data: any)`
Called when server sends display-related events (tables, menus, etc.).

```javascript
onDisplay: (data) => {
  if (Array.isArray(data)) {
    // Custom table rendering
    renderCustomTable(data);
  } else if (data.type === 'menu') {
    // Custom menu rendering
    renderCustomMenu(data.items);
  }
}
```

#### `onInput(request: Object)`
Called when server requests input from user.

**Parameters:**
- `request.requestId` - ID to send back with response
- `request.prompt` - Prompt text
- `request.type` - Input type (text, number, etc.)

```javascript
onInput: (request) => {
  // Show custom input dialog
  const value = await showCustomInputDialog(request.prompt, request.type);
  
  // Send response back
  client.sendInputResponse(request.requestId, value);
}
```

---

### Error Hook

#### `onError(error: Error)`
Called when an error occurs (connection errors, parsing errors, etc.).

```javascript
onError: (error) => {
  console.error('❌ Error:', error);
  
  // Custom error handling
  if (error.message.includes('timeout')) {
    showRetryDialog();
  } else if (error.message.includes('authentication')) {
    redirectToLogin();
  } else {
    showErrorNotification(error.message);
  }
}
```

---

## Usage Patterns

### Pattern 1: Disable autoTheme & Use Custom Rendering

```javascript
const client = new BifrostClient('ws://localhost:8765', {
  autoTheme: false,  // ⚠️ No automatic zTheme loading
  hooks: {
    onConnected: () => {
      // Load your own CSS framework
      loadBootstrap();
    },
    onDisplay: (data) => {
      // Use your own rendering
      if (Array.isArray(data)) {
        $('#myTable').DataTable({ data });
      }
    }
  }
});
```

### Pattern 2: Analytics & Logging

```javascript
const client = new BifrostClient('ws://localhost:8765', {
  hooks: {
    onMessage: (msg) => {
      // Log to analytics
      analytics.track('bifrost_message', {
        type: msg.type,
        timestamp: Date.now()
      });
    },
    onError: (error) => {
      // Report to error tracking
      Sentry.captureException(error);
    }
  }
});
```

### Pattern 3: Real-Time Collaboration

```javascript
const client = new BifrostClient('ws://localhost:8765', {
  hooks: {
    onBroadcast: (msg) => {
      // Handle real-time updates
      switch (msg.type) {
        case 'user_typing':
          showTypingIndicator(msg.user);
          break;
        case 'document_updated':
          refreshDocument(msg.documentId);
          break;
        case 'cursor_moved':
          updateRemoteCursor(msg.userId, msg.position);
          break;
      }
    }
  }
});
```

### Pattern 4: Connection Status UI

```javascript
const client = new BifrostClient('ws://localhost:8765', {
  hooks: {
    onConnecting: () => {
      statusEl.className = 'status connecting';
      statusEl.textContent = 'Connecting...';
    },
    onConnected: () => {
      statusEl.className = 'status connected';
      statusEl.textContent = 'Connected';
    },
    onDisconnected: (reason) => {
      statusEl.className = 'status disconnected';
      statusEl.textContent = reason.wasClean ? 'Disconnected' : 'Connection Lost';
    }
  }
});
```

### Pattern 5: Message Transformation

```javascript
const client = new BifrostClient('ws://localhost:8765', {
  hooks: {
    onMessage: (msg) => {
      // Transform dates from strings to Date objects
      if (msg.result && Array.isArray(msg.result)) {
        msg.result.forEach(item => {
          if (item.created_at) {
            item.created_at = new Date(item.created_at);
          }
        });
      }
    }
  }
});
```

### Pattern 6: Custom Authentication Flow

```javascript
const client = new BifrostClient('ws://localhost:8765', {
  token: getAuthToken(),
  hooks: {
    onError: async (error) => {
      if (error.message.includes('authentication')) {
        // Try to refresh token
        const newToken = await refreshAuthToken();
        client.options.token = newToken;
        
        // Reconnect with new token
        await client.connect();
      }
    }
  }
});
```

---

## Dynamic Hook Registration

You can register hooks at runtime:

```javascript
const client = new BifrostClient('ws://localhost:8765');

// Register hook later
client.registerHook('onMessage', (msg) => {
  console.log('New hook:', msg);
});

// Unregister hook
client.unregisterHook('onMessage');

// List all hooks
console.log('Active hooks:', client.listHooks());
```

---

## Complete Example: Custom Bifrost Events Without zTheme

```javascript
// Initialize without zTheme
const client = new BifrostClient('ws://localhost:8765', {
  autoTheme: false,  // 🚫 No automatic CSS loading
  debug: true,
  hooks: {
    // Connection status
    onConnected: () => {
      document.getElementById('status').style.color = 'green';
      document.getElementById('status').textContent = 'Online';
    },
    
    onDisconnected: () => {
      document.getElementById('status').style.color = 'red';
      document.getElementById('status').textContent = 'Offline';
    },
    
    // Custom message handling
    onMessage: (msg) => {
      // Add to message log
      const log = document.getElementById('messageLog');
      log.innerHTML += `<div>${JSON.stringify(msg)}</div>`;
    },
    
    // Custom display rendering (no zTheme)
    onDisplay: (data) => {
      const container = document.getElementById('content');
      
      if (Array.isArray(data)) {
        // Render with Material-UI table (example)
        container.innerHTML = `
          <table class="mui-table">
            <thead><tr>${Object.keys(data[0]).map(k => `<th>${k}</th>`).join('')}</tr></thead>
            <tbody>
              ${data.map(row => `
                <tr>${Object.values(row).map(v => `<td>${v}</td>`).join('')}</tr>
              `).join('')}
            </tbody>
          </table>
        `;
      }
    },
    
    // Custom error handling
    onError: (error) => {
      // Use your own notification system
      toast.error(error.message, {
        position: 'top-right',
        autoClose: 5000
      });
    },
    
    // Handle broadcasts (real-time updates)
    onBroadcast: (msg) => {
      if (msg.type === 'data_updated') {
        // Refresh your UI
        refreshDataTable();
      }
    }
  }
});

// Connect
await client.connect();

// Use CRUD operations (works with or without zTheme)
const users = await client.read('users');
```

---

## Best Practices

1. **Keep Hooks Simple**: Each hook should do one thing well
2. **Don't Block**: Hooks should be fast. Use async operations carefully
3. **Handle Errors**: Wrap hook logic in try-catch if needed
4. **Use autoTheme: false**: For complete control over styling
5. **Compose Behavior**: Combine multiple hooks for complex logic
6. **Log Strategically**: Use `onMessage` for debugging, remove in production

---

## Hook Execution Order

When a message arrives:

1. `onMessage` (always first)
2. Check if response → resolve promise
3. Check if display event → `onDisplay`
4. Check if input request → `onInput`
5. Otherwise → `onBroadcast`

---

## FAQ

**Q: Can I modify the message in a hook?**  
A: Yes in `onMessage`, but it won't affect internal processing. Hooks are observers.

**Q: Can I use async functions as hooks?**  
A: Yes, but be aware they won't block message processing.

**Q: What if I don't want zTheme at all?**  
A: Set `autoTheme: false` and use custom rendering in hooks.

**Q: Can I have multiple handlers for the same hook?**  
A: Currently no. Last registered hook wins. Compose logic within one function.

**Q: Do hooks affect performance?**  
A: Minimal impact. Hooks are simple function calls.

---

## See Also

- [zComm Guide](../../../Documentation/zComm_GUIDE.md)
- [User Manager v2 Demo](../../../Demos/User Manager/index_v2.html)
- [Release Notes](../../../Documentation/Release/RELEASE_1.5.4.md)

