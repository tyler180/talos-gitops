# Dynasty FF frontend

Deploys the `tyler180/dynasty-ff-frontend` Next.js app at https://dynasty-ff.k8s.749rmw.com. It shows roster, salary cap and rookie draft analysis for MFL league 79286, read from the dynasty-ff backend (AWS API Gateway and Lambda).

One stateless replica runs the Next.js standalone server as UID 1001 with a read-only root filesystem. Its only writable paths are `emptyDir` volumes at `/app/.next/cache` and `/tmp`. The probes use the public `/api/health`. No Secrets are needed: the browser signs in with Authorization Code + PKCE as a public OIDC client, and the app holds no client secret.

## Image and releases

`tyler180/dynasty-ff-frontend` publishes `ghcr.io/tyler180/dynasty-ff-frontend` (public) on every push to `main`, tagged `sha-<commit>` and `latest`. The Deployment pins an image digest. To release, take the digest of the new `sha-<commit>` tag and change the `image:` line in a PR:

```sh
docker buildx imagetools inspect ghcr.io/tyler180/dynasty-ff-frontend:sha-<commit>
```

Roll back by restoring the previous digest. There is no release bot for this app yet.

The OIDC issuer, client ID, API URL and league coordinates are `NEXT_PUBLIC_*` values compiled into the image at build time, not runtime environment. Changing any of them needs a new image build, not a manifest change.

## Sign-in (Authentik)

The app and the backend API both expect an Authentik application with slug `dynasty-ff`, so the issuer is `https://auth.k8s.749rmw.com/application/o/dynasty-ff/`. Its provider must be a **public** OAuth2/OpenID provider with:

- client ID `dynasty-ff-frontend` (the backend's API Gateway JWT authorizer checks this audience)
- the `authorization_code` grant type enabled (if it is empty, Authentik rejects every sign-in with `invalid_request`)
- redirect URIs `https://dynasty-ff.k8s.749rmw.com/auth/callback` and `http://localhost:3000/auth/callback`

These Authentik objects live in Authentik's database, not in Git. If sign-in fails with `oidc_discovery_failed`, the issuer URL above returns 404: the application or its slug is missing.

## Hostname and API access

`dynasty-ff.k8s.749rmw.com` uses the Gateway's existing `*.k8s.749rmw.com` HTTPS listener and wildcard certificate. That DNS name resolves to the Gateway's LAN address, so the app is reachable only on the home network or VPN.

The browser calls the backend API directly, so the backend must allow this origin. `https://dynasty-ff.k8s.749rmw.com` has to be in `api_allowed_origins` in `tyler180/dynasty-ff-backend` (`terraform/variables.tf`); otherwise every API call fails CORS after sign-in.

## Validation

```sh
kubectl kustomize applications/dynasty-ff
kubectl kustomize infrastructure
```

Argo CD automatically syncs this application without pruning. Root keeps its manual sync policy, so sync `root` once after merging to create the `dynasty-ff` Application.
