# How to Verify Configuration Signatures

**Goal:** Cryptographically verify config hasn't been tampered with

**Time:** 10 minutes

**Security Level:** ⭐⭐⭐ High - Prevents config tampering attacks

**Prerequisites:**
- Public verification key (`keys/verification_key.pem`)
- Config artifact to verify (from `get_config`)
- Python 3.12+ with cryptography library

---

## Why Verify Signatures?

Every config artifact from mcp-orchestration is signed with **Ed25519**:

- **Integrity:** Detect if config was modified after signing
- **Authenticity:** Confirm config came from mcp-orchestration server
- **Non-repudiation:** Publisher can't deny creating config
- **Trust:** Verify config hasn't been tampered with during transmission

**Security Principle:** Never trust, always verify.

---

## Understanding Ed25519

**Ed25519** is a modern elliptic curve signature algorithm:

| Property | Value | Benefit |
|----------|-------|---------|
| Algorithm | EdDSA (Ed25519) | State-of-the-art security |
| Key Size | 32 bytes (256 bits) | Compact keys |
| Signature Size | 64 bytes | Small signatures |
| Speed | ~60,000 sigs/sec | Very fast |
| Security Level | ⭐⭐⭐ High | Resistant to known attacks |

**Comparison to RSA:**
- Smaller keys (32 bytes vs 256+ bytes)
- Faster verification (~3x faster)
- More secure against side-channel attacks

---

## Step 1: Get Verification Key

The verification key is **public** and should be distributed with the server.

### Option A: Download from Server

```bash
# If server provides public key endpoint
curl https://your-server.com/keys/verification_key.pem > verification_key.pem

# Or from GitHub repository
curl https://raw.githubusercontent.com/liminalcommons/mcp-orchestration/main/keys/verification_key.pem > verification_key.pem
```

---

### Option B: Use Local Key (Development)

If running server locally:

```bash
cp keys/verification_key.pem ~/Downloads/verification_key.pem
```

---

### Verify Key Format

```bash
# Should start with: -----BEGIN PUBLIC KEY-----
head -1 verification_key.pem

# Should be PEM-encoded Ed25519 public key
openssl pkey -pubin -in verification_key.pem -text -noout

# Expected output:
# ED25519 Public-Key:
# pub:
#     [32 bytes of hex data]
```

---

## Step 2: Fetch Config to Verify

### Using Claude Desktop

Ask Claude:

> Get the default config for claude-desktop and save the artifact

---

### Using Python

```python
from examples.python_client.client import MCPOrchestrationClient
import json

client = MCPOrchestrationClient()
config = client.get_config("claude-desktop", "default")

# Save complete artifact (includes signature)
with open("config.json", "w") as f:
    json.dump(config, f, indent=2)

print(f"✓ Config saved to config.json")
print(f"  Artifact ID: {config['artifact_id']}")
print(f"  Signature Algorithm: {config['signature']['algorithm']}")
```

---

## Step 3: Verify Signature

### Using Verification Script

```bash
python examples/python_client/verify.py config.json verification_key.pem
```

**Expected Output (Valid Signature):**

```
✓ Signature verification PASSED

Config Details:
  Client: claude-desktop
  Profile: default
  Artifact ID: a7f3b2c1d4e5f6...
  Issued: 2025-10-23T17:00:00Z
  Schema: claude-desktop-config-v1

Signature:
  Algorithm: Ed25519
  Key ID: default
  Value: YmFzZTY0c2ln... (64 bytes)

Provenance:
  Publisher: mcp-orchestration
  Generator: chora-compose+jinja2
  Tooling Version: 0.1.0

✓ The config payload has NOT been tampered with.
  It was signed by: mcp-orchestration
  Signature is cryptographically valid.
```

---

**Expected Output (Invalid Signature):**

```
✗ Signature verification FAILED

WARNING: This config may have been tampered with!

Config Details:
  Client: claude-desktop
  Profile: default
  Artifact ID: a7f3b2c1d4e5f6...

Signature Check:
  ✗ Cryptographic verification failed
  ✗ Payload may have been modified
  ✗ Signature may be forged

⚠️  DO NOT use this configuration!

Action Required:
  1. Fetch a fresh copy from the server
  2. Verify again with trusted verification key
  3. If still fails, contact server administrator
  4. Check for man-in-the-middle attacks
```

---

## Step 4: Manual Verification (Advanced)

If you want to understand the verification process:

```python
#!/usr/bin/env python3
"""
Manual Ed25519 signature verification.

Demonstrates the cryptographic process step-by-step.
"""

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature
import base64
import json
from pathlib import Path

def verify_config_signature(config_path: Path, pubkey_path: Path) -> bool:
    """Verify config artifact signature."""

    # Step 1: Load public key
    print("[1/4] Loading public key...")
    with open(pubkey_path, "rb") as f:
        public_key = serialization.load_pem_public_key(f.read())

    if not isinstance(public_key, Ed25519PublicKey):
        raise ValueError("Key must be Ed25519 public key")

    print(f"      ✓ Loaded Ed25519 public key from {pubkey_path.name}")

    # Step 2: Load config artifact
    print("[2/4] Loading config artifact...")
    with open(config_path, "r") as f:
        config = json.load(f)

    payload = config["payload"]
    signature_b64 = config["signature"]["value"]
    algorithm = config["signature"]["algorithm"]

    if algorithm != "Ed25519":
        raise ValueError(f"Unsupported algorithm: {algorithm}")

    print(f"      ✓ Loaded config (artifact ID: {config['artifact_id'][:12]}...)")

    # Step 3: Prepare data for verification
    print("[3/4] Preparing data for verification...")

    # IMPORTANT: Serialize payload deterministically
    # - sort_keys=True: Ensures consistent key ordering
    # - separators=(',', ':'): No extra whitespace
    payload_bytes = json.dumps(
        payload,
        sort_keys=True,
        separators=(',', ':')
    ).encode('utf-8')

    signature_bytes = base64.b64decode(signature_b64)

    print(f"      ✓ Payload: {len(payload_bytes)} bytes")
    print(f"      ✓ Signature: {len(signature_bytes)} bytes")

    # Step 4: Verify signature
    print("[4/4] Verifying signature...")

    try:
        public_key.verify(signature_bytes, payload_bytes)
        print("      ✓ Signature is cryptographically valid")
        return True
    except InvalidSignature:
        print("      ✗ Signature verification failed!")
        return False

# Usage
if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        print("Usage: python verify_manual.py config.json verification_key.pem")
        sys.exit(1)

    config_path = Path(sys.argv[1])
    pubkey_path = Path(sys.argv[2])

    valid = verify_config_signature(config_path, pubkey_path)

    if valid:
        print("\n✓ Signature verification PASSED")
        sys.exit(0)
    else:
        print("\n✗ Signature verification FAILED")
        sys.exit(1)
```

---

## Success Criteria (AC-4)

This is **Acceptance Criteria 4** from the Wave 1 specification:

- [ ] Valid configs verify successfully
- [ ] Tampered configs fail verification
- [ ] Verification completes in <100ms
- [ ] Clear error messages on failure
- [ ] Instructions work without server access (offline verification)
- [ ] Verification script provided in `examples/python_client/`
- [ ] Documentation explains verification process clearly
- [ ] Public key distribution documented

---

## What Can Go Wrong?

### Scenario 1: Tampered Payload

```python
# Attacker modifies payload
config["payload"]["mcpServers"]["malicious-server"] = {...}

# Signature no longer matches
# verify() → FAILS ✗
```

**Detection:** Signature verification fails immediately.

---

### Scenario 2: Forged Signature

```python
# Attacker creates fake signature
config["signature"]["value"] = "fake-signature-base64"

# Signature doesn't match payload
# verify() → FAILS ✗
```

**Detection:** Ed25519 verification rejects forged signatures.

---

### Scenario 3: Wrong Public Key

```python
# Using wrong verification key
# Even valid signature will fail

# verify() → FAILS ✗
```

**Detection:** All signatures fail, not just one. Indicates key mismatch.

---

## Security Best Practices

### 1. Store Verification Key Securely

```bash
# Good: Read-only for owner
chmod 400 verification_key.pem

# Bad: World-readable
chmod 644 verification_key.pem  # ❌ Don't do this
```

---

### 2. Verify on Every Fetch

```python
# Good: Always verify
config = client.get_config("claude-desktop", "default")
if not verifier.verify(config):
    raise SecurityError("Signature verification failed!")

# Bad: Skip verification (trust on first use)
config = client.get_config("claude-desktop", "default")
# Use config without verification ❌
```

---

### 3. Don't Ignore Failures

```python
# Bad: Ignore verification failures
try:
    verifier.verify(config)
except:
    pass  # ❌ Never do this!

# Good: Fail fast
if not verifier.verify(config):
    raise SecurityError("Config verification failed - potential tampering")
```

---

### 4. Rotate Keys Periodically

**Server Administrator:**
- Rotate signing keys every 90 days
- Keep old keys for 30-day overlap
- Announce rotation schedule

**Client:**
- Update verification key when rotated
- Support multiple keys during transition

---

### 5. Verify Before Storing

```python
# Good: Verify then store
config = client.get_config("claude-desktop", "default")
if verifier.verify(config):
    save_config(config)
else:
    raise SecurityError("Verification failed")

# Bad: Store then verify
config = client.get_config("claude-desktop", "default")
save_config(config)  # ❌ Saved unverified config!
if not verifier.verify(config):
    # Too late - already saved
    pass
```

---

## Troubleshooting

### Verification fails for valid config

**Symptom:** Known-good config fails verification

**Possible Causes:**
1. Wrong verification key
2. Payload modified accidentally (whitespace, key order)
3. Base64 decoding issue
4. Key rotation (using old key)

**Solution:**

```bash
# 1. Verify you have correct public key
sha256sum verification_key.pem
# Compare with server-published hash

# 2. Re-fetch config
python -c "
from examples.python_client.client import MCPOrchestrationClient
client = MCPOrchestrationClient()
config = client.get_config('claude-desktop', 'default')
import json
with open('fresh_config.json', 'w') as f:
    json.dump(config, f, indent=2)
"

# 3. Verify again
python examples/python_client/verify.py fresh_config.json verification_key.pem
```

---

### All verifications fail

**Symptom:** Every config fails verification

**Diagnosis:** Wrong verification key

**Solution:**

```bash
# Check key matches server
curl https://your-server.com/keys/verification_key.pem | \
  sha256sum

# Compare to your local key
sha256sum verification_key.pem

# If different, download fresh key
curl https://your-server.com/keys/verification_key.pem > verification_key.pem
```

---

### Verification too slow

**Symptom:** Verification takes >100ms

**Target:** <100ms (high performance requirement)

**Solution:**

Ed25519 is extremely fast (~60,000 verifications/second). If slow:

```python
import time

# Measure verification time
start = time.perf_counter()
verifier.verify(config)
elapsed_ms = (time.perf_counter() - start) * 1000

print(f"Verification took {elapsed_ms:.2f}ms")

# If >100ms, check:
# - CPU throttling
# - Swap usage (memory pressure)
# - Old cryptography library version
```

---

## Key Rotation

### Server Side (Wave 2)

```bash
# Generate new keypair
python scripts/generate_keypair.py --output keys/

# Publish new public key
cp keys/verification_key.pem public/keys/verification_key_v2.pem

# Announce rotation
# Keep old key active for 30 days
# Sign new artifacts with new key
```

---

### Client Side

```python
# Support multiple keys during rotation
verifiers = [
    ArtifactVerifier("keys/verification_key_v1.pem"),
    ArtifactVerifier("keys/verification_key_v2.pem"),
]

def verify_with_any(config, verifiers):
    """Try verification with all known keys."""
    for verifier in verifiers:
        if verifier.verify(config):
            return True
    return False

# Use during transition period
if verify_with_any(config, verifiers):
    apply_config(config)
```

---

## What You Learned

- Why cryptographic signature verification is critical
- How Ed25519 provides strong security with compact keys
- How to verify config artifacts using public key cryptography
- Signature verification catches tampering and forgery
- Best practices for key management and verification workflows
- Performance expectation: <100ms verification time

---

## Next Steps

- **[How to Use Configs in Your MCP Client](05-use-config.md)** - Apply verified configs
- **[Understanding Config Provenance](../explanation/config-provenance.md)** - Learn about config metadata
- **[Security Architecture](../explanation/security-architecture.md)** - Deep dive into crypto design

---

**Status:** Wave 1 E2E Test 4
**Acceptance Criteria:** AC-4, FR-4 (signature verification)
**Last Updated:** 2025-10-23
