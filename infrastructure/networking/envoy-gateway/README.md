# Envoy Gateway

`application.yaml` installs the Envoy Gateway Helm chart.
`config-application.yaml` manages the GatewayClass and Gateway in `config/`.
Both Applications are listed in the infrastructure root Kustomization.

The `eg` GatewayClass uses the default Envoy proxy configuration. The `public`
Gateway address is supplied by the SOPS-encrypted local configuration. The
checked-in example address is `192.0.2.10`; the public hostname is
`*.k8s.749rmw.com`. Routes from other namespaces may attach to this Gateway;
keep each HTTPRoute with its application and explicitly reference the Gateway
in namespace `envoy-gateway-system`.

## Initial validation

After merging the files, sync `root`, then `envoy-gateway-config`.
Verify the GatewayClass is Accepted, the Gateway is Programmed, and the proxy
LoadBalancer Service receives the configured address. No HTTPRoutes are included here,
so application responses are not expected until a route and backend are added.

## Enable HTTPS

HTTPS is intentionally deferred during initial connectivity validation. Before
adding a port 443 HTTPS listener, provision a trusted wildcard certificate for
the configured wildcard domain into the `wildcard-k8s-749rmw-com-tls` Secret in namespace
`envoy-gateway-system`. Do not commit certificate private keys to Git.

Then add an HTTPS listener using TLS termination and a certificate reference to
that Secret. DNS records must resolve the intended hostnames to the Gateway IP.
Use HTTPS before routing applications that carry credentials or sensitive data.
