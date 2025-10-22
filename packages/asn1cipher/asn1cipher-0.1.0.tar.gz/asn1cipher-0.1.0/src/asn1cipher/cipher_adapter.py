from .block_cipher import BlockCipher
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

class TripleDESCipher(BlockCipher):
    """TripleDES block cipher"""
    
    def __init__(self, key: bytes):
        """
        Args:
            key: 8/16/24-byte key
        """
        self._key = key
    
    @property
    def block_size(self) -> int:
        return 8
    
    def encrypt_block(self, plaintext: bytes) -> bytes:
        cipher = Cipher(
            algorithms.TripleDES(self._key),
            modes.ECB(),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        return encryptor.update(plaintext) + encryptor.finalize()
    
    def decrypt_block(self, ciphertext: bytes) -> bytes:
        cipher = Cipher(
            algorithms.TripleDES(self._key),
            modes.ECB(),
            backend=default_backend()
        )
        decryptor = cipher.decryptor()
        return decryptor.update(ciphertext) + decryptor.finalize()


class AESCipher(BlockCipher):
    """AES block cipher"""
    
    def __init__(self, key: bytes):
        """
        Args:
            key: 16, 24, or 32-byte key (AES-128, AES-192, AES-256)
        """
        self._key = key
        self._algorithm = algorithms.AES
    
    @property
    def block_size(self) -> int:
        return 16
    
    def encrypt_block(self, plaintext: bytes) -> bytes:
        cipher = Cipher(
            self._algorithm(self._key),
            modes.ECB(),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        return encryptor.update(plaintext) + encryptor.finalize()
    
    def decrypt_block(self, ciphertext: bytes) -> bytes:
        cipher = Cipher(
            self._algorithm(self._key),
            modes.ECB(),
            backend=default_backend()
        )
        decryptor = cipher.decryptor()
        return decryptor.update(ciphertext) + decryptor.finalize()