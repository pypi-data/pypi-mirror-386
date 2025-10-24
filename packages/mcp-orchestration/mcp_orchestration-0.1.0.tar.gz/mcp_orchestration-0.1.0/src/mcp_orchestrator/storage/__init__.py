"""Content-addressable storage for configuration artifacts.

This module provides storage and retrieval of signed configuration artifacts
using SHA-256 content addressing.
"""

__all__ = ["ArtifactStore", "ConfigArtifact", "StorageError"]

from .artifacts import ArtifactStore, ConfigArtifact, StorageError
