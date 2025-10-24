"""Integration tests for complete MCP orchestration flow.

These tests validate that all components work together correctly:
- Storage, crypto, registry, diff
- End-to-end workflows
"""

from datetime import datetime, timezone
from pathlib import Path

import pytest

from mcp_orchestrator.crypto import ArtifactSigner, verify_signature
from mcp_orchestrator.diff import compare_configs
from mcp_orchestrator.registry import get_default_registry
from mcp_orchestrator.storage import ArtifactStore, ConfigArtifact


class TestEndToEndFlow:
    """Test complete end-to-end workflows."""

    @pytest.fixture
    def temp_storage(self, tmp_path: Path) -> Path:
        """Create temporary storage directory."""
        return tmp_path / "storage"

    @pytest.fixture
    def initialized_storage(self, temp_storage: Path) -> tuple[ArtifactStore, ArtifactSigner]:
        """Initialize storage with sample configs."""
        store = ArtifactStore(base_path=temp_storage)
        signer = ArtifactSigner.generate(key_id="test-integration")

        # Save keys
        key_path = temp_storage / "keys" / "signing_key.pem"
        signer.save_private_key(key_path)
        signer.save_public_key(temp_storage / "keys" / "verification_key.pem")

        # Create sample configs for claude-desktop/default
        payload = {
            "mcpServers": {
                "filesystem": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-filesystem", "/test"],
                }
            }
        }

        artifact_id = store.compute_artifact_id(payload)
        signature = signer.sign(payload)

        artifact = ConfigArtifact(
            artifact_id=artifact_id,
            client_id="claude-desktop",
            profile_id="default",
            created_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            payload=payload,
            signature=signature,
            signing_key_id=signer.key_id,
            metadata={"generator": "test"},
        )

        store.store(artifact)

        return store, signer

    def test_registry_integration(self) -> None:
        """Test registry provides expected client data."""
        registry = get_default_registry()

        clients = registry.list_clients()
        assert len(clients) >= 2  # claude-desktop, cursor

        client_ids = [c.client_id for c in clients]
        assert "claude-desktop" in client_ids
        assert "cursor" in client_ids

        # Verify claude-desktop has profiles
        claude_profiles = registry.get_profiles("claude-desktop")
        assert len(claude_profiles) >= 1
        profile_ids = [p.profile_id for p in claude_profiles]
        assert "default" in profile_ids

    def test_storage_retrieval_with_signature(
        self, initialized_storage: tuple[ArtifactStore, ArtifactSigner]
    ) -> None:
        """Test retrieving signed artifact from storage."""
        store, signer = initialized_storage

        # Retrieve artifact
        artifact = store.get("claude-desktop", "default")

        # Verify structure
        assert artifact.client_id == "claude-desktop"
        assert artifact.profile_id == "default"
        assert len(artifact.artifact_id) == 64
        assert "mcpServers" in artifact.payload

        # Verify signature
        public_key_path = store.base_path / "keys" / "verification_key.pem"
        is_valid = verify_signature(
            artifact.payload, artifact.signature, public_key_path
        )
        assert is_valid is True

    def test_diff_same_config_is_up_to_date(
        self, initialized_storage: tuple[ArtifactStore, ArtifactSigner]
    ) -> None:
        """Test diff with identical local/remote shows up-to-date."""
        store, signer = initialized_storage

        # Get current config
        artifact = store.get("claude-desktop", "default")

        # Diff against itself
        result = compare_configs(artifact.payload, artifact.payload)

        assert result.status == "up-to-date"
        assert result.total_changes == 0
        assert len(result.servers_added) == 0
        assert len(result.servers_removed) == 0
        assert len(result.servers_modified) == 0

    def test_diff_modified_config_is_outdated(
        self, initialized_storage: tuple[ArtifactStore, ArtifactSigner]
    ) -> None:
        """Test diff detects modifications."""
        store, signer = initialized_storage

        # Get current config
        artifact = store.get("claude-desktop", "default")

        # Modify local payload (deep copy to avoid mutating artifact)
        import copy
        local_payload = copy.deepcopy(artifact.payload)
        local_payload["mcpServers"]["filesystem"]["args"] = [
            "-y",
            "@modelcontextprotocol/server-filesystem",
            "/modified",
        ]

        # Diff
        result = compare_configs(local_payload, artifact.payload)

        assert result.status == "outdated"
        assert result.total_changes >= 1
        assert len(result.servers_modified) >= 1

        # Should show filesystem as modified
        modified_servers = [s["server_id"] for s in result.servers_modified]
        assert "filesystem" in modified_servers

    def test_diff_with_added_server(
        self, initialized_storage: tuple[ArtifactStore, ArtifactSigner]
    ) -> None:
        """Test diff detects added servers in remote."""
        store, signer = initialized_storage

        # Get current config
        artifact = store.get("claude-desktop", "default")

        # Remove a server from local
        local_payload = {"mcpServers": {}}  # Empty local

        # Diff
        result = compare_configs(local_payload, artifact.payload)

        assert result.status == "outdated"
        assert len(result.servers_added) >= 1
        assert "filesystem" in result.servers_added

    def test_signature_verification_end_to_end(
        self, initialized_storage: tuple[ArtifactStore, ArtifactSigner]
    ) -> None:
        """Test complete signature verification workflow."""
        store, signer = initialized_storage

        # Get config
        artifact = store.get("claude-desktop", "default")

        # Verify signature with public key
        public_key_path = store.base_path / "keys" / "verification_key.pem"
        is_valid = verify_signature(
            artifact.payload, artifact.signature, public_key_path
        )

        assert is_valid is True

        # Tamper with payload and verify fails
        tampered_payload = artifact.payload.copy()
        tampered_payload["mcpServers"]["TAMPERED"] = {"command": "evil"}

        is_valid_tampered = verify_signature(
            tampered_payload, artifact.signature, public_key_path
        )

        assert is_valid_tampered is False

    def test_complete_workflow_generate_sign_store_retrieve_verify(
        self, temp_storage: Path
    ) -> None:
        """Test complete workflow from generation to verification."""
        # 1. Initialize components
        store = ArtifactStore(base_path=temp_storage)
        signer = ArtifactSigner.generate(key_id="workflow-test")

        key_path = temp_storage / "keys" / "signing_key.pem"
        public_key_path = temp_storage / "keys" / "verification_key.pem"
        signer.save_private_key(key_path)
        signer.save_public_key(public_key_path)

        # 2. Generate config
        payload = {
            "mcpServers": {
                "test-server": {
                    "command": "test",
                    "args": ["--arg"],
                }
            }
        }

        # 3. Compute artifact ID
        artifact_id = store.compute_artifact_id(payload)

        # 4. Sign
        signature = signer.sign(payload)

        # 5. Create artifact
        artifact = ConfigArtifact(
            artifact_id=artifact_id,
            client_id="test-client",
            profile_id="test-profile",
            created_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            payload=payload,
            signature=signature,
            signing_key_id=signer.key_id,
            metadata={"test": "workflow"},
        )

        # 6. Store
        store.store(artifact)

        # 7. Retrieve
        retrieved = store.get("test-client", "test-profile")

        # 8. Verify
        assert retrieved.artifact_id == artifact_id
        assert retrieved.payload == payload

        is_valid = verify_signature(retrieved.payload, retrieved.signature, public_key_path)
        assert is_valid is True


class TestCliIntegration:
    """Test CLI init command integration."""

    def test_init_creates_artifacts_and_keys(self, tmp_path: Path) -> None:
        """Test that init command creates artifacts and signing keys."""
        storage_path = tmp_path / "cli-test-storage"

        # Run init via Click testing
        from click.testing import CliRunner
        from mcp_orchestrator.cli_init import init_configs

        runner = CliRunner()
        result = runner.invoke(
            init_configs, ["--storage-path", str(storage_path)]
        )

        assert result.exit_code == 0
        assert "Created: 3 configurations" in result.output

        # Verify artifacts directory exists and has files
        artifacts_dir = storage_path / "artifacts"
        assert artifacts_dir.exists()
        artifacts = list(artifacts_dir.glob("*.json"))
        assert len(artifacts) == 3

        # Verify keys directory exists and has keys
        keys_dir = storage_path / "keys"
        assert (keys_dir / "signing_key.pem").exists()
        assert (keys_dir / "verification_key.pem").exists()

        # Verify indexes exist
        assert (storage_path / "index" / "claude-desktop" / "default.json").exists()
        assert (storage_path / "index" / "claude-desktop" / "dev.json").exists()
        assert (storage_path / "index" / "cursor" / "default.json").exists()

    def test_init_regenerate_flag(self, tmp_path: Path) -> None:
        """Test that --regenerate recreates existing configs."""
        storage_path = tmp_path / "cli-regen-test"

        from click.testing import CliRunner
        from mcp_orchestrator.cli_init import init_configs

        runner = CliRunner()

        # First run
        result1 = runner.invoke(
            init_configs, ["--storage-path", str(storage_path)]
        )
        assert result1.exit_code == 0
        assert "Created: 3" in result1.output

        # Second run without --regenerate (should skip)
        result2 = runner.invoke(
            init_configs, ["--storage-path", str(storage_path)]
        )
        assert result2.exit_code == 0
        assert "Skipped: 3" in result2.output
        assert "Created: 0" in result2.output

        # Third run with --regenerate
        result3 = runner.invoke(
            init_configs, ["--storage-path", str(storage_path), "--regenerate"]
        )
        assert result3.exit_code == 0
        assert "Created: 3" in result3.output
