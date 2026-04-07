import json
from decouple import config
from web3 import Web3
from eth_account import Account
import logging

logger = logging.getLogger(__name__)

# Basic ABI for the Certificate contract we wrote
CERTIFICATE_ABI = json.loads('''[
    {
        "inputs": [],
        "stateMutability": "nonpayable",
        "type": "constructor"
    },
    {
        "anonymous": false,
        "inputs": [
            {
                "indexed": true,
                "internalType": "string",
                "name": "certificateHash",
                "type": "string"
            },
            {
                "indexed": false,
                "internalType": "string",
                "name": "candidateId",
                "type": "string"
            },
            {
                "indexed": false,
                "internalType": "string",
                "name": "score",
                "type": "string"
            },
            {
                "indexed": false,
                "internalType": "uint256",
                "name": "timestamp",
                "type": "uint256"
            }
        ],
        "name": "CertificateMinted",
        "type": "event"
    },
    {
        "inputs": [
            {
                "internalType": "string",
                "name": "_hash",
                "type": "string"
            },
            {
                "internalType": "string",
                "name": "_candidateId",
                "type": "string"
            },
            {
                "internalType": "string",
                "name": "_score",
                "type": "string"
            }
        ],
        "name": "mintCertificate",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "string",
                "name": "_hash",
                "type": "string"
            }
        ],
        "name": "verifyCertificate",
        "outputs": [
            {
                "internalType": "string",
                "name": "",
                "type": "string"
            },
            {
                "internalType": "string",
                "name": "",
                "type": "string"
            },
            {
                "internalType": "uint256",
                "name": "",
                "type": "uint256"
            },
            {
                "internalType": "bool",
                "name": "",
                "type": "bool"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    }
]''')

def init_web3():
    infura_url = config('INFURA_URL', default='https://polygon-mumbai.infura.io/v3/YOUR_INFURA_PROJECT_ID')
    w3 = Web3(Web3.HTTPProvider(infura_url))
    return w3

def mint_certificate(certificate_hash: str, candidate_id: str, score: str):
    """
    Mints an immutable certificate on the blockchain.
    """
    private_key = config('PRIVATE_KEY', default='0x0000000000000000000000000000000000000000000000000000000000000000')
    contract_address = config('CONTRACT_ADDRESS', default='0x0000000000000000000000000000000000000000')

    w3 = init_web3()

    # Skip actual minting if default values are used to prevent errors in testnet demo mode
    if contract_address == '0x0000000000000000000000000000000000000000' or not w3.is_connected():
        logger.warning(f"Blockchain Trust Layer: Simulated minting for {certificate_hash} (Keys not configured)")
        return "simulate_tx_hash_" + certificate_hash

    try:
        account = Account.from_key(private_key)
        contract = w3.eth.contract(address=contract_address, abi=CERTIFICATE_ABI)
        
        # Build Transaction
        nonce = w3.eth.get_transaction_count(account.address)
        tx = contract.functions.mintCertificate(
            certificate_hash,
            str(candidate_id),
            str(score)
        ).build_transaction({
            'chainId': w3.eth.chain_id,
            'gas': 2000000,
            'maxFeePerGas': w3.to_wei('2', 'gwei'),
            'maxPriorityFeePerGas': w3.to_wei('1', 'gwei'),
            'nonce': nonce,
        })
        
        # Sign and Send Transaction
        signed_tx = w3.eth.account.sign_transaction(tx, private_key=private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        logger.info(f"Certificate Minted on blockchain: {tx_receipt.transactionHash.hex()}")
        return tx_receipt.transactionHash.hex()
        
    except Exception as e:
        logger.error(f"Blockchain Minting Error: {e}")
        return None

def verify_certificate(certificate_hash: str):
    """
    Verifies a certificate existence and data on the blockchain.
    """
    contract_address = config('CONTRACT_ADDRESS', default='0x0000000000000000000000000000000000000000')
    w3 = init_web3()
    
    if contract_address == '0x0000000000000000000000000000000000000000' or not w3.is_connected():
        logger.warning(f"Blockchain Trust Layer: Simulated verifying for {certificate_hash}")
        # Return mock data for local testing
        import time
        return {
            'candidateId': 'Simulated Candidate',
            'score': '85',
            'timestamp': int(time.time()),
            'exists': True
        }

    try:
        contract = w3.eth.contract(address=contract_address, abi=CERTIFICATE_ABI)
        result = contract.functions.verifyCertificate(certificate_hash).call()
        
        return {
            'candidateId': result[0],
            'score': result[1],
            'timestamp': result[2],
            'exists': result[3]
        }
    except Exception as e:
        logger.error(f"Blockchain Verification Error: {e}")
        return None
