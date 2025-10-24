"""Encryption handling for Bedrock protocol."""
import os
from typing import Optional, Tuple
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
from .types import ProtocolError

class SessionCrypto:
    """Handles session encryption using AES-GCM."""
    
    def __init__(self, key: bytes):
        if len(key) != 32:
            raise ValueError("Session key must be 32 bytes")
        self._aes = AESGCM(key)
    
    def encrypt(self, data: bytes, associated_data: Optional[bytes] = None) -> bytes:
        """Encrypt data using AES-GCM with a random nonce."""
        try:
            nonce = os.urandom(12)  # 96-bit nonce for AES-GCM
            ciphertext = self._aes.encrypt(nonce, data, associated_data)
            return nonce + ciphertext
        except Exception as e:
            raise ProtocolError(f"Encryption failed: {e}")
    
    def decrypt(self, data: bytes, associated_data: Optional[bytes] = None) -> bytes:
        """Decrypt data using AES-GCM."""
        if len(data) < 12:
            raise ProtocolError("Invalid encrypted data")
        try:
            nonce = data[:12]
            ciphertext = data[12:]
            return self._aes.decrypt(nonce, ciphertext, associated_data)
        except Exception as e:
            raise ProtocolError(f"Decryption failed: {e}")

class KeyExchange:
    """Handles ECDH key exchange."""
    
    def __init__(self):
        self._private_key = ec.generate_private_key(ec.SECP256R1())
        self._shared_key: Optional[bytes] = None
    
    @property
    def public_key_bytes(self) -> bytes:
        """Get the public key in compressed format."""
        return self._private_key.public_key().public_bytes(
            encoding=serialization.Encoding.X962,
            format=serialization.PublicFormat.CompressedPoint
        )
    
    def compute_shared(self, peer_public_key_bytes: bytes) -> bytes:
        """Compute the shared secret using the peer's public key."""
        try:
            peer_public_key = ec.EllipticCurvePublicKey.from_encoded_point(
                ec.SECP256R1(),
                peer_public_key_bytes
            )
            shared = self._private_key.exchange(ec.ECDH(), peer_public_key)
            self._shared_key = shared
            return shared
        except Exception as e:
            raise ProtocolError(f"Key exchange failed: {e}")
    
    @property
    def shared_key(self) -> Optional[bytes]:
        """Get the computed shared key if available."""
        return self._shared_key

def generate_session_key() -> Tuple[bytes, bytes]:
    """Generate a new session key pair (encryption key, salt)."""
    return os.urandom(32), os.urandom(16)