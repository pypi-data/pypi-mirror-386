"""
asn1cipher - ASN.1 encrypted content encryption/decryption library

This library provides functionality to encrypt and decrypt encrypted content
using asn1crypto's EncryptionAlgorithm and EncryptedContentInfo.
"""

from .provider import Provider
from .block_cipher import BlockCipher, BlockMode
from .block_mode import ECB, CBC
from .exceptions import (
    Asn1CipherError,
    UnsupportedAlgorithmError,
    DecryptionError,
    EncryptionError,
    InvalidPasswordError,
)

__version__ = "0.1.0"
__all__ = [
    "Provider",
    "BlockCipher",
    "BlockMode",
    "ECB",
    "CBC",
    "Asn1CipherError",
    "UnsupportedAlgorithmError",
    "DecryptionError",
    "EncryptionError",
    "InvalidPasswordError",
]