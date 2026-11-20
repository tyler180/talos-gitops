# URL shortener / video host

Deploys `tyler180/url-shortener` (the current source implements a video host and importer).

Open https://vid.749rmw.com/import (sign in when prompted) to import a video, or `/upload/local` to upload through the browser. Generated links use this HTTPS hostname. This is a new installation; existing local videos and Twitter cookies are not migrated.

One replica uses a 10 GiB `nas-nfs` volume at `/videos`, with a Recreate strategy to avoid overlapping cleanup jobs. The app's default retention deletes videos after 30 days. NFS capacity requests do not necessarily enforce a NAS quota.

Importing and uploading require an Authentik login; watching shared videos (`/watch/`, `/v/`) does not. Any Authentik user can sign in. The Authentik application `videohost` uses a confidential OAuth2/OpenID provider (`Provider for Video host`, implicit consent, hashed-user-ID subject, strict redirect URI `https://vid.749rmw.com/auth/callback`, grant type `authorization_code`), with no policy bindings, so every authenticated Authentik user is allowed; add a binding in Authentik to restrict it. Issuer: `https://auth.k8s.749rmw.com/application/o/videohost/`.

The provider must have the `authorization_code` grant type enabled. If it is empty (as happens when a provider is created through the API without `grant_types`), Authentik rejects every sign-in at the authorize step with `invalid_request` and `The request is otherwise malformed`, redirecting straight back to `/auth/callback?error=...`.

`url-shortener-oidc` is encrypted under `infrastructure/secrets/` with keys `client-id`, `client-secret` and `session-key`. The session key signs login cookies (12 hours, stateless); rotating it signs everyone out, and the app cannot revoke a single session. The old shared upload token and its `url-shortener-auth` Secret are no longer used. The probes use the public `/healthz`. These Authentik objects live in Authentik's database, not in Git: back it up, and if the provider is recreated, replace `client-id` and `client-secret` in the encrypted Secret.

Releases come from `tyler180/url-shortener`: pushing a `vMAJOR.MINOR.PATCH` tag builds `server/Dockerfile` for linux/amd64, publishes `tyler180/url-shortener:<tag>` to Docker Hub, and opens a `deploy/url-shortener-<tag>` PR here that changes only the image line. The workflow gets its `talos-gitops` token from the existing `tyler180-gitops-bot` GitHub App (`GITOPS_APP_ID` variable and `GITOPS_APP_PRIVATE_KEY` secret in the app repository), scoped to this repository with contents and pull-request write. Review and merge the PR; the bot's PR uses the bare tag, so pin it to the published digest if you want an immutable reference. A PR that also changes arguments, environment or Secrets must be merged before (or together with) the image that needs them: an image that cannot start with the old arguments will crash-loop under the Recreate strategy and take the site down.

Validation:

```sh
kubectl kustomize applications/url-shortener
kubectl kustomize infrastructure
```

Argo CD automatically syncs this application without pruning. Root and cluster-secrets retain their existing manual sync policies. When a change references a new Secret, sync `cluster-secrets` first (or immediately after merging): otherwise the pod stays in `CreateContainerConfigError` (`secret ... not found`) and, with Recreate, the old pod is already gone. Without Prune, a Secret deleted from Git stays in the cluster and `cluster-secrets` shows it OutOfSync; that is harmless. Roll back by restoring the previous image digest in Git; the PVC remains intact.

Reddit may block anonymous post metadata with HTTP 403. Direct `https://v.redd.it/<video-id>` links import the public DASH manifest with video and audio. Authenticated post imports are supported with `-reddit-cookies`, and the user-approved Reddit session is stored as a SOPS-encrypted Secret mounted read-only at `/run/secrets/reddit/cookies.txt`. The app uses a private temporary copy for each import. If the session expires or is revoked, replace the encrypted cookie file and reconcile `cluster-secrets`; the mounted Secret updates without rebuilding the image. To revoke app access, remove the cookie argument, mount, volume, and encrypted Secret through GitOps, then sign out the exported Reddit session in Reddit account settings.

The canonical hostname is `vid.749rmw.com`, with a dedicated Gateway listener and cert-manager certificate. The previous `url-shortener.k8s.749rmw.com` routes remain available so existing video links continue working. Its authoritative Route 53 A record targets the existing Gateway address.

## Hostnames and DNS

- `vid.749rmw.com` is the canonical name. The Authentik callback and the sign-in cookies (`__Host-` prefixed, so host-only) are tied to it, which is why sign-in only completes there.
- `video.749rmw.com` is an alias that redirects. In Nginx Proxy Manager, proxy host `vid.749rmw.com, video.749rmw.com` forwards to the Gateway at `https://192.168.3.240:443` with `Host: vid.749rmw.com` and has a server-level `if ($host = video.749rmw.com) { return 301 https://vid.749rmw.com$request_uri; }` ahead of the `location /` block. Paths and queries are preserved, so old `video.749rmw.com/watch/...` links keep working. Without the redirect, sign-in started on `video` fails with "missing sign-in state", because the login cookie is set on `video` but the callback returns to `vid`. NPM's configuration is not in Git; keep this redirect when editing that host.
- DNS is Terraform-managed in `tyler180/749rmw` (`module.public_749rmw`, public Route 53 zone). The zone has a wildcard `*.749rmw.com` pointing at the private NPM address `192.168.1.55`, so any name without its own record resolves to a LAN-only address and fails from outside the home network and from any device that cannot reach the LAN. `vid` has an explicit public A record, and `video` is an explicit CNAME to `vid`. A new public hostname needs its own record.
- Uploads and imports pass through NPM, whose default proxy timeouts are shorter than the app's two-minute import limit. If a long import or large upload fails at the proxy, raise the timeouts and body-size limit on that proxy host.
