from cryptography.fernet import Fernet
from base64 import b64decode, b64encode
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes
import hashlib
import hmac


class SymmetricCrypto(object):

    """
    Symmetric Cryptography uses Fernet algorithm to encrypt and decrypt the data

    The class provides methods to encrypt/decrypt
    - The Data
    - The Files
    """

    def __init__(self, key: str):
        self.fernet = Fernet(key.encode())

    def encrypt(self, data_file_path, cipher_file_path):
        with open(data_file_path, 'rb') as read_fp:
            cipher_data = self.fernet.encrypt(read_fp.read())
        with open(cipher_file_path, 'wb') as write_fp:
            write_fp.write(cipher_data)

    def encrypt_data_to_file(self, data: bytes, cipher_file_path):
        with open(cipher_file_path, 'wb') as write_fp:
            write_fp.write(self.encrypt_data(data))

    def encrypt_data(self, data: bytes):
        return self.fernet.encrypt(data)

    def decrypt(self, cipher_file_path, data_file_path):
        with open(cipher_file_path, 'rb') as read_fp:
            data = self.fernet.decrypt(read_fp.read())
        with open(data_file_path, 'wb') as write_fp:
            write_fp.write(data)

    def decrypt_file_to_data(self, cipher_file_path):
        with open(cipher_file_path, 'rb') as read_fp:
            return self.decrypt_data(read_fp.read())

    def decrypt_data(self, data: bytes):
        return self.fernet.decrypt(data)


class HmacHash(object):

    def __init__(self, secret: str):
        self.secret = secret

    def hash(self, data: str):
        return hmac.new(self.secret.encode(), data.encode(), hashlib.sha256).hexdigest()

    def is_hash_match(self, data, hashed_value: str, chars_length: int = 0) -> bool:
        """
        Verify if the given hashed_value is a match
        """
        if chars_length == 0:
            return hmac.new(self.secret.encode(), data.encode(), hashlib.sha256).hexdigest() == hashed_value
        return hmac.new(self.secret.encode(), data.encode(), hashlib.sha256).hexdigest()[-chars_length:] == hashed_value


class AESCrypto(object):

    def __init__(self, key):
        # Decode the base64-encoded key
        self.key = b64decode(key)
        if len(self.key) not in (16, 32):
            raise ValueError("Key must be either 16 bytes (128 bits) or 32 bytes (256 bits) long")

    def encrypt(self, data):
        iv = get_random_bytes(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        padded_data = pad(data.encode('utf-8'), AES.block_size)
        encrypted_data = cipher.encrypt(padded_data)
        return b64encode(iv + encrypted_data).decode('utf-8')

    def decrypt(self, encrypted_data):
        encrypted_data = b64decode(encrypted_data)
        iv = encrypted_data[:AES.block_size]
        encrypted_data = encrypted_data[AES.block_size:]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        decrypted_data = unpad(cipher.decrypt(encrypted_data), AES.block_size)
        return decrypted_data.decode('utf-8')