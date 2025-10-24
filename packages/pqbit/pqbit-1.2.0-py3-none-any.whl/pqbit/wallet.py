import hashlib
import secrets
from pqbit import dilithium_keypair, dilithium_sign, dilithium_verify

# 🔑 Word pool for seed generation
WORDS = [
    "cast",
    "home",
    "entropy", 
    "quantum", 
    "freedom", 
    "mesh", 
    "signal", 
    "guardian", 
    "kyber", 
    "falcon", 
    "dilithium",
    "obfs", 
    "wireguard", 
    "python", 
    "crypto", 
    "secure", 
    "offline", 
    "verify", 
    "broadcast", 
    "latency",
    "packet", 
    "node", 
    "tunnel", 
    "peer", 
    "trust", 
    "cloak", 
    "route", 
    "audit", 
    "token", 
    "wallet",
    "green", 
    "bit", 
    "hash", 
    "shield", 
    "liberty", 
    "post"
]

def generate_wallet():
    """
    Generates a post-quantum wallet with:
    - 36-word seed phrase
    - SHA3-512 digest of seed
    - Dilithium5 keypair
    - Signature of digest using secret key
    - SHA3-512 fingerprint of public key
    """
    seed_words = [secrets.choice(WORDS) for _ in range(36)]
    seed_phrase = " ".join(seed_words)
    digest = hashlib.sha3_512(seed_phrase.encode()).digest()

    public_key, secret_key = dilithium_keypair()
    signature = dilithium_sign(digest, secret_key)

    return {
        "seed": seed_phrase,
        "digest": digest.hex(),
        "public_key": hashlib.sha3_512(public_key).hexdigest(),  # fingerprint
        "raw_public_key": public_key.hex(),                      # required for verification
        "signature": signature.hex()
    }

def verify_wallet(wallet: dict) -> bool:
    """
    Verifies the wallet's signature using the raw public key and digest.
    Returns True if valid, False otherwise.
    """
    try:
        digest = bytes.fromhex(wallet["digest"])
        public_key = bytes.fromhex(wallet["raw_public_key"])
        signature = bytes.fromhex(wallet["signature"])
        return dilithium_verify(digest, signature, public_key)
    except (KeyError, ValueError):
        return False

