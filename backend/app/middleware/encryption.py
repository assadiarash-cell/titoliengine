"""Encryption at rest per documenti uploadati.

Usa Fernet (AES-128-CBC) per cifrare i file su disco.
La chiave è derivata dal secret_key dell'applicazione.
"""
import base64
import hashlib
from cryptography.fernet import Fernet


def _derive_key(secret: str) -> bytes:
    """Deriva una chiave Fernet valida (32 bytes base64) dal secret_key."""
    key_bytes = hashlib.sha256(secret.encode()).digest()
    return base64.urlsafe_b64encode(key_bytes)


def encrypt_file_content(content: bytes, secret_key: str) -> bytes:
    """Cifra il contenuto di un file con Fernet (AES).

    Args:
        content: bytes del file originale.
        secret_key: chiave segreta dell'applicazione.

    Returns:
        bytes cifrati.
    """
    f = Fernet(_derive_key(secret_key))
    return f.encrypt(content)


def decrypt_file_content(encrypted: bytes, secret_key: str) -> bytes:
    """Decifra il contenuto di un file.

    Args:
        encrypted: bytes cifrati.
        secret_key: chiave segreta dell'applicazione.

    Returns:
        bytes originali.
    """
    f = Fernet(_derive_key(secret_key))
    return f.decrypt(encrypted)
