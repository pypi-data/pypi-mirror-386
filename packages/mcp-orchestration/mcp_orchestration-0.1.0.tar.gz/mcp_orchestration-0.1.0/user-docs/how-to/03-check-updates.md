# How to Check for Configuration Updates

**Goal:** Determine if your local config is outdated

**Time:** 3 minutes

**Prerequisites:**
- You have fetched a config previously (see [How to Get Your First Config](02-get-first-config.md))
- You know your current `artifact_id`

---

## Why Check for Updates?

Configuration updates happen when:
- New MCP servers are added to the registry
- Server configurations change (new env vars, updated commands)
- Security patches require config changes
- Profile-specific settings are updated

**Best Practice:** Check for updates daily or before deploying changes.

---

## Using Claude Desktop

### Step 1: Get Your Current Artifact ID

If you don't know your current config's artifact ID:

```python
# Read your Claude Desktop config
import json
from pathlib import Path

config_path = Path.home() / "Library/Application Support/Claude/claude_desktop_config.json"
with open(config_path) as f:
    current_config = json.load(f)

# Compute artifact ID
import hashlib
config_str = json.dumps(current_config, sort_keys=True)
current_artifact_id = hashlib.sha256(config_str.encode()).hexdigest()

print(f"Current artifact ID: {current_artifact_id}")
```

---

### Step 2: Check for Updates

Ask Claude:

> Check if my claude-desktop config is up to date. My current artifact ID is a7f3b2c1d4e5f6789012345678901234567890abcdef1234567890abcdef1234

**Expected Response (Up-to-Date):**

```
Your configuration is up-to-date! ✓

Status: up-to-date
Current artifact ID: a7f3b2c1d4e5f6...
Latest artifact ID:  a7f3b2c1d4e5f6...

No updates needed. Your config matches the latest version.
```

**Expected Response (Outdated):**

```
⚠️ Your configuration is outdated. A new version is available.

Status: outdated
Current artifact ID: a7f3b2c1d4e5f6...
Latest artifact ID:  f6e5d4c3b2a198...

What changed:
- Updated example-server command path
- Added new environment variable: MCP_SERVER_TIMEOUT
- Security patch: disabled experimental-tool

Recommendation: Fetch the latest config and review changes before applying.
```

---

## Using Python Client

```python
from examples.python_client.client import MCPOrchestrationClient

client = MCPOrchestrationClient()

# Your current artifact ID
current_id = "a7f3b2c1d4e5f6789012345678901234567890abcdef1234567890abcdef1234"

# Check for updates
result = client.diff_config(
    client_id="claude-desktop",
    profile="default",
    current_artifact_id=current_id
)

if result["status"] == "outdated":
    print("⚠️  New config available!")
    print(f"   Current: {result['current_artifact_id'][:12]}...")
    print(f"   Latest:  {result['latest_artifact_id'][:12]}...")

    if result.get("changelog"):
        print(f"\nWhat changed:\n{result['changelog']}")

    # Fetch latest config
    new_config = client.get_config("claude-desktop", "default")

    # Compare and apply...
    print("\nFetching latest config...")
else:
    print("✓ Config is up-to-date")
```

---

## Success Criteria (AC-2)

This is **Acceptance Criteria 2** from the Wave 1 specification:

- [ ] `diff_config` correctly reports "up-to-date" when artifact IDs match
- [ ] Reports "outdated" when artifact IDs differ
- [ ] Returns both `current_artifact_id` and `latest_artifact_id`
- [ ] Response time <200ms p95 (NFR-4)
- [ ] Includes `changelog` when outdated (if available)
- [ ] Idempotent: Same inputs always produce same result (FR-9)

---

## Automated Update Check

### Daily Check Script

Create `scripts/check_config_updates.py`:

```python
#!/usr/bin/env python3
"""
Check for config updates daily.

Usage:
    python scripts/check_config_updates.py

Exit codes:
    0 - Config up-to-date
    1 - Config outdated
    2 - Error
"""

import sys
import json
from pathlib import Path
from examples.python_client.client import MCPOrchestrationClient

def main():
    # Load current config
    config_path = Path.home() / "Library/Application Support/Claude/claude_desktop_config.json"

    if not config_path.exists():
        print("❌ Claude Desktop config not found", file=sys.stderr)
        return 2

    with open(config_path) as f:
        current_config = json.load(f)

    # Compute current artifact ID
    import hashlib
    config_str = json.dumps(current_config, sort_keys=True)
    current_id = hashlib.sha256(config_str.encode()).hexdigest()

    # Check for updates
    client = MCPOrchestrationClient()

    try:
        result = client.diff_config(
            client_id="claude-desktop",
            profile="default",  # or read from config
            current_artifact_id=current_id
        )
    except Exception as e:
        print(f"❌ Error checking for updates: {e}", file=sys.stderr)
        return 2

    if result["status"] == "outdated":
        print("⚠️  Config update available")
        print(f"   Latest: {result['latest_artifact_id'][:12]}...")
        if result.get("changelog"):
            print(f"\n{result['changelog']}")
        return 1
    else:
        print("✓ Config up-to-date")
        return 0

if __name__ == "__main__":
    sys.exit(main())
```

---

### Add to Crontab

```bash
# Make executable
chmod +x scripts/check_config_updates.py

# Check daily at 9am
crontab -e

# Add this line:
0 9 * * * cd /path/to/mcp-orchestration && python scripts/check_config_updates.py
```

---

### Email Notifications

Modify script to send email when updates are available:

```python
def send_notification(result):
    """Send email notification about config update."""
    import smtplib
    from email.message import EmailMessage

    msg = EmailMessage()
    msg.set_content(f"""
    MCP Config Update Available

    Status: {result['status']}
    Latest ID: {result['latest_artifact_id']}

    Changelog:
    {result.get('changelog', 'No changelog available')}

    Run 'get_config' to fetch the latest version.
    """)

    msg['Subject'] = 'MCP Config Update Available'
    msg['From'] = 'mcp-orchestration@example.com'
    msg['To'] = 'you@example.com'

    # Send email (configure SMTP settings)
    with smtplib.SMTP('localhost') as s:
        s.send_message(msg)
```

---

## Troubleshooting

### Wrong status reported

**Symptom:** `diff_config` says "up-to-date" but configs clearly differ

**Possible Causes:**
1. Artifact ID computed incorrectly
2. JSON serialization order matters (must use `sort_keys=True`)
3. Whitespace differences in payload

**Solution:**

```python
# Verify artifact ID computation
import json
import hashlib

# Method 1: What you're using
your_id = "..."

# Method 2: How server computes it
payload = {"mcpServers": {...}}  # Your payload
canonical = json.dumps(payload, sort_keys=True)
server_id = hashlib.sha256(canonical.encode()).hexdigest()

assert your_id == server_id, f"Mismatch: {your_id} vs {server_id}"
```

---

### Slow response

**Symptom:** `diff_config` takes >200ms

**Performance Requirement:** NFR-4 states discovery calls should be <200ms p95

**Possible Causes:**
1. Large artifact storage (thousands of configs)
2. Network latency (remote server)
3. Disk I/O bottleneck

**Solution:**

```bash
# Check response time distribution
cat var/telemetry/events.jsonl | \
  grep diff_config | \
  jq '.fields.duration_ms' | \
  sort -n | \
  awk '{
    count++
    sum += $1
    if (count % 20 == 0) print "p" (count/20*5) ": " $1 "ms"
  }'
```

If consistently >200ms, consider:
- Caching latest artifact IDs in memory
- Using faster storage (SSD)
- Indexing artifact IDs

---

### Connection errors

**Symptom:**
```
ConnectionError: Failed to connect to MCP server
```

**Solution:**
1. Verify MCP server is running
2. Check Claude Desktop config has correct path
3. Restart Claude Desktop
4. Check server logs for crashes

---

## Understanding Diff Results

### Up-to-Date Response

```json
{
  "status": "up-to-date",
  "current_artifact_id": "a7f3b2c1d4e5f6...",
  "latest_artifact_id": "a7f3b2c1d4e5f6...",
  "changelog": null
}
```

**Meaning:** Your config matches the latest version. No action needed.

---

### Outdated Response

```json
{
  "status": "outdated",
  "current_artifact_id": "a7f3b2c1d4e5f6...",
  "latest_artifact_id": "f6e5d4c3b2a198...",
  "changelog": "- Updated server command\n- Added env var: TIMEOUT"
}
```

**Meaning:** A new config version exists. Review changes and update.

**Action:**
1. Read changelog
2. Fetch latest config with `get_config`
3. Review differences
4. Apply update
5. Test

---

## Changelog Format

Changelogs follow this format:

```
- Added: New MCP server 'database-server'
- Updated: example-server command path (/usr/local/bin → /opt/bin)
- Removed: Deprecated experimental-server
- Security: Patched vulnerability in auth-server config
```

**Change Types:**
- **Added:** New servers or configuration options
- **Updated:** Modified existing configurations
- **Removed:** Deleted servers or deprecated options
- **Security:** Security-related changes (apply immediately!)
- **Breaking:** Changes that require manual intervention

---

## What You Learned

- How to check for updates with `diff_config` (FR-9)
- Content-addressable artifacts enable easy diff/status checks
- Response codes: "up-to-date" vs "outdated"
- How to automate update checks (cron, scripts)
- Performance expectation: <200ms p95 (NFR-4)
- Changelogs provide human-readable change summaries

---

## Best Practices

1. **Check regularly:** Daily or before deployments
2. **Read changelogs:** Don't blindly apply updates
3. **Test in dev first:** Apply to dev profile before prod
4. **Backup current config:** Keep copy before updating
5. **Monitor for security updates:** Apply immediately
6. **Automate checks:** Use cron or CI/CD integration

---

## Next Steps

- **[How to Verify Signatures](04-verify-signatures.md)** - Verify config integrity before applying updates
- **[How to Use Configs](05-use-config.md)** - Apply updated configs to your MCP client
- **[Automating Config Updates](06-automate-updates.md)** - Full automation workflow (Wave 2)

---

**Status:** Wave 1 E2E Test 3
**Acceptance Criteria:** AC-2, FR-9, NFR-4
**Last Updated:** 2025-10-23
