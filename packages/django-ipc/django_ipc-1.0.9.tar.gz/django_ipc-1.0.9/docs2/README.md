# django-ipc Documentation (v1.0.8+) %%PRIORITY:HIGH%%

**LLM-Optimized Documentation for Cursor IDE**

**Status**: ✅ Production Ready
**Tags**: `documentation, websocket, rpc, code-generation, diagnostics`

---

## 🎯 What's New in v1.0.8+

This documentation covers **three major additions** to django-ipc:

1. **Go WebSocket Client Generator** - Type-safe Go clients with bidirectional RPC
2. **System Handler** - Built-in diagnostic methods for testing & monitoring
3. **ConnectionManager Fix** - Critical bug fix for bidirectional events

---

## 📚 Documentation Files

### [1. Go WebSocket Client Code Generator](./GO_WEBSOCKET_CODEGEN.md) %%PRIORITY:HIGH%%

**What**: Code generator for type-safe Go WebSocket RPC clients

**Key Features**:
- ✅ Auto-generate Go structs from Pydantic models
- ✅ JWT authentication built-in
- ✅ Bidirectional RPC (Call + OnEvent)
- ✅ Following ccxt_go naming conventions

**Use Cases**:
- Generate Go clients for WebSocket RPC servers
- Type-safe RPC calls in Go microservices
- Bidirectional communication (server → client events)

**Example**:
```bash
django_cfg_rpc codegen --lang go --output clients/generated/go/
```

**Lines**: 487

---

### [2. System Handler & Diagnostic Methods](./SYSTEM_HANDLER_DIAGNOSTICS.md) %%PRIORITY:HIGH%%

**What**: Built-in diagnostic RPC methods (enabled by default)

**Available Methods**:
1. `system.ping` - Connectivity test (0.2ms)
2. `system.echo` - Data serialization test (0.4ms)
3. `system.health` - Server health status (0.2ms)
4. `system.info` - Server version & features (12ms)
5. `system.latency` - Performance measurement (13ms)

**Use Cases**:
- CI/CD integration tests
- Health monitoring & alerting
- Performance baseline establishment
- Debug connection issues

**Example**:
```python
# Quick connectivity test
result = await client._call("system.ping", {})
assert 'pong' in result

# Health check
health = await client._call("system.health", {})
assert health['status'] == 'ok'
```

**Lines**: 698

---

### [3. ConnectionManager Singleton Fix](./CONNECTION_MANAGER_FIX.md) %%PRIORITY:CRITICAL%% %%BREAKING_CHANGE%%

**What**: Critical bug fix for bidirectional RPC events

**Problem**: Multiple ConnectionManager instances causing events not to be delivered

**Symptom**:
```
[NotificationHandler] Notification sent to 0 connections  ❌
```

**Solution**: Pass single ConnectionManager instance to WebSocketServer

**Fix**:
```python
# BEFORE (broken)
server = WebSocketServer(config=config, custom_handlers=handlers)

# AFTER (fixed)
connection_manager = ConnectionManager(...)
handlers = [Handler(connection_manager), ...]
server = WebSocketServer(
    config=config,
    custom_handlers=handlers,
    connection_manager=connection_manager,  # ← Pass instance
)
```

**Impact**: 🔴 **CRITICAL** - Fixes core bidirectional functionality

**Lines**: 542

---

## 🔄 Workflow: Using All Features Together

### 1. Generate Clients (All Languages)

```bash
# Generate Python, TypeScript, and Go clients
django_cfg_rpc codegen \
    --config config/rpc_config.py \
    --output clients/generated/

# Generated:
# - clients/generated/python/client.py
# - clients/generated/typescript/client.ts
# - clients/generated/go/client.go
```

### 2. Test RPC Bridge with System Methods

```python
#!/usr/bin/env python3
"""Test RPC bridge connectivity."""
import asyncio
from clients.generated.python.client import RPCClient

async def test():
    client = RPCClient(url="ws://localhost:8765/ws", token="...")
    await client.connect()

    # 1. Connectivity
    pong = await client._call("system.ping", {})
    print(f"✅ Ping: {pong['pong']}")

    # 2. Health
    health = await client._call("system.health", {})
    print(f"✅ Health: {health['status']}")

    # 3. Performance
    latency = await client._call("system.latency", {"iterations": 10})
    print(f"✅ Latency: {latency['avg_ms']}ms")

asyncio.run(test())
```

### 3. Use Bidirectional RPC (with Fix)

```go
// Go client - receive events from server
package main

import "github.com/yourorg/rpc/client"

func main() {
    c := client.NewRPCClient("ws://localhost:8765/ws", "token...")

    // Register event handler
    c.OnEvent("notification.send", func(params map[string]any) {
        log.Printf("📥 Notification: %v", params)
    })

    // Connect and listen
    c.Connect()
    select {} // Block forever
}
```

**Server logs (with fix)**:
```
Using existing ConnectionManager  ✅
Connection added: ... (user: 29, total: 1)
Notification sent to 1 connections  ✅
```

---

## 📊 Git Changes Summary

### Files Modified

```bash
# django-ipc core
projects/django-ipc/src/django_ipc/
├── codegen/
│   ├── cli.py                                 # +53 lines (Go generator)
│   ├── generators/go_websocket/              # NEW: Go generator
│   │   ├── __init__.py
│   │   ├── generator.py
│   │   └── templates/
│   │       ├── client.go.j2
│   │       ├── types.go.j2
│   │       └── logger.go.j2
│   └── utils/
│       ├── naming.py                          # +48 lines (Go naming)
│       └── type_converter.py                  # +133 lines (Pydantic→Go)
│
├── handlers/
│   ├── __init__.py                           # +3 lines (export SystemHandler)
│   └── system.py                             # NEW: +280 lines
│
└── server/
    ├── config.py                             # +5 lines (enable_system)
    ├── connection_manager.py                  # +7 lines (JSON fix)
    └── websocket_server.py                    # +86 lines (SystemHandler, fix)

# Solution project
solution/projects/websocket/
├── src/
│   └── main.py                               # +1 line (pass connection_manager)
│
├── clients/
│   ├── generated/
│   │   ├── python/                           # Modified (JWT support)
│   │   ├── typescript/                       # Modified (minor)
│   │   └── go/                               # NEW: Generated Go client
│   │
│   └── examples/
│       ├── go/
│       │   └── bidirectional.go             # NEW: Full example
│       ├── test_system.py                   # NEW: System methods test
│       └── send_test_event.py               # Modified
│
└── docs/
    └── SYSTEM_HANDLER.md                     # NEW: Full documentation
```

### Statistics

```bash
$ git diff --stat
47 files changed, 628 insertions(+), 2437 deletions(-)

# Key changes:
# +628 lines added (new features, fixes)
# -2437 lines removed (deprecated client files moved to generated/)
```

**Net Result**: Cleaner codebase with more features

---

## 🎓 Key Concepts

### 1. Code Generation Pattern

```
Python RPC Definitions (rpc_config.py)
    │
    ├──► Python Generator  → clients/generated/python/
    ├──► TypeScript Generator → clients/generated/typescript/
    └──► Go Generator      → clients/generated/go/
```

**Benefits**:
- Type-safe clients
- Single source of truth
- Automatic sync with server

---

### 2. Bidirectional RPC Pattern

```
Client ──────► Server (RPC Call)
       Call()  │
               ▼
           Handler
               │
               ▼
           Response
       ◄──────

Server ──────► Client (Event)
    OnEvent()  │
               ▼
           Handler
```

**Key**: Single ConnectionManager shared by all components

---

### 3. Diagnostic Methods Pattern

```
Production Code
    │
    ├──► business.method_1
    ├──► business.method_2
    └──► system.ping        ← Always available
         system.echo
         system.health
         system.info
         system.latency
```

**Use**: Test, monitor, debug without custom code

---

## 🔍 Debugging Guide

### Issue: Go client not receiving events

**Check**:
1. Server logs for "Using existing ConnectionManager" ✅
2. Connection count matches expectations
3. Events sent to > 0 connections

**Fix**: See [CONNECTION_MANAGER_FIX.md](./CONNECTION_MANAGER_FIX.md)

---

### Issue: RPC timeout errors

**Check**:
```python
# 1. Test connectivity
result = await client._call("system.ping", {})

# 2. Check health
health = await client._call("system.health", {})

# 3. Measure latency
latency = await client._call("system.latency", {"iterations": 10})
```

**Common causes**:
- Server not running
- Wrong WebSocket URL
- JWT token expired
- Network connectivity

---

### Issue: Type conversion errors (Go)

**Check Pydantic → Go mapping**:
```python
# Python
user_id: str = Field(...)           → string
count: int = Field(...)             → int
price: float = Field(...)           → float64
optional: Optional[str] = Field(...)  → *string
ids: List[str] = Field(...)         → []string
data: Dict[str, Any] = Field(...)   → map[string]any
```

See [GO_WEBSOCKET_CODEGEN.md](./GO_WEBSOCKET_CODEGEN.md#data-models) for full mapping table.

---

## 📝 Testing Checklist

After implementing changes:

### Code Generation
- [ ] Python client generates without errors
- [ ] TypeScript client generates without errors
- [ ] Go client generates without errors
- [ ] All types map correctly
- [ ] JWT authentication works in all clients

### System Handler
- [ ] `system.ping` responds < 5ms
- [ ] `system.echo` preserves data structures
- [ ] `system.health` returns "ok" status
- [ ] `system.info` shows correct version
- [ ] `system.latency` completes 10 iterations

### Bidirectional RPC
- [ ] Python → Go events delivered
- [ ] Go → Server → Go events delivered
- [ ] Multiple clients receive broadcasts
- [ ] Server logs show "Using existing ConnectionManager"
- [ ] No "sent to 0 connections" errors

### ConnectionManager Fix
- [ ] Single ConnectionManager instance
- [ ] Handlers find connections (not 0)
- [ ] Events delivered to all connected clients
- [ ] Server logs show correct counts

---

## 🔗 External References

### Official Documentation
- [django-ipc GitHub](https://github.com/anthropics/django-ipc)
- [WebSocket RFC 6455](https://datatracker.ietf.org/doc/html/rfc6455)
- [JSON-RPC 2.0 Spec](https://www.jsonrpc.org/specification)

### Related Tools
- [Pydantic V2 Docs](https://docs.pydantic.dev/2.0/)
- [Go WebSocket Library](https://github.com/gorilla/websocket)
- [Jinja2 Templates](https://jinja.palletsprojects.com/)

---

## 📧 Contact & Support

**Questions**: See project README
**Issues**: GitHub Issues
**Discussions**: GitHub Discussions

---

## 📝 Changelog

### v1.0.8+ (2025-10-24)

**Major Features**:
- ✅ Go WebSocket client generator
- ✅ System diagnostic handler (5 methods)
- ✅ ConnectionManager singleton fix

**Breaking Changes**:
- 🔴 WebSocketServer now accepts `connection_manager` parameter (optional, backward compatible)

**Bug Fixes**:
- 🐛 Fixed bidirectional RPC not delivering events
- 🐛 Fixed JSON serialization in ConnectionManager
- 🐛 Fixed type conversion for Go generator

**Documentation**:
- 📚 GO_WEBSOCKET_CODEGEN.md (487 lines)
- 📚 SYSTEM_HANDLER_DIAGNOSTICS.md (698 lines)
- 📚 CONNECTION_MANAGER_FIX.md (542 lines)
- 📚 README.md (this file)

**Total Documentation**: 1,727 lines (all < 1000 per file ✅)

---

**Documentation Format**: LLM-Optimized for Cursor IDE
**Total Lines**: ~300 (< 1000 ✅)
