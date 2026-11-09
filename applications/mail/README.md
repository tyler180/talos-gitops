# Mail server deployment

Handwritten Kustomize manifests; no chart generator was used.

The root Argo CD Application registers `mail`, which manages the Stalwart
StatefulSet, namespace, private management Service, StorageClass, PV and PVC.
`cluster-secrets` manages the SOPS-encrypted `mail-bootstrap` Secret separately.
Pruning is disabled; the PV and PVC additionally prevent Argo prune/delete.

The 50Gi local volume is retained on cp02 at
`/var/lib/kubelet/local-volumes/mail`, with `etc` and `data` directories owned
by UID/GID 2000. Rebuilding cp02 requires restoring this directory from backup;
PV capacity is scheduling metadata, not a directory quota.

This is an unfinished private installation. The LLC mailboxes, production TLS, DNS,
router forwarding, backup/restore verification and delivery checks remain.
Management is available at https://mail-admin.k8s.749rmw.com/admin/ from the
192.168.1.0/24 LAN only, using the existing wildcard TLS certificate.
Plain HTTP port-forwarding supports API diagnostics but not the normal OAuth
WebUI login. STALWART_PUBLIC_URL supplies the trusted HTTPS admin origin.
The recovery administrator Secret is temporary bootstrap configuration; remove
its environment reference after a permanent administrator login is verified.

See [SSO.md](SSO.md) for the verified Authentik integration and recovery access.
