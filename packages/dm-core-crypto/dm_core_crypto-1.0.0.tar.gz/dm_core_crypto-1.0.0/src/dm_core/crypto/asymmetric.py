from base64 import b64decode, b64encode
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from Crypto.Util.number import ceil_div
from Crypto import Util, Hash
import binascii
import json
import logging

logger = logging.getLogger()


class AsymmetricCrypto(object):

    def __init__(self, public_key: str=None, private_key: str=None):
        if public_key is not None:
            self.public_key = RSA.import_key(b64decode(public_key).decode())
        if private_key is not None:
            self.private_key = RSA.import_key(b64decode(private_key).decode())

    def _encryption_block_size(self):
        modBits = Util.number.size(self.public_key.n)
        hLen = Hash.SHA256.block_size
        return ceil_div(modBits, 8) - 2 * hLen - 2  # Convert from bits to bytes

    def _decryption_block_size(self):
        modBits = Util.number.size(self.private_key.n)
        return ceil_div(modBits, 8)

    def encrypt(self, data: bytes):
        """
        Encryption should be performed using public key
        """
        cipher = PKCS1_OAEP.new(self.public_key)
        chunk_size = self._encryption_block_size()
        chunks = len(data) // chunk_size
        encrypted_data = b''
        i = 0
        while i < chunks:
            encrypted_data_chunk = cipher.encrypt(data[chunk_size * i: chunk_size * (i + 1)])
            encrypted_data += encrypted_data_chunk
            i += 1
        encrypted_data += cipher.encrypt(data[chunk_size * i: len(data)])
        return b64encode(encrypted_data).decode()

    def decrypt(self, cipher, byte_data=False):
        """
        Decryption should be performed using private key
        """
        try:
            b64_decoded_text = b64decode(cipher)
            chunk_size = self._decryption_block_size()
            cipher = PKCS1_OAEP.new(self.private_key)
            chunks = len(b64_decoded_text) // chunk_size
            decrypted_json_data = b''
            for i in range(chunks):
                decrypted_json_data_chunk = cipher.decrypt(b64_decoded_text[chunk_size * i: chunk_size * (i + 1)])
                decrypted_json_data += decrypted_json_data_chunk
            if not byte_data:
                data = json.loads(decrypted_json_data)
            else:
                data = b64encode(decrypted_json_data).decode()
        except (Exception, binascii.Error) as e:
            logger.error("Unable to decrypt message: {}".format(str(e)))
            return None
        else:
            return data

    def sign(self, data: bytes):
        hash = SHA256.new(data)
        return PKCS1_v1_5.new(self.private_key).sign(hash)

    def verify_sign(self, data: bytes, signature: bytes) -> bool:
        hasher = SHA256.new(data)
        return PKCS1_v1_5.new(self.public_key).verify(hasher, signature)
