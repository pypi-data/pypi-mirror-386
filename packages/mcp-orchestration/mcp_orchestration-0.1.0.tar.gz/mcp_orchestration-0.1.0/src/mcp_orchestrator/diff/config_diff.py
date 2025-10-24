"""Configuration diff algorithm for comparing MCP server configs.

This module implements server-level and field-level diff for MCP configurations,
detecting additions, removals, and modifications.
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ConfigChangeType(str, Enum):
    """Type of configuration change."""

    ADDED = "added"
    REMOVED = "removed"
    MODIFIED = "modified"
    UNCHANGED = "unchanged"


class ServerChange(BaseModel):
    """Details of a server configuration change."""

    server_id: str = Field(..., description="Server identifier")
    change_type: ConfigChangeType = Field(..., description="Type of change")
    changes: list[dict[str, Any]] = Field(
        default_factory=list, description="List of field-level changes"
    )


class DiffResult(BaseModel):
    """Result of comparing two configurations."""

    status: str = Field(
        ..., description="up-to-date, outdated, diverged, or unknown"
    )
    servers_added: list[str] = Field(
        default_factory=list, description="Server IDs added in remote"
    )
    servers_removed: list[str] = Field(
        default_factory=list, description="Server IDs removed in remote"
    )
    servers_modified: list[dict[str, Any]] = Field(
        default_factory=list, description="Servers with configuration changes"
    )
    servers_unchanged: list[str] = Field(
        default_factory=list, description="Server IDs with no changes"
    )
    total_changes: int = Field(0, description="Total number of changes")


def _diff_values(
    path: str, local_val: Any, remote_val: Any
) -> list[dict[str, Any]]:
    """Recursively diff two values and return list of changes.

    Args:
        path: JSON path to current value (e.g., 'command', 'args[0]')
        local_val: Local value
        remote_val: Remote value

    Returns:
        List of change dictionaries with path, old_value, new_value
    """
    changes = []

    # If values are equal, no changes
    if local_val == remote_val:
        return changes

    # If types differ, report as simple change
    if type(local_val) != type(remote_val):
        changes.append(
            {"path": path, "old_value": local_val, "new_value": remote_val}
        )
        return changes

    # Dict: Recursively diff fields
    if isinstance(local_val, dict) and isinstance(remote_val, dict):
        all_keys = set(local_val.keys()) | set(remote_val.keys())
        for key in all_keys:
            key_path = f"{path}.{key}" if path else key

            if key not in local_val:
                # Added in remote
                changes.append(
                    {"path": key_path, "old_value": None, "new_value": remote_val[key]}
                )
            elif key not in remote_val:
                # Removed in remote
                changes.append(
                    {"path": key_path, "old_value": local_val[key], "new_value": None}
                )
            else:
                # Potentially modified
                nested_changes = _diff_values(key_path, local_val[key], remote_val[key])
                changes.extend(nested_changes)

    # List: Compare element by element
    elif isinstance(local_val, list) and isinstance(remote_val, list):
        max_len = max(len(local_val), len(remote_val))
        for i in range(max_len):
            elem_path = f"{path}[{i}]"

            if i >= len(local_val):
                # Added in remote
                changes.append(
                    {"path": elem_path, "old_value": None, "new_value": remote_val[i]}
                )
            elif i >= len(remote_val):
                # Removed in remote
                changes.append(
                    {"path": elem_path, "old_value": local_val[i], "new_value": None}
                )
            else:
                # Potentially modified
                nested_changes = _diff_values(elem_path, local_val[i], remote_val[i])
                changes.extend(nested_changes)

    # Scalar: Simple value change
    else:
        changes.append({"path": path, "old_value": local_val, "new_value": remote_val})

    return changes


def compare_configs(
    local_payload: dict[str, Any], remote_payload: dict[str, Any]
) -> DiffResult:
    """Compare local and remote MCP configurations.

    Args:
        local_payload: Local configuration payload (must have 'mcpServers' key)
        remote_payload: Remote configuration payload (must have 'mcpServers' key)

    Returns:
        DiffResult with status and detailed changes

    Example:
        >>> local = {"mcpServers": {"filesystem": {"command": "npx"}}}
        >>> remote = {"mcpServers": {"filesystem": {"command": "node"}}}
        >>> result = compare_configs(local, remote)
        >>> print(result.status)  # "outdated"
        >>> print(result.total_changes)  # 1
    """
    # Extract mcpServers sections
    local_servers = local_payload.get("mcpServers", {})
    remote_servers = remote_payload.get("mcpServers", {})

    # Find added/removed/potentially modified servers
    local_ids = set(local_servers.keys())
    remote_ids = set(remote_servers.keys())

    added_ids = list(remote_ids - local_ids)
    removed_ids = list(local_ids - remote_ids)
    common_ids = local_ids & remote_ids

    # Check for modifications in common servers
    modified_servers = []
    unchanged_servers = []

    for server_id in common_ids:
        local_config = local_servers[server_id]
        remote_config = remote_servers[server_id]

        # Diff the server configurations
        changes = _diff_values("", local_config, remote_config)

        if changes:
            modified_servers.append(
                {"server_id": server_id, "changes": changes}
            )
        else:
            unchanged_servers.append(server_id)

    # Determine overall status
    total_changes = len(added_ids) + len(removed_ids) + len(modified_servers)

    if total_changes == 0:
        status = "up-to-date"
    elif removed_ids:
        # Local has servers not in remote = diverged
        status = "diverged"
    else:
        # Remote has additions/modifications but no removals = outdated
        status = "outdated"

    return DiffResult(
        status=status,
        servers_added=added_ids,
        servers_removed=removed_ids,
        servers_modified=modified_servers,
        servers_unchanged=unchanged_servers,
        total_changes=total_changes,
    )
