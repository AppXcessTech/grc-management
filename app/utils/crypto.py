"""
Encryption utilities for sensitive AWS credentials at rest.
Uses AES-256-GCM for symmetric encryption with a secret key.
"""
import os
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag
from typing import Optional


# Key should be 32 bytes for AES-256
def get_encryption_key() -> bytes:
    """Get encryption key from environment variable.
    
    The key must be a base64-encoded 32-byte value.
    Generate one with: python -c "import os,base64; print(base64.b64encode(os.urandom(32)).decode())"
    """
    key_b64 = os.environ.get("AWS_CREDENTIALS_ENCRYPTION_KEY", "")
    if not key_b64:
        raise ValueError(
            "AWS_CREDENTIALS_ENCRYPTION_KEY environment variable not set. "
            "Generate a key with: python -c \"import os,base64; print(base64.b64encode(os.urandom(32)).decode())\""
        )
    try:
        return base64.b64decode(key_b64)
    except Exception as e:
        raise ValueError(f"Invalid AWS_CREDENTIALS_ENCRYPTION_KEY: {e}")


class AESEncryption:
    """AES-256-GCM encryption/decryption wrapper."""
    
    def __init__(self, key: Optional[bytes] = None):
        self.key = key or get_encryption_key()
        if len(self.key) != 32:
            raise ValueError("Encryption key must be 32 bytes for AES-256")
        self._aesgcm = AESGCM(self.key)
    
    def encrypt(self, plaintext: str) -> str:
        """Encrypt a string and return base64-encoded ciphertext with nonce.
        
        Format: base64(nonce + tag + ciphertext)
        """
        if plaintext is None:
            return None
        if not isinstance(plaintext, str):
            plaintext = str(plaintext)
        
        # Generate a random 96-bit nonce (recommended for GCM)
        nonce = os.urandom(12)
        
        # Encrypt
        ciphertext = self._aesgcm.encrypt(nonce, plaintext.encode('utf-8'), None)
        
        # Prepend nonce and encode as base64
        encrypted = nonce + ciphertext
        return base64.b64encode(encrypted).decode('ascii')
    
    def decrypt(self, encrypted: str) -> str:
        """Decrypt a base64-encoded ciphertext and return the original string."""
        if encrypted is None:
            return None
        if not isinstance(encrypted, str):
            return None
            
        try:
            # Decode from base64
            encrypted_bytes = base64.b64decode(encrypted)
            
            # Extract nonce (first 12 bytes) and ciphertext
            nonce = encrypted_bytes[:12]
            ciphertext = encrypted_bytes[12:]
            
            # Decrypt
            plaintext = self._aesgcm.decrypt(nonce, ciphertext, None)
            return plaintext.decode('utf-8')
        except InvalidTag:
            raise ValueError("Decryption failed: invalid tag (wrong key or corrupted data)")
        except Exception as e:
            raise ValueError(f"Decryption failed: {e}")


# Lazy-initialized global instance (to avoid import-time crash when env var isn't ready)
_encryptor: AESEncryption | None = None


def get_encryptor() -> AESEncryption:
    global _encryptor
    if _encryptor is None:
        _encryptor = AESEncryption()
    return _encryptor


def encrypt_value(value: str) -> str:
    """Encrypt a value for storage in the database."""
    if value is None:
        return None
    return get_encryptor().encrypt(value)


def decrypt_value(encrypted: str) -> str:
    """Decrypt a value from the database."""
    if encrypted is None:
        return None
    return get_encryptor().decrypt(encrypted)


def generate_key() -> str:
    """Generate a new encryption key (for initial setup)."""
    key = os.urandom(32)
    return base64.b64encode(key).decode('ascii')