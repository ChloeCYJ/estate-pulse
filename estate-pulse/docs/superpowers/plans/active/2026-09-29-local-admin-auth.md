# Local Administrator Authentication Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add one Auth0-independent local administrator account that centrally protects the existing administrator UI in both Commercial and Legacy modes.

**Architecture:** A Python service verifies a deployment-level username and Argon2 password hash loaded from Streamlit secrets, returning a dedicated administrator principal that is never persisted as a customer account. A Streamlit-only adapter owns login/session/logout state, and `app.py` routes every administrator entry point through one authorization gate before calling the existing administrator renderer.

**Tech Stack:** Python 3.14.6, Streamlit 1.59.0, argon2-cffi 25.x, unittest.

**Spec:** `docs/superpowers/specs/2026-09-29-local-admin-auth-design.md`

## Global Constraints

- Do not add local customer accounts, administrator CRUD, multiple administrator accounts, password reset, OTP, login-attempt lockout, automatic session expiry, or granular roles.
- Keep the local administrator principal separate from `app_user`, `auth_identity`, finance profiles, and saved analyses.
- Store only the username and Argon2 hash in ignored Streamlit secrets; never store or log the plaintext password.
- Keep all authentication and authorization decisions in Python. Never send administrator credentials, hashes, or principals to React.
- `?admin=1` selects the administrator portal but never grants authorization.
- Preserve the existing Legacy administrator renderer and all Commercial customer behavior.
- Do not modify or commit `.env`, `cmd.txt`, `data/app.db`, or any real `.streamlit/secrets.toml`.
- Implement first and add focused tests afterward, per the user's explicit instruction not to use TDD.

## Review Focus

- A malformed Argon2 hash must fail closed with a configuration error, not crash or authenticate.
- A correct password paired with the wrong username must receive the same generic failure as a wrong password.
- An Auth0-authenticated customer must not satisfy the local administrator gate.
- Commercial `?admin=1` and the Legacy administrator menu must both use the same gate and must not call the administrator renderer directly.
- Logout must clear only local administrator session keys and must not disturb customer or search session state.

---

### Task 1: Add local administrator credential verification

**Files:**
- Modify: `requirements.txt`
- Create: `modules/services/local_admin_auth_service.py`
- Create: `tests/test_local_admin_auth_service.py`

**Interfaces:**
- Produces: `LocalAdminConfig(enabled: bool, username: str | None, password_hash: str | None)`
- Produces: `LocalAdminPrincipal(username: str, role: Literal["admin"] = "admin")`
- Produces: `LocalAdminAuthenticationError(code: str)` with sanitized codes `admin_disabled`, `admin_not_configured`, and `invalid_credentials`
- Produces: `LocalAdminAuthService(config: LocalAdminConfig)`
- Produces: `LocalAdminAuthService.authenticate(*, username: str, password: str) -> LocalAdminPrincipal`

- [ ] **Step 1: Add the Argon2 dependency**

Add `argon2-cffi>=25.1,<26.0` to `requirements.txt` and install the updated requirements into `.venv314` if the package is not already available.

- [ ] **Step 2: Implement the credential service**

Use `hmac.compare_digest()` for normalized username comparison and `argon2.PasswordHasher().verify()` for password verification. Verify the password even when the username differs so the service does not expose the configured username through a fast path. Convert mismatch, malformed hash, disabled configuration, and placeholder configuration into the exact sanitized error codes above.

- [ ] **Step 3: Add focused service tests after implementation**

Cover correct credentials, wrong password, wrong username with correct password, disabled configuration, missing/placeholder values, malformed hash, fixed `admin` role, and log records that contain no submitted password or configured hash.

- [ ] **Step 4: Run focused verification**

Run: `.\.venv314\Scripts\python -m unittest tests.test_local_admin_auth_service -v`

Expected: all local administrator service tests pass.

- [ ] **Step 5: Commit the credential service**

```powershell
git add requirements.txt modules/services/local_admin_auth_service.py tests/test_local_admin_auth_service.py
git commit -m "Add local administrator credential service"
```

### Task 2: Add the Streamlit administrator session and login gate

**Files:**
- Create: `modules/ui/local_admin_auth.py`
- Create: `tests/test_local_admin_auth.py`

**Interfaces:**
- Consumes: `LocalAdminConfig`, `LocalAdminPrincipal`, and `LocalAdminAuthService` from Task 1
- Produces: `LOCAL_ADMIN_SESSION_KEY = "local_admin_principal"`
- Produces: `load_local_admin_config(secrets: Mapping[str, object]) -> LocalAdminConfig`
- Produces: `load_local_admin_principal(session_state: Mapping[str, object]) -> LocalAdminPrincipal | None`
- Produces: `authenticate_local_admin(*, session_state: MutableMapping[str, object], auth_service: LocalAdminAuthService, username: str, password: str) -> LocalAdminPrincipal | None`
- Produces: `logout_local_admin(session_state: MutableMapping[str, object]) -> None`
- Produces: `render_local_admin_gate(*, auth_service: LocalAdminAuthService, admin_renderer: Callable[[], None]) -> None`

- [ ] **Step 1: Implement safe configuration loading**

Read only the `[local_admin]` mapping from the supplied secrets object. Missing secrets files, absent sections, non-mapping values, and placeholder values must return a disabled or unconfigured `LocalAdminConfig` without exposing the underlying exception.

- [ ] **Step 2: Implement session helpers and the native login form**

Store only `{"username": ..., "role": "admin"}` in the dedicated session key. Render a Streamlit form with username/password inputs, a generic invalid-credentials message, setup guidance for unavailable configuration, and an explicit logout button for an authenticated principal. Do not add attempt counters or timestamps.

- [ ] **Step 3: Add focused adapter tests after implementation**

Cover configuration loading, login success, generic failure, malformed session payload rejection, persistence across reruns without timeout, logout preserving unrelated/customer state, and renderer invocation only after local authentication.

- [ ] **Step 4: Run focused verification**

Run: `.\.venv314\Scripts\python -m unittest tests.test_local_admin_auth -v`

Expected: all Streamlit adapter tests pass.

- [ ] **Step 5: Commit the Streamlit gate**

```powershell
git add modules/ui/local_admin_auth.py tests/test_local_admin_auth.py
git commit -m "Add local administrator login gate"
```

### Task 3: Protect every administrator route

**Files:**
- Modify: `app.py`
- Modify: `tests/test_app_shell.py`

**Interfaces:**
- Consumes: `load_local_admin_config(...)`, `LocalAdminAuthService`, and `render_local_admin_gate(...)`
- Changes: `render_app_shell(*, settings, user_pages, admin_pages, local_admin_auth_service, admin_portal_requested: bool = False) -> None`
- Produces: `is_admin_portal_requested(query_params: Mapping[str, object]) -> bool`, true only when the final `admin` value equals `"1"`

- [ ] **Step 1: Wire local administrator configuration in `main()`**

Load configuration from `st.secrets`, construct one `LocalAdminAuthService`, and calculate the route selector from `st.query_params`. Configuration failures must produce a disabled/unconfigured service rather than aborting customer startup.

- [ ] **Step 2: Gate Commercial and Legacy administrator entry points**

Check `admin_portal_requested` before the Commercial dashboard early return. Route both `?admin=1` and the Legacy administrator menu through `render_local_admin_gate(...)`; no branch may call the administrator renderer directly without the gate.

- [ ] **Step 3: Add routing tests after implementation**

Cover Commercial default dashboard behavior, Commercial `?admin=1`, Legacy user navigation, Legacy administrator navigation, an existing Auth0 customer session that lacks a local administrator session, and query values other than exact `"1"`.

- [ ] **Step 4: Run focused verification**

Run: `.\.venv314\Scripts\python -m unittest tests.test_app_shell tests.test_local_admin_auth -v`

Expected: all app-shell and local administrator gate tests pass.

- [ ] **Step 5: Commit centralized route protection**

```powershell
git add app.py tests/test_app_shell.py
git commit -m "Protect administrator routes with local login"
```

### Task 4: Add secure provisioning guidance and release verification

**Files:**
- Create: `scripts/hash_local_admin_password.py`
- Create: `tests/test_hash_local_admin_password.py`
- Modify: `.streamlit/secrets.toml.example`
- Modify: `tests/test_runtime_metadata.py`
- Modify: `AGENTS.md`
- Modify: `README.md`
- Modify: `docs/ARCHITECTURE.md`
- Modify: `docs/COMMERCIAL_UI.md`
- Modify: `commercial_ui/README.md`
- Modify: `docs/superpowers/plans/active/2026-09-29-local-admin-auth.md`

**Interfaces:**
- Produces: `generate_password_hash(password: str, confirmation: str) -> str`
- Produces command: `.\.venv314\Scripts\python scripts\hash_local_admin_password.py`
- Adds safe `[local_admin]` placeholders to `.streamlit/secrets.toml.example`

- [ ] **Step 1: Implement the non-echoing hash generator**

Use `getpass.getpass()` twice, reject mismatched values, reject passwords shorter than 16 characters, and print only the Argon2 hash. Never accept the password as a command-line argument.

- [ ] **Step 2: Add script and metadata tests after implementation**

Test matching strong passwords, mismatch rejection, short-password rejection, Argon2 verification of the output, the pinned dependency range, ignored real secrets, safe placeholders, and absence of real Argon2 hashes from the committed example.

- [ ] **Step 3: Update operating documentation**

Document `?admin=1`, hash generation, secrets configuration, explicit logout behavior, no lockout/timeout by product decision, HTTPS/strong-password requirements, and recommended ingress rate limiting. State that the account is not a customer identity and that administrator database operations still depend on the database.

- [ ] **Step 4: Run focused documentation and script verification**

Run: `.\.venv314\Scripts\python -m unittest tests.test_hash_local_admin_password tests.test_runtime_metadata -v`

Expected: all provisioning and metadata tests pass.

- [ ] **Step 5: Run the required Python verification**

Run: `.\.venv314\Scripts\python -m unittest discover -s tests -v`

Expected: all available tests pass. If `TEST_DATABASE_URL` is absent, also run the suite excluding `tests/test_postgres_smoke.py` and report PostgreSQL verification as unavailable rather than passed.

- [ ] **Step 6: Run the required frontend verification**

From `commercial_ui/frontend`, run:

```powershell
cmd /c npm.cmd run typecheck
cmd /c npm.cmd run lint
cmd /c npm.cmd run test
cmd /c npm.cmd run build
```

Expected: every command exits 0.

- [ ] **Step 7: Run Streamlit smoke verification**

Run the app in both `legacy` and `commercial` modes. Confirm the normal customer route starts, `?admin=1` shows the local login/setup gate, and no real administrator secret is printed. A real credential login remains pending until the operator configures ignored local secrets.

- [ ] **Step 8: Review and commit the final scope**

Run `git diff --check` and `git status --short`. Stage only the local administrator files and the already requested active-document updates; exclude `.env`, `cmd.txt`, `data/app.db`, and real secrets.

```powershell
git add scripts/hash_local_admin_password.py tests/test_hash_local_admin_password.py .streamlit/secrets.toml.example tests/test_runtime_metadata.py AGENTS.md README.md docs/ARCHITECTURE.md docs/COMMERCIAL_UI.md commercial_ui/README.md docs/superpowers/plans/active/2026-09-29-local-admin-auth.md
git commit -m "Document local administrator operations"
```

## References

- [Streamlit query parameters](https://docs.streamlit.io/develop/api-reference/caching-and-state)
- [Streamlit secrets](https://docs.streamlit.io/develop/api-reference/connections/st.secrets)
- [argon2-cffi password hashing](https://argon2-cffi.readthedocs.io/en/stable/howto.html)
