import hashlib
from pqc.sign.falcon_1024 import keypair as generate_keypair, sign, verify

def generate():
    pk, sk = generate_keypair()
    digest = hashlib.sha3_512(pk).digest()
    signature = sign(digest, sk)
    return {
        "public_key": hashlib.sha256(pk).hexdigest(),
        "raw_public_key": pk.hex(),
        "digest": digest.hex(),
        "signature": signature.hex(),
        "private_key": sk.hex()
    }

def verify_signature(message: bytes, signature: bytes, public_key: bytes) -> bool:
    try:
        verify(signature, message, public_key)
        return True
    except Exception:
        return False

def verify_wallet(wallet: dict) -> bool:
    try:
        digest = bytes.fromhex(wallet["digest"])
        public_key = bytes.fromhex(wallet["raw_public_key"])
        signature = bytes.fromhex(wallet["signature"])
        return verify_signature(digest, signature, public_key)
    except (KeyError, ValueError):
        return False

def export_keys(format="json"):
    wallet = generate()
    return wallet

def sign_message(message: bytes, private_key: bytes) -> bytes:
    return sign(message, private_key)

def load_private_key(path="wallet.json") -> bytes:
    import json
    with open(path) as f:
        wallet = json.load(f)
    return bytes.fromhex(wallet["private_key"])
