#!/usr/bin/env python3
"""Create/update Route53 credentials without plaintext files or command arguments."""
import getpass
import json
from pathlib import Path
import subprocess


def main():
    kubeconfig = Path.home() / "Projects/talos-physical/kubeconfig"
    command = ["kubectl", "--kubeconfig", str(kubeconfig), "--request-timeout=15s"]
    subprocess.run(command + ["get", "namespace", "cert-manager"], check=True)
    print(f"Target kubeconfig: {kubeconfig}")
    access_key = getpass.getpass("AWS access key ID (hidden): ").strip()
    secret_key = getpass.getpass("AWS secret access key (hidden): ").strip()
    if not access_key or not secret_key:
        raise SystemExit("Both credential fields are required; nothing was changed.")
    secret = {
        "apiVersion": "v1", "kind": "Secret", "type": "Opaque",
        "metadata": {"name": "route53-credentials", "namespace": "cert-manager"},
        "stringData": {"access-key-id": access_key, "secret-access-key": secret_key},
    }
    # Server-side apply avoids putting credentials in a last-applied annotation.
    result = subprocess.run(
        command + ["apply", "--server-side", "--field-manager=route53-bootstrap", "-f", "-"],
        input=json.dumps(secret), text=True, capture_output=True,
    )
    if result.returncode:
        # Do not echo an API error that might contain the submitted Secret.
        raise SystemExit("Secret update failed. Check cluster access and permissions; credential output suppressed.")
    print("Secret route53-credentials configured in cert-manager.")


if __name__ == "__main__":
    main()
