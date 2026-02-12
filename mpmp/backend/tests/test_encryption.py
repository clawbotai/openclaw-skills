"""Tests for PHI encryption/decryption."""
import os
import pytest

# Patch settings before import
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://x:x@localhost/x")
os.environ.setdefault("PHI_ENCRYPTION_KEY", os.urandom(32).hex())

from app.core.encryption import encrypt_phi, decrypt_phi


class TestEncryption:
    def test_roundtrip(self):
        plaintext = "John Doe"
        encrypted = encrypt_phi(plaintext)
        assert encrypted != plaintext
        assert decrypt_phi(encrypted) == plaintext

    def test_empty_string(self):
        assert encrypt_phi("") == ""
        assert decrypt_phi("") == ""

    def test_unicode(self):
        text = "José García-López 日本語"
        assert decrypt_phi(encrypt_phi(text)) == text

    def test_different_nonces(self):
        """Same plaintext produces different ciphertext (random nonce)."""
        a = encrypt_phi("test")
        b = encrypt_phi("test")
        assert a != b  # Different nonces
        assert decrypt_phi(a) == decrypt_phi(b) == "test"

    def test_long_text(self):
        text = "A" * 10000
        assert decrypt_phi(encrypt_phi(text)) == text

    def test_tamper_detection(self):
        """Modifying ciphertext should raise."""
        encrypted = encrypt_phi("sensitive data")
        import base64
        raw = bytearray(base64.b64decode(encrypted))
        raw[15] ^= 0xFF  # Flip a byte
        tampered = base64.b64encode(bytes(raw)).decode()
        with pytest.raises(Exception):
            decrypt_phi(tampered)
