# Prometheus and Grafana

This directory installs the Prometheus Community `kube-prometheus-stack` chart through Argo CD. It provides Prometheus, the Prometheus Operator, kube-state-metrics, node-exporter, and Grafana with the upstream Kubernetes dashboards.

Grafana is available at `https://grafana.k8s.749rmw.com`. Its admin credential is stored in the SOPS-encrypted `infrastructure/secrets/grafana-admin.sops.yaml` Secret. To read it locally:

```sh
sops --decrypt infrastructure/secrets/grafana-admin.sops.yaml
```

## Authentication

Grafana uses authentik as its OpenID Connect provider. The OAuth client ID and
secret are stored in the SOPS-encrypted
`infrastructure/secrets/grafana-oauth.sops.yaml` Secret and injected into the
Grafana container as environment variables so they are not rendered into a
ConfigMap.

The authentik application entitlements map to Grafana organization roles:

- `Grafana Admins` becomes `Admin`.
- `Grafana Editors` becomes `Editor`.
- Users without either entitlement become `Viewer`.

The local Grafana login form remains enabled as a recovery path. The local
admin credential above is not replaced by OAuth.

## Alerting and platform metrics

Alertmanager is enabled and connected to Prometheus. The chart's default `null`
receiver deliberately sends no external notifications until a destination is
chosen. Alerts can be inspected through Grafana's Alertmanager data source.
The always-firing Watchdog is expected; it does not yet verify external delivery.
Alertmanager currently uses ephemeral storage, so silences and notification
history do not survive pod replacement.

Argo CD controller, API server, repository server, ApplicationSet controller,
and notifications controller expose internal metrics Services and ServiceMonitors.
Authentik server and worker expose their internal metrics the same way.
The `Platform / Argo CD and Authentik` dashboard is provisioned from
`applications/grafana/platform-dashboard.yaml` and uses the `prometheus` data source.
Platform rules report sustained unhealthy/out-of-sync Argo applications and
missing controller/authentik scrape targets; the stack's TargetDown rules cover
discovered targets whose scrapes fail.

Next steps: select an external notification receiver, provide local block-backed
storage for Prometheus, and design centralized log collection and retention.
Loki, log collectors, tracing, and application request instrumentation are not
installed by this change.

## Storage

Grafana uses a 5 GiB `nas-nfs` PVC so saved dashboards and settings survive pod replacement.

The Grafana chart's `initChownData` container is disabled because Synology NFS root-squash rejects its recursive `chown`. The dynamically provisioned NFS directory remains writable by Grafana's non-root UID/GID.

Prometheus intentionally does not use `nas-nfs`. Prometheus does not support NFS for its local TSDB because it can corrupt the database. Until a local block-backed StorageClass is available, Prometheus uses a 20 GiB `emptyDir`, retains at most 15 days or 16 GB, and loses historical metrics when its pod is rescheduled or replaced. The monitoring configuration, dashboards, and alerts remain reproducible through GitOps.

When local persistent storage is available, replace `prometheus.prometheusSpec.storageSpec.emptyDir` with a `volumeClaimTemplate` that uses that StorageClass.

## Talos control-plane metrics

The kube-controller-manager, kube-scheduler, etcd, and kube-proxy monitors and their matching rules are disabled. Their metrics ports are not reachable from the pod network with the current Talos configuration. Kubelet, cAdvisor, API server, node-exporter, kube-state-metrics, Prometheus, and Grafana monitoring remain enabled.

The `monitoring` namespace uses the privileged Pod Security profile because node-exporter needs host network, host PID, hostPath, and host port access to collect node metrics. Other monitoring workloads retain their chart-defined non-root container security contexts.

## First sync

Keep **Prune**, **Force**, and **Replace** unchecked for the first sync.

1. Sync the root Application. This creates the `monitoring` namespace and the two child Applications.
2. Sync `cluster-secrets` so the encrypted Grafana admin Secret is applied.
3. Sync `kube-prometheus-stack` and review the diff before confirming.
4. Sync `grafana-config` to add the HTTPS route and HTTP-to-HTTPS redirect.

Verify the rollout with:

```sh
kubectl --kubeconfig "$HOME/Projects/talos-physical/kubeconfig" \
  get pods,pvc -n monitoring

kubectl --kubeconfig "$HOME/Projects/talos-physical/kubeconfig" \
  get prometheus,servicemonitor,podmonitor,prometheusrule -n monitoring

kubectl --kubeconfig "$HOME/Projects/talos-physical/kubeconfig" \
  get httproute -n monitoring
```
