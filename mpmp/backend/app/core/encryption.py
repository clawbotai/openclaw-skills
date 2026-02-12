"""AES-256-GCM encryption for PHI columns.

Every encrypted value is stored as: nonce(12) || ciphertext || tag(16), base64-encoded.
"""
import base64
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.core.config import settings

_KEY: bytes = bytes.fromhex(settings.PHI_ENCRYPTION_KEY)
_GCM = AESGCM(_KEY)


def encrypt_phi(plaintext: str) -> str:
    """Encrypt a PHI string → base64 blob."""
    if not plaintext:
        return ""
    nonce = os.urandom(12)
    ct = _GCM.encrypt(nonce, plaintext.encode("utf-8"), None)
    return base64.b64encode(nonce + ct).decode("ascii")


def decrypt_phi(blob: str) -> str:
    """Decrypt a base64 blob → PHI string."""
    if not blob:
        return ""
    raw = base64.b64decode(blob)
    nonce = raw[:12]
    ct = raw[12:]
    return _GCM.decrypt(nonce, ct, None).decode("utf-8")
