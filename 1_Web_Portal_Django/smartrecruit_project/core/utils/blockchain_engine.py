import hashlib
import uuid

# Pre-defined valid hashes for simulation (Degrees from top universities)
VALID_CREDENTIAL_HASHES = [
    "5d41402abc4b2a76b9719d911017c592", # Hello (Simulated Degree 1)
    "7d1a54128b2222b8fca81a674ed7675e", # Degree 2
    "e10adc3949ba59abbe56e057f20f883e", # 123456 (Simulated Degree 3)
]

def verify_hash_on_chain(certificate_hash):
    """
    Simulates a decentralized ledger verification call.
    Returns (success, tx_id)
    """
    if certificate_hash in VALID_CREDENTIAL_HASHES:
        # Simulate a real transaction ID
        tx_id = f"0x{uuid.uuid4().hex}"
        return True, tx_id
    
    return False, None

def generate_certificate_hash(content):
    """
    Helper to generate a hash for any certificate content.
    """
    return hashlib.md5(content.encode()).hexdigest()
