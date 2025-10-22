from typing import Optional, Dict, Callable, Tuple

from asn1crypto.algos import EncryptionAlgorithm, Pbes1Params, Pbkdf2Params
from asn1crypto.cms import EncryptedContentInfo
from asn1crypto.core import OctetString

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend

from .exceptions import (
    UnsupportedAlgorithmError,
    DecryptionError,
    EncryptionError,
    InvalidPasswordError,
)
from .cipher import Cipher
from .block_cipher import BlockCipher
from .block_mode import ECB, CBC
from .rc2_cipher import RC2Cipher
from .cipher_adapter import TripleDESCipher, AESCipher

class Provider:
    """
    Encryption/Decryption Provider class
    
    Performs encryption/decryption by combining key derivation functions
    (PBKDF1, PBKDF2, PKCS12 KDF) with Cipher.
    
    To add a custom BlockCipher:
    1. Implement by inheriting from BlockCipher
    2. Register with register_cipher_factory()
    """

    def __init__(self) -> None:
        """Initialize Provider"""
        # Cipher factory: cipher name -> BlockCipher creation function
        self._cipher_factories: Dict[str, Callable[[bytes], BlockCipher]] = {}
        self._register_cipher_factories()

    def register_cipher_factory(
        self, cipher_name: str, factory: Callable[[bytes], BlockCipher]
    ) -> None:
        """
        Register Cipher factory
        
        Args:
            cipher_name: Cipher name (e.g., "rc2", "aes", "tripledes")
            factory: BlockCipher creation function (key) -> BlockCipher
        """
        self._cipher_factories[cipher_name] = factory

    def decrypt(
        self, encrypted_content_info: EncryptedContentInfo, password: str
    ) -> bytes:
        """
        Decrypt EncryptedContentInfo
        
        Args:
            encrypted_content_info: Encrypted content information
            password: Decryption password (str)
            
        Returns:
            Decrypted plaintext (bytes)
            
        Raises:
            UnsupportedAlgorithmError: Unsupported algorithm
            DecryptionError: Decryption failure
            InvalidPasswordError: Invalid password
        """
        enc_algo = encrypted_content_info["content_encryption_algorithm"]
        encrypted_content = encrypted_content_info["encrypted_content"]

        if encrypted_content is None:
            raise DecryptionError("No encrypted content")
        
        # Derive key and IV
        key, iv = self._derive_key_and_iv(password, enc_algo)

        # Determine cipher algorithm and mode
        cipher_algo, mode_name = self._get_cipher_and_mode(enc_algo)

        # Decrypt
        try:
            return self._decrypt_with_cipher(
                encrypted_content.native, key, iv, cipher_algo, mode_name
            )
        except Exception as e:
            raise DecryptionError(e)

    def encrypt(
        self,
        plaintext: bytes,
        password: str,
        encryption_algorithm: EncryptionAlgorithm,
    ) -> EncryptedContentInfo:
        """
        Encrypt plaintext and create EncryptedContentInfo
        
        Args:
            plaintext: Plaintext to encrypt (bytes)
            password: Encryption password (str)
            encryption_algorithm: Encryption algorithm
            
        Returns:
            Encrypted content information (EncryptedContentInfo)
            
        Raises:
            UnsupportedAlgorithmError: Unsupported algorithm
            EncryptionError: Encryption failure
        """
        try:
            # Derive key and IV
            key, iv = self._derive_key_and_iv(password, encryption_algorithm)
            
            # Determine cipher algorithm and mode
            cipher_algo, mode_name = self._get_cipher_and_mode(encryption_algorithm)
            
            # Encrypt
            encrypted_content = self._encrypt_with_cipher(
                plaintext, key, iv, cipher_algo, mode_name
            )
            
            return EncryptedContentInfo({
                "content_type": "data",
                "content_encryption_algorithm": encryption_algorithm,
                "encrypted_content": OctetString(encrypted_content),
            })
        except Exception as e:
            if isinstance(e, (UnsupportedAlgorithmError, EncryptionError)):
                raise
            raise EncryptionError(f"Error during encryption: {e}") from e

    def _register_cipher_factories(self) -> None:
        """Register default Cipher factories"""
        self.register_cipher_factory("des", lambda key: TripleDESCipher(key))
        self.register_cipher_factory("tripledes", TripleDESCipher)
        self.register_cipher_factory("rc2", RC2Cipher)
        self.register_cipher_factory("aes", AESCipher)

    def _derive_key_and_iv(
        self, password: str, enc_algo: EncryptionAlgorithm
    ) -> Tuple[bytes, Optional[bytes]]:
        """
        Derive key and IV
        
        Args:
            password: Password
            enc_algo: Encryption algorithm
            
        Returns:
            (key, iv) tuple
        """
        algo_name = enc_algo["algorithm"].native
        
        # PBES1 algorithm
        if algo_name.startswith("pbes1_"):
            return self._derive_pbes1(password, enc_algo)
        
        # PBES2 algorithm
        elif algo_name == "pbes2":
            return self._derive_pbes2(password, enc_algo)
        
        # PKCS12 algorithm
        elif algo_name.startswith("pkcs12_"):
            return self._derive_pkcs12(password, enc_algo)
        
        else:
            raise ValueError(f"unknown algorithm: {enc_algo['algorithm']}")

    def _get_cipher_and_mode(
        self, enc_algo: EncryptionAlgorithm
    ) -> Tuple[str, str]:
        """
        Determine cipher algorithm and mode
        
        Args:
            enc_algo: Encryption algorithm
            
        Returns:
            (cipher_algo, mode_name) tuple
        """
        algo_name = enc_algo["algorithm"].native
        
        # PBES1: pbes1_{hash}_{cipher}
        if algo_name.startswith("pbes1_"):
            _, hash_algo, cipher_algo = algo_name.split("_", 2)
            return (cipher_algo, "cbc")
        
        # PBES2
        elif algo_name == "pbes2":
            encryption_scheme = enc_algo["parameters"]["encryption_scheme"]
            cipher_algo = encryption_scheme.encryption_cipher
            mode = encryption_scheme.encryption_mode
            return (cipher_algo, mode)
        
        # PKCS12: pkcs12_sha1_{cipher}_{keysize}
        elif algo_name.startswith("pkcs12_"):
            parts = algo_name.split("_")
            cipher_algo = parts[2]
            # Normalize tripledes to "tripledes"
            if cipher_algo == "tripledes":
                return ("tripledes", "cbc")
            return (cipher_algo, "cbc")
        
        # Direct encryption
        else:
            cipher_algo = enc_algo.encryption_cipher
            mode = enc_algo.encryption_mode
            return (cipher_algo, mode)

    # ===== Key derivation functions =====

    def _derive_pbes1(
        self, password: str, enc_algo: EncryptionAlgorithm
    ) -> Tuple[bytes, bytes]:
        """Derive PBES1 key and IV"""
        algo_name = enc_algo["algorithm"].native
        params = enc_algo["parameters"]
        
        salt = params["salt"].native
        iterations = params["iterations"].native
        
        # Parse algorithm: pbes1_{hash}_{cipher}
        _, hash_algo, cipher_algo = algo_name.split("_", 2)
        
        # Determine key length
        key_len = 8 if cipher_algo in ["des", "rc2"] else 16
        
        # Derive key and IV with PBKDF1 (generate key + IV together)
        derived = self._pbkdf1(password.encode("utf-8"), salt, iterations, hash_algo, key_len + 8)
        key = derived[:key_len]
        iv = derived[key_len : key_len + 8]
        
        return (key, iv)

    def _derive_pbes2(
        self, password: str, enc_algo: EncryptionAlgorithm
    ) -> Tuple[bytes, Optional[bytes]]:
        """
        PBES2 키와 IV 파생

        TEST OK
        """
        params = enc_algo["parameters"]
        kdf_algo = params["key_derivation_func"]
        encryption_scheme = params["encryption_scheme"]
        
        # Derive key with KDF
        key = self._derive_key_pbkdf2(password.encode("utf-8"), kdf_algo, encryption_scheme)
        
        # Get IV from encryption_scheme
        iv = encryption_scheme.encryption_iv
        
        return (key, iv)

    def _derive_pkcs12(
        self, password: str, enc_algo: EncryptionAlgorithm
    ) -> Tuple[bytes, Optional[bytes]]:
        """Derive PKCS#12 key and IV"""
        algo_name = enc_algo["algorithm"].native
        params = enc_algo["parameters"]
        
        salt = params["salt"].native
        iterations = params["iterations"].native
        
        # Parse algorithm: pkcs12_sha1_{cipher}_{keysize}
        parts = algo_name.split("_")
        cipher_algo = parts[2]
        
        # Determine key length
        key_len_map = {
            "rc4_128": 16,
            "rc4_40": 5,
            "tripledes_3key": 24,
            "tripledes_2key": 16,
            "rc2_128": 16,
            "rc2_40": 5,
        }
        key_len = key_len_map.get("_".join(parts[2:]), 16)
        
        # Derive key with PKCS12 KDF (ID=1)
        key = self._pkcs12_kdf(password, salt, iterations, key_len, 1, "sha1")
        
        # Derive IV (ID=2, block ciphers only)
        iv = None
        if cipher_algo in ["tripledes", "rc2"]:
            iv = self._pkcs12_kdf(password, salt, iterations, 8, 2, "sha1")
        
        return (key, iv)

    # ===== KDF implementations =====
    
    def _pbkdf1(
        self, password: bytes, salt: bytes, iterations: int, hash_algo: str, key_len: int
    ) -> bytes:
        """
        PBKDF1 key derivation function
        
        Args:
            password: Password
            salt: Salt
            iterations: Iteration count
            hash_algo: Hash algorithm ('md2', 'md5', 'sha1')
            key_len: Key length to generate
            
        Returns:
            Derived key
        """
        hash_map = {
            "md5": hashes.MD5(),
            "sha1": hashes.SHA1(),
        }
        
        if hash_algo not in hash_map:
            raise UnsupportedAlgorithmError(f"Unsupported hash for PBKDF1: {hash_algo}")
        
        hash_obj = hash_map[hash_algo]
        
        # PBKDF1: Iterate Hash(password + salt)
        key = password + salt
        for _ in range(iterations):
            digest = hashes.Hash(hash_obj, backend=default_backend())
            digest.update(key)
            key = digest.finalize()
        
        return key[:key_len]

    def _derive_key_pbkdf2(
        self,
        password: bytes,
        kdf_algo: EncryptionAlgorithm,
        encryption_scheme: EncryptionAlgorithm,
    ) -> bytes:
        """Derive key with PBKDF2"""
        kdf_name = kdf_algo["algorithm"].native
        
        if kdf_name != "pbkdf2":
            raise UnsupportedAlgorithmError(f"Unsupported KDF: {kdf_name}")
        
        params = kdf_algo["parameters"]
        salt_choice = params["salt"]
        
        if salt_choice.name == "specified":
            salt = salt_choice.native
        else:
            raise UnsupportedAlgorithmError("other_source salt is not supported")
        
        iterations = params["iteration_count"].native
        
        # PRF (default: HMAC-SHA1)
        prf = params["prf"]
        prf_algo = prf["algorithm"].native
        
        hash_map = {
            "sha1": hashes.SHA1(),
            "sha224": hashes.SHA224(),
            "sha256": hashes.SHA256(),
            "sha384": hashes.SHA384(),
            "sha512": hashes.SHA512(),
        }
        
        if prf_algo not in hash_map:
            raise UnsupportedAlgorithmError(f"Unsupported PRF: {prf_algo}")
        
        # Key length
        key_length = params["key_length"]
        if key_length is None or key_length.native is None:
            key_length = encryption_scheme.key_length
        else:
            key_length = key_length.native
        
        # Derive key with PBKDF2
        kdf = PBKDF2HMAC(
            algorithm=hash_map[prf_algo],
            length=key_length,
            salt=salt,
            iterations=iterations,
            backend=default_backend(),
        )
        return kdf.derive(password)

    @staticmethod
    def _pkcs12_kdf(
        password: str,
        salt: bytes,
        iterations: int,
        key_len: int,
        id_byte: int,
        hash_algo: str = "sha1",
    ) -> bytes:
        """
        PKCS#12 key derivation function (RFC 7292 Appendix B.2)
        
        Args:
            password: Password
            salt: Salt
            iterations: Iteration count (r)
            key_len: Key length to generate (n bytes)
            id_byte: ID byte (1=key, 2=IV, 3=MAC)
            hash_algo: Hash algorithm
            
        Returns:
            Derived key
        """
        
        hash_map = {
            "sha1": hashes.SHA1(),
            "sha256": hashes.SHA256(),
            "sha384": hashes.SHA384(),
            "sha512": hashes.SHA512(),
        }
        hash_obj = hash_map[hash_algo]
        if hash_obj is None:
            raise UnsupportedAlgorithmError(
                f"Unsupported hash for PKCS12 KDF: {hash_algo}"
            )

        # u, v are in bytes
        u = hash_obj.digest_size
        v = hash_obj.block_size

        # 1. D (diversifier): Repeat ID byte v times
        D = bytes([id_byte] * v)

        # Encode password in UTF-16BE and add null terminator
        if password:
            password_bytes = password.encode("utf-16-be") + b"\x00\x00"
        else:
            password_bytes = b""

        p = len(password_bytes)
        s = len(salt)

        S = b""
        # 2. S: Pad salt to v*ceiling(s/v) bytes
        if s > 0:
            # ceiling(s/v)
            total_len = v * ((s + v - 1) // v)
            while len(S) < total_len:
                S += salt
            S = S[:total_len]

        P = b""
        # 3. P: Pad password to v*ceiling(p/v) bytes
        if p > 0:
            total_len = v * ((p + v - 1) // v)
            while len(P) < total_len:
                P += password_bytes
            P = P[:total_len]

        # 4. I = S || P
        I = S + P
        
        # 5. c = ceiling(n/u)
        c = (key_len + u - 1) // u

        # 6. Generate A_1, A_2, ..., A_c
        A = b""
        
        for i in range(1, c + 1):
            # A. A_i = H^r(D||I)
            A_i = D + I
            for _ in range(iterations):
                digest = hashes.Hash(hash_obj, backend=default_backend())
                digest.update(A_i)
                A_i = digest.finalize()
            
            # 7. Add A_i to A
            A += A_i
            
            # C. Update I (if not last iteration and I is not empty)
            if i < c and len(I) > 0:
                # B. B = Expand A_i to v bytes
                B = (A_i * ((v // len(A_i)) + 1))[:v]
                
                # Divide I into v-byte blocks and add (B+1) to each block
                I_new = bytearray()
                for j in range(0, len(I), v):
                    I_j = I[j:j + v]
                    # I_j + B + 1 mod 2^(v*8)
                    I_j_int = int.from_bytes(I_j, "big")
                    B_int = int.from_bytes(B, "big")
                    I_j_new = (I_j_int + B_int + 1) % (2 ** (v * 8))
                    I_new.extend(I_j_new.to_bytes(v, "big"))
                I = bytes(I_new)
        
        # 8. Return first n bytes of A
        return A[:key_len]

    # ===== Encryption/Decryption helper methods =====
    
    def _decrypt_with_cipher(
        self,
        ciphertext: bytes,
        key: bytes,
        iv: Optional[bytes],
        cipher_algo: str,
        mode_name: str,
    ) -> bytes:
        """Decrypt with specified cipher and mode"""
        # Create BlockCipher
        block_cipher = self._create_block_cipher(key, cipher_algo)
        
        # Create BlockMode
        block_mode = self._create_block_mode(mode_name, iv, block_cipher.block_size)
        
        # Combine Cipher
        cipher = Cipher(block_cipher, block_mode)
        
        # Decrypt
        return cipher.decrypt(ciphertext, padding=True)

    def _encrypt_with_cipher(
        self,
        plaintext: bytes,
        key: bytes,
        iv: Optional[bytes],
        cipher_algo: str,
        mode_name: str,
    ) -> bytes:
        """Encrypt with specified cipher and mode"""
        # Create BlockCipher
        block_cipher = self._create_block_cipher(key, cipher_algo)
        
        # Create BlockMode
        block_mode = self._create_block_mode(mode_name, iv, block_cipher.block_size)
        
        # Combine Cipher
        cipher = Cipher(block_cipher, block_mode)
        
        # Encrypt
        return cipher.encrypt(plaintext, padding=True)

    def _create_block_cipher(self, key: bytes, cipher_algo: str) -> BlockCipher:
        """Create BlockCipher object"""
        factory = self._cipher_factories.get(cipher_algo)
        if factory is None:
            raise UnsupportedAlgorithmError(f"Unsupported cipher: {cipher_algo}")
        return factory(key)
    
    def _create_block_mode(self, mode_name: str, iv: Optional[bytes], block_size: int):
        """Create BlockMode object"""
        if mode_name == "ecb":
            return ECB()
        elif mode_name == "cbc":
            if iv is None:
                iv = b"\x00" * block_size
            elif len(iv) != block_size:
                raise ValueError(f"invalid iv size: expected={block_size}, actual={len(iv)}")
            return CBC(iv)
        elif mode_name in ["ofb", "cfb"]:
            # OFB, CFB are not yet implemented as BlockMode
            raise UnsupportedAlgorithmError(
                f"Mode {mode_name} is not yet implemented as BlockMode."
            )
        else:
            raise UnsupportedAlgorithmError(f"Unsupported mode: {mode_name}")
