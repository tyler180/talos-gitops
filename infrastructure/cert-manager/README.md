# Certificates for the physical cluster

Manual-sync rollout. The old repository remains intact. The old
`secrets/route53-credentials.enc.yaml` is empty; there are no credentials to copy.
Both Route53 credential fields are Secret references, with the Secret in
`cert-manager` (the default ClusterIssuer resource namespace).

1. Commit/push these files and sync `root` in Argo CD to register the two apps.
2. Sync `cert-manager`. Leave Prune, Force and Replace unchecked.
3. Wait for the controller, webhook and CA injector:

```sh
export KUBECONFIG="$HOME/Projects/talos-physical/kubeconfig"
kubectl -n cert-manager rollout status deployment/cert-manager
kubectl -n cert-manager rollout status deployment/cert-manager-webhook
kubectl -n cert-manager rollout status deployment/cert-manager-cainjector
```

4. Create the credentials using the helper (requires Python 3 and SOPS):

```sh
python3 "$HOME/Projects/talos-gitops/infrastructure/cert-manager/bootstrap-route53-secret.py"
```

The helper encrypts both values using the repository SOPS configuration, writes
only ciphertext to `infrastructure/secrets/route53-credentials.sops.yaml`, and
registers it with KSOPS. Commit/push and sync `cluster-secrets` before proceeding.
Complete the SOPS rollout in `infrastructure/argocd/SOPS.md` first.

5. Validate the custom resources now that their CRDs and webhook exist:

```sh
SOPS_AGE_KEY_FILE="$HOME/.config/sops/age/talos-gitops.agekey" \
  kustomize build --enable-alpha-plugins --enable-exec \
  "$HOME/Projects/talos-gitops/overlays/live/infrastructure/cert-manager/config" | \
  kubectl apply --dry-run=server -f -
```

6. Sync `cert-manager-config` (Prune, Force and Replace unchecked), then verify:

```sh
kubectl wait --for=condition=Ready clusterissuer/letsencrypt-route53 --timeout=120s
kubectl -n envoy-gateway-system wait --for=condition=Ready certificate --all --timeout=300s
kubectl -n envoy-gateway-system get certificate,certificaterequest,order,challenge
```

The AWS principal needs Route53 DNS01 permissions for the configured hosted
zone. The hosted-zone ID is supplied by the SOPS-encrypted local configuration; its
current IAM permissions should be verified before deployment.
See https://cert-manager.io/docs/configuration/acme/dns01/route53/ for required
permissions. If issuance fails, inspect Certificate/Order/Challenge events.
No inbound Internet port forwarding is needed for DNS01 validation.

## Enable HTTPS after the certificate is Ready

Add this second listener under `spec.listeners` in
`infrastructure/networking/envoy-gateway/config/gateway.yaml`, keeping HTTP:

```yaml
    - name: https
      protocol: HTTPS
      port: 443
      hostname: "*.k8s.749rmw.com"
      tls:
        mode: Terminate
        certificateRefs:
          - name: wildcard-k8s-749rmw-com-tls
      allowedRoutes:
        namespaces:
          from: All
```

Commit/push and sync `envoy-gateway-config`, then test without bypassing TLS
verification:

```sh
curl --noproxy '*' --resolve whoami.k8s.749rmw.com:443:192.0.2.10 https://whoami.k8s.749rmw.com/
```

The existing whoami HTTPRoute has no sectionName restriction, so it can attach
to both matching listeners. HTTPS is deliberately staged until its Secret exists.
