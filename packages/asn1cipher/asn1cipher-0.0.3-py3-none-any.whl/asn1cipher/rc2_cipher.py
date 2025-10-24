from typing import List

from .block_cipher import BlockCipher

class RC2Cipher(BlockCipher):
    """
    RC2 Block Cipher (RFC 2268)
    - Block size: 8 bytes
    - Key size: variable
    """

    pi_table = [
        0xd9, 0x78, 0xf9, 0xc4, 0x19, 0xdd, 0xb5, 0xed,
        0x28, 0xe9, 0xfd, 0x79, 0x4a, 0xa0, 0xd8, 0x9d,
        0xc6, 0x7e, 0x37, 0x83, 0x2b, 0x76, 0x53, 0x8e,
        0x62, 0x4c, 0x64, 0x88, 0x44, 0x8b, 0xfb, 0xa2,
        0x17, 0x9a, 0x59, 0xf5, 0x87, 0xb3, 0x4f, 0x13,
        0x61, 0x45, 0x6d, 0x8d, 0x9, 0x81, 0x7d, 0x32,
        0xbd, 0x8f, 0x40, 0xeb, 0x86, 0xb7, 0x7b, 0xb,
        0xf0, 0x95, 0x21, 0x22, 0x5c, 0x6b, 0x4e, 0x82,
        0x54, 0xd6, 0x65, 0x93, 0xce, 0x60, 0xb2, 0x1c,
        0x73, 0x56, 0xc0, 0x14, 0xa7, 0x8c, 0xf1, 0xdc,
        0x12, 0x75, 0xca, 0x1f, 0x3b, 0xbe, 0xe4, 0xd1,
        0x42, 0x3d, 0xd4, 0x30, 0xa3, 0x3c, 0xb6, 0x26,
        0x6f, 0xbf, 0xe, 0xda, 0x46, 0x69, 0x7, 0x57,
        0x27, 0xf2, 0x1d, 0x9b, 0xbc, 0x94, 0x43, 0x3,
        0xf8, 0x11, 0xc7, 0xf6, 0x90, 0xef, 0x3e, 0xe7,
        0x6, 0xc3, 0xd5, 0x2f, 0xc8, 0x66, 0x1e, 0xd7,
        0x8, 0xe8, 0xea, 0xde, 0x80, 0x52, 0xee, 0xf7,
        0x84, 0xaa, 0x72, 0xac, 0x35, 0x4d, 0x6a, 0x2a,
        0x96, 0x1a, 0xd2, 0x71, 0x5a, 0x15, 0x49, 0x74,
        0x4b, 0x9f, 0xd0, 0x5e, 0x4, 0x18, 0xa4, 0xec,
        0xc2, 0xe0, 0x41, 0x6e, 0xf, 0x51, 0xcb, 0xcc,
        0x24, 0x91, 0xaf, 0x50, 0xa1, 0xf4, 0x70, 0x39,
        0x99, 0x7c, 0x3a, 0x85, 0x23, 0xb8, 0xb4, 0x7a,
        0xfc, 0x2, 0x36, 0x5b, 0x25, 0x55, 0x97, 0x31,
        0x2d, 0x5d, 0xfa, 0x98, 0xe3, 0x8a, 0x92, 0xae,
        0x5, 0xdf, 0x29, 0x10, 0x67, 0x6c, 0xba, 0xc9,
        0xd3, 0x0, 0xe6, 0xcf, 0xe1, 0x9e, 0xa8, 0x2c,
        0x63, 0x16, 0x1, 0x3f, 0x58, 0xe2, 0x89, 0xa9,
        0xd, 0x38, 0x34, 0x1b, 0xab, 0x33, 0xff, 0xb0,
        0xbb, 0x48, 0xc, 0x5f, 0xb9, 0xb1, 0xcd, 0x2e,
        0xc5, 0xf3, 0xdb, 0x47, 0xe5, 0xa5, 0x9c, 0x77,
        0xa, 0xa6, 0x20, 0x68, 0xfe, 0x7f, 0xc1, 0xad
    ]

    def __init__(self, key: bytes):
        """
        Args:
            key: RC2 key (e.g., 5 bytes)
        """
        if not (1 <= len(key) <= 128):
            raise ValueError("RC2 key length must be between 1 and 128 bytes")
        self._key = key
        self.working_key = self._generate_working_key(key, len(key) * 8)

    @property
    def block_size(self) -> int:
        return 8

    # ========== Internal utility functions ==========

    @staticmethod
    def _rotate_left(x: int, y: int) -> int:
        x &= 0xFFFF
        return ((x << y) | (x >> (16 - y))) & 0xFFFF

    def _generate_working_key(self, key: bytes, bits: int) -> List[int]:
        xkey = [0] * 128
        for i in range(len(key)):
            xkey[i] = key[i]

        # Phase 1: expand key to 128 bytes
        if len(key) < 128:
            idx = 0
            x = xkey[len(key) - 1]
            for i in range(len(key), 128):
                x = self.pi_table[(x + xkey[idx]) & 0xFF]
                idx += 1
                xkey[i] = x

        # Phase 2: reduce effective key bits
        T = (bits + 7) >> 3
        x = self.pi_table[xkey[128 - T] & (0xFF >> (7 & -bits))]
        xkey[128 - T] = x
        for i in range(128 - T - 1, -1, -1):
            x = self.pi_table[x ^ xkey[i + T]]
            xkey[i] = x

        # Phase 3: generate 64 16-bit words
        new_key = [0] * 64
        for i in range(64):
            new_key[i] = xkey[2 * i] + (xkey[2 * i + 1] << 8)
        return new_key

    # ========== Encryption / Decryption ==========

    def encrypt_block(self, plaintext: bytes) -> bytes:
        if len(plaintext) != 8:
            raise ValueError("RC2 block size must be 8 bytes")

        x10 = plaintext[0] | (plaintext[1] << 8)
        x32 = plaintext[2] | (plaintext[3] << 8)
        x54 = plaintext[4] | (plaintext[5] << 8)
        x76 = plaintext[6] | (plaintext[7] << 8)

        # MIX 1~16
        for i in range(0, 16 + 1, 4):
            x10 = self._rotate_left(x10 + (x32 & ~x76) + (x54 & x76) + self.working_key[i], 1)
            x32 = self._rotate_left(x32 + (x54 & ~x10) + (x76 & x10) + self.working_key[i + 1], 2)
            x54 = self._rotate_left(x54 + (x76 & ~x32) + (x10 & x32) + self.working_key[i + 2], 3)
            x76 = self._rotate_left(x76 + (x10 & ~x54) + (x32 & x54) + self.working_key[i + 3], 5)

        x10 = (x10 + self.working_key[x76 & 63]) & 0xFFFF
        x32 = (x32 + self.working_key[x10 & 63]) & 0xFFFF
        x54 = (x54 + self.working_key[x32 & 63]) & 0xFFFF
        x76 = (x76 + self.working_key[x54 & 63]) & 0xFFFF

        # MIX 17~40
        for i in range(20, 40 + 1, 4):
            x10 = self._rotate_left(x10 + (x32 & ~x76) + (x54 & x76) + self.working_key[i], 1)
            x32 = self._rotate_left(x32 + (x54 & ~x10) + (x76 & x10) + self.working_key[i + 1], 2)
            x54 = self._rotate_left(x54 + (x76 & ~x32) + (x10 & x32) + self.working_key[i + 2], 3)
            x76 = self._rotate_left(x76 + (x10 & ~x54) + (x32 & x54) + self.working_key[i + 3], 5)

        x10 = (x10 + self.working_key[x76 & 63]) & 0xFFFF
        x32 = (x32 + self.working_key[x10 & 63]) & 0xFFFF
        x54 = (x54 + self.working_key[x32 & 63]) & 0xFFFF
        x76 = (x76 + self.working_key[x54 & 63]) & 0xFFFF

        # MIX 41~63
        for i in range(44, 64, 4):
            x10 = self._rotate_left(x10 + (x32 & ~x76) + (x54 & x76) + self.working_key[i], 1)
            x32 = self._rotate_left(x32 + (x54 & ~x10) + (x76 & x10) + self.working_key[i + 1], 2)
            x54 = self._rotate_left(x54 + (x76 & ~x32) + (x10 & x32) + self.working_key[i + 2], 3)
            x76 = self._rotate_left(x76 + (x10 & ~x54) + (x32 & x54) + self.working_key[i + 3], 5)

        return bytes([
            x10 & 0xFF, (x10 >> 8) & 0xFF,
            x32 & 0xFF, (x32 >> 8) & 0xFF,
            x54 & 0xFF, (x54 >> 8) & 0xFF,
            x76 & 0xFF, (x76 >> 8) & 0xFF
        ])

    def decrypt_block(self, ciphertext: bytes) -> bytes:
        if len(ciphertext) != 8:
            raise ValueError("RC2 block size must be 8 bytes")

        x10 = ciphertext[0] | (ciphertext[1] << 8)
        x32 = ciphertext[2] | (ciphertext[3] << 8)
        x54 = ciphertext[4] | (ciphertext[5] << 8)
        x76 = ciphertext[6] | (ciphertext[7] << 8)

        # MIX 63~41
        for i in range(60, 43, -4):
            x76 = (self._rotate_left(x76, 11) - ((x10 & ~x54) + (x32 & x54) + self.working_key[i + 3])) & 0xFFFF
            x54 = (self._rotate_left(x54, 13) - ((x76 & ~x32) + (x10 & x32) + self.working_key[i + 2])) & 0xFFFF
            x32 = (self._rotate_left(x32, 14) - ((x54 & ~x10) + (x76 & x10) + self.working_key[i + 1])) & 0xFFFF
            x10 = (self._rotate_left(x10, 15) - ((x32 & ~x76) + (x54 & x76) + self.working_key[i])) & 0xFFFF

        x76 = (x76 - self.working_key[x54 & 63]) & 0xFFFF
        x54 = (x54 - self.working_key[x32 & 63]) & 0xFFFF
        x32 = (x32 - self.working_key[x10 & 63]) & 0xFFFF
        x10 = (x10 - self.working_key[x76 & 63]) & 0xFFFF

        # MIX 40~17
        for i in range(40, 19, -4):
            x76 = (self._rotate_left(x76, 11) - ((x10 & ~x54) + (x32 & x54) + self.working_key[i + 3])) & 0xFFFF
            x54 = (self._rotate_left(x54, 13) - ((x76 & ~x32) + (x10 & x32) + self.working_key[i + 2])) & 0xFFFF
            x32 = (self._rotate_left(x32, 14) - ((x54 & ~x10) + (x76 & x10) + self.working_key[i + 1])) & 0xFFFF
            x10 = (self._rotate_left(x10, 15) - ((x32 & ~x76) + (x54 & x76) + self.working_key[i])) & 0xFFFF

        x76 = (x76 - self.working_key[x54 & 63]) & 0xFFFF
        x54 = (x54 - self.working_key[x32 & 63]) & 0xFFFF
        x32 = (x32 - self.working_key[x10 & 63]) & 0xFFFF
        x10 = (x10 - self.working_key[x76 & 63]) & 0xFFFF

        # MIX 16~0
        for i in range(16, -1, -4):
            x76 = (self._rotate_left(x76, 11) - ((x10 & ~x54) + (x32 & x54) + self.working_key[i + 3])) & 0xFFFF
            x54 = (self._rotate_left(x54, 13) - ((x76 & ~x32) + (x10 & x32) + self.working_key[i + 2])) & 0xFFFF
            x32 = (self._rotate_left(x32, 14) - ((x54 & ~x10) + (x76 & x10) + self.working_key[i + 1])) & 0xFFFF
            x10 = (self._rotate_left(x10, 15) - ((x32 & ~x76) + (x54 & x76) + self.working_key[i])) & 0xFFFF

        return bytes([
            x10 & 0xFF, (x10 >> 8) & 0xFF,
            x32 & 0xFF, (x32 >> 8) & 0xFF,
            x54 & 0xFF, (x54 >> 8) & 0xFF,
            x76 & 0xFF, (x76 >> 8) & 0xFF
        ])
