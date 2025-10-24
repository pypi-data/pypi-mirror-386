"""
asn1cipher - ASN.1 encrypted content encryption/decryption library

This library provides functionality to encrypt and decrypt encrypted content
using asn1crypto's EncryptionAlgorithm and EncryptedContentInfo.
"""

from .provider import Provider, CustomAlgorithm
from .block_cipher import BlockCipher, BlockMode
from .exceptions import (
    Asn1CipherError,
    UnsupportedAlgorithmError,
    DecryptionError,
    EncryptionError,
    InvalidPasswordError,
)

__version__ = "0.0.3"

__all__ = [
    "Provider",
    "CustomAlgorithm",
    "BlockCipher",
    "BlockMode",
    "Asn1CipherError",
    "UnsupportedAlgorithmError",
    "DecryptionError",
    "EncryptionError",
    "InvalidPasswordError",
]