import argparse
import json
import os
import yaml
import qrcode
from pqbit.wallet import (
    generate,
    verify_signature,
    export_keys,
    verify_wallet,
    sign_message,
    load_private_key
)

def main():
    parser = argparse.ArgumentParser(
        description="pqbit — Post-Quantum Wallet CLI"
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # generate
    gen_parser = subparsers.add_parser("generate", help="Generate a new wallet")
    gen_parser.add_argument("--output", help="Save wallet to file (JSON)")

    # verify
    ver_parser = subparsers.add_parser("verify", help="Verify a signature")
    ver_parser.add_argument("--message", required=True, help="Path to message file")
    ver_parser.add_argument("--signature", required=True, help="Path to signature file")
    ver_parser.add_argument("--public-key", required=True, help="Path to public key file")

    # export
    exp_parser = subparsers.add_parser("export", help="Export wallet keys")
    exp_parser.add_argument("--format", choices=["pem", "json"], default="json", help="Export format")
    exp_parser.add_argument("--yaml", action="store_true", help="Export as YAML")

    # inspect
    ins_parser = subparsers.add_parser("inspect", help="Inspect and verify wallet(s)")
    ins_parser.add_argument("wallet_file", nargs="+", help="Path(s) to wallet.json file(s)")
    ins_parser.add_argument("--json", action="store_true", help="Output result as JSON")
    ins_parser.add_argument("--quiet", action="store_true", help="Suppress output (exit code only)")
    ins_parser.add_argument("--fingerprint-only", action="store_true", help="Print only wallet fingerprint")

    # batch-sign
    batch_parser = subparsers.add_parser("batch-sign", help="Sign multiple files")
    batch_parser.add_argument("files", nargs="+", help="Files to sign")
    batch_parser.add_argument("--output-dir", default="signed", help="Directory to save signatures")

    # qr
    qr_parser = subparsers.add_parser("qr", help="Generate QR code from public key")
    qr_parser.add_argument("wallet_file", help="Path to wallet.json")
    qr_parser.add_argument("--output", default="pubkey.png", help="Output image file")

    args = parser.parse_args()

    if args.command == "generate":
        wallet = generate()
        if args.output:
            with open(args.output, "w") as f:
                json.dump(wallet, f, indent=2)
            print(f"Wallet saved to {args.output}")
        else:
            print(json.dumps(wallet, indent=2))

    elif args.command == "verify":
        with open(args.message, "rb") as f:
            message = f.read()
        with open(args.signature, "rb") as f:
            signature = f.read()
        with open(args.public_key, "rb") as f:
            pubkey = f.read()

        result = verify_signature(message, signature, pubkey)
        print("✅ Signature is valid" if result else "❌ Signature is invalid")

    elif args.command == "export":
        keys = export_keys(format=args.format)
        if args.yaml:
            print(yaml.dump(keys, sort_keys=False))
        else:
            print(json.dumps(keys, indent=2))

    elif args.command == "inspect":
        for path in args.wallet_file:
            try:
                with open(path, "r") as f:
                    wallet = json.load(f)

                result = verify_wallet(wallet)
                fingerprint = wallet.get("public_key", "[missing]")

                if args.quiet:
                    exit(0 if result else 1)

                if args.fingerprint_only:
                    print(fingerprint)
                    continue

                if args.json:
                    print(json.dumps({
                        "file": path,
                        "fingerprint": fingerprint,
                        "valid": result
                    }, indent=2))
                else:
                    print(f"\n🔍", path)
                    print(f"Fingerprint: {fingerprint}")
                    print("✅ Signature is valid" if result else "❌ Signature is invalid")

            except Exception as e:
                if args.json:
                    print(json.dumps({
                        "file": path,
                        "error": str(e)
                    }, indent=2))
                elif not args.quiet:
                    print(f"\n⚠️ Failed to inspect {path}: {e}")

    elif args.command == "batch-sign":
        os.makedirs(args.output_dir, exist_ok=True)
        privkey = load_private_key()
        for path in args.files:
            try:
                with open(path, "rb") as f:
                    msg = f.read()
                sig = sign_message(msg, privkey)
                sig_path = os.path.join(args.output_dir, os.path.basename(path) + ".sig")
                with open(sig_path, "wb") as out:
                    out.write(sig)
                print(f"✅ Signed {path} → {sig_path}")
            except Exception as e:
                print(f"❌ Failed to sign {path}: {e}")

    elif args.command == "qr":
        with open(args.wallet_file) as f:
            wallet = json.load(f)
        pubkey = wallet["raw_public_key"]
        img = qrcode.make(pubkey)
        img.save(args.output)
        print(f"📱 QR code saved to {args.output}")

if __name__ == "__main__":
    main()
