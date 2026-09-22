# Certificates for the physical cluster

Manual-sync rollout. The old repository remains intact. The old
`secrets/route53-credentials.enc.yaml` is empty; there are no credentials to copy.
Both Route53 credential fields are Secret references, with the Secret in
`cert-manager` (the default ClusterIssuer resource namespace).

1. Commit/push these files and sync `root` in Argo CD to register the two apps.
2. Sync `cert-manager`. Leave Prune, Force and Replace unchecked.
3. Wait for the controller, webhook and CA injector:

```sh
export KUBECONFIG=/Users/tylermclean/Projects/talos-physical/kubeconfig
kubectl -n cert-manager rollout status deployment/cert-manager
kubectl -n cert-manager rollout status deployment/cert-manager-webhook
kubectl -n cert-manager rollout status deployment/cert-manager-cainjector
```

4. Create the credentials using the helper (requires Python 3 and kubectl):

```sh
python3 /Users/tylermclean/Projects/talos-gitops/infrastructure/cert-manager/bootstrap-route53-secret.py
```

The helper explicitly targets the physical kubeconfig and privately prompts for
both AWS values. It sends the Secret through stdin without creating a plaintext
file. This is a manual bootstrap dependency, not an Argo-managed Secret. Keep the
credentials in your password manager and rerun the helper for cluster recovery
or credential rotation. Do not commit credentials or decrypted Secret manifests.

5. Validate the custom resources now that their CRDs and webhook exist:

```sh
kubectl apply --dry-run=server -k /Users/tylermclean/Projects/talos-gitops/infrastructure/cert-manager/config
```

6. Sync `cert-manager-config` (Prune, Force and Replace unchecked), then verify:

```sh
kubectl wait --for=condition=Ready clusterissuer/letsencrypt-route53 --timeout=120s
kubectl -n envoy-gateway-system wait --for=condition=Ready certificate/wildcard-k8s-749rmw-com --timeout=300s
kubectl -n envoy-gateway-system get certificate,certificaterequest,order,challenge
```

The AWS principal needs Route53 DNS01 permissions for hosted zone
`Z04272303NZ93YPTT8MBI`; its current IAM permissions have not been verified.
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
curl --noproxy '*' --resolve whoami.k8s.749rmw.com:443:192.168.3.240 https://whoami.k8s.749rmw.com/
```

The existing whoami HTTPRoute has no sectionName restriction, so it can attach
to both matching listeners. HTTPS is deliberately staged until its Secret exists.
