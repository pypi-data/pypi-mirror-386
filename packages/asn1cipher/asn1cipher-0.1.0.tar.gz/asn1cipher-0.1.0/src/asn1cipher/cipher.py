from .block_cipher import BlockCipher, BlockMode

class Cipher:
    """
    Cipher class
    
    Performs encryption/decryption by combining BlockCipher and BlockMode.
    """
    
    def __init__(self, block_cipher: BlockCipher, mode: BlockMode):
        """
        Initialize Cipher
        
        Args:
            block_cipher: Block cipher to use
            mode: Block cipher mode to use
        """
        self.block_cipher = block_cipher
        self.mode = mode
    
    @property
    def block_size(self) -> int:
        """Block size"""
        return self.block_cipher.block_size
    
    def encrypt(self, plaintext: bytes, padding: bool = True) -> bytes:
        """
        Encrypt
        
        Args:
            plaintext: Plaintext to encrypt
            padding: Whether to apply PKCS7 padding
            
        Returns:
            Encrypted data
        """
        return self.mode.encrypt(self.block_cipher, plaintext, padding)
    
    def decrypt(self, ciphertext: bytes, padding: bool = True) -> bytes:
        """
        Decrypt
        
        Args:
            ciphertext: Ciphertext to decrypt
            padding: Whether to remove PKCS7 padding
            
        Returns:
            Decrypted data
        """
        return self.mode.decrypt(self.block_cipher, ciphertext, padding)