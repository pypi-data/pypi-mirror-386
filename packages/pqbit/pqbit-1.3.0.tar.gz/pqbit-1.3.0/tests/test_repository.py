import pytest
from pqbit.wallet import generate, verify_wallet, sign_message, verify_signature

def test_keypair_and_signature():
    wallet = generate()
    message = b"pqbit repository test"
    privkey = bytes.fromhex(wallet["private_key"])
    pubkey = bytes.fromhex(wallet["raw_public_key"])
    signature = sign_message(message, privkey)
    assert verify_signature(message, signature, pubkey) is True

def test_wallet_integrity():
    wallet = generate()
    assert verify_wallet(wallet)
