import os
import base64
from cryptography.fernet import Fernet
from django.conf import settings

# In a production environment, the ENCRYPTION_KEY should be in environment variables.
# For this implementation, we will check for it in settings or generate a fallback (Not for Prod).
MASTER_KEY = getattr(settings, 'SECRET_KEY_METADATA', settings.SECRET_KEY[:32])
# Fernet keys must be 32 url-safe base64-encoded bytes.
ENCRYPTION_KEY = base64.urlsafe_b64encode(MASTER_KEY.encode().ljust(32)[:32])

cipher_suite = Fernet(ENCRYPTION_KEY)

def encrypt_value(raw_text):
    if not raw_text:
        return ""
    return cipher_suite.encrypt(raw_text.encode()).decode()

def decrypt_value(encrypted_text):
    if not encrypted_text:
        return ""
    try:
        return cipher_suite.decrypt(encrypted_text.encode()).decode()
    except Exception:
        # Fallback for non-encrypted or corrupted data
        return "[DECRYPTION_FAILED]"
