"""Tests for content-addressable storage module."""

from datetime import datetime
from pathlib import Path

import pytest

from mcp_orchestrator.storage import ArtifactStore, ConfigArtifact, StorageError


class TestArtifactStore:
    """Test content-addressable artifact storage."""

    @pytest.fixture
    def store(self, tmp_path: Path) -> ArtifactStore:
        """Create artifact store in temp directory."""
        return ArtifactStore(base_path=tmp_path)

    @pytest.fixture
    def sample_artifact(self) -> ConfigArtifact:
        """Create sample configuration artifact."""
        payload = {
            "mcpServers": {
                "filesystem": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-filesystem"],
                }
            }
        }

        # Compute artifact ID
        import hashlib
        import json

        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        artifact_id = hashlib.sha256(canonical.encode()).hexdigest()

        return ConfigArtifact(
            artifact_id=artifact_id,
            client_id="claude-desktop",
            profile_id="default",
            created_at=datetime.utcnow().isoformat() + "Z",
            payload=payload,
            signature="VGVzdFNpZ25hdHVyZQ==",
            signing_key_id="test-key",
            metadata={"generator": "test"},
        )

    def test_init_creates_directories(self, tmp_path: Path) -> None:
        """Test that initialization creates required directories."""
        store = ArtifactStore(base_path=tmp_path)

        assert (tmp_path / "artifacts").exists()
        assert (tmp_path / "index").exists()
        assert (tmp_path / "keys").exists()

    def test_compute_artifact_id(self, store: ArtifactStore) -> None:
        """Test computing SHA-256 artifact ID from payload."""
        payload = {"b": 2, "a": 1}

        artifact_id = store.compute_artifact_id(payload)

        # Should be 64-character hex string
        assert len(artifact_id) == 64
        assert all(c in "0123456789abcdef" for c in artifact_id)

    def test_compute_artifact_id_deterministic(self, store: ArtifactStore) -> None:
        """Test that artifact ID computation is deterministic."""
        payload = {"mcpServers": {"filesystem": {"command": "npx"}}}

        id1 = store.compute_artifact_id(payload)
        id2 = store.compute_artifact_id(payload)

        assert id1 == id2

    def test_compute_artifact_id_canonical(self, store: ArtifactStore) -> None:
        """Test that artifact ID is same regardless of key order."""
        payload1 = {"b": 2, "a": 1}
        payload2 = {"a": 1, "b": 2}

        id1 = store.compute_artifact_id(payload1)
        id2 = store.compute_artifact_id(payload2)

        assert id1 == id2

    def test_verify_artifact_id_valid(
        self, store: ArtifactStore, sample_artifact: ConfigArtifact
    ) -> None:
        """Test verifying valid artifact ID."""
        is_valid = store.verify_artifact_id(sample_artifact)
        assert is_valid is True

    def test_verify_artifact_id_invalid(
        self, store: ArtifactStore, sample_artifact: ConfigArtifact
    ) -> None:
        """Test verifying invalid artifact ID."""
        # Tamper with artifact ID
        sample_artifact.artifact_id = "0" * 64

        is_valid = store.verify_artifact_id(sample_artifact)
        assert is_valid is False

    def test_store_artifact(
        self, store: ArtifactStore, sample_artifact: ConfigArtifact
    ) -> None:
        """Test storing an artifact."""
        store.store(sample_artifact)

        # Artifact file should exist
        artifact_path = store.artifacts_dir / f"{sample_artifact.artifact_id}.json"
        assert artifact_path.exists()

        # Index should be updated
        index_path = (
            store.index_dir
            / sample_artifact.client_id
            / f"{sample_artifact.profile_id}.json"
        )
        assert index_path.exists()

    def test_store_artifact_invalid_id(
        self, store: ArtifactStore, sample_artifact: ConfigArtifact
    ) -> None:
        """Test storing artifact with invalid ID raises error."""
        # Tamper with artifact ID
        sample_artifact.artifact_id = "0" * 64

        with pytest.raises(StorageError, match="Artifact ID mismatch"):
            store.store(sample_artifact)

    def test_get_artifact_by_id(
        self, store: ArtifactStore, sample_artifact: ConfigArtifact
    ) -> None:
        """Test retrieving artifact by content-addressable ID."""
        store.store(sample_artifact)

        retrieved = store.get_by_id(sample_artifact.artifact_id)

        assert retrieved.artifact_id == sample_artifact.artifact_id
        assert retrieved.client_id == sample_artifact.client_id
        assert retrieved.payload == sample_artifact.payload
        assert retrieved.signature == sample_artifact.signature

    def test_get_artifact_by_id_not_found(self, store: ArtifactStore) -> None:
        """Test retrieving nonexistent artifact raises error."""
        fake_id = "a" * 64

        with pytest.raises(StorageError, match="not found"):
            store.get_by_id(fake_id)

    def test_get_artifact_by_client_profile(
        self, store: ArtifactStore, sample_artifact: ConfigArtifact
    ) -> None:
        """Test retrieving latest artifact for client/profile."""
        store.store(sample_artifact)

        retrieved = store.get(sample_artifact.client_id, sample_artifact.profile_id)

        assert retrieved.artifact_id == sample_artifact.artifact_id
        assert retrieved.client_id == sample_artifact.client_id
        assert retrieved.profile_id == sample_artifact.profile_id

    def test_get_artifact_profile_not_found(self, store: ArtifactStore) -> None:
        """Test retrieving nonexistent profile raises error."""
        with pytest.raises(StorageError, match="not found"):
            store.get("unknown-client", "default")

    def test_list_clients_empty(self, store: ArtifactStore) -> None:
        """Test listing clients when none exist."""
        clients = store.list_clients()
        assert clients == []

    def test_list_clients(
        self, store: ArtifactStore, sample_artifact: ConfigArtifact
    ) -> None:
        """Test listing clients after storing artifacts."""
        store.store(sample_artifact)

        # Store another client
        artifact2 = sample_artifact.model_copy()
        artifact2.client_id = "cursor"
        store.store(artifact2)

        clients = store.list_clients()
        assert set(clients) == {"claude-desktop", "cursor"}

    def test_list_profiles(
        self, store: ArtifactStore, sample_artifact: ConfigArtifact
    ) -> None:
        """Test listing profiles for a client."""
        # Store artifacts for multiple profiles
        store.store(sample_artifact)

        artifact_dev = sample_artifact.model_copy()
        artifact_dev.profile_id = "dev"
        # Need to recompute artifact_id since we changed profile_id
        # But payload is same, so ID should be same
        store.store(artifact_dev)

        profiles = store.list_profiles(sample_artifact.client_id)
        assert set(profiles) == {"default", "dev"}

    def test_list_profiles_client_not_found(self, store: ArtifactStore) -> None:
        """Test listing profiles for nonexistent client raises error."""
        with pytest.raises(StorageError, match="not found"):
            store.list_profiles("unknown-client")

    def test_get_profile_metadata(
        self, store: ArtifactStore, sample_artifact: ConfigArtifact
    ) -> None:
        """Test getting profile metadata without loading artifact."""
        store.store(sample_artifact)

        metadata = store.get_profile_metadata(
            sample_artifact.client_id, sample_artifact.profile_id
        )

        assert metadata.client_id == sample_artifact.client_id
        assert metadata.profile_id == sample_artifact.profile_id
        assert metadata.latest_artifact_id == sample_artifact.artifact_id
        assert metadata.updated_at  # Should have timestamp

    def test_exists(self, store: ArtifactStore, sample_artifact: ConfigArtifact) -> None:
        """Test checking if artifact exists."""
        assert store.exists(sample_artifact.artifact_id) is False

        store.store(sample_artifact)

        assert store.exists(sample_artifact.artifact_id) is True

    def test_store_idempotent(
        self, store: ArtifactStore, sample_artifact: ConfigArtifact
    ) -> None:
        """Test that storing same artifact multiple times is idempotent."""
        store.store(sample_artifact)
        store.store(sample_artifact)  # Should not raise error

        # Should only have one artifact file
        artifacts = list(store.artifacts_dir.glob("*.json"))
        assert len(artifacts) == 1

    def test_update_index_only(
        self, store: ArtifactStore, sample_artifact: ConfigArtifact
    ) -> None:
        """Test storing artifact without updating index."""
        # Store without updating index
        store.store(sample_artifact, update_index=False)

        # Artifact should exist
        assert store.exists(sample_artifact.artifact_id) is True

        # Index should not exist
        index_path = (
            store.index_dir
            / sample_artifact.client_id
            / f"{sample_artifact.profile_id}.json"
        )
        assert not index_path.exists()

    def test_profile_index_updates(
        self, store: ArtifactStore, sample_artifact: ConfigArtifact
    ) -> None:
        """Test that profile index updates to latest artifact."""
        # Store first version
        store.store(sample_artifact)

        # Create new version (different payload = different artifact_id)
        artifact_v2 = sample_artifact.model_copy()
        artifact_v2.payload["mcpServers"]["new-server"] = {"command": "test"}
        artifact_v2.artifact_id = store.compute_artifact_id(artifact_v2.payload)

        store.store(artifact_v2)

        # Index should point to v2
        metadata = store.get_profile_metadata(
            sample_artifact.client_id, sample_artifact.profile_id
        )
        assert metadata.latest_artifact_id == artifact_v2.artifact_id

        # Both artifacts should still exist in storage
        assert store.exists(sample_artifact.artifact_id) is True
        assert store.exists(artifact_v2.artifact_id) is True
