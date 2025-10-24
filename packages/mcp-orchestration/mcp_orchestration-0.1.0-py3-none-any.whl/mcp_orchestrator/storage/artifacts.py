"""Content-addressable artifact storage.

This module implements storage for signed configuration artifacts using:
- SHA-256 content addressing (FR-4)
- Immutable artifact storage
- Profile-based indexing

Storage layout:
~/.mcp-orchestration/
├── artifacts/
│   └── {artifact_id}.json      # Content-addressable artifacts
├── index/
│   └── {client_id}/
│       └── {profile_id}.json   # Points to latest artifact_id
└── keys/
    ├── signing_key.pem         # Private key (server only)
    └── verification_key.pem    # Public key (for distribution)
"""

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class ConfigArtifact(BaseModel):
    """Signed configuration artifact.

    This model represents a complete, signed configuration artifact that can be
    stored and retrieved from the artifact store.

    Fields match the get_config tool output schema from MCP_SERVER_SPEC.md.
    """

    artifact_id: str = Field(
        ...,
        description="SHA-256 hash of payload (content-addressable ID)",
        pattern=r"^[a-f0-9]{64}$",
    )
    client_id: str = Field(..., description="Client family identifier")
    profile_id: str = Field(..., description="Profile identifier")
    created_at: str = Field(..., description="ISO 8601 timestamp")
    payload: dict[str, Any] = Field(
        ..., description="MCP client configuration (mcpServers structure)"
    )
    signature: str = Field(..., description="Base64-encoded Ed25519 signature")
    signing_key_id: str = Field(..., description="Identifier for public key")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Generator metadata"
    )

    def model_dump_json(self, **kwargs: Any) -> str:
        """Serialize to canonical JSON."""
        # Override to ensure consistent ordering
        kwargs.setdefault("by_alias", True)
        kwargs.setdefault("exclude_none", False)
        return super().model_dump_json(**kwargs)


class ProfileIndex(BaseModel):
    """Index entry for a client/profile combination."""

    client_id: str
    profile_id: str
    latest_artifact_id: str
    updated_at: str  # ISO 8601


class StorageError(Exception):
    """Raised when storage operations fail."""

    pass


class ArtifactStore:
    """Content-addressable storage for configuration artifacts.

    This class manages:
    1. Artifact storage (immutable, content-addressed by SHA-256)
    2. Profile indexes (mutable, point to latest artifact)
    3. Artifact retrieval by ID or client/profile

    Example:
        >>> store = ArtifactStore()
        >>> artifact = ConfigArtifact(
        ...     artifact_id="abc123...",
        ...     client_id="claude-desktop",
        ...     profile_id="default",
        ...     payload={"mcpServers": {...}},
        ...     signature="...",
        ...     signing_key_id="prod-2025",
        ...     created_at="2025-10-23T14:30:00Z"
        ... )
        >>> store.store(artifact)
        >>> retrieved = store.get("claude-desktop", "default")
    """

    def __init__(self, base_path: str | Path | None = None):
        """Initialize artifact store.

        Args:
            base_path: Base directory for storage (defaults to ~/.mcp-orchestration)
        """
        if base_path is None:
            base_path = Path.home() / ".mcp-orchestration"

        self.base_path = Path(base_path)
        self.artifacts_dir = self.base_path / "artifacts"
        self.index_dir = self.base_path / "index"
        self.keys_dir = self.base_path / "keys"

        # Ensure directories exist
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self.keys_dir.mkdir(parents=True, exist_ok=True)

    def compute_artifact_id(self, payload: dict[str, Any]) -> str:
        """Compute SHA-256 artifact ID from payload.

        This must match the canonicalization used for signing:
        - Keys sorted alphabetically
        - No whitespace (compact separators)
        - UTF-8 encoding

        Args:
            payload: Configuration payload

        Returns:
            64-character hexadecimal SHA-256 hash
        """
        canonical_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        canonical_bytes = canonical_json.encode("utf-8")
        return hashlib.sha256(canonical_bytes).hexdigest()

    def verify_artifact_id(self, artifact: ConfigArtifact) -> bool:
        """Verify that artifact_id matches payload hash.

        Args:
            artifact: Artifact to verify

        Returns:
            True if artifact_id matches computed hash, False otherwise
        """
        computed_id = self.compute_artifact_id(artifact.payload)
        return computed_id == artifact.artifact_id

    def store(self, artifact: ConfigArtifact, update_index: bool = True) -> None:
        """Store artifact and optionally update profile index.

        Args:
            artifact: Artifact to store
            update_index: Whether to update the profile index (default True)

        Raises:
            StorageError: If artifact_id doesn't match payload or storage fails
        """
        # Verify artifact ID matches payload
        if not self.verify_artifact_id(artifact):
            computed = self.compute_artifact_id(artifact.payload)
            raise StorageError(
                f"Artifact ID mismatch: claimed {artifact.artifact_id}, "
                f"computed {computed}"
            )

        try:
            # Store artifact (idempotent - same artifact_id always has same content)
            artifact_path = self.artifacts_dir / f"{artifact.artifact_id}.json"
            artifact_json = artifact.model_dump_json(indent=2)
            artifact_path.write_text(artifact_json, encoding="utf-8")

            # Update profile index if requested
            if update_index:
                self._update_index(
                    artifact.client_id, artifact.profile_id, artifact.artifact_id
                )

        except Exception as e:
            raise StorageError(f"Failed to store artifact: {e}")

    def _update_index(
        self, client_id: str, profile_id: str, artifact_id: str
    ) -> None:
        """Update profile index to point to latest artifact.

        Args:
            client_id: Client family identifier
            profile_id: Profile identifier
            artifact_id: Artifact ID to set as latest
        """
        # Ensure client directory exists
        client_dir = self.index_dir / client_id
        client_dir.mkdir(parents=True, exist_ok=True)

        # Write index entry
        index_path = client_dir / f"{profile_id}.json"
        index_entry = ProfileIndex(
            client_id=client_id,
            profile_id=profile_id,
            latest_artifact_id=artifact_id,
            updated_at=datetime.utcnow().isoformat() + "Z",
        )

        index_path.write_text(index_entry.model_dump_json(indent=2), encoding="utf-8")

    def get_by_id(self, artifact_id: str) -> ConfigArtifact:
        """Retrieve artifact by content-addressable ID.

        Args:
            artifact_id: SHA-256 hash of artifact

        Returns:
            ConfigArtifact

        Raises:
            StorageError: If artifact not found or cannot be read
        """
        artifact_path = self.artifacts_dir / f"{artifact_id}.json"

        if not artifact_path.exists():
            raise StorageError(f"Artifact not found: {artifact_id}")

        try:
            artifact_json = artifact_path.read_text(encoding="utf-8")
            return ConfigArtifact.model_validate_json(artifact_json)
        except Exception as e:
            raise StorageError(f"Failed to load artifact {artifact_id}: {e}")

    def get(self, client_id: str, profile_id: str = "default") -> ConfigArtifact:
        """Retrieve latest artifact for client/profile.

        Args:
            client_id: Client family identifier
            profile_id: Profile identifier (defaults to 'default')

        Returns:
            ConfigArtifact

        Raises:
            StorageError: If profile index or artifact not found
        """
        # Read profile index
        index_path = self.index_dir / client_id / f"{profile_id}.json"

        if not index_path.exists():
            raise StorageError(
                f"Profile index not found: {client_id}/{profile_id}. "
                f"Available clients: {self.list_clients()}"
            )

        try:
            index_json = index_path.read_text(encoding="utf-8")
            index_entry = ProfileIndex.model_validate_json(index_json)

            # Retrieve artifact by ID
            return self.get_by_id(index_entry.latest_artifact_id)

        except Exception as e:
            raise StorageError(f"Failed to retrieve artifact for {client_id}/{profile_id}: {e}")

    def list_clients(self) -> list[str]:
        """List all client IDs with stored configurations.

        Returns:
            List of client_id strings
        """
        if not self.index_dir.exists():
            return []

        return [
            d.name for d in self.index_dir.iterdir() if d.is_dir() and not d.name.startswith(".")
        ]

    def list_profiles(self, client_id: str) -> list[str]:
        """List all profile IDs for a client.

        Args:
            client_id: Client family identifier

        Returns:
            List of profile_id strings

        Raises:
            StorageError: If client not found
        """
        client_dir = self.index_dir / client_id

        if not client_dir.exists():
            raise StorageError(
                f"Client not found: {client_id}. "
                f"Available: {self.list_clients()}"
            )

        return [
            p.stem for p in client_dir.glob("*.json") if p.is_file()
        ]

    def get_profile_metadata(self, client_id: str, profile_id: str) -> ProfileIndex:
        """Get profile index metadata without loading artifact.

        Args:
            client_id: Client family identifier
            profile_id: Profile identifier

        Returns:
            ProfileIndex with latest_artifact_id and updated_at

        Raises:
            StorageError: If profile index not found
        """
        index_path = self.index_dir / client_id / f"{profile_id}.json"

        if not index_path.exists():
            raise StorageError(f"Profile not found: {client_id}/{profile_id}")

        try:
            index_json = index_path.read_text(encoding="utf-8")
            return ProfileIndex.model_validate_json(index_json)
        except Exception as e:
            raise StorageError(f"Failed to read profile metadata: {e}")

    def exists(self, artifact_id: str) -> bool:
        """Check if artifact exists in storage.

        Args:
            artifact_id: SHA-256 hash of artifact

        Returns:
            True if artifact exists, False otherwise
        """
        artifact_path = self.artifacts_dir / f"{artifact_id}.json"
        return artifact_path.exists()
