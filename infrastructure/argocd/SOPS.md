# SOPS / age / KSOPS rollout

The private key is outside Git at:
`$HOME/.config/sops/age/talos-gitops.agekey`

Back up this file in your password manager before relying on encrypted secrets.
It is installed as `argocd/sops-age`, key `keys.txt`. Do not commit it.
The public recipient in `.sops.yaml` can safely be committed.

Private addresses, filesystem paths, node selectors, and cloud identifiers are
stored in SOPS-encrypted files under `overlays/live/` or in encrypted application
Secrets under `infrastructure/secrets/`. Public `749rmw.com` hostnames remain in
the ordinary manifests. The public bases can be rendered without the age private
key; Argo CD follows the live overlays to restore local-only values.

Validate public examples without credentials:

```sh
kubectl kustomize applications/mm-inches
kubectl kustomize infrastructure
```

Validate a live overlay locally without writing decrypted output to disk:

```sh
SOPS_AGE_KEY_FILE="$HOME/.config/sops/age/talos-gitops.agekey" \
  kustomize build --enable-alpha-plugins --enable-exec \
  overlays/live/infrastructure/root >/dev/null
```

When migrating an existing installation, commit and push these changes before
repointing the bootstrap Application. Apply the updated source path once, then
review the root diff before syncing:

```sh
kubectl --kubeconfig "$HOME/Projects/talos-physical/kubeconfig" \
  apply -f bootstrap/root-application.yaml
```

Keep Prune, Force, and Replace unchecked.

1. Commit/push the repository changes and sync `root`.
2. Sync `argocd` with Prune, Force and Replace unchecked.
3. Wait for `argocd-repo-server` to finish rolling out:

```sh
export KUBECONFIG="$HOME/Projects/talos-physical/kubeconfig"
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
kubectl --kubeconfig "$HOME/Projects/talos-physical/kubeconfig" -n argocd create secret generic sops-age --from-file=keys.txt="$HOME/.config/sops/age/talos-gitops.agekey"
```

For local SOPS editing/decryption set `SOPS_AGE_KEY_FILE` to that private key path.
Never redirect decrypted output into the repository. SOPS protects Git contents;
Kubernetes Secret access still requires appropriate RBAC. Restart repo-server
after changing its mounted key if decryption remains cached or fails.
