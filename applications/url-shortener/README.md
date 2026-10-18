# URL shortener / video host

Deploys `tyler180/url-shortener` (the current source implements a video host and importer).

Open https://url-shortener.k8s.749rmw.com/import to import a video, or `/upload/local` to upload through the browser. Generated links use this HTTPS hostname. This is a new installation; existing local videos and Twitter cookies are not migrated.

One replica uses a 10 GiB `nas-nfs` volume at `/videos`, with a Recreate strategy to avoid overlapping cleanup jobs. The app's default retention deletes videos after 30 days. NFS capacity requests do not necessarily enforce a NAS quota.

`url-shortener-auth` is encrypted under `infrastructure/secrets/`. Its `token` key supplies the shared token required by the `/upload` API. The application does not authenticate `/import` or `/upload/local`; the token is not a site login.

The image is built from source commit `072b0f862cbbd21da0588d046fe971f38c0397ce` using `server/Dockerfile` for linux/amd64 and pinned by digest. The app repository's current release workflow targets a different source layout and needs repair before future automated releases can work. Publish and verify a new image, then update `deployment.yaml` through a reviewed GitOps PR.

Validation:

```sh
kubectl kustomize applications/url-shortener
kubectl kustomize infrastructure
```

Argo CD automatically syncs this application without pruning. Root and cluster-secrets retain their existing manual sync policies. Roll back by restoring the previous image digest in Git; the PVC remains intact.
