#!/usr/bin/env python3
"""Encrypt Route53 credentials for GitOps; never write plaintext to disk."""
import getpass
import json
from pathlib import Path
import subprocess


def main():
    root = Path(__file__).resolve().parents[2]
    destination = root / "infrastructure/secrets/route53-credentials.sops.yaml"
    access = getpass.getpass("AWS access key ID (hidden): ").strip()
    secret = getpass.getpass("AWS secret access key (hidden): ").strip()
    if not access or not secret:
        raise SystemExit("Both fields are required; no files changed.")
    resource = {"apiVersion": "v1", "kind": "Secret", "type": "Opaque",
                "metadata": {"name": "route53-credentials", "namespace": "cert-manager"},
                "stringData": {"access-key-id": access, "secret-access-key": secret}}
    result = subprocess.run(
        ["sops", "--encrypt", "--config", str(root / ".sops.yaml"),
         "--filename-override", str(destination), "--input-type", "json",
         "--output-type", "yaml", "/dev/stdin"],
        input=json.dumps(resource), text=True, capture_output=True)
    if result.returncode:
        raise SystemExit("Encryption failed; no credentials written. Check SOPS installation/configuration.")
    destination.write_text(result.stdout)
    generator = destination.parent / "secret-generator.yaml"
    content = generator.read_text()
    if "  - route53-credentials.sops.yaml" not in content:
        generator.write_text(content.rstrip() + "\n  - route53-credentials.sops.yaml\n")
    print("Encrypted credentials saved. Commit/push and sync cluster-secrets after cert-manager is installed.")


if __name__ == "__main__":
    main()
