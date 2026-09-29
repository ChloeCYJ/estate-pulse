# Local Administrator Authentication Design

## Goal

Provide one application-local administrator account that can access the existing
legacy administration surface when Auth0 or social login is unavailable. Keep
this account separate from customer identities, finance profiles, and saved
analyses.

## Scope

- One deployment-level local administrator account
- Username and Argon2 password hash stored only in ignored Streamlit secrets
- Native Streamlit login form and session state
- A central authorization gate for every existing administrator entry point
- Administrator access in both Commercial and Legacy UI modes
- Explicit administrator logout
- Safe configuration guidance and a password-hash generation script

The first version does not include local customer accounts, administrator account
management UI, multiple administrators, password reset, OTP, login-attempt
lockout, automatic session expiry, or granular administrator roles.

## Architecture

### Credential boundary

Add a `[local_admin]` section to `.streamlit/secrets.toml`:

```toml
[local_admin]
enabled = false
username = "REPLACE_WITH_ADMIN_USERNAME"
password_hash = "REPLACE_WITH_ARGON2_PASSWORD_HASH"
```

The committed example contains placeholders only. The password is never stored
or logged. A management script accepts a password through a non-echoing prompt
and prints an Argon2 hash for manual placement in the secrets file.

### Authentication service

`LocalAdminAuthService` receives immutable configuration and verifies credentials.
It compares usernames in constant time and verifies the supplied password with
Argon2. Missing, disabled, placeholder, or malformed configuration fails closed
with a sanitized error.

Successful authentication returns a `LocalAdminPrincipal` with the fixed role
`admin`. It does not create an `app_user` or `auth_identity` row and cannot own a
customer finance profile or saved analysis.

### Streamlit session and UI

A Python-only Streamlit adapter renders the local administrator login form,
stores the authenticated principal in dedicated session keys, and clears those
keys on logout. Credentials and hashes never enter React ViewModels or component
events.

Per product decision, the application does not track failed-attempt counts and
does not apply an automatic administrator-session timeout. Authentication remains
valid until explicit logout, browser session termination, or application restart.

### Routing and authorization

- `?admin=1` opens the administrator portal in either UI mode.
- Selecting the existing Legacy administrator menu uses the same authorization
  gate.
- The query parameter selects a route only; it grants no authorization.
- The existing administrator renderer is called only after the gate returns an
  authenticated `LocalAdminPrincipal`.
- Auth0 customer authentication never grants administrator access.

The administrator portal remains a legacy Streamlit surface. No Commercial React
administrator screen is added in this phase.

## Security and failure behavior

- Local administrator authentication is independent of Auth0 and social providers.
- Database-dependent administrator operations still require the application
  database to be available.
- Disabled or invalid configuration shows setup guidance without exposing secret
  values or parser errors.
- Failed login returns one generic message and does not identify whether the
  username or password was wrong.
- Login success, failure, and logout are logged without credential values.
- HTTPS and a strong unique administrator password are required in production.
- Because application lockout is intentionally disabled, production ingress or a
  reverse proxy should rate-limit requests to the administrator route.

## Expected code changes

- Add Argon2 runtime dependency.
- Add local administrator configuration loading without reading credentials from
  `.env` or the database.
- Add the authentication service, Streamlit adapter, and hash generation script.
- Gate administrator routing in `app.py` for both UI modes.
- Extend the safe secrets example and current architecture/operations documents.
- Add focused authentication, routing, and configuration tests after the
  implementation; do not use a test-first workflow for this feature.

## Verification

- Correct credentials open the administrator renderer.
- Incorrect credentials and disabled/malformed configuration fail closed.
- Commercial and Legacy administrator entry points use the same gate.
- Customer Auth0 sessions cannot bypass the gate.
- Logout removes local administrator session state.
- No password or password hash appears in serialized UI data or logs.
- Required Python, frontend, and Streamlit smoke commands remain green.
