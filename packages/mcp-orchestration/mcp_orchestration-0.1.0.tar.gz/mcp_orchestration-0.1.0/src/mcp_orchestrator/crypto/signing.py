"""Ed25519 signing and verification for configuration artifacts.

This module implements cryptographic signing using Ed25519 (RFC 8032) to ensure
artifact integrity and authenticity (AC-1).

Key Concepts:
- Signing: Server signs artifacts with private key
- Verification: Clients verify signatures with public key
- Canonical JSON: Sort keys, no whitespace for deterministic hashing
"""

import base64
import json
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)


class SigningError(Exception):
    """Raised when signing or verification fails."""

    pass


class ArtifactSigner:
    """Ed25519 signer for configuration artifacts.

    This class handles:
    1. Private key loading/generation
    2. Payload canonicalization (deterministic JSON)
    3. Signature generation
    4. Public key export for distribution

    Example:
        >>> signer = ArtifactSigner.from_file("signing_key.pem")
        >>> payload = {"mcpServers": {...}}
        >>> signature = signer.sign(payload)
        >>> artifact = {
        ...     "payload": payload,
        ...     "signature": signature,
        ...     "signing_key_id": "prod-2025"
        ... }
    """

    def __init__(self, private_key: Ed25519PrivateKey, key_id: str = "default"):
        """Initialize signer with private key.

        Args:
            private_key: Ed25519 private key for signing
            key_id: Identifier for this signing key (e.g., 'prod-2025')
        """
        self.private_key = private_key
        self.key_id = key_id

    @classmethod
    def from_file(cls, path: str | Path, key_id: str = "default") -> "ArtifactSigner":
        """Load private key from PEM file.

        Args:
            path: Path to PEM-encoded private key file
            key_id: Identifier for this signing key

        Returns:
            ArtifactSigner instance

        Raises:
            SigningError: If key file cannot be read or parsed
        """
        try:
            key_path = Path(path)
            key_bytes = key_path.read_bytes()

            private_key = serialization.load_pem_private_key(
                key_bytes,
                password=None,
            )

            if not isinstance(private_key, Ed25519PrivateKey):
                raise SigningError(f"Key at {path} is not an Ed25519 private key")

            return cls(private_key, key_id=key_id)

        except FileNotFoundError:
            raise SigningError(f"Signing key not found: {path}")
        except Exception as e:
            raise SigningError(f"Failed to load signing key: {e}")

    @classmethod
    def generate(cls, key_id: str = "default") -> "ArtifactSigner":
        """Generate new Ed25519 key pair.

        Args:
            key_id: Identifier for this signing key

        Returns:
            ArtifactSigner instance with newly generated key
        """
        private_key = Ed25519PrivateKey.generate()
        return cls(private_key, key_id=key_id)

    def save_private_key(self, path: str | Path) -> None:
        """Save private key to PEM file.

        Args:
            path: Where to save the private key

        Raises:
            SigningError: If key cannot be written
        """
        try:
            key_path = Path(path)
            key_path.parent.mkdir(parents=True, exist_ok=True)

            pem = self.private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            )

            key_path.write_bytes(pem)
            key_path.chmod(0o600)  # Read/write for owner only

        except Exception as e:
            raise SigningError(f"Failed to save private key: {e}")

    def save_public_key(self, path: str | Path) -> None:
        """Save public verification key to PEM file.

        This key should be distributed to clients for signature verification.

        Args:
            path: Where to save the public key

        Raises:
            SigningError: If key cannot be written
        """
        try:
            key_path = Path(path)
            key_path.parent.mkdir(parents=True, exist_ok=True)

            public_key = self.private_key.public_key()
            pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )

            key_path.write_bytes(pem)

        except Exception as e:
            raise SigningError(f"Failed to save public key: {e}")

    def sign(self, payload: dict[str, Any]) -> str:
        """Sign a configuration payload.

        The payload is canonicalized to deterministic JSON before signing:
        - Keys sorted alphabetically
        - No whitespace (compact separators)
        - UTF-8 encoding

        Args:
            payload: Configuration payload to sign (typically mcpServers object)

        Returns:
            Base64-encoded signature string

        Raises:
            SigningError: If signing fails
        """
        try:
            # Canonicalize payload to deterministic JSON
            canonical_json = json.dumps(
                payload, sort_keys=True, separators=(",", ":")
            )
            canonical_bytes = canonical_json.encode("utf-8")

            # Sign
            signature_bytes = self.private_key.sign(canonical_bytes)

            # Encode as Base64
            signature_b64 = base64.b64encode(signature_bytes).decode("ascii")

            return signature_b64

        except Exception as e:
            raise SigningError(f"Failed to sign payload: {e}")


def verify_signature(
    payload: dict[str, Any],
    signature_b64: str,
    public_key_path: str | Path,
) -> bool:
    """Verify an artifact signature.

    Args:
        payload: Configuration payload (same structure as was signed)
        signature_b64: Base64-encoded signature string
        public_key_path: Path to PEM-encoded public verification key

    Returns:
        True if signature is valid, False otherwise

    Raises:
        SigningError: If verification key cannot be loaded
    """
    try:
        # Load public key
        key_path = Path(public_key_path)
        key_bytes = key_path.read_bytes()

        public_key = serialization.load_pem_public_key(key_bytes)
        if not isinstance(public_key, Ed25519PublicKey):
            raise SigningError(
                f"Key at {public_key_path} is not an Ed25519 public key"
            )

        # Canonicalize payload
        canonical_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        canonical_bytes = canonical_json.encode("utf-8")

        # Decode signature
        signature_bytes = base64.b64decode(signature_b64)

        # Verify
        try:
            public_key.verify(signature_bytes, canonical_bytes)
            return True
        except Exception:
            return False

    except FileNotFoundError:
        raise SigningError(f"Verification key not found: {public_key_path}")
    except Exception as e:
        raise SigningError(f"Failed to verify signature: {e}")
