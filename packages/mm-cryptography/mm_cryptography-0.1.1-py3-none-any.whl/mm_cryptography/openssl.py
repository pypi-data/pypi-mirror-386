import base64
import secrets
import textwrap
from hashlib import pbkdf2_hmac

from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


class OpensslAes256Cbc:
    """
    AES-256-CBC encryption/decryption compatible with OpenSSL's `enc -aes-256-cbc -pbkdf2 -iter 1000000`.

    Provides both raw-byte and Base64-encoded interfaces:
      • encrypt_bytes / decrypt_bytes: work with bytes
      • encrypt_base64 / decrypt_base64: work with Base64 strings (with automatic line breaks for OpenSSL compatibility)

    Usage:
        >>> cipher = OpensslAes256Cbc(password="mypassword")
        >>> # raw bytes
        >>> ciphertext = cipher.encrypt_bytes(b"secret")
        >>> plaintext = cipher.decrypt_bytes(ciphertext)
        >>> # Base64 convenience with automatic line formatting
        >>> token = cipher.encrypt_base64("secret message")
        >>> result = cipher.decrypt_base64(token)
        >>> print(result)
        secret message

    OpenSSL compatibility:
        echo "secret message" |
          openssl enc -aes-256-cbc -pbkdf2 -iter 1000000 -salt -base64 -pass pass:mypassword

        echo "U2FsdGVkX1/dGGdg6SExWgtKxvuLroWqhezy54aTt1g=" |
          openssl enc -d -aes-256-cbc -pbkdf2 -iter 1000000 -base64 -pass pass:mypassword
    """

    MAGIC_HEADER = b"Salted__"
    SALT_SIZE = 8
    KEY_SIZE = 32  # AES-256 key size in bytes
    BLOCK_SIZE_BYTES = 16  # AES block size in bytes (also IV size for CBC mode)
    BLOCK_SIZE_BITS = BLOCK_SIZE_BYTES * 8  # AES block size in bits (for PKCS7 padding)
    ITERATIONS = 1_000_000
    HEADER_LEN = len(MAGIC_HEADER)

    def __init__(self, password: str) -> None:
        """
        Initialize the cipher with password. Uses a fixed iteration count of 1,000,000.

        Args:
            password: Password for encryption/decryption
        """
        self._password = password.encode("utf-8")

    def _derive_key_iv(self, salt: bytes) -> tuple[bytes, bytes]:
        key_iv = pbkdf2_hmac(
            hash_name="sha256",
            password=self._password,
            salt=salt,
            iterations=self.ITERATIONS,
            dklen=self.KEY_SIZE + self.BLOCK_SIZE_BYTES,
        )
        return key_iv[: self.KEY_SIZE], key_iv[self.KEY_SIZE :]

    def encrypt_bytes(self, plaintext: bytes) -> bytes:
        """Encrypt raw bytes and return encrypted bytes (OpenSSL compatible)."""
        salt = secrets.token_bytes(self.SALT_SIZE)
        key, iv = self._derive_key_iv(salt)

        padder = padding.PKCS7(self.BLOCK_SIZE_BITS).padder()
        padded = padder.update(plaintext) + padder.finalize()

        cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(padded) + encryptor.finalize()

        return self.MAGIC_HEADER + salt + ciphertext

    def decrypt_bytes(self, encrypted: bytes) -> bytes:
        """Decrypt raw encrypted bytes (as produced by encrypt_bytes)."""
        if not encrypted.startswith(self.MAGIC_HEADER):
            raise ValueError("Invalid format: missing OpenSSL salt header")

        salt = encrypted[self.HEADER_LEN : self.HEADER_LEN + self.SALT_SIZE]
        ciphertext = encrypted[self.HEADER_LEN + self.SALT_SIZE :]

        key, iv = self._derive_key_iv(salt)
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
        decryptor = cipher.decryptor()

        try:
            padded = decryptor.update(ciphertext) + decryptor.finalize()
        except ValueError as exc:
            raise ValueError("Decryption failed: wrong password or corrupted data") from exc

        unpadder = padding.PKCS7(self.BLOCK_SIZE_BITS).unpadder()
        try:
            data = unpadder.update(padded) + unpadder.finalize()
        except ValueError as exc:
            raise ValueError("Decryption failed: wrong password or corrupted data") from exc

        return data

    def encrypt_base64(self, plaintext: str) -> str:
        """Encrypt a UTF-8 string and return Base64-encoded encrypted data with line breaks for OpenSSL compatibility."""
        raw = self.encrypt_bytes(plaintext.encode("utf-8"))
        b64_encoded = base64.b64encode(raw).decode("ascii")
        return textwrap.fill(b64_encoded, width=64)

    def decrypt_base64(self, b64_encoded: str) -> str:
        """Decode Base64, decrypt bytes, and return UTF-8 string. Handles base64 with or without line breaks."""
        try:
            # Remove all whitespace (spaces, newlines, tabs) to handle formatted base64
            cleaned_b64 = "".join(b64_encoded.split())
            raw = base64.b64decode(cleaned_b64)
        except Exception as exc:
            raise ValueError("Invalid base64 format") from exc
        plaintext_bytes = self.decrypt_bytes(raw)
        return plaintext_bytes.decode("utf-8")
