import json
from pqbit import verify_wallet, generate_wallet

def test_wallet_generation_and_verification():
    wallet = generate_wallet()
    assert verify_wallet(wallet), "Generated wallet failed verification"

def test_wallet_sample_verification():
    with open("tests/wallet_sample.json", "r") as f:
        wallet = json.load(f)
    assert verify_wallet(wallet), "Sample wallet failed verification"
