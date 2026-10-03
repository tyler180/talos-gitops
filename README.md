
## Jobtracker continuous deployment

Jobtracker releases open `automation/jobtracker` PRs through `tyler180-gitops-bot[bot]`. The Jobtracker GitOps workflow tests the promotion policy, renders Jobtracker and infrastructure, and automatically merges only advancing digest-pinned image changes. It loads the unattended promotion policy from the trusted base commit and locks the merge to the validated head SHA. Storage, routing, environment, Argo registration, and other infrastructure changes require normal PRs.

The Jobtracker Application enables automated sync, self-healing, and bounded retries with pruning and empty-app deletion disabled. Root and other apps retain their existing sync policy. To roll back, merge a normal human PR restoring a previous digest. To pause deployment, change Jobtracker's `spec.syncPolicy.automated.enabled` to `false` in GitOps and reconcile that Application through root.
