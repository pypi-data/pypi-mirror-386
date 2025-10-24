# How to Get Your First MCP Configuration

**Goal:** Retrieve a validated, signed configuration for Claude Desktop

**Time:** 5 minutes

**Prerequisites:**
- mcp-orchestration MCP server configured
- Completed [How to Discover Clients](01-discover-clients.md)

---

## Step 1: Choose Client and Profile

First, see what profiles are available for your client.

Ask Claude:

> What profiles are available for claude-desktop?

**Expected Response:**

```
The claude-desktop client has these profiles available:

- default: Standard configuration for general use
- dev: Development configuration with verbose logging
- prod: Production configuration optimized for performance
```

---

## Step 2: Fetch Configuration

Now fetch the configuration for your chosen profile.

Ask Claude:

> Get the default config for claude-desktop

**Expected Response:**

Claude should call `get_config(client_id="claude-desktop", profile="default")` and return:

```json
{
  "artifact_id": "a7f3b2c1d4e5f6789012345678901234567890abcdef1234567890abcdef1234",
  "client_id": "claude-desktop",
  "profile": "default",
  "payload": {
    "mcpServers": {
      "example-server": {
        "command": "mcp-server",
        "args": [],
        "env": {
          "MCP_SERVER_LOG_LEVEL": "INFO"
        }
      }
    }
  },
  "schema_ref": "claude-desktop-config-v1",
  "version": "1.0.0",
  "issued_at": "2025-10-23T17:00:00Z",
  "signature": {
    "algorithm": "Ed25519",
    "value": "YmFzZTY0c2lnbmF0dXJl...",
    "key_id": "default"
  },
  "provenance": {
    "publisher_id": "mcp-orchestration",
    "tooling_version": "0.1.0",
    "generated_at": "2025-10-23T17:00:00Z",
    "generator": "chora-compose+jinja2"
  }
}
```

---

## Step 3: Understanding the Response

### Core Fields

| Field | Description | Example |
|-------|-------------|---------|
| `artifact_id` | SHA-256 hash of payload (content-addressable) | "a7f3b2c1..." (64 chars) |
| `client_id` | Target MCP client | "claude-desktop" |
| `profile` | Configuration profile | "default" |
| `payload` | **Actual MCP client config** | {"mcpServers": {...}} |
| `version` | Artifact version | "1.0.0" |
| `issued_at` | When config was generated | ISO 8601 timestamp |

### Signature Fields

| Field | Description | Security Level |
|-------|-------------|----------------|
| `algorithm` | Signature algorithm | Ed25519 (⭐⭐⭐ High) |
| `value` | Base64-encoded signature | Verifies payload integrity |
| `key_id` | Signing key identifier | "default" |

### Provenance Fields

Shows where the config came from:

- `publisher_id`: Who generated it ("mcp-orchestration")
- `tooling_version`: Generator version ("0.1.0")
- `generated_at`: Generation timestamp
- `generator`: Tool used ("chora-compose+jinja2")

---

## Step 4: Verify Signature (Optional but Recommended)

The artifact includes a cryptographic signature. To verify:

```python
# Save config to config.json
import json

config = {
    # ... (paste the config from Step 2)
}

with open("config.json", "w") as f:
    json.dump(config, f, indent=2)

# Run verification
python examples/python_client/verify.py config.json keys/verification_key.pem
```

**Expected Output:**

```
✓ Signature verification PASSED

Config Details:
  Client: claude-desktop
  Profile: default
  Artifact ID: a7f3b2c1...
  Issued: 2025-10-23T17:00:00Z

Signature:
  Algorithm: Ed25519
  Key ID: default

The config payload has NOT been tampered with.
It was signed by: mcp-orchestration
```

See [How to Verify Signatures](04-verify-signatures.md) for detailed instructions.

---

## Step 5: Using the Payload

The `payload` field contains the actual MCP client configuration. For Claude Desktop:

```json
{
  "mcpServers": {
    "example-server": {
      "command": "mcp-server",
      "args": [],
      "env": {
        "MCP_SERVER_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

This is what you'll add to `claude_desktop_config.json`. See [How to Use Configs](05-use-config.md) for instructions.

---

## Using Python Client

For programmatic access:

```python
from examples.python_client.client import MCPOrchestrationClient
import json

# Initialize client
client = MCPOrchestrationClient()

# Fetch config
config = client.get_config("claude-desktop", "default")

# Print details
print(f"Artifact ID: {config['artifact_id']}")
print(f"Version: {config['version']}")
print(f"Issued: {config['issued_at']}")
print()

# Save payload
with open("claude_desktop_config.json", "w") as f:
    json.dump(config["payload"], f, indent=2)

print("✓ Config saved to claude_desktop_config.json")
```

---

## Success Criteria (AC-1)

This is **Acceptance Criteria 1** from the Wave 1 specification:

- [ ] Config artifact returned for at least one client + profile
- [ ] `artifact_id` is 64-character hex string (SHA-256)
- [ ] `payload` contains valid MCP client configuration
- [ ] `signature.algorithm` is "Ed25519"
- [ ] `signature.value` is non-empty base64 string
- [ ] Response time <300ms p95 (NFR-3 requirement)
- [ ] Config validates against schema (FR-6)
- [ ] Signature can be verified (AC-4, FR-4)

---

## Troubleshooting

### Unknown client or profile

**Symptom:**
```
Error: Unknown client 'xyz' or profile 'abc'
```

**Solution:**
- Verify client exists: Run `list_clients` (How-To 1)
- Verify profile exists: Run `list_profiles(client_id)`
- Check spelling (case-sensitive)

---

### Signature verification fails

**Symptom:**
```
✗ Signature verification FAILED
```

**Possible Causes:**
1. Payload was tampered with
2. Wrong verification key
3. Signature was corrupted during transmission

**Solution:**
1. Fetch fresh config from server
2. Verify you're using correct verification key
3. Check network connection (no proxies modifying data)
4. Contact server admin if problem persists

---

### Empty payload

**Symptom:**
```json
{"payload": {}}
```

**Possible Causes:**
1. Template not found for client/profile combination
2. chora-compose generator failed
3. Config generation script has bugs

**Solution:**

Check server logs:

```bash
tail -f var/telemetry/events.jsonl | grep generate_config

# Look for error events
```

Report to admin if template is missing.

---

### Slow response (>300ms)

**Symptom:** Takes a long time to generate config

**Performance Requirement:** NFR-3 states config retrieval should be <300ms p95

**Possible Causes:**
1. First request (template compilation overhead)
2. Complex template with many includes
3. Network latency (remote server)

**Solution:**

```bash
# Check performance metrics
cat var/telemetry/events.jsonl | \
  grep get_config | \
  jq '.fields.duration_ms' | \
  sort -n | \
  tail -5

# If consistently >300ms, investigate:
# - Template complexity
# - Storage I/O (SSD vs HDD)
# - CPU usage during generation
```

---

## What You Learned

- How to fetch configs with `get_config` (FR-4)
- Config artifacts are **content-addressable** (artifact_id = SHA-256 hash)
- All configs are **cryptographically signed** with Ed25519
- Configs are generated from templates using **chora-compose**
- Provenance tracks who generated the config and when
- Performance expectation: <300ms p95 (NFR-3)

---

## Content-Addressable Storage

The `artifact_id` is computed as:

```python
import hashlib
import json

payload = {...}  # Your config payload
payload_str = json.dumps(payload, sort_keys=True)
artifact_id = hashlib.sha256(payload_str.encode()).hexdigest()

# Result: "a7f3b2c1..." (64 hex chars)
```

**Benefits:**
- **Immutable:** Same payload always produces same ID
- **Tamper-evident:** Any change produces different ID
- **Deduplication:** Identical configs share same artifact
- **Diff-friendly:** Compare IDs to detect changes

---

## Next Steps

- **[How to Check for Config Updates](03-check-updates.md)** - Use `diff_config` to check for new versions
- **[How to Verify Signatures](04-verify-signatures.md)** - Cryptographically verify config integrity
- **[How to Use Configs in Your MCP Client](05-use-config.md)** - Apply config to Claude Desktop or Cursor
- **[Understanding Config Provenance](../explanation/config-provenance.md)** - Learn about config generation metadata

---

**Status:** Wave 1 E2E Test 2
**Acceptance Criteria:** AC-1, FR-4, NFR-3
**Last Updated:** 2025-10-23
