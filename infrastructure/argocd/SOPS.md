# SOPS / age / KSOPS rollout

The private key is outside Git at:
`/Users/tylermclean/.config/sops/age/talos-gitops.agekey`

Back up this file in your password manager before relying on encrypted secrets.
It is installed as `argocd/sops-age`, key `keys.txt`. Do not commit it.
The public recipient in `.sops.yaml` can safely be committed.

1. Commit/push the repository changes and sync `root`.
2. Sync `argocd` with Prune, Force and Replace unchecked.
3. Wait for `argocd-repo-server` to finish rolling out:

```sh
export KUBECONFIG=/Users/tylermclean/Projects/talos-physical/kubeconfig
kubectl -n argocd rollout status deployment/argocd-repo-server
```

4. Sync `cluster-secrets`. Its encrypted smoke test contains only dummy data.
   Verify without displaying real credentials:

```sh
kubectl -n argocd get secret sops-smoke-test -o jsonpath='{.data.test}' | base64 --decode
```

Expected: `sops-decryption-works`.

5. Install `cert-manager`, then run the Route53 helper documented in
   `infrastructure/cert-manager/README.md`. It now encrypts credentials for Git
   instead of creating a live Secret directly. Commit/push and sync
   `cluster-secrets`, then sync `cert-manager-config`.

KSOPS v4.5.1 is installed with its shell-free `install` command. Argo's bundled
Kustomize remains in use. Exec plugins are enabled globally: only trusted writers
should have access to repositories that this Argo installation renders.

## Recovery

Restore the backed-up age key outside Git, then bootstrap the Secret before
syncing Argo's repo-server configuration:

```sh
kubectl --kubeconfig /Users/tylermclean/Projects/talos-physical/kubeconfig -n argocd create secret generic sops-age --from-file=keys.txt=/Users/tylermclean/.config/sops/age/talos-gitops.agekey
```

For local SOPS editing/decryption set `SOPS_AGE_KEY_FILE` to that private key path.
Never redirect decrypted output into the repository. SOPS protects Git contents;
Kubernetes Secret access still requires appropriate RBAC. Restart repo-server
after changing its mounted key if decryption remains cached or fails.
