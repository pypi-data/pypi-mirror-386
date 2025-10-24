# How to Discover Available MCP Clients

**Goal:** Find out which MCP clients mcp-orchestration supports

**Time:** 2 minutes

**Prerequisites:** mcp-orchestration MCP server configured in Claude Desktop

---

## Using Claude Desktop

Open Claude Desktop and ask:

> Show me all supported MCP clients

**Expected Response:**

Claude should call `list_clients` and return something like:

```
Here are the supported MCP clients:

1. **Claude Desktop** (claude-desktop)
   - Profiles: default, dev, prod
   - Capabilities: env_vars, stdio_transport
   - Schema: claude-desktop-config-v1

2. **Cursor** (cursor)
   - Profiles: default, dev
   - Capabilities: env_vars, stdio_transport
   - Schema: cursor-config-v1

3. **Example Client** (example-client)
   - Profiles: default
   - Capabilities: basic_mcp
   - Schema: generic-mcp-v1
```

---

## Alternative Prompts

Try these variations:

- "List all MCP client families"
- "What clients can I get configurations for?"
- "Show available client types"

---

## Using Python Client

If you prefer programmatic access:

```python
from examples.python_client.client import MCPOrchestrationClient

client = MCPOrchestrationClient()
clients = client.list_clients()

for c in clients:
    print(f"{c['name']} ({c['client_id']})")
    print(f"  Profiles: {', '.join(c['profiles'])}")
    print(f"  Capabilities: {', '.join(c['capabilities'])}")
    print()
```

**Expected Output:**

```
Claude Desktop (claude-desktop)
  Profiles: default, dev, prod
  Capabilities: env_vars, stdio_transport

Cursor (cursor)
  Profiles: default, dev
  Capabilities: env_vars, stdio_transport

Example Client (example-client)
  Profiles: default
  Capabilities: basic_mcp
```

---

## Success Criteria

- [ ] Command returns 3+ clients
- [ ] Each client has at least 1 profile
- [ ] Each client has a `client_id` field
- [ ] Each client has a `schemas` array
- [ ] Response completes in <5 seconds
- [ ] Response time <200ms p95 (performance requirement NFR-4)

---

## Understanding the Response

### Client Fields

| Field | Description | Example |
|-------|-------------|---------|
| `client_id` | Unique identifier | "claude-desktop" |
| `name` | Human-readable name | "Claude Desktop" |
| `profiles` | Available config profiles | ["default", "dev", "prod"] |
| `capabilities` | Client features | ["env_vars", "stdio_transport"] |
| `schemas` | Supported config schemas | [{"schema_ref": "claude-desktop-config-v1", ...}] |

### Profile Types

- **default**: Standard configuration for general use
- **dev**: Development configuration (verbose logging, debug tools)
- **prod**: Production configuration (optimized, secure)

---

## Troubleshooting

### No clients returned

**Symptom:** `list_clients` returns empty array `[]`

**Possible Causes:**
1. No client registry files in `data/clients/` directory
2. Client JSON files are malformed
3. MCP server not initialized properly

**Solution:**

```bash
# Check client registry exists
ls -la data/clients/

# Expected: claude-desktop.json, cursor.json, example-client.json
# If missing, regenerate client registry:
python scripts/init_client_registry.py
```

---

### Slow response (>5 seconds)

**Symptom:** Takes a long time to list clients

**Possible Causes:**
1. Large number of client files
2. Network latency (if using remote server)
3. File I/O issues

**Solution:**

```bash
# Check telemetry for performance issues
tail -f var/telemetry/events.jsonl | grep list_clients

# Look for slow_query events
```

---

### MCP server not running

**Symptom:** Claude says "Tool not available" or similar

**Possible Causes:**
1. MCP server not configured in Claude Desktop config
2. Server crashed or failed to start
3. Configuration path incorrect

**Solution:**

Check Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "mcp-orchestration": {
      "command": "/path/to/.venv/bin/python",
      "args": ["-m", "mcp_orchestration.mcp.server"],
      "cwd": "/absolute/path/to/mcp-orchestration",
      "env": {}
    }
  }
}
```

Restart Claude Desktop after configuration changes.

---

## What You Learned

- How to discover supported MCP clients using `list_clients`
- Client registry structure (client_id, profiles, capabilities)
- How to interpret profile types (default, dev, prod)
- Performance expectations (FR-1, NFR-4)

---

## Next Steps

- **[How to Get Your First Config](02-get-first-config.md)** - Fetch a configuration artifact
- **[How to List Profiles for a Client](02a-list-profiles.md)** - Get detailed profile information
- **[Understanding Client Capabilities](../explanation/client-capabilities.md)** - Learn what capabilities mean

---

**Status:** Wave 1 E2E Test 1
**Acceptance Criteria:** FR-1 (List supported client families)
**Last Updated:** 2025-10-23
