# asn1cipher

A Python library for encrypting and decrypting ASN.1 encrypted content. Uses `asn1crypto` library's `EncryptionAlgorithm` and `EncryptedContentInfo`.

## Features

**Algorithm Oid**

- **PBES1** support (`1.2.840.113549.1.5.X`)
- **PKCS#12** encryption support (`1.2.840.113549.1.12.1.X`)
- **PBES2/PBKDF2** support (`1.2.840.113549.1.5.13`)

**Cipher Algorithm**
- **RC2** block cipher
- **Custom Block Cipher Support** (BlockCipher abstraction)

## Quick Start

### Basic Usage

[examples/basic_usage.py](examples/basic_usage.py)

```python
from asn1cipher import Provider
from asn1crypto.algos import EncryptionAlgorithm, Pbes1Params
from asn1crypto.core import OctetString
import os

# Create Provider instance
provider = Provider()

# Data to encrypt and password
plaintext = b"Hello, World! This is a secret message."
password = b"my_secret_password"

# Configure PBES1 (SHA1 + DES) algorithm
encryption_algorithm = EncryptionAlgorithm({
    'algorithm': 'pbes1_sha1_des',
    'parameters': Pbes1Params({
        'salt': os.urandom(8),
        'iterations': 10000,
    })
})

# Encrypt
encrypted_content_info = provider.encrypt(
    plaintext=plaintext,
    password=password,
    encryption_algorithm=encryption_algorithm
)

# Decrypt
decrypted = provider.decrypt(
    encrypted_content_info=encrypted_content_info,
    password=password
)

assert decrypted == plaintext
print("✓ Encryption/decryption successful!")
```

## License

Apache-2.0 License

## Contributing

Contributions are welcome! Please submit a Pull Request.

## Related Projects

- [asn1crypto](https://github.com/wbond/asn1crypto) - ASN.1 parsing and serialization
- [cryptography](https://github.com/pyca/cryptography) - Python cryptography library

## Author

Your Name <your.email@example.com>