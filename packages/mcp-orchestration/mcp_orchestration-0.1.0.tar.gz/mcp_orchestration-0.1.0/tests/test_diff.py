"""Tests for configuration diff module."""

import pytest

from mcp_orchestrator.diff import ConfigChangeType, DiffResult, compare_configs


class TestConfigDiff:
    """Test configuration diff algorithm."""

    def test_identical_configs_are_up_to_date(self) -> None:
        """Test that identical configs show up-to-date status."""
        local = {
            "mcpServers": {
                "filesystem": {"command": "npx", "args": ["fs-server"]},
            }
        }
        remote = {
            "mcpServers": {
                "filesystem": {"command": "npx", "args": ["fs-server"]},
            }
        }

        result = compare_configs(local, remote)

        assert result.status == "up-to-date"
        assert result.total_changes == 0
        assert len(result.servers_added) == 0
        assert len(result.servers_removed) == 0
        assert len(result.servers_modified) == 0
        assert "filesystem" in result.servers_unchanged

    def test_detect_added_server(self) -> None:
        """Test detection of added servers in remote."""
        local = {
            "mcpServers": {
                "filesystem": {"command": "npx", "args": ["fs-server"]},
            }
        }
        remote = {
            "mcpServers": {
                "filesystem": {"command": "npx", "args": ["fs-server"]},
                "brave-search": {"command": "npx", "args": ["brave-search"]},
            }
        }

        result = compare_configs(local, remote)

        assert result.status == "outdated"
        assert result.total_changes == 1
        assert "brave-search" in result.servers_added
        assert len(result.servers_removed) == 0
        assert "filesystem" in result.servers_unchanged

    def test_detect_removed_server(self) -> None:
        """Test detection of removed servers in remote."""
        local = {
            "mcpServers": {
                "filesystem": {"command": "npx", "args": ["fs-server"]},
                "brave-search": {"command": "npx", "args": ["brave-search"]},
            }
        }
        remote = {
            "mcpServers": {
                "filesystem": {"command": "npx", "args": ["fs-server"]},
            }
        }

        result = compare_configs(local, remote)

        assert result.status == "diverged"  # Removals = diverged
        assert result.total_changes == 1
        assert len(result.servers_added) == 0
        assert "brave-search" in result.servers_removed
        assert "filesystem" in result.servers_unchanged

    def test_detect_modified_server_command(self) -> None:
        """Test detection of modified server command."""
        local = {
            "mcpServers": {
                "filesystem": {"command": "npx", "args": ["fs-server"]},
            }
        }
        remote = {
            "mcpServers": {
                "filesystem": {"command": "node", "args": ["fs-server"]},
            }
        }

        result = compare_configs(local, remote)

        assert result.status == "outdated"
        assert result.total_changes == 1
        assert len(result.servers_modified) == 1

        modified = result.servers_modified[0]
        assert modified["server_id"] == "filesystem"
        assert len(modified["changes"]) >= 1

        # Check that command change is detected
        change_paths = [c["path"] for c in modified["changes"]]
        assert "command" in change_paths

    def test_detect_modified_server_args(self) -> None:
        """Test detection of modified server arguments."""
        local = {
            "mcpServers": {
                "filesystem": {
                    "command": "npx",
                    "args": ["-y", "fs-server", "/old/path"],
                },
            }
        }
        remote = {
            "mcpServers": {
                "filesystem": {
                    "command": "npx",
                    "args": ["-y", "fs-server", "/new/path"],
                },
            }
        }

        result = compare_configs(local, remote)

        assert result.status == "outdated"
        assert len(result.servers_modified) == 1

        modified = result.servers_modified[0]
        changes = modified["changes"]

        # Should detect args[2] change
        arg_changes = [c for c in changes if "args[2]" in c["path"]]
        assert len(arg_changes) == 1
        assert arg_changes[0]["old_value"] == "/old/path"
        assert arg_changes[0]["new_value"] == "/new/path"

    def test_detect_added_env_var(self) -> None:
        """Test detection of added environment variable."""
        local = {
            "mcpServers": {
                "api-server": {
                    "command": "api",
                    "env": {"API_KEY": "key1"},
                },
            }
        }
        remote = {
            "mcpServers": {
                "api-server": {
                    "command": "api",
                    "env": {"API_KEY": "key1", "DEBUG": "true"},
                },
            }
        }

        result = compare_configs(local, remote)

        assert result.status == "outdated"
        assert len(result.servers_modified) == 1

        modified = result.servers_modified[0]
        changes = modified["changes"]

        # Should detect env.DEBUG addition
        debug_changes = [c for c in changes if "env.DEBUG" in c["path"]]
        assert len(debug_changes) == 1
        assert debug_changes[0]["old_value"] is None
        assert debug_changes[0]["new_value"] == "true"

    def test_multiple_changes(self) -> None:
        """Test detection of multiple changes at once."""
        local = {
            "mcpServers": {
                "filesystem": {"command": "npx", "args": ["fs"]},
            }
        }
        remote = {
            "mcpServers": {
                "filesystem": {"command": "node", "args": ["fs", "--verbose"]},
                "brave-search": {"command": "npx", "args": ["brave"]},
            }
        }

        result = compare_configs(local, remote)

        assert result.status == "outdated"
        assert result.total_changes == 2  # 1 added, 1 modified
        assert len(result.servers_added) == 1
        assert len(result.servers_modified) == 1
        assert "brave-search" in result.servers_added
        assert result.servers_modified[0]["server_id"] == "filesystem"

    def test_empty_local_config(self) -> None:
        """Test diff when local config is empty."""
        local = {"mcpServers": {}}
        remote = {
            "mcpServers": {
                "filesystem": {"command": "npx", "args": ["fs"]},
                "brave-search": {"command": "npx", "args": ["brave"]},
            }
        }

        result = compare_configs(local, remote)

        assert result.status == "outdated"
        assert len(result.servers_added) == 2
        assert "filesystem" in result.servers_added
        assert "brave-search" in result.servers_added
        assert len(result.servers_removed) == 0

    def test_empty_remote_config(self) -> None:
        """Test diff when remote config is empty."""
        local = {
            "mcpServers": {
                "filesystem": {"command": "npx", "args": ["fs"]},
            }
        }
        remote = {"mcpServers": {}}

        result = compare_configs(local, remote)

        assert result.status == "diverged"  # Local has servers not in remote
        assert len(result.servers_removed) == 1
        assert "filesystem" in result.servers_removed
        assert len(result.servers_added) == 0

    def test_diff_result_model(self) -> None:
        """Test DiffResult model creation."""
        result = DiffResult(
            status="outdated",
            servers_added=["new-server"],
            servers_removed=[],
            servers_modified=[{"server_id": "old-server", "changes": []}],
            servers_unchanged=["same-server"],
            total_changes=2,
        )

        assert result.status == "outdated"
        assert len(result.servers_added) == 1
        assert result.total_changes == 2

    def test_nested_field_changes(self) -> None:
        """Test detection of deeply nested field changes."""
        local = {
            "mcpServers": {
                "api": {
                    "command": "api",
                    "config": {"nested": {"deep": {"value": "old"}}},
                },
            }
        }
        remote = {
            "mcpServers": {
                "api": {
                    "command": "api",
                    "config": {"nested": {"deep": {"value": "new"}}},
                },
            }
        }

        result = compare_configs(local, remote)

        assert result.status == "outdated"
        assert len(result.servers_modified) == 1

        modified = result.servers_modified[0]
        changes = modified["changes"]

        # Should detect nested.deep.value change
        value_changes = [c for c in changes if "nested.deep.value" in c["path"]]
        assert len(value_changes) == 1
        assert value_changes[0]["old_value"] == "old"
        assert value_changes[0]["new_value"] == "new"
