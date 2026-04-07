import hashlib
import time
import random
import logging

logger = logging.getLogger(__name__)

def verify_certificate_hash(cert_hash):
    """
    Simulates a connection to a decentralized ledger (Polygon/Ethereum Testnet).
    In a real-world scenario, this would use web3.py to query a Smart Contract.
    
    Returns:
        tuple: (is_verified, metadata)
    """
    logger.info(f"[Blockchain] Initiating sync for hash: {cert_hash}")
    
    # Simulate network latency
    time.sleep(1.5)
    
    if not cert_hash:
        return False, {"error": "No hash provided"}

    # PROTOTYPE RULESET:
    # 1. Hashes starting with "SR_VERIFY_" are always valid (Internal Testnet)
    # 2. Hashes starting with "CERT_" are valid if they end in an even number (Simulated Ledger)
    # 3. Everything else is rejected as 'Unverified/Tampered'
    
    is_verified = False
    metadata = {}
    
    if cert_hash.startswith("SR_VERIFY_"):
        is_verified = True
        metadata = {
            "node": "SmartRecruit-Alpha-01",
            "block_height": random.randint(15000000, 16000000),
            "issuer": "Global Tech University (Verified)",
            "timestamp": time.ctime()
        }
    elif cert_hash.startswith("CERT_"):
        # Dummy check: last character check
        last_char = cert_hash[-1]
        if last_char.isdigit() and int(last_char) % 2 == 0:
            is_verified = True
            metadata = {
                "node": "Polygon-Mumbai-Sandbox",
                "block_height": random.randint(30000000, 31000000),
                "issuer": "OpenCert standard",
                "timestamp": time.ctime()
            }
        else:
            is_verified = False
            metadata = {"error": "Hash discrepancy on-chain"}
    else:
        is_verified = False
        metadata = {"error": "Record not found on decentralized ledger"}
        
    if is_verified:
        logger.info(f"[Blockchain] Hash {cert_hash} VERIFIED by node {metadata.get('node')}")
    else:
        logger.warning(f"[Blockchain] Hash {cert_hash} FAILED verification.")
        
    return is_verified, metadata

def generate_verification_summary(is_verified, metadata):
    """
    Generates a human-readable summary for the recruiter dashboard.
    """
    if is_verified:
        return f"Verified via {metadata.get('node')} at Block {metadata.get('block_height')}. Issued by {metadata.get('issuer')}."
    else:
        return f"Verification Failed: {metadata.get('error', 'Unknown Error')}. Manual verification required."
