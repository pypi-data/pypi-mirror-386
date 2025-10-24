# MCP Orchestration Server Specification

**Version:** 0.1.0 (Wave 1)
**Status:** Draft
**Last Updated:** 2025-10-23

---

## Overview

This document specifies the MCP (Model Context Protocol) server implementation for mcp-orchestration. The server exposes tools and resources that enable AI applications (like Claude Desktop) to discover, retrieve, validate, and compare MCP client configurations.

**Purpose:** Define the contract between mcp-orchestration server and MCP clients for Wave 1 functionality.

**Scope:** Wave 1 Foundation capabilities only (client discovery, config retrieval, signing, diff/status). Governance features (Wave 2) are deferred.

---

## Server Identity

```json
{
  "name": "mcp-orchestration",
  "version": "0.1.0",
  "description": "MCP client configuration orchestration and distribution",
  "protocol_version": "2024-11-05",
  "capabilities": {
    "tools": {},
    "resources": {},
    "prompts": {}
  }
}
```

**Entry Point:** `mcp-orchestration` (from pyproject.toml)

**Implementation:** FastMCP-based server (`src/mcp_orchestration/mcp/server.py`)

---

## Tools (4)

Tools are functions that AI applications can call to perform actions.

### Tool 1: `list_clients`

**Purpose:** Discover supported MCP client families (FR-1)

**Description:**
Lists all MCP client families supported by the orchestration system. Each client family represents a distinct MCP implementation (e.g., Claude Desktop, Cursor).

**Input Schema:**
```json
{
  "type": "object",
  "properties": {},
  "required": []
}
```

No input parameters required.

**Output Schema:**
```json
{
  "type": "object",
  "properties": {
    "clients": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "client_id": {
            "type": "string",
            "description": "Unique identifier (e.g., 'claude-desktop', 'cursor')"
          },
          "display_name": {
            "type": "string",
            "description": "Human-readable name (e.g., 'Claude Desktop')"
          },
          "platform": {
            "type": "string",
            "enum": ["macos", "windows", "linux", "cross-platform"],
            "description": "Primary platform"
          },
          "config_location": {
            "type": "string",
            "description": "Default config file path pattern"
          },
          "available_profiles": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Profile IDs available for this client"
          }
        },
        "required": ["client_id", "display_name", "platform", "available_profiles"]
      }
    },
    "count": {
      "type": "integer",
      "description": "Total number of clients"
    }
  },
  "required": ["clients", "count"]
}
```

**Example Output:**
```json
{
  "clients": [
    {
      "client_id": "claude-desktop",
      "display_name": "Claude Desktop",
      "platform": "macos",
      "config_location": "~/Library/Application Support/Claude/claude_desktop_config.json",
      "available_profiles": ["default", "dev", "prod"]
    },
    {
      "client_id": "cursor",
      "display_name": "Cursor IDE",
      "platform": "cross-platform",
      "config_location": "~/.cursor/mcp_config.json",
      "available_profiles": ["default", "dev"]
    }
  ],
  "count": 2
}
```

**Performance Requirement:** p95 < 200ms (NFR-4)

**Errors:**
- None expected (always returns list, may be empty)

---

### Tool 2: `list_profiles`

**Purpose:** List available configuration profiles for a client

**Description:**
Returns all profiles available for a given client family. Profiles represent different configuration sets (e.g., dev, staging, prod).

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "client_id": {
      "type": "string",
      "description": "Client family identifier"
    }
  },
  "required": ["client_id"]
}
```

**Output Schema:**
```json
{
  "type": "object",
  "properties": {
    "client_id": {
      "type": "string",
      "description": "Client family identifier"
    },
    "profiles": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "profile_id": {
            "type": "string",
            "description": "Profile identifier (e.g., 'default', 'dev', 'prod')"
          },
          "display_name": {
            "type": "string",
            "description": "Human-readable profile name"
          },
          "description": {
            "type": "string",
            "description": "Profile purpose/usage"
          },
          "latest_artifact_id": {
            "type": "string",
            "description": "SHA-256 hash of latest config artifact"
          },
          "updated_at": {
            "type": "string",
            "format": "date-time",
            "description": "ISO 8601 timestamp of last update"
          }
        },
        "required": ["profile_id", "display_name", "latest_artifact_id", "updated_at"]
      }
    },
    "count": {
      "type": "integer",
      "description": "Number of profiles"
    }
  },
  "required": ["client_id", "profiles", "count"]
}
```

**Example Output:**
```json
{
  "client_id": "claude-desktop",
  "profiles": [
    {
      "profile_id": "default",
      "display_name": "Default",
      "description": "Standard configuration for most users",
      "latest_artifact_id": "a3f2c1b9e8d7f6a5b4c3d2e1f0a9b8c7d6e5f4a3b2c1d0e9f8a7b6c5d4e3f2a1",
      "updated_at": "2025-10-23T14:30:00Z"
    },
    {
      "profile_id": "dev",
      "display_name": "Development",
      "description": "Development tools and debug servers",
      "latest_artifact_id": "b4e3d2c1f0a9b8c7d6e5f4a3b2c1d0e9f8a7b6c5d4e3f2a1b0c9d8e7f6a5b4c3",
      "updated_at": "2025-10-22T09:15:00Z"
    }
  ],
  "count": 2
}
```

**Performance Requirement:** p95 < 200ms (NFR-4)

**Errors:**
```json
{
  "error": "client_not_found",
  "message": "Client 'unknown-client' not found",
  "available_clients": ["claude-desktop", "cursor"]
}
```

---

### Tool 3: `get_config`

**Purpose:** Retrieve signed configuration artifact (AC-1, FR-4)

**Description:**
Fetches the latest (or specified) configuration artifact for a client/profile combination. Returns a cryptographically signed artifact with content-addressable identifier.

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "client_id": {
      "type": "string",
      "description": "Client family identifier"
    },
    "profile_id": {
      "type": "string",
      "description": "Profile identifier (defaults to 'default')"
    },
    "artifact_id": {
      "type": "string",
      "description": "Optional: specific artifact hash to retrieve"
    }
  },
  "required": ["client_id"]
}
```

**Output Schema:**
```json
{
  "type": "object",
  "properties": {
    "artifact_id": {
      "type": "string",
      "pattern": "^[a-f0-9]{64}$",
      "description": "SHA-256 hash of payload (content-addressable ID)"
    },
    "client_id": {
      "type": "string",
      "description": "Client family identifier"
    },
    "profile_id": {
      "type": "string",
      "description": "Profile identifier"
    },
    "created_at": {
      "type": "string",
      "format": "date-time",
      "description": "ISO 8601 timestamp"
    },
    "payload": {
      "type": "object",
      "description": "MCP client configuration (mcpServers structure)"
    },
    "signature": {
      "type": "string",
      "description": "Base64-encoded Ed25519 signature"
    },
    "signing_key_id": {
      "type": "string",
      "description": "Identifier for public key verification"
    },
    "metadata": {
      "type": "object",
      "properties": {
        "generator": {
          "type": "string",
          "description": "Tool that generated config (e.g., 'chora-compose')"
        },
        "generator_version": {
          "type": "string",
          "description": "Version of generator"
        }
      }
    }
  },
  "required": [
    "artifact_id",
    "client_id",
    "profile_id",
    "created_at",
    "payload",
    "signature",
    "signing_key_id"
  ]
}
```

**Example Output:**
```json
{
  "artifact_id": "a3f2c1b9e8d7f6a5b4c3d2e1f0a9b8c7d6e5f4a3b2c1d0e9f8a7b6c5d4e3f2a1",
  "client_id": "claude-desktop",
  "profile_id": "default",
  "created_at": "2025-10-23T14:30:00Z",
  "payload": {
    "mcpServers": {
      "filesystem": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", "/Users/user/projects"]
      },
      "brave-search": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-brave-search"],
        "env": {
          "BRAVE_API_KEY": "${BRAVE_API_KEY}"
        }
      }
    }
  },
  "signature": "bXlzaWduYXR1cmU...base64...",
  "signing_key_id": "orchestration-prod-2025",
  "metadata": {
    "generator": "chora-compose",
    "generator_version": "0.1.0"
  }
}
```

**Performance Requirement:** p95 < 300ms (NFR-3)

**Errors:**
```json
{
  "error": "client_not_found",
  "message": "Client 'unknown-client' not found"
}
```

```json
{
  "error": "profile_not_found",
  "message": "Profile 'unknown-profile' not found for client 'claude-desktop'",
  "available_profiles": ["default", "dev", "prod"]
}
```

```json
{
  "error": "artifact_not_found",
  "message": "Artifact 'abc123...' not found"
}
```

---

### Tool 4: `diff_config`

**Purpose:** Compare configurations and detect updates (AC-2, FR-9)

**Description:**
Compares a local configuration against the latest orchestrated version. Returns diff report showing additions, modifications, removals, and update availability.

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "client_id": {
      "type": "string",
      "description": "Client family identifier"
    },
    "profile_id": {
      "type": "string",
      "description": "Profile identifier (defaults to 'default')"
    },
    "local_artifact_id": {
      "type": "string",
      "description": "SHA-256 hash of local config (optional)"
    },
    "local_payload": {
      "type": "object",
      "description": "Local MCP configuration payload (alternative to local_artifact_id)"
    }
  },
  "required": ["client_id"],
  "oneOf": [
    {"required": ["local_artifact_id"]},
    {"required": ["local_payload"]}
  ]
}
```

**Output Schema:**
```json
{
  "type": "object",
  "properties": {
    "status": {
      "type": "string",
      "enum": ["up-to-date", "outdated", "diverged", "unknown"],
      "description": "Comparison result"
    },
    "local_artifact_id": {
      "type": "string",
      "description": "Hash of local config"
    },
    "remote_artifact_id": {
      "type": "string",
      "description": "Hash of latest orchestrated config"
    },
    "diff": {
      "type": "object",
      "properties": {
        "servers_added": {
          "type": "array",
          "items": {"type": "string"},
          "description": "Server IDs added in remote"
        },
        "servers_removed": {
          "type": "array",
          "items": {"type": "string"},
          "description": "Server IDs removed in remote"
        },
        "servers_modified": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "server_id": {"type": "string"},
              "changes": {
                "type": "array",
                "items": {
                  "type": "object",
                  "properties": {
                    "path": {"type": "string"},
                    "old_value": {},
                    "new_value": {}
                  }
                }
              }
            }
          },
          "description": "Servers with configuration changes"
        },
        "servers_unchanged": {
          "type": "array",
          "items": {"type": "string"},
          "description": "Server IDs with no changes"
        }
      }
    },
    "summary": {
      "type": "object",
      "properties": {
        "total_changes": {"type": "integer"},
        "added_count": {"type": "integer"},
        "removed_count": {"type": "integer"},
        "modified_count": {"type": "integer"}
      }
    },
    "recommendation": {
      "type": "string",
      "description": "Human-readable action recommendation"
    }
  },
  "required": ["status", "local_artifact_id", "remote_artifact_id", "diff", "summary"]
}
```

**Example Output (Up-to-Date):**
```json
{
  "status": "up-to-date",
  "local_artifact_id": "a3f2c1b9e8d7f6a5b4c3d2e1f0a9b8c7d6e5f4a3b2c1d0e9f8a7b6c5d4e3f2a1",
  "remote_artifact_id": "a3f2c1b9e8d7f6a5b4c3d2e1f0a9b8c7d6e5f4a3b2c1d0e9f8a7b6c5d4e3f2a1",
  "diff": {
    "servers_added": [],
    "servers_removed": [],
    "servers_modified": [],
    "servers_unchanged": ["filesystem", "brave-search"]
  },
  "summary": {
    "total_changes": 0,
    "added_count": 0,
    "removed_count": 0,
    "modified_count": 0
  },
  "recommendation": "Your configuration is current. No updates needed."
}
```

**Example Output (Outdated):**
```json
{
  "status": "outdated",
  "local_artifact_id": "b4e3d2c1f0a9b8c7d6e5f4a3b2c1d0e9f8a7b6c5d4e3f2a1b0c9d8e7f6a5b4c3",
  "remote_artifact_id": "a3f2c1b9e8d7f6a5b4c3d2e1f0a9b8c7d6e5f4a3b2c1d0e9f8a7b6c5d4e3f2a1",
  "diff": {
    "servers_added": ["github"],
    "servers_removed": [],
    "servers_modified": [
      {
        "server_id": "brave-search",
        "changes": [
          {
            "path": "args[0]",
            "old_value": "@modelcontextprotocol/server-brave-search@0.1.0",
            "new_value": "@modelcontextprotocol/server-brave-search@0.2.0"
          }
        ]
      }
    ],
    "servers_unchanged": ["filesystem"]
  },
  "summary": {
    "total_changes": 2,
    "added_count": 1,
    "removed_count": 0,
    "modified_count": 1
  },
  "recommendation": "Update available: 1 new server, 1 server updated. Run 'get_config' to fetch latest."
}
```

**Performance Requirement:** p95 < 200ms (NFR-4)

**Errors:**
```json
{
  "error": "client_not_found",
  "message": "Client 'unknown-client' not found"
}
```

---

## Resources (2)

Resources expose structured data that can be read by MCP clients.

### Resource 1: `capabilities://server`

**Purpose:** Server capability advertisement

**Description:**
Exposes the orchestration server's capabilities, version, and supported features. Allows clients to discover what the server can do.

**URI:** `capabilities://server`

**MIME Type:** `application/json`

**Content Schema:**
```json
{
  "type": "object",
  "properties": {
    "name": {"type": "string"},
    "version": {"type": "string"},
    "wave": {"type": "string"},
    "capabilities": {
      "type": "object",
      "properties": {
        "tools": {
          "type": "array",
          "items": {"type": "string"},
          "description": "Available tool names"
        },
        "resources": {
          "type": "array",
          "items": {"type": "string"},
          "description": "Available resource URIs"
        },
        "prompts": {
          "type": "array",
          "items": {"type": "string"},
          "description": "Available prompt names"
        }
      }
    },
    "features": {
      "type": "object",
      "properties": {
        "content_addressing": {"type": "boolean"},
        "cryptographic_signing": {"type": "boolean"},
        "signature_algorithm": {"type": "string"},
        "diff_reports": {"type": "boolean"},
        "profile_support": {"type": "boolean"}
      }
    },
    "endpoints": {
      "type": "object",
      "properties": {
        "verification_key_url": {"type": "string"}
      }
    }
  }
}
```

**Example Content:**
```json
{
  "name": "mcp-orchestration",
  "version": "0.1.0",
  "wave": "Wave 1: Foundation",
  "capabilities": {
    "tools": ["list_clients", "list_profiles", "get_config", "diff_config"],
    "resources": ["capabilities://server", "capabilities://clients"],
    "prompts": []
  },
  "features": {
    "content_addressing": true,
    "cryptographic_signing": true,
    "signature_algorithm": "Ed25519",
    "diff_reports": true,
    "profile_support": true
  },
  "endpoints": {
    "verification_key_url": "https://mcp-orchestration.example.com/keys/verification_key.pem"
  }
}
```

---

### Resource 2: `capabilities://clients`

**Purpose:** Client family capability matrix

**Description:**
Exposes detailed capability information for each supported client family. Shows which features and configurations are supported per client.

**URI:** `capabilities://clients`

**MIME Type:** `application/json`

**Content Schema:**
```json
{
  "type": "object",
  "properties": {
    "clients": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "client_id": {"type": "string"},
          "display_name": {"type": "string"},
          "version_min": {"type": "string"},
          "version_max": {"type": "string"},
          "config_format": {
            "type": "string",
            "enum": ["json", "yaml", "toml"]
          },
          "supports": {
            "type": "object",
            "properties": {
              "environment_variables": {"type": "boolean"},
              "command_args": {"type": "boolean"},
              "working_directory": {"type": "boolean"},
              "multiple_servers": {"type": "boolean"}
            }
          },
          "limitations": {
            "type": "object",
            "properties": {
              "max_servers": {"type": "integer"},
              "max_env_vars_per_server": {"type": "integer"}
            }
          }
        }
      }
    }
  }
}
```

**Example Content:**
```json
{
  "clients": [
    {
      "client_id": "claude-desktop",
      "display_name": "Claude Desktop",
      "version_min": "0.5.0",
      "version_max": null,
      "config_format": "json",
      "supports": {
        "environment_variables": true,
        "command_args": true,
        "working_directory": true,
        "multiple_servers": true
      },
      "limitations": {
        "max_servers": null,
        "max_env_vars_per_server": null
      }
    },
    {
      "client_id": "cursor",
      "display_name": "Cursor IDE",
      "version_min": "0.1.0",
      "version_max": null,
      "config_format": "json",
      "supports": {
        "environment_variables": true,
        "command_args": true,
        "working_directory": false,
        "multiple_servers": true
      },
      "limitations": {
        "max_servers": 20,
        "max_env_vars_per_server": 50
      }
    }
  ]
}
```

---

## Prompts (0)

**Wave 1 Decision:** No prompts in initial release.

**Rationale:** Prompts are useful for guided workflows (e.g., "Help me migrate to latest config"). Defer to Wave 2 when we have governance context (approval flows, policy checks).

**Planned Wave 2 Prompts:**
- `migrate_config`: Interactive configuration migration assistant
- `troubleshoot_config`: Debug config application issues
- `policy_check`: Validate config against organizational policies

---

## Implementation Requirements

### Cryptographic Signing (AC-1)

**Algorithm:** Ed25519 (RFC 8032)

**Key Management:**
- Signing key: Private key for artifact signing (server-side only)
- Verification key: Public key distributed for signature verification (client-side)

**Signature Process:**
1. Normalize payload to canonical JSON (sorted keys, no whitespace)
2. Compute signature: `signature = Ed25519.sign(private_key, canonical_payload_bytes)`
3. Encode signature as Base64
4. Include in artifact as `signature` field

**Verification Process:**
```python
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
import json, base64

# Load verification key
with open("verification_key.pem", "rb") as f:
    public_key = Ed25519PublicKey.from_public_bytes(f.read())

# Canonicalize payload
canonical = json.dumps(payload, sort_keys=True, separators=(',', ':')).encode()

# Verify
signature_bytes = base64.b64decode(artifact["signature"])
try:
    public_key.verify(signature_bytes, canonical)
    # ✓ Valid
except:
    # ✗ Invalid
```

**Verification Key Distribution:**
- Resource endpoint: `capabilities://server` includes `verification_key_url`
- HTTPS endpoint: `https://mcp-orchestration.example.com/keys/verification_key.pem`
- Local path: `~/.mcp-orchestration/verification_key.pem`

---

### Content-Addressable Storage (FR-4)

**Artifact ID:** SHA-256 hash of canonical payload

**Computation:**
```python
import hashlib
import json

canonical_payload = json.dumps(payload, sort_keys=True, separators=(',', ':')).encode()
artifact_id = hashlib.sha256(canonical_payload).hexdigest()
```

**Properties:**
- Deterministic: Same payload → same artifact_id
- Immutable: Artifact content never changes after creation
- Verifiable: Clients can recompute hash to verify integrity

**Storage Path:** `~/.mcp-orchestration/artifacts/{artifact_id}.json`

---

### Performance Requirements

**NFR-3: Config retrieval** < 300ms p95
- Includes: Artifact lookup, payload read, signature computation
- Optimization: In-memory cache for frequently accessed artifacts

**NFR-4: List operations** < 200ms p95
- Includes: `list_clients`, `list_profiles`, `diff_config`
- Optimization: Pre-computed metadata index

**Measurement:** Instrument all tool handlers with timing metrics

---

### Error Handling

**Principle:** Return structured error objects, not exceptions

**Error Response Format:**
```json
{
  "error": "error_code",
  "message": "Human-readable error description",
  "details": {
    "field": "additional context"
  }
}
```

**Common Error Codes:**
- `client_not_found`: Unknown client_id
- `profile_not_found`: Unknown profile_id for client
- `artifact_not_found`: Artifact doesn't exist
- `invalid_input`: Malformed request parameters
- `signature_error`: Signature computation failed
- `internal_error`: Unexpected server error

---

## Testing Strategy

**E2E Tests:** Five how-to guides serve as acceptance tests
1. [01-discover-clients.md](../../user-docs/how-to/01-discover-clients.md) → Test `list_clients`
2. [02-get-first-config.md](../../user-docs/how-to/02-get-first-config.md) → Test `get_config` + signing
3. [03-check-updates.md](../../user-docs/how-to/03-check-updates.md) → Test `diff_config`
4. [04-verify-signatures.md](../../user-docs/how-to/04-verify-signatures.md) → Test signature verification
5. [05-use-config.md](../../user-docs/how-to/05-use-config.md) → Test config application

**Unit Tests:**
- Tool handlers (mock storage layer)
- Signature generation/verification
- Artifact ID computation
- Diff algorithm

**Integration Tests:**
- Tool → Storage → chora-compose flow
- End-to-end with real Claude Desktop

**Performance Tests:**
- Measure p95 latency for NFR-3, NFR-4
- Load test with 100 concurrent `get_config` calls

---

## Dependencies

**Runtime:**
- `fastmcp>=0.3.0` - MCP server framework
- `cryptography>=41.0.0` - Ed25519 signing/verification
- `pydantic>=2.0.0` - Schema validation
- `chora-compose>=0.1.0` - Config generation (imported as library)

**Development:**
- `pytest>=8.3.0` - Testing framework
- `pytest-asyncio>=0.24.0` - Async test support

---

## Future Enhancements (Wave 2+)

**Deferred to Wave 2:**
- Prompts for guided workflows
- Policy validation tool
- Config approval flows
- Audit logging

**Deferred to Wave 3:**
- AI-powered config analysis
- Anomaly detection
- Telemetry integration

**Deferred to Wave 4:**
- Multi-tenant support
- Federation protocol
- Marketplace integration

---

## Success Criteria

Wave 1 is complete when:
- [ ] All 4 tools implemented and functional
- [ ] Both resources expose correct data
- [ ] AC-1: Configs signed with Ed25519
- [ ] AC-2: Diff reports show up-to-date/outdated status
- [ ] AC-4: Signature verification works (manual + automated)
- [ ] NFR-3: `get_config` < 300ms p95
- [ ] NFR-4: List operations < 200ms p95
- [ ] All 5 E2E how-to guides pass when executed by Claude Desktop

---

## References

- [Wave 1 Vision](MCP_CONFIG_ORCHESTRATION.md#wave-1-foundation-v010)
- [Solution Specification](spec.md)
- [E2E Test Guides](../../user-docs/how-to/)
- [MCP Protocol Specification](https://spec.modelcontextprotocol.io/)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)

---

**Status:** Ready for implementation
**Next Steps:** Phase 1 - Integrate chora-compose as Python library
