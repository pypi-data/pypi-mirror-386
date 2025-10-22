import hashlib


class Hasher(object):

    def hash(self, input_string: str, algorithm: str = 'sha256') -> str:
        """
         Hashes a given string using the specified algorithm and returns the hexadecimal digest.

         :param input_string: The string to be hashed.
         :param algorithm: The hashing algorithm to use (default is 'sha256').
         :return: The hexadecimal digest of the hashed string.
         """
        try:
            # Create a new hash object using the specified algorithm
            hash_obj = hashlib.new(algorithm)
            # Update the hash object with the bytes of the input string
            hash_obj.update(input_string.encode('utf-8'))
            # Return the hexadecimal digest of the hash
            return hash_obj.hexdigest()
        except ValueError:
            return f"Error: Unsupported hashing algorithm '{algorithm}'"
