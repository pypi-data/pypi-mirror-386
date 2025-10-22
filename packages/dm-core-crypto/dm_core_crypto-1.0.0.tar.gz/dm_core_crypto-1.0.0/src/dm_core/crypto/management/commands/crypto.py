import sys

from django.core.management import BaseCommand
from django.conf import settings
from dm_core.crypto.symmetric import SymmetricCrypto


class Command(BaseCommand):

    help = 'Encrypt / Decrypt fixtures'

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)
        service = settings.SERVICE
        fernet_key = getattr(settings, f"{service.upper()}_FERNET_KEY")
        self.crypto = SymmetricCrypto(fernet_key)

    def add_arguments(self, parser):
        parser.add_argument("-a", "--action", dest="action", required=True, help="encrypt/decrypt")
        parser.add_argument("-i", "--input", dest="input", required=True, help="Input file path")
        parser.add_argument("-o", "--output", dest="output", required=True, help="Output file path")

    def handle(self, *args, **kwargs):
        if kwargs['action'] == 'encrypt':
            self.crypto.encrypt(kwargs['input'], kwargs['output'])
        elif kwargs['action'] == 'decrypt':
            self.crypto.decrypt(kwargs['input'], kwargs['output'])
        else:
            sys.stdout.write('Unknown action. Allowed actions - [encrypt|decrypt]')
        sys.stdout.write('crypto command executed successfully')