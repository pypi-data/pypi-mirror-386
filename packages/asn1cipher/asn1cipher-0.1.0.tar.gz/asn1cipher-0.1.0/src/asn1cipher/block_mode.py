"""Block cipher mode implementations (ECB, CBC)"""

from .block_cipher import BlockMode, BlockCipher


class ECB(BlockMode):
    """
    ECB (Electronic Codebook) mode
    """
    
    def encrypt(self, cipher: BlockCipher, plaintext: bytes, padding: bool = True) -> bytes:
        """
        Encrypt with ECB mode
        
        Args:
            cipher: Block cipher to use
            plaintext: Plaintext to encrypt
            padding: Whether to apply PKCS7 padding
            
        Returns:
            Encrypted data
        """
        if padding:
            plaintext = self.add_pkcs7_padding(plaintext, cipher.block_size)
        
        ciphertext = b""
        for i in range(0, len(plaintext), cipher.block_size):
            block = plaintext[i:i + cipher.block_size]
            ciphertext += cipher.encrypt_block(block)
        
        return ciphertext
    
    def decrypt(self, cipher: BlockCipher, ciphertext: bytes, padding: bool = True) -> bytes:
        """
        Decrypt with ECB mode
        
        Args:
            cipher: Block cipher to use
            ciphertext: Ciphertext to decrypt
            padding: Whether to remove PKCS7 padding
            
        Returns:
            Decrypted data
        """
        plaintext = b""
        for i in range(0, len(ciphertext), cipher.block_size):
            block = ciphertext[i:i + cipher.block_size]
            plaintext += cipher.decrypt_block(block)
        
        if padding:
            plaintext = self.remove_pkcs7_padding(plaintext, cipher.block_size)
        
        return plaintext


class CBC(BlockMode):
    """
    CBC (Cipher Block Chaining) mode
    """
    
    def __init__(self, iv: bytes):
        """
        Initialize CBC mode
        
        Args:
            iv: Initialization Vector
        """
        self.iv = iv
    
    def encrypt(self, cipher: BlockCipher, plaintext: bytes, padding: bool = True) -> bytes:
        """
        Encrypt with CBC mode
        
        Args:
            cipher: Block cipher to use
            plaintext: Plaintext to encrypt
            padding: Whether to apply PKCS7 padding
            
        Returns:
            Encrypted data
        """
        if padding:
            plaintext = self.add_pkcs7_padding(plaintext, cipher.block_size)
        
        ciphertext = b""
        prev_block = self.iv
        
        for i in range(0, len(plaintext), cipher.block_size):
            block = plaintext[i:i + cipher.block_size]
            # XOR with previous ciphertext block (or IV for first block)
            xored = bytes(a ^ b for a, b in zip(block, prev_block))
            encrypted = cipher.encrypt_block(xored)
            ciphertext += encrypted
            prev_block = encrypted
        
        return ciphertext
    
    def decrypt(self, cipher: BlockCipher, ciphertext: bytes, padding: bool = True) -> bytes:
        """
        Decrypt with CBC mode
        
        Args:
            cipher: Block cipher to use
            ciphertext: Ciphertext to decrypt
            padding: Whether to remove PKCS7 padding
            
        Returns:
            Decrypted data
        """
        plaintext = b""
        prev_block = self.iv
        
        for i in range(0, len(ciphertext), cipher.block_size):
            block = ciphertext[i:i + cipher.block_size]
            decrypted = cipher.decrypt_block(block)
            # XOR with previous ciphertext block (or IV for first block)
            xored = bytes(a ^ b for a, b in zip(decrypted, prev_block))
            plaintext += xored
            prev_block = block
        
        if padding:
            plaintext = self.remove_pkcs7_padding(plaintext, cipher.block_size)
        
        return plaintext