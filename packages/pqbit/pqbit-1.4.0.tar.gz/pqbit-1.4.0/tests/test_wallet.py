import pytest
from pqbit.wallet import generate, verify_wallet, verify_signature, sign_message

def test_wallet_generation():
    wallet = generate()
    assert "public_key" in wallet
    assert "private_key" in wallet
    assert "signature" in wallet
    assert "digest" in wallet

def test_wallet_verification():
    wallet = generate()
    assert verify_wallet(wallet) is True

def test_signature_verification():
    wallet = generate()
    digest = bytes.fromhex(wallet["digest"])
    signature = bytes.fromhex(wallet["signature"])
    pubkey = bytes.fromhex(wallet["raw_public_key"])
    assert verify_signature(digest, signature, pubkey) is True

def test_message_signing():
    wallet = generate()
    message = b"hello world"
    privkey = bytes.fromhex(wallet["private_key"])
    signature = sign_message(message, privkey)
    pubkey = bytes.fromhex(wallet["raw_public_key"])
    assert verify_signature(message, signature, pubkey) is True
