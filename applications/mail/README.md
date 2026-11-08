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

This is an unfinished private installation. Mailboxes, production TLS, DNS,
router forwarding, backup/restore verification and delivery checks remain.
Management is reachable only through the cluster Service or kubectl port-forward.
The recovery administrator Secret is temporary bootstrap configuration; remove
its environment reference after a permanent administrator login is verified.
