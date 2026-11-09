# Authentik sign-in

Configured and browser-verified on 2026-11-08 against Stalwart 1.0.3 and
Authentik 2026.8.3. These settings live in each application's persistent database;
Argo CD manages the Kubernetes deployment, not these database objects.

## Sign in

Open https://mail-admin.k8s.749rmw.com/admin/ and enter `tyler180` (your Authentik
username) or `tyler@749rmw.com` (the mapped Stalwart account). If Authentik prompts
for an account, use `tyler180`. Stalwart may request fresh authentication even
when an Authentik session exists. The integration follows the existing Authentik
authentication flow; this change does not configure a new MFA policy.

## Authentik configuration

- Application slug: `stalwart`; provider: `Provider for Stalwart` (ID 4).
- Public client ID: `stalwart-webui`; asymmetric signing with the existing
  Authentik signing certificate. No client secret is required by the WebUI.
- Grants: authorization_code and refresh_token; WebUI uses PKCE S256.
- Strict callback URLs:
  - https://mail-admin.k8s.749rmw.com/admin/oauth/callback
  - https://mail-admin.k8s.749rmw.com/account/oauth/callback
- Access binding: only user `tyler180`, not every Authentik user.
- Standard openid, email and profile mappings plus a dedicated scope mapping
  `urn:stalwart:oauth:scope:full`. Attach the full scope only to this provider.
  Its expression maps the permitted user to the mailbox:

```python
if request.user.username != "tyler180":
    return {}
return {"mail_account": "tyler@749rmw.com"}
```

## Stalwart configuration

- OIDC Directory: `Authentik` (ID jnsfz0ywaaaa).
- Issuer: https://auth.k8s.749rmw.com/application/o/stalwart/ (trailing slash).
- Accepted audience: `stalwart-webui`. Audience and TLS validation remain enabled;
  opaque token validation is disabled, unscoped tokens are rejected.
- Username claim: `mail_account`; name/groups claims unset. This avoids mapping
  the Authentik user's external contact email to an unintended mailbox.
- Authentication singleton directoryId: jnsfz0ywaaaa.
- WebUI Application oauthClientId: `stalwart-webui`; oauthScopes contains
  `urn:stalwart:oauth:scope:full`.
- A matching local public OAuthClient with authorizationCode grant, full scope
  and both callback URLs preserves local recovery sign-in.
- Account `tyler@749rmw.com` has the Admin role explicitly. No default admin role
  or automatic elevation for other identities was configured.

`admin` remains the local recovery username using the encrypted bootstrap
Secret. The recovery credential is intentionally retained until a permanent
independent recovery procedure is established. Do not remove it simply because
SSO works. Do not change the WebUI static client ID without updating both the
Authentik client and Stalwart local OAuthClient.

## Verification and limits

A browser authorization-code/PKCE round trip used the existing Authentik session,
received consent for the dedicated full-access scope, returned to Stalwart and
opened Management with account `tyler@749rmw.com`. A separate Basic-auth API call
verified recovery credentials after enabling OIDC. The configuration survived a
pod replacement before the browser test.

This verifies WebUI SSO, not IMAP/SMTP client OAuth, mail delivery or MFA
challenge enforcement. The two LLC mailboxes and production mail delivery setup
remain unfinished. Back up both applications' databases to preserve this setup.
