# How to Use Distributed Configs in Your MCP Client

**Goal:** Apply fetched config to Claude Desktop or Cursor

**Time:** 15 minutes

**Prerequisites:**
- Fetched and verified a config artifact ([How to Get Config](02-get-first-config.md))
- Verified signature ([How to Verify Signatures](04-verify-signatures.md))
- Backup of current config

---

## Overview

Once you've fetched a validated config, you need to apply it to your MCP client. This guide covers:

1. Applying configs to Claude Desktop
2. Applying configs to Cursor
3. Merging with existing configs
4. Testing and rollback

**Safety First:** Always backup your current config before applying updates!

---

## For Claude Desktop

### Step 1: Locate Claude Desktop Config File

**macOS:**
```bash
open ~/Library/Application\ Support/Claude/
# Edit: claude_desktop_config.json
```

**Windows:**
```powershell
start %APPDATA%\Claude\
# Edit: claude_desktop_config.json
```

**Linux:**
```bash
cd ~/.config/Claude/
# Edit: claude_desktop_config.json
```

---

### Step 2: Backup Current Config

**IMPORTANT:** Always backup before changes!

```bash
# macOS/Linux
cp ~/Library/Application\ Support/Claude/claude_desktop_config.json{,.backup}

# Windows
copy %APPDATA%\Claude\claude_desktop_config.json %APPDATA%\Claude\claude_desktop_config.json.backup
```

---

### Step 3: Fetch Latest Config

Ask Claude:

> Get the prod config for claude-desktop

Save the `payload` field - that's your MCP client config.

Or use Python:

```python
from examples.python_client.client import MCPOrchestrationClient
import json

client = MCPOrchestrationClient()
config = client.get_config("claude-desktop", "prod")

# Extract payload
new_config_payload = config["payload"]

# Save to file
with open("new_config.json", "w") as f:
    json.dump(new_config_payload, f, indent=2)

print("✓ Config saved to new_config.json")
```

---

### Step 4: Merge Configs

**Option A: Replace Entire Config** (Simple, but loses custom servers)

```json
{
  "mcpServers": {
    // Entire content from fetched payload
    "server-1": {...},
    "server-2": {...}
  }
}
```

---

**Option B: Merge with Existing** (Recommended)

```python
#!/usr/bin/env python3
"""
Merge fetched config with existing Claude Desktop config.

Preserves your custom servers while adding orchestrated servers.
"""

import json
from pathlib import Path

def merge_configs(existing_path: Path, new_payload: dict) -> dict:
    """
    Merge new config with existing, preserving custom servers.

    Strategy:
    - Keep all existing servers NOT in new payload
    - Add/update servers from new payload
    - New payload servers override existing
    """

    # Load existing config
    with open(existing_path) as f:
        existing = json.load(f)

    existing_servers = existing.get("mcpServers", {})
    new_servers = new_payload.get("mcpServers", {})

    # Merge: new servers override, custom servers preserved
    merged_servers = {**existing_servers, **new_servers}

    return {
        "mcpServers": merged_servers
    }

# Usage
if __name__ == "__main__":
    existing_path = Path.home() / "Library/Application Support/Claude/claude_desktop_config.json"

    # Load new payload from orchestration
    with open("new_config.json") as f:
        new_payload = json.load(f)

    # Merge
    merged = merge_configs(existing_path, new_payload)

    # Save merged config
    with open(existing_path, "w") as f:
        json.dump(merged, f, indent=2)

    print("✓ Config merged successfully")
    print(f"  Total servers: {len(merged['mcpServers'])}")
```

---

### Step 5: Validate Merged Config

Before restarting Claude Desktop, validate the config:

```bash
# Check JSON is valid
python -m json.tool ~/Library/Application\ Support/Claude/claude_desktop_config.json

# If valid:
# ✓ JSON is valid

# If invalid:
# JSONDecodeError: Expecting ',' delimiter: line 15 column 5
```

---

### Step 6: Restart Claude Desktop

1. **Fully quit** (⌘+Q on macOS, not just close window)
2. **Relaunch** Claude Desktop
3. **Wait 10-15 seconds** for MCP servers to initialize

---

### Step 7: Test New Servers

Ask Claude:

> List all MCP tools

**Expected:** You should see tools from newly added servers!

Test a specific tool:

> Use the [tool-name] tool from [server-name]

---

## For Cursor IDE

### Step 1: Locate Cursor MCP Config

```bash
# Cursor stores MCP config in:
~/.cursor/mcp_config.json
```

---

### Step 2: Fetch and Apply

```python
from examples.python_client.client import MCPOrchestrationClient
import json
from pathlib import Path

client = MCPOrchestrationClient()
config = client.get_config("cursor", "dev")

# Save to Cursor config location
cursor_config_path = Path.home() / ".cursor/mcp_config.json"
cursor_config_path.parent.mkdir(parents=True, exist_ok=True)

with open(cursor_config_path, "w") as f:
    json.dump(config["payload"], f, indent=2)

print("✓ Cursor config updated")
```

---

### Step 3: Reload Cursor

Cursor automatically detects config changes. If not:

1. Open Cursor Settings
2. Navigate to MCP Servers
3. Click "Reload Configuration"

---

## Automated Config Sync

### Sync Script

Create `scripts/sync_config.sh`:

```bash
#!/bin/bash
# Fetch latest config and apply to Claude Desktop
# Usage: ./scripts/sync_config.sh [client-id] [profile]

set -euo pipefail

CLIENT_ID="${1:-claude-desktop}"
PROFILE="${2:-default}"

echo "=== MCP Config Sync ==="
echo "Client: $CLIENT_ID"
echo "Profile: $PROFILE"
echo

# Fetch config using Python client
echo "[1/4] Fetching latest config..."
CONFIG=$(python3 << EOF
from examples.python_client.client import MCPOrchestrationClient
import json

client = MCPOrchestrationClient()
config = client.get_config("$CLIENT_ID", "$PROFILE")

# Verify signature
from examples.python_client.verify import verify_config
if not verify_config(config, "keys/verification_key.pem"):
    print("ERROR: Signature verification failed!", file=sys.stderr)
    sys.exit(1)

print(json.dumps(config["payload"], indent=2))
EOF
)

if [ $? -ne 0 ]; then
    echo "✗ Config fetch failed"
    exit 1
fi

echo "✓ Config fetched and verified"

# Backup existing config
echo "[2/4] Backing up existing config..."
CONFIG_PATH=~/Library/Application\ Support/Claude/claude_desktop_config.json
cp "$CONFIG_PATH"{,.backup-$(date +%Y%m%d-%H%M%S)}
echo "✓ Backup created"

# Write new config
echo "[3/4] Applying new config..."
echo "$CONFIG" > "$CONFIG_PATH"
echo "✓ Config updated"

# Validate JSON
echo "[4/4] Validating config..."
python3 -m json.tool "$CONFIG_PATH" > /dev/null
echo "✓ Config is valid JSON"

echo
echo "=== Config Sync Complete ==="
echo "Next: Restart Claude Desktop to apply changes"
```

---

### Make Executable

```bash
chmod +x scripts/sync_config.sh

# Run sync
./scripts/sync_config.sh claude-desktop prod
```

---

### Schedule Automatic Sync

```bash
# Add to crontab (sync daily at 8am)
crontab -e

# Add this line:
0 8 * * * cd /path/to/mcp-orchestration && ./scripts/sync_config.sh claude-desktop prod
```

---

## Success Criteria

- [ ] Config applies without JSON errors
- [ ] MCP servers from config are accessible in client
- [ ] Tools from new servers work correctly
- [ ] Custom servers preserved (if using merge)
- [ ] Can rollback to backup if needed
- [ ] Restart completes in <30 seconds
- [ ] All MCP tools accessible after restart

---

## Rollback Procedure

If something breaks after applying config:

### Quick Rollback

```bash
# Restore most recent backup
cp ~/Library/Application\ Support/Claude/claude_desktop_config.json{.backup,}

# Or specific backup
cp ~/Library/Application\ Support/Claude/claude_desktop_config.json.backup-20251023-090000 \
   ~/Library/Application\ Support/Claude/claude_desktop_config.json

# Restart Claude Desktop
killall "Claude Desktop"
open -a "Claude Desktop"
```

---

### Verify Rollback

Ask Claude:

> List MCP tools

Confirm you see expected tools (old config).

---

## Troubleshooting

### Claude Desktop won't start

**Symptom:** App crashes on launch after config update

**Cause:** Invalid JSON or malformed config

**Solution:**

```bash
# 1. Restore backup
cp ~/Library/Application\ Support/Claude/claude_desktop_config.json{.backup,}

# 2. Validate original config
python -m json.tool ~/Library/Application\ Support/Claude/claude_desktop_config.json.backup

# 3. Fix issues and reapply
```

---

### MCP servers not loading

**Symptom:** Claude starts but no MCP tools available

**Possible Causes:**
1. Server command path incorrect
2. Missing environment variables
3. Permissions issue
4. Server crashed during init

**Solution:**

Check Claude Desktop logs:

**macOS:**
```bash
tail -f ~/Library/Logs/Claude/mcp-*.log
```

Look for error messages like:
```
Error: Command not found: /wrong/path/to/server
Error: Permission denied
Error: Server crashed with exit code 1
```

Fix command paths in config:

```json
{
  "mcpServers": {
    "my-server": {
      "command": "/usr/local/bin/my-server",  // Verify this path exists
      "args": [],
      "env": {}
    }
  }
}
```

---

### Servers conflict

**Symptom:** Two servers with same name

**Cause:** Merge didn't handle name collision

**Solution:**

```python
# Rename conflicting server
merged_servers["my-server-orchestrated"] = new_servers["my-server"]
merged_servers["my-server-custom"] = existing_servers["my-server"]
```

Or choose one:

```python
# Keep orchestrated version (recommended)
merged_servers = {**existing_servers, **new_servers}  # new wins

# Keep custom version
merged_servers = {**new_servers, **existing_servers}  # existing wins
```

---

### Slow startup

**Symptom:** Claude Desktop takes >30 seconds to start

**Cause:** Too many MCP servers (>10)

**Solution:**

Disable unused servers:

```json
{
  "mcpServers": {
    "active-server-1": {...},
    "active-server-2": {...}
    // Comment out or remove unused servers
    // "unused-server": {...}
  }
}
```

Or use profiles to separate dev/prod servers.

---

## Best Practices

### 1. Always Backup

```bash
# Before any change
cp config.json{,.backup-$(date +%Y%m%d)}
```

---

### 2. Test in Dev Profile First

```bash
# 1. Apply to dev profile
./scripts/sync_config.sh claude-desktop dev

# 2. Test thoroughly
# 3. Then apply to prod
./scripts/sync_config.sh claude-desktop prod
```

---

### 3. Version Control Your Config

```bash
# Track Claude Desktop config in git
cd ~/Library/Application\ Support/Claude/
git init
git add claude_desktop_config.json
git commit -m "Baseline config"

# After each update
git diff  # Review changes
git add claude_desktop_config.json
git commit -m "Applied config from mcp-orchestration (v1.2.3)"
```

---

### 4. Document Custom Servers

Keep a `CUSTOM_SERVERS.md`:

```markdown
# Custom MCP Servers

## my-personal-server
- Purpose: Local development tool
- Path: /Users/me/projects/my-server
- DO NOT REMOVE when syncing orchestrated configs

## experimental-server
- Purpose: Testing new MCP features
- Temporary - can remove after testing
```

---

### 5. Monitor for Issues

```bash
# Watch Claude logs during first use
tail -f ~/Library/Logs/Claude/mcp-*.log

# Check for:
# - Server start failures
# - Tool call errors
# - Timeout warnings
```

---

## Advanced: Config Diff

Before applying, see what changed:

```python
import json
import difflib

# Load existing and new
with open("existing_config.json") as f:
    existing = json.load(f)

with open("new_config.json") as f:
    new = json.load(f)

# Pretty print for diff
existing_str = json.dumps(existing, indent=2, sort_keys=True)
new_str = json.dumps(new, indent=2, sort_keys=True)

# Diff
diff = difflib.unified_diff(
    existing_str.splitlines(),
    new_str.splitlines(),
    fromfile="existing",
    tofile="new",
    lineterm=""
)

print("\n".join(diff))
```

**Output:**

```diff
--- existing
+++ new
@@ -5,7 +5,10 @@
       "command": "/old/path/to/server",
       "args": [],
-      "env": {}
+      "env": {
+        "NEW_VAR": "value"
+      }
     }
+    "new-server": {...}
   }
 }
```

---

## What You Learned

- How to apply configs to Claude Desktop and Cursor
- Merge strategies (replace vs merge)
- Backup and rollback procedures
- Automated config sync scripts
- Troubleshooting config application issues
- Best practices for config management

---

## Next Steps

- **[Automate Config Updates](06-automate-updates.md)** - Full automation (Wave 2)
- **[Monitor MCP Server Health](07-monitor-health.md)** - Track server status
- **[Troubleshooting MCP Configs](../troubleshooting/mcp-configs.md)** - Common issues

---

**Status:** Wave 1 E2E Test 5
**Last Updated:** 2025-10-23
