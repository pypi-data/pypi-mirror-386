"""Tests for cryptographic signing module."""

import base64
import json
from pathlib import Path

import pytest

from mcp_orchestrator.crypto import ArtifactSigner, SigningError, verify_signature


class TestArtifactSigner:
    """Test Ed25519 signing operations."""

    def test_generate_signer(self) -> None:
        """Test generating new signing key."""
        signer = ArtifactSigner.generate(key_id="test-key")
        assert signer.key_id == "test-key"
        assert signer.private_key is not None

    def test_sign_payload(self) -> None:
        """Test signing a configuration payload."""
        signer = ArtifactSigner.generate(key_id="test")
        payload = {"mcpServers": {"filesystem": {"command": "npx"}}}

        signature = signer.sign(payload)

        # Signature should be base64-encoded
        assert isinstance(signature, str)
        assert len(signature) > 0

        # Should be valid base64
        signature_bytes = base64.b64decode(signature)
        assert len(signature_bytes) == 64  # Ed25519 signatures are 64 bytes

    def test_sign_deterministic(self) -> None:
        """Test that signing same payload produces same signature."""
        signer = ArtifactSigner.generate(key_id="test")
        payload = {"mcpServers": {"filesystem": {"command": "npx"}}}

        sig1 = signer.sign(payload)
        sig2 = signer.sign(payload)

        assert sig1 == sig2

    def test_sign_canonical_json(self) -> None:
        """Test that signing uses canonical JSON (key order doesn't matter)."""
        signer = ArtifactSigner.generate(key_id="test")

        # Two payloads with same data but different key orders
        payload1 = {"b": 2, "a": 1}
        payload2 = {"a": 1, "b": 2}

        sig1 = signer.sign(payload1)
        sig2 = signer.sign(payload2)

        # Should produce identical signatures
        assert sig1 == sig2

    def test_save_and_load_private_key(self, tmp_path: Path) -> None:
        """Test saving and loading private key."""
        key_path = tmp_path / "signing_key.pem"

        # Generate and save
        signer1 = ArtifactSigner.generate(key_id="test")
        signer1.save_private_key(key_path)

        assert key_path.exists()

        # Load and verify same key
        signer2 = ArtifactSigner.from_file(key_path, key_id="test")

        payload = {"test": "data"}
        sig1 = signer1.sign(payload)
        sig2 = signer2.sign(payload)

        assert sig1 == sig2

    def test_save_public_key(self, tmp_path: Path) -> None:
        """Test exporting public verification key."""
        public_key_path = tmp_path / "verification_key.pem"

        signer = ArtifactSigner.generate(key_id="test")
        signer.save_public_key(public_key_path)

        assert public_key_path.exists()

        # Public key should be PEM-encoded
        content = public_key_path.read_text()
        assert "BEGIN PUBLIC KEY" in content
        assert "END PUBLIC KEY" in content

    def test_load_nonexistent_key(self, tmp_path: Path) -> None:
        """Test loading nonexistent key raises error."""
        with pytest.raises(SigningError, match="not found"):
            ArtifactSigner.from_file(tmp_path / "nonexistent.pem")

    def test_private_key_permissions(self, tmp_path: Path) -> None:
        """Test that private key is saved with restricted permissions."""
        key_path = tmp_path / "signing_key.pem"

        signer = ArtifactSigner.generate(key_id="test")
        signer.save_private_key(key_path)

        # Check permissions (owner read/write only)
        stat = key_path.stat()
        assert stat.st_mode & 0o777 == 0o600


class TestVerifySignature:
    """Test signature verification."""

    def test_verify_valid_signature(self, tmp_path: Path) -> None:
        """Test verifying a valid signature."""
        public_key_path = tmp_path / "verification_key.pem"

        # Generate key pair and sign
        signer = ArtifactSigner.generate(key_id="test")
        signer.save_public_key(public_key_path)

        payload = {"mcpServers": {"filesystem": {"command": "npx"}}}
        signature = signer.sign(payload)

        # Verify signature
        is_valid = verify_signature(payload, signature, public_key_path)
        assert is_valid is True

    def test_verify_invalid_signature(self, tmp_path: Path) -> None:
        """Test verifying an invalid signature."""
        public_key_path = tmp_path / "verification_key.pem"

        signer = ArtifactSigner.generate(key_id="test")
        signer.save_public_key(public_key_path)

        payload = {"mcpServers": {"filesystem": {"command": "npx"}}}
        signature = signer.sign(payload)

        # Tamper with payload
        tampered_payload = {"mcpServers": {"filesystem": {"command": "TAMPERED"}}}

        # Verification should fail
        is_valid = verify_signature(tampered_payload, signature, public_key_path)
        assert is_valid is False

    def test_verify_wrong_key(self, tmp_path: Path) -> None:
        """Test verifying with wrong public key."""
        key1_path = tmp_path / "key1.pem"
        key2_path = tmp_path / "key2.pem"

        # Generate two different key pairs
        signer1 = ArtifactSigner.generate(key_id="key1")
        signer2 = ArtifactSigner.generate(key_id="key2")

        signer1.save_public_key(key1_path)
        signer2.save_public_key(key2_path)

        # Sign with key1
        payload = {"test": "data"}
        signature = signer1.sign(payload)

        # Try to verify with key2 (should fail)
        is_valid = verify_signature(payload, signature, key2_path)
        assert is_valid is False

    def test_verify_missing_public_key(self, tmp_path: Path) -> None:
        """Test verification with missing public key."""
        payload = {"test": "data"}
        signature = "fake_signature"

        with pytest.raises(SigningError, match="not found"):
            verify_signature(payload, signature, tmp_path / "nonexistent.pem")

    def test_verify_canonical_json(self, tmp_path: Path) -> None:
        """Test that verification uses canonical JSON."""
        public_key_path = tmp_path / "verification_key.pem"

        signer = ArtifactSigner.generate(key_id="test")
        signer.save_public_key(public_key_path)

        # Sign payload with one key order
        payload_signed = {"b": 2, "a": 1}
        signature = signer.sign(payload_signed)

        # Verify with different key order (should still work)
        payload_verify = {"a": 1, "b": 2}
        is_valid = verify_signature(payload_verify, signature, public_key_path)
        assert is_valid is True
