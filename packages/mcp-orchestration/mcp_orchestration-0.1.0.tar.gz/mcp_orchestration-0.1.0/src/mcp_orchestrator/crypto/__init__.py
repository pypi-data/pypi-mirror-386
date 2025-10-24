"""Cryptographic operations for MCP orchestration.

This module provides Ed25519 signing and verification for configuration artifacts.
"""

__all__ = ["ArtifactSigner", "verify_signature", "SigningError"]

from .signing import ArtifactSigner, SigningError, verify_signature
