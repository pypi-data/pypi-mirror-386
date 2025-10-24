"""MCP orchestration server implementation.

This module implements the Model Context Protocol server for MCP client
configuration orchestration and distribution.

Wave 1 (Foundation v0.1.0):
- 4 tools: list_clients, list_profiles, get_config, diff_config
- 2 resources: capabilities://server, capabilities://clients
- 0 prompts (deferred to Wave 2)
"""

import json
from typing import Any

from fastmcp import FastMCP

from mcp_orchestrator.diff import compare_configs
from mcp_orchestrator.registry import get_default_registry
from mcp_orchestrator.storage import ArtifactStore, StorageError

# Initialize MCP server
mcp = FastMCP("mcp-orchestration")

# Initialize global state (will be set on server startup)
_registry = get_default_registry()
_store = ArtifactStore()  # Uses default ~/.mcp-orchestration path


# =============================================================================
# TOOLS (4)
# =============================================================================


@mcp.tool()
async def list_clients() -> dict[str, Any]:
    """List supported MCP client families.

    Returns information about all MCP client families supported by the
    orchestration system (e.g., Claude Desktop, Cursor).

    Performance: p95 < 200ms (NFR-4)

    Returns:
        Dictionary with:
        - clients: List of client objects with id, display_name, platform, etc.
        - count: Total number of clients
    """
    # Get clients from registry
    registry_clients = _registry.list_clients()

    # Build response with client metadata
    clients = []
    for client_def in registry_clients:
        # Get profile IDs from registry
        profile_ids = [p.profile_id for p in client_def.default_profiles]

        clients.append(
            {
                "client_id": client_def.client_id,
                "display_name": client_def.display_name,
                "platform": client_def.platform,
                "config_location": client_def.config_location,
                "available_profiles": profile_ids,
            }
        )

    return {
        "clients": clients,
        "count": len(clients),
    }


@mcp.tool()
async def list_profiles(client_id: str) -> dict[str, Any]:
    """List available configuration profiles for a client.

    Returns all profiles available for a given client family. Profiles represent
    different configuration sets (e.g., dev, staging, prod).

    Performance: p95 < 200ms (NFR-4)

    Args:
        client_id: Client family identifier (e.g., 'claude-desktop', 'cursor')

    Returns:
        Dictionary with:
        - client_id: Client family identifier
        - profiles: List of profile objects
        - count: Number of profiles

    Raises:
        ValueError: If client_id not found
    """
    # Validate client exists in registry
    if not _registry.has_client(client_id):
        available = _registry.client_ids()
        raise ValueError(
            f"Client '{client_id}' not found. Available: {available}"
        )

    # Get profile definitions from registry
    profile_defs = _registry.get_profiles(client_id)

    # Try to get stored profiles for artifact metadata
    try:
        stored_profile_ids = _store.list_profiles(client_id)
    except StorageError:
        # Client not in storage yet - use registry only
        stored_profile_ids = []

    profiles = []
    for profile_def in profile_defs:
        profile_data = {
            "profile_id": profile_def.profile_id,
            "display_name": profile_def.display_name,
            "description": profile_def.description,
        }

        # Add storage metadata if available
        if profile_def.profile_id in stored_profile_ids:
            try:
                metadata = _store.get_profile_metadata(
                    client_id, profile_def.profile_id
                )
                profile_data["latest_artifact_id"] = metadata.latest_artifact_id
                profile_data["updated_at"] = metadata.updated_at
            except StorageError:
                # Profile exists in storage list but metadata unavailable
                profile_data["latest_artifact_id"] = None
                profile_data["updated_at"] = None
        else:
            # Profile not yet in storage
            profile_data["latest_artifact_id"] = None
            profile_data["updated_at"] = None

        profiles.append(profile_data)

    return {
        "client_id": client_id,
        "profiles": profiles,
        "count": len(profiles),
    }


@mcp.tool()
async def get_config(
    client_id: str,
    profile_id: str = "default",
    artifact_id: str | None = None,
) -> dict[str, Any]:
    """Retrieve signed configuration artifact.

    Fetches the latest (or specified) configuration artifact for a client/profile
    combination. Returns a cryptographically signed artifact with content-addressable
    identifier.

    Performance: p95 < 300ms (NFR-3)

    Args:
        client_id: Client family identifier (e.g., 'claude-desktop')
        profile_id: Profile identifier (defaults to 'default')
        artifact_id: Optional specific artifact hash to retrieve

    Returns:
        Dictionary with:
        - artifact_id: SHA-256 hash of payload (content-addressable ID)
        - client_id: Client family identifier
        - profile_id: Profile identifier
        - created_at: ISO 8601 timestamp
        - payload: MCP client configuration (mcpServers structure)
        - signature: Base64-encoded Ed25519 signature
        - signing_key_id: Identifier for public key verification
        - metadata: Generator info

    Raises:
        ValueError: If client_id or profile_id not found, or artifact_id invalid
    """
    # Validate client exists
    if not _registry.has_client(client_id):
        available = _registry.client_ids()
        raise ValueError(
            f"Client '{client_id}' not found. Available: {available}"
        )

    # Retrieve artifact from storage
    try:
        if artifact_id:
            # Get specific artifact by ID
            artifact = _store.get_by_id(artifact_id)
        else:
            # Get latest artifact for client/profile
            artifact = _store.get(client_id, profile_id)

        # Convert ConfigArtifact to tool response format
        return {
            "artifact_id": artifact.artifact_id,
            "client_id": artifact.client_id,
            "profile_id": artifact.profile_id,
            "created_at": artifact.created_at,
            "payload": artifact.payload,
            "signature": artifact.signature,
            "signing_key_id": artifact.signing_key_id,
            "metadata": artifact.metadata,
        }

    except StorageError as e:
        # Convert storage errors to tool errors
        if "not found" in str(e).lower():
            if artifact_id:
                raise ValueError(f"Artifact '{artifact_id}' not found") from e
            else:
                raise ValueError(
                    f"No configuration found for {client_id}/{profile_id}. "
                    f"Run 'mcp-orchestration init-configs' to create initial configs."
                ) from e
        else:
            raise ValueError(f"Failed to retrieve configuration: {e}") from e


@mcp.tool()
async def diff_config(
    client_id: str,
    profile_id: str = "default",
    local_artifact_id: str | None = None,
    local_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Compare configurations and detect updates.

    Compares a local configuration against the latest orchestrated version.
    Returns diff report showing additions, modifications, removals, and update
    availability.

    Performance: p95 < 200ms (NFR-4)

    Args:
        client_id: Client family identifier
        profile_id: Profile identifier (defaults to 'default')
        local_artifact_id: SHA-256 hash of local config (optional)
        local_payload: Local MCP configuration payload (alternative to local_artifact_id)

    Returns:
        Dictionary with:
        - status: 'up-to-date', 'outdated', 'diverged', or 'unknown'
        - local_artifact_id: Hash of local config
        - remote_artifact_id: Hash of latest orchestrated config
        - diff: Object with servers_added, servers_removed, servers_modified, servers_unchanged
        - summary: Counts of changes
        - recommendation: Human-readable action recommendation

    Raises:
        ValueError: If client_id not found or neither local_artifact_id nor local_payload provided
    """
    # Validate inputs
    if not local_artifact_id and not local_payload:
        raise ValueError("Must provide either local_artifact_id or local_payload")

    if not _registry.has_client(client_id):
        available = _registry.client_ids()
        raise ValueError(
            f"Client '{client_id}' not found. Available: {available}"
        )

    # Get local payload if only artifact_id provided
    if local_artifact_id and not local_payload:
        try:
            local_artifact = _store.get_by_id(local_artifact_id)
            local_payload = local_artifact.payload
        except StorageError:
            # Artifact not in storage - can't compare
            raise ValueError(
                f"Local artifact '{local_artifact_id}' not found in storage. "
                "Provide local_payload instead."
            )

    # Compute local artifact ID if not provided
    if not local_artifact_id and local_payload:
        local_artifact_id = _store.compute_artifact_id(local_payload)

    # Get remote configuration
    try:
        remote_artifact = _store.get(client_id, profile_id)
    except StorageError as e:
        raise ValueError(
            f"No remote configuration found for {client_id}/{profile_id}"
        ) from e

    # Compare configurations
    diff_result = compare_configs(local_payload, remote_artifact.payload)

    # Generate human-readable recommendation
    if diff_result.status == "up-to-date":
        recommendation = "Your configuration is current. No updates needed."
    elif diff_result.status == "outdated":
        recommendation = (
            f"Update available: {len(diff_result.servers_added)} new server(s), "
            f"{len(diff_result.servers_modified)} server(s) updated. "
            "Run 'get_config' to fetch latest."
        )
    elif diff_result.status == "diverged":
        recommendation = (
            f"Configuration diverged: Your local config has {len(diff_result.servers_removed)} "
            "server(s) not in remote. Review changes carefully before updating."
        )
    else:
        recommendation = "Unable to determine configuration status."

    return {
        "status": diff_result.status,
        "local_artifact_id": local_artifact_id,
        "remote_artifact_id": remote_artifact.artifact_id,
        "diff": {
            "servers_added": diff_result.servers_added,
            "servers_removed": diff_result.servers_removed,
            "servers_modified": diff_result.servers_modified,
            "servers_unchanged": diff_result.servers_unchanged,
        },
        "summary": {
            "total_changes": diff_result.total_changes,
            "added_count": len(diff_result.servers_added),
            "removed_count": len(diff_result.servers_removed),
            "modified_count": len(diff_result.servers_modified),
        },
        "recommendation": recommendation,
    }


# =============================================================================
# RESOURCES (2)
# =============================================================================


@mcp.resource("capabilities://server")
async def server_capabilities() -> str:
    """Expose server capabilities and features.

    Returns information about the orchestration server's capabilities, version,
    and supported features.

    Returns:
        JSON string with server metadata
    """
    capabilities = {
        "name": "mcp-orchestration",
        "version": "0.1.0",
        "wave": "Wave 1: Foundation",
        "capabilities": {
            "tools": ["list_clients", "list_profiles", "get_config", "diff_config"],
            "resources": ["capabilities://server", "capabilities://clients"],
            "prompts": [],
        },
        "features": {
            "content_addressing": True,
            "cryptographic_signing": True,
            "signature_algorithm": "Ed25519",
            "diff_reports": True,
            "profile_support": True,
        },
        "endpoints": {
            "verification_key_url": "https://mcp-orchestration.example.com/keys/verification_key.pem"
        },
    }
    return json.dumps(capabilities, indent=2)


@mcp.resource("capabilities://clients")
async def client_capabilities() -> str:
    """Expose client family capability matrix.

    Returns detailed capability information for each supported client family,
    showing which features and configurations are supported per client.

    Returns:
        JSON string with client capability matrix
    """
    # Build capabilities from registry
    registry_clients = _registry.list_clients()

    client_list = []
    for client_def in registry_clients:
        client_list.append(
            {
                "client_id": client_def.client_id,
                "display_name": client_def.display_name,
                "version_min": client_def.version_min,
                "version_max": client_def.version_max,
                "config_format": client_def.config_format,
                "supports": {
                    "environment_variables": client_def.capabilities.environment_variables,
                    "command_args": client_def.capabilities.command_args,
                    "working_directory": client_def.capabilities.working_directory,
                    "multiple_servers": client_def.capabilities.multiple_servers,
                },
                "limitations": {
                    "max_servers": client_def.limitations.max_servers,
                    "max_env_vars_per_server": client_def.limitations.max_env_vars_per_server,
                },
            }
        )

    capabilities = {"clients": client_list}
    return json.dumps(capabilities, indent=2)


# =============================================================================
# ENTRY POINT
# =============================================================================


def main() -> None:
    """Run the MCP orchestration server."""
    mcp.run()


if __name__ == "__main__":
    main()
