import os
import base64
from cryptography.fernet import Fernet
from django.conf import settings

def get_encryption_key():
    """Generates a key based on SECRET_KEY for deterministic encryption."""
    # Use the first 32 characters of SECRET_KEY and base64 encode it
    key = base64.urlsafe_b64encode(settings.SECRET_KEY[:32].encode().ljust(32, b'0'))
    return key

def encrypt_token(token_string):
    """Encrypts a string using Fernet."""
    if not token_string:
        return None
    f = Fernet(get_encryption_key())
    return f.encrypt(token_string.encode()).decode()

def decrypt_token(encrypted_token):
    """Decrypts a string using Fernet."""
    if not encrypted_token:
        return None
    try:
        f = Fernet(get_encryption_key())
        return f.decrypt(encrypted_token.encode()).decode()
    except Exception:
        return None
