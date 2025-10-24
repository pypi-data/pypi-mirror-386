"""Block cipher abstraction"""

from abc import ABC, abstractmethod


class BlockCipher(ABC):
    """
    Block cipher abstract class
    
    All block cipher implementations must inherit from this class.
    Only implements block-level encryption/decryption; mode handling is managed by the Cipher class.
    """
    
    @property
    @abstractmethod
    def block_size(self) -> int:
        """Block size (in bytes)"""
        pass
    
    @abstractmethod
    def encrypt_block(self, plaintext: bytes) -> bytes:
        """
        Encrypt a single block
        
        Args:
            plaintext: Plaintext block to encrypt (block_size bytes)
            
        Returns:
            Encrypted block (block_size bytes)
        """
        pass
    
    @abstractmethod
    def decrypt_block(self, ciphertext: bytes) -> bytes:
        """
        Decrypt a single block
        
        Args:
            ciphertext: Ciphertext block to decrypt (block_size bytes)
            
        Returns:
            Decrypted block (block_size bytes)
        """
        pass

class BlockMode(ABC):
    """
    Block cipher mode abstract base class
    
    Defined in block_cipher.py to prevent circular references.
    Concrete mode implementations (ECB, CBC, etc.) are in block_mode.py.
    """

    @abstractmethod
    def encrypt(self, cipher: BlockCipher, plaintext: bytes, padding: bool = True) -> bytes:
        """
        Encrypt

        Args:
            cipher: Block cipher to use
            plaintext: Plaintext to encrypt
            padding: Whether to apply PKCS7 padding

        Returns:
            Encrypted data
        """
        pass

    @abstractmethod
    def decrypt(self, cipher: BlockCipher, ciphertext: bytes, padding: bool = True) -> bytes:
        """
        Decrypt
        
        Args:
            cipher: Block cipher to use
            ciphertext: Ciphertext to decrypt
            padding: Whether to remove PKCS7 padding
            
        Returns:
            Decrypted data
        """
        pass

    @staticmethod
    def add_pkcs7_padding(data: bytes, block_size: int) -> bytes:
        """Add PKCS7 padding"""
        padding_len = block_size - (len(data) % block_size)
        return data + bytes([padding_len] * padding_len)

    @staticmethod
    def remove_pkcs7_padding(data: bytes, block_size: int) -> bytes:
        """Remove PKCS7 padding"""
        if len(data) == 0:
            return data
        padding_len = data[-1]
        if padding_len > block_size:
            raise ValueError(f"invalid padding size: pad={padding_len}")
        if data[-padding_len:] != bytes([padding_len]) * padding_len:
            raise ValueError(f"invalid padding value: pad={padding_len}")
        return data[:-padding_len]
