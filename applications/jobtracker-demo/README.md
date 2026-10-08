# Jobtracker read-only demo

Independent deployment in namespace `jobtracker-demo`, managed by its own Argo Application. The image is digest pinned and must contain `DEMO_MODE=true` support. The private Jobtracker archive is never mounted: demo storage is a 64 MiB `emptyDir`, and each process seeds a new temporary directory with fictional applications.

The demo permits browsing, searching, filtering, sorting, notes and archived descriptions. All write/import/upload requests are rejected by the server. Application and description pages identify the data as fictional.

The cluster route accepts `jobtracker-demo.k8s.749rmw.com`; HTTP redirects to HTTPS through the existing Envoy public gateway. The proposed public alias `jobtracker-demo.749rmw.com` requires an external proxy that terminates TLS for that alias and forwards HTTPS to the cluster hostname, using `jobtracker-demo.k8s.749rmw.com` for both the upstream Host header and TLS server name. Internet DNS and ingress forwarding are configured separately. A public DNS record must reach the ingress over a public route rather than resolve solely to a private address.

Auto-sync and self-healing are enabled for this application; pruning, force and replace are disabled. The main Jobtracker release pipeline promotes the private deployment separately. To update this demo, submit a reviewed change to its image digest in `app.yaml`.

Validate with `kubectl kustomize applications/jobtracker-demo` and `kubectl kustomize infrastructure`. Verify Argo health, rollout, image digest, mock data banner, and rejection of POST/PUT/PATCH/DELETE before sharing the URL.
