# Prometheus and Grafana

This directory installs the Prometheus Community `kube-prometheus-stack` chart through Argo CD. It provides Prometheus, the Prometheus Operator, kube-state-metrics, node-exporter, and Grafana with the upstream Kubernetes dashboards.

Grafana is available at `https://grafana.k8s.749rmw.com`. Its admin credential is stored in the SOPS-encrypted `infrastructure/secrets/grafana-admin.sops.yaml` Secret. To read it locally:

```sh
sops --decrypt infrastructure/secrets/grafana-admin.sops.yaml
```

## Storage

Grafana uses a 5 GiB `nas-nfs` PVC so saved dashboards and settings survive pod replacement.

Prometheus intentionally does not use `nas-nfs`. Prometheus does not support NFS for its local TSDB because it can corrupt the database. Until a local block-backed StorageClass is available, Prometheus uses a 20 GiB `emptyDir`, retains at most 15 days or 16 GB, and loses historical metrics when its pod is rescheduled or replaced. The monitoring configuration, dashboards, and alerts remain reproducible through GitOps.

When local persistent storage is available, replace `prometheus.prometheusSpec.storageSpec.emptyDir` with a `volumeClaimTemplate` that uses that StorageClass.

## Talos control-plane metrics

The kube-controller-manager, kube-scheduler, etcd, and kube-proxy monitors and their matching rules are disabled. Their metrics ports are not reachable from the pod network with the current Talos configuration. Kubelet, cAdvisor, API server, node-exporter, kube-state-metrics, Prometheus, and Grafana monitoring remain enabled.

## First sync

Keep **Prune**, **Force**, and **Replace** unchecked for the first sync.

1. Sync the root Application. This creates the `monitoring` namespace and the two child Applications.
2. Sync `cluster-secrets` so the encrypted Grafana admin Secret is applied.
3. Sync `kube-prometheus-stack` and review the diff before confirming.
4. Sync `grafana-config` to add the HTTPS route and HTTP-to-HTTPS redirect.

Verify the rollout with:

```sh
kubectl --kubeconfig /Users/tylermclean/Projects/talos-physical/kubeconfig \
  get pods,pvc -n monitoring

kubectl --kubeconfig /Users/tylermclean/Projects/talos-physical/kubeconfig \
  get prometheus,servicemonitor,podmonitor,prometheusrule -n monitoring

kubectl --kubeconfig /Users/tylermclean/Projects/talos-physical/kubeconfig \
  get httproute -n monitoring
```
