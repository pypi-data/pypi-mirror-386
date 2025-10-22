"""asn1cipher exception classes"""


class Asn1CipherError(Exception):
    """Base exception class for asn1cipher"""
    pass


class UnsupportedAlgorithmError(Asn1CipherError):
    """Unsupported algorithm exception"""
    pass


class DecryptionError(Asn1CipherError):
    cause: Exception

    def __init__(self, cause: Exception):
        self.cause = cause
        super().__init__(f"Decryption failed: {cause}")


class EncryptionError(Asn1CipherError):
    """Encryption failure exception"""
    pass


class InvalidPasswordError(Asn1CipherError):
    """Invalid password exception"""
    pass