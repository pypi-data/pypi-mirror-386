from base64 import b64decode, b64encode
from Crypto.Random import get_random_bytes
from Crypto.PublicKey import RSA
from cryptography.fernet import Fernet


class GenerateKeys(object):

    def build_rsa_key(self, key_length = 2048):
        """
        Generate public and private key
        """
        key = RSA.generate(key_length)
        return key.publickey().export_key(), key.export_key()

    def build_fernet_key(self):
        """
        Generate fernet key
        """
        return Fernet.generate_key()

    def build_aes_key(self, key_length=32):
        if key_length not in (16, 32):
            raise ValueError("Key length must be either 16 bytes (128 bits) or 32 bytes (256 bits)")
        key = get_random_bytes(key_length)
        return b64encode(key).decode('utf-8')
