# Commercial Authentication and Personal Assets Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Auth0-brokered Google, Kakao, and Naver authentication to Commercial mode and connect one user-owned finance profile plus saved analyses to the authenticated account.

**Architecture:** Streamlit completes OIDC with Auth0, converts verified claims to an internal `app_user`, and injects that user's ID into protected Python workflows. Repositories enforce user ownership for finance profiles and saved analyses; React renders typed authentication and finance ViewModels and emits events without receiving tokens or performing authorization.

**Tech Stack:** Python 3.14.6, Streamlit 1.59.0, Authlib 1.x, SQLite, PostgreSQL/psycopg 3.x, unittest, React 19.1.1, TypeScript 5.8.3, Vitest 3.2.4.

**Spec:** `docs/superpowers/specs/2026-09-28-commercial-auth-personal-assets-design.md`

## Current Checkpoint

- Implemented: Auth0/Streamlit authentication boundary, internal identity persistence, user-owned finance profile, user-scoped saved analyses, protected-action resume, React account/profile UI, safe configuration guidance, and login-required SearchHome actions.
- Verified: non-PostgreSQL Python suite, frontend tests/typecheck/lint/build, and Commercial Streamlit startup health.
- Remaining: live Google/Kakao/Naver login checks, PostgreSQL smoke tests with `TEST_DATABASE_URL`, deployed-flow smoke, and AnalysisDashboard visual/responsive QA.

The detailed checklists below preserve the original execution sequence. Use this
checkpoint and `docs/COMMERCIAL_UI.md` as the current status source instead of
interpreting unchecked historical steps as unimplemented product work.

## Global Constraints

- Keep Streamlit as the owner of authentication, routing, and session state.
- Use Auth0 as the OIDC broker for Google, Kakao, and Naver; do not implement provider OAuth exchanges in React or application services.
- Treat `(issuer, subject)` as the external identity key; never merge accounts by email.
- Keep raw tokens, secrets, DB access, external API calls, and authorization decisions out of React.
- Keep existing legacy finance and analysis operations available for rollback; Commercial methods must never fall back to unowned legacy rows.
- Keep existing unowned `user_finance_profile` and `analysis_result` rows intact.
- Permit at most one owned finance profile per internal user.
- Preserve Python 3.14.6, Streamlit 1.59.0, Node.js 24.18.0, SQLite fallback, and PostgreSQL compatibility.
- Do not modify `.env`, `data/app.db`, `.venv/`, or other protected runtime artifacts.
- Do not implement account-linking UI, email-based linking, membership withdrawal, or multiple finance scenarios in this phase.

## Review Focus

- Missing or malformed OIDC `iss`/`sub` claims must fail closed without creating a partial user; Task 3 tests this.
- Concurrent first-login attempts for the same `(issuer, subject)` must resolve to one account; Task 1 tests uniqueness and recovery.
- Two provider subjects reporting the same email must remain separate accounts; Tasks 1 and 3 test this.
- Login followed by first finance-profile creation must resume the pending analysis without losing search criteria; Task 5 tests this.
- Guessed finance-profile or saved-analysis IDs belonging to another user must return no data and perform no mutation; Task 2 tests this.

---

### Task 1: Add internal users and external identity persistence

**Files:**
- Modify: `modules/repositories/database.py`
- Create: `modules/repositories/user_account_repository.py`
- Create: `migrations/postgres/0003_commercial_auth_user_ownership.sql`
- Create: `tests/test_user_account_repository.py`
- Create: `tests/test_commercial_auth_schema.py`
- Modify: `tests/test_postgres_smoke.py`

**Interfaces:**
- Produces: `UserAccountRepository(database_path: Path | str)`
- Produces: `UserAccountRepository.get_by_identity(*, issuer: str, subject: str) -> dict | None`
- Produces: `UserAccountRepository.create_user_with_identity(*, issuer: str, subject: str, provider: str, email: str | None, display_name: str | None) -> dict`
- Produces: `UserAccountRepository.touch_identity(*, identity_id: int) -> None`
- Produces tables `app_user` and `auth_identity`, unique `(issuer, subject)`, and timestamps stored through the existing UTC helper.
- Produces nullable `user_id` columns on `user_finance_profile` and `analysis_result` for later task use.

- [ ] **Step 1: Write failing SQLite schema and repository tests**

Add tests asserting that initialization creates both account tables, leaves existing finance and analysis rows with `user_id IS NULL`, returns the joined user/identity row, and raises or resolves safely when the same `(issuer, subject)` is created twice.

- [ ] **Step 2: Add the concurrent-login recovery test**

Patch the initial identity lookup to miss once, force the insert path to encounter the unique identity, then assert the repository returns the already-created account and leaves exactly one `app_user` and one `auth_identity`.

- [ ] **Step 3: Run the focused tests and confirm they fail**

Run: `.\.venv314\Scripts\python -m unittest tests.test_commercial_auth_schema tests.test_user_account_repository -v`

Expected: FAIL because the account tables and repository do not exist.

- [ ] **Step 4: Implement the additive SQLite schema**

Define `app_user` before owned tables, define `auth_identity` with its foreign key and unique identity constraint, add nullable ownership columns to fresh schemas, and extend SQLite compatibility initialization to add missing ownership columns and indexes without rewriting existing row values.

- [ ] **Step 5: Implement the atomic account repository**

Use one `get_connection(...)` transaction for `create_user_with_identity(...)`. Insert the application user and identity together; if identity uniqueness wins in another transaction, roll back the attempted user and return `get_by_identity(...)` instead of leaving an orphan.

- [ ] **Step 6: Add the PostgreSQL migration and smoke assertions**

Create `0003_commercial_auth_user_ownership.sql` with idempotent tables, nullable ownership columns, foreign keys, and indexes. Extend the PostgreSQL smoke test to assert the new schema when `TEST_DATABASE_URL` is available.

- [ ] **Step 7: Run the focused tests until green**

Run: `.\.venv314\Scripts\python -m unittest tests.test_commercial_auth_schema tests.test_user_account_repository -v`

Expected: PASS.

- [ ] **Step 8: Commit the persistence foundation**

```powershell
git add modules/repositories/database.py modules/repositories/user_account_repository.py migrations/postgres/0003_commercial_auth_user_ownership.sql tests/test_user_account_repository.py tests/test_commercial_auth_schema.py tests/test_postgres_smoke.py
git commit -m "Add commercial user identity persistence"
```

### Task 2: Enforce ownership in finance and saved-analysis repositories

**Files:**
- Modify: `modules/repositories/finance_profile_repository.py`
- Modify: `modules/repositories/analysis_repository.py`
- Modify: `tests/test_finance_profile_repository.py`
- Create: `tests/test_analysis_repository_ownership.py`

**Interfaces:**
- Consumes: nullable ownership columns and `app_user.id` from Task 1.
- Produces: `UserFinanceProfileRepository.get_for_user(user_id: int) -> dict | None`
- Produces: `UserFinanceProfileRepository.create_for_user(*, user_id: int, payload: Mapping[str, object]) -> int`
- Produces: `UserFinanceProfileRepository.update_for_user(*, user_id: int, payload: Mapping[str, object]) -> bool`
- Produces: `AnalysisRepository.create(payload: dict) -> int`, accepting optional `payload["user_id"]` while retaining legacy unowned creates.
- Produces: `AnalysisRepository.list_recent_for_user(*, user_id: int, limit: int = 20) -> list[dict]`
- Produces: `AnalysisRepository.get_by_id_for_user(*, analysis_id: int, user_id: int) -> dict | None`

- [ ] **Step 1: Write failing finance ownership tests**

Create two users and assert one profile per user, `get_for_user()` isolation, rejection of a second owned profile, and `update_for_user()` returning `False` without changing another user's row.

- [ ] **Step 2: Write failing saved-analysis ownership tests**

Insert owned and unowned analyses and assert `list_recent_for_user()` and `get_by_id_for_user()` return only the requested user's rows. Include a guessed ID from another user and assert `None`.

- [ ] **Step 3: Run the focused tests and confirm they fail**

Run: `.\.venv314\Scripts\python -m unittest tests.test_finance_profile_repository tests.test_analysis_repository_ownership -v`

Expected: FAIL because user-scoped methods are missing.

- [ ] **Step 4: Implement user-scoped finance methods**

Keep existing `create`, `get`, `get_latest`, `list_all`, `update`, and `delete` unchanged for legacy callers. New methods must include `user_id` in every `SELECT` and `UPDATE` predicate and write the owner on insert.

- [ ] **Step 5: Implement user-scoped analysis methods**

Persist optional `user_id` in `create()`. Reuse the existing recent-card joins, adding `ar.user_id = ?`; scope detail lookup by both analysis ID and user ID. Do not change legacy `list_recent()` or `get_by_id()` semantics.

- [ ] **Step 6: Run the focused tests until green**

Run: `.\.venv314\Scripts\python -m unittest tests.test_finance_profile_repository tests.test_analysis_repository_ownership -v`

Expected: PASS.

- [ ] **Step 7: Commit ownership enforcement**

```powershell
git add modules/repositories/finance_profile_repository.py modules/repositories/analysis_repository.py tests/test_finance_profile_repository.py tests/test_analysis_repository_ownership.py
git commit -m "Scope commercial data by user"
```

### Task 3: Build the Auth0-to-Streamlit authentication boundary

**Files:**
- Modify: `requirements.txt`
- Create: `modules/services/auth_service.py`
- Create: `modules/ui/commercial_auth.py`
- Modify: `commercial_ui/component.py`
- Modify: `app.py`
- Create: `tests/test_auth_service.py`
- Create: `tests/test_commercial_auth.py`
- Modify: `tests/test_commercial_component_contract.py`
- Modify: `tests/test_app_shell.py`

**Interfaces:**
- Consumes: `UserAccountRepository` from Task 1 and Streamlit `st.user`, `st.login("auth0")`, and `st.logout()`.
- Produces: `VerifiedIdentity(issuer: str, subject: str, provider: str, email: str | None, display_name: str | None)`.
- Produces: `AuthenticatedUser(id: int, display_name: str | None, email: str | None, provider: str)`.
- Produces: `AuthService.resolve(identity: VerifiedIdentity) -> AuthenticatedUser`.
- Produces: `CommercialAuthContext(user: AuthenticatedUser | None, error_code: str | None)`.
- Produces: `resolve_commercial_auth_context(*, user_claims: Mapping[str, object], auth_service: AuthService) -> CommercialAuthContext`.
- Produces: `build_commercial_auth_view_model(*, context: CommercialAuthContext, has_finance_profile: bool) -> dict[str, object]`.
- Produces: `clear_commercial_sensitive_state(session_state: MutableMapping[str, object]) -> None`.
- Extends `render_commercial_ui(...)` with `auth_view_model` and callbacks for `login_requested`, `logout_requested`, and `finance_profile_requested`.

- [ ] **Step 1: Write failing service tests**

Assert first login provisions one account, repeated login reuses it and updates last-login time, two subjects with the same email create different users, and missing issuer or subject raises a sanitized authentication error before repository mutation.

- [ ] **Step 2: Write failing Streamlit boundary tests**

Assert anonymous, authenticated, and provisioning-error ViewModels; assert logout clears active analysis, pending protected actions, and page notices while preserving the safe search query; assert no raw claims or tokens appear in serialized ViewModels.

- [ ] **Step 3: Run the focused tests and confirm they fail**

Run: `.\.venv314\Scripts\python -m unittest tests.test_auth_service tests.test_commercial_auth tests.test_commercial_component_contract tests.test_app_shell -v`

Expected: FAIL because the auth service, adapter, dependency, and component events are missing.

- [ ] **Step 4: Add Authlib and implement the auth service**

Add `Authlib>=1.3.2,<2.0` to `requirements.txt`. Normalize only `iss`, `sub`, `email`, and `name`; derive the display-only provider label from the Auth0 subject prefix, and pass the stable issuer/subject pair to the account repository.

- [ ] **Step 5: Implement the Streamlit auth adapter**

Treat `is_logged_in` as the session gate, fail closed on malformed claims, return sanitized error codes, and expose login/logout helpers that call Streamlit only from Python. Sensitive-state clearing must not remove the search query keys.

- [ ] **Step 6: Wire account repositories and auth context in `app.py`**

Instantiate `UserAccountRepository` and `AuthService`. Resolve the Commercial auth context once per rerun and inject it into the Commercial root; do not require authentication for the legacy app shell.

- [ ] **Step 7: Extend the component envelope and events**

Add the auth ViewModel to every Commercial envelope and register the three new component callbacks. Do not serialize `st.user`, ID tokens, access tokens, or secrets.

- [ ] **Step 8: Run the focused tests until green**

Run: `.\.venv314\Scripts\python -m unittest tests.test_auth_service tests.test_commercial_auth tests.test_commercial_component_contract tests.test_app_shell -v`

Expected: PASS.

- [ ] **Step 9: Commit the authentication boundary**

```powershell
git add requirements.txt modules/services/auth_service.py modules/ui/commercial_auth.py commercial_ui/component.py app.py tests/test_auth_service.py tests/test_commercial_auth.py tests/test_commercial_component_contract.py tests/test_app_shell.py
git commit -m "Add Auth0 commercial authentication boundary"
```

### Task 4: Connect one current personal finance profile to the authenticated user

**Files:**
- Create: `modules/services/finance_profile_service.py`
- Create: `modules/ui/viewmodels/finance_profile.py`
- Create: `modules/ui/commercial_finance_profile_page.py`
- Modify: `modules/ui/finance_profile_form.py`
- Modify: `modules/ui/commercial_page_state.py`
- Modify: `app.py`
- Create: `tests/test_finance_profile_service.py`
- Create: `tests/test_finance_profile_viewmodel.py`
- Create: `tests/test_commercial_finance_profile_page.py`
- Modify: `tests/test_finance_profile_form.py`
- Modify: `tests/test_commercial_page_state.py`

**Interfaces:**
- Consumes: user-scoped finance repository methods from Task 2 and `AuthenticatedUser` from Task 3.
- Produces: `FinanceProfileValidationError(field_errors: dict[str, str])`.
- Produces: `build_finance_profile_payload(*, cash_amount_eok: float, annual_income_eok: float, interest_rate_percent: float, credit_loan_balance_eok: float, other_loan_balance_eok: float, home_count: int, owned_real_estate_value_eok: float, owned_real_estate_debt_eok: float, use_manual_ltv: bool, manual_ltv_rate: float | None, existing_profile: Mapping[str, object] | None = None) -> dict[str, object]`.
- Produces: `FinanceProfileService.get_current(user_id: int) -> dict | None`.
- Produces: `FinanceProfileService.save_current(*, user_id: int, payload: Mapping[str, object]) -> dict`.
- Produces: `build_finance_profile_view_model(*, profile: dict | None, status: str = "ready", field_errors: dict[str, str] | None = None, notice: dict[str, str] | None = None) -> dict[str, object]`.
- Produces: `render_commercial_finance_profile_page(*, auth_context: CommercialAuthContext, auth_view_model: dict[str, object], finance_profile_service: FinanceProfileService) -> None`.
- Extends `CommercialPageState.commercial_page` with `"finance_profile"` and adds `resume_action: Literal["analysis", "finance_profile"] | None`.

- [ ] **Step 1: Write failing payload and validation tests**

Pin the existing 억-to-won conversion, derived total debt, percent-to-ratio conversion, required positive cash, ambiguous `0 < interest_rate_percent < 1`, and manual LTV range. Update the legacy form test to consume the shared payload builder without changing legacy behavior.

- [ ] **Step 2: Write failing profile service and ViewModel tests**

Assert first save creates, later save updates the same row ID, a different user's row is untouched, empty state includes zero/default form values, and error state includes field errors without raw exceptions.

- [ ] **Step 3: Write failing page-state and page-event tests**

Assert an authenticated user can open the finance page, submit `finance_profile_saved`, receive a success notice, and return to SearchHome while retaining `resume_action="analysis"` when an analysis was pending.

- [ ] **Step 4: Run the focused tests and confirm they fail**

Run: `.\.venv314\Scripts\python -m unittest tests.test_finance_profile_service tests.test_finance_profile_viewmodel tests.test_commercial_finance_profile_page tests.test_finance_profile_form tests.test_commercial_page_state -v`

Expected: FAIL because the service, ViewModel, page, and route do not exist.

- [ ] **Step 5: Extract and preserve finance normalization rules**

Move the shared normalization and validation into `finance_profile_service.py`; make the legacy form call the shared builder. Keep the stored schema fields and monetary semantics unchanged.

- [ ] **Step 6: Implement current-profile upsert and the page adapter**

The service resolves only `get_for_user(user_id)`, creates when absent, and updates by owner when present. The page rejects anonymous access before repository calls, maps component payloads through the shared builder, and returns sanitized field/storage errors.

- [ ] **Step 7: Add the finance route to canonical Commercial state and app routing**

Preserve pending search and analysis state when entering the page. On successful save, route back to SearchHome; keep the pending analysis resume marker until Task 5 consumes it.

- [ ] **Step 8: Run the focused tests until green**

Run: `.\.venv314\Scripts\python -m unittest tests.test_finance_profile_service tests.test_finance_profile_viewmodel tests.test_commercial_finance_profile_page tests.test_finance_profile_form tests.test_commercial_page_state -v`

Expected: PASS.

- [ ] **Step 9: Commit the personal-assets workflow**

```powershell
git add modules/services/finance_profile_service.py modules/ui/viewmodels/finance_profile.py modules/ui/commercial_finance_profile_page.py modules/ui/finance_profile_form.py modules/ui/commercial_page_state.py app.py tests/test_finance_profile_service.py tests/test_finance_profile_viewmodel.py tests/test_commercial_finance_profile_page.py tests/test_finance_profile_form.py tests/test_commercial_page_state.py
git commit -m "Connect personal assets to commercial users"
```

### Task 5: Gate and resume Commercial analysis and saved results

**Files:**
- Modify: `modules/services/analysis_service.py`
- Modify: `modules/ui/search_home_page.py`
- Modify: `modules/ui/commercial_analysis_page.py`
- Modify: `modules/ui/viewmodels/search_home.py`
- Modify: `app.py`
- Modify: `tests/test_analysis_service_phase2.py`
- Modify: `tests/test_search_home_page.py`
- Modify: `tests/test_commercial_analysis_page.py`
- Modify: `tests/test_search_home_viewmodel.py`
- Modify: `tests/test_app_shell.py`

**Interfaces:**
- Consumes: authenticated internal user ID, user-scoped repositories, finance profile service, and `resume_action` from Tasks 2–4.
- Changes: `AnalysisService.save_completed_analysis_result(active_result: dict, *, user_id: int | None = None) -> int`.
- Changes: `render_search_home_page(..., auth_context: CommercialAuthContext, auth_view_model: dict[str, object], finance_profile_service: FinanceProfileService) -> None`.
- Changes: `handle_analysis_requested(..., user_id: int | None, finance_profile_service: FinanceProfileService) -> CommercialPageState`.
- Changes: `render_commercial_analysis_page(*, analysis_repository, analysis_service, auth_context: CommercialAuthContext, auth_view_model: dict[str, object]) -> None`.
- Changes: `handle_save_requested(..., user_id: int | None) -> CommercialPageState`.
- Produces: `resume_pending_commercial_action(...) -> bool`, returning whether the caller must rerun.

- [ ] **Step 1: Write failing guest-gate tests**

Assert public search works without a user, recent saved analyses are empty for guests, analysis/save/profile navigation stores a sanitized login-required notice, no protected repository/service call occurs, and the pending analysis request remains available.

- [ ] **Step 2: Write failing resume-flow tests**

Start as a guest with a search query and pending analysis, simulate successful login with no profile, save the first profile, then assert the flow returns to SearchHome and executes the original analysis once with that user's profile ID while retaining the original query.

- [ ] **Step 3: Write failing owned-analysis tests**

Assert Commercial recent cards use `list_recent_for_user`, saved detail uses `get_by_id_for_user`, saving passes `user_id` into `save_completed_analysis_result`, and a cross-user saved analysis renders not-found without exposing row data.

- [ ] **Step 4: Run the focused tests and confirm they fail**

Run: `.\.venv314\Scripts\python -m unittest tests.test_analysis_service_phase2 tests.test_search_home_page tests.test_commercial_analysis_page tests.test_search_home_viewmodel tests.test_app_shell -v`

Expected: FAIL because protected actions still use global finance and analysis access.

- [ ] **Step 5: Scope SearchHome data and analysis execution**

Guests receive no recent saved rows. Authenticated users use `get_for_user()` and `list_recent_for_user()`. Remove every Commercial `get_latest()` call. A guest analysis request records `resume_action="analysis"`; an authenticated request with no profile routes to `finance_profile`.

- [ ] **Step 6: Implement deterministic resume behavior**

On an authenticated rerun, consume `resume_action="finance_profile"` by routing to the finance page. For `resume_action="analysis"`, route to finance when missing; otherwise clear the marker before executing the preserved request so failures do not loop. Preserve safe search criteria throughout.

- [ ] **Step 7: Scope save and reopen behavior**

Write `user_id` when promoting a live result to saved. Reopen and verify it through `get_by_id_for_user()`. Keep existing legacy service calls valid through the optional `user_id=None` default.

- [ ] **Step 8: Run the focused tests until green**

Run: `.\.venv314\Scripts\python -m unittest tests.test_analysis_service_phase2 tests.test_search_home_page tests.test_commercial_analysis_page tests.test_search_home_viewmodel tests.test_app_shell -v`

Expected: PASS.

- [ ] **Step 9: Commit the protected Commercial flow**

```powershell
git add modules/services/analysis_service.py modules/ui/search_home_page.py modules/ui/commercial_analysis_page.py modules/ui/viewmodels/search_home.py app.py tests/test_analysis_service_phase2.py tests/test_search_home_page.py tests/test_commercial_analysis_page.py tests/test_search_home_viewmodel.py tests/test_app_shell.py
git commit -m "Protect and resume commercial analysis"
```

### Task 6: Render authentication and personal assets in React

**Files:**
- Create: `commercial_ui/frontend/src/contracts/auth.ts`
- Create: `commercial_ui/frontend/src/contracts/financeProfile.ts`
- Modify: `commercial_ui/frontend/src/contracts/searchHome.ts`
- Modify: `commercial_ui/frontend/src/contracts/analysisDashboard.ts`
- Modify: `commercial_ui/frontend/src/contracts/index.ts`
- Create: `commercial_ui/frontend/src/components/AccountActions.tsx`
- Create: `commercial_ui/frontend/src/renderers/FinanceProfileRenderer.tsx`
- Create: `commercial_ui/frontend/src/renderers/FinanceProfileRenderer.test.tsx`
- Modify: `commercial_ui/frontend/src/renderers/SearchHomeRenderer.tsx`
- Modify: `commercial_ui/frontend/src/renderers/SearchHomeRenderer.test.tsx`
- Modify: `commercial_ui/frontend/src/renderers/AnalysisDashboardRenderer.tsx`
- Modify: `commercial_ui/frontend/src/renderers/AnalysisDashboardRenderer.test.tsx`
- Modify: `commercial_ui/frontend/src/index.tsx`
- Modify: `commercial_ui/frontend/src/design-system/global.css`

**Interfaces:**
- Consumes: auth and finance ViewModels plus component events from Tasks 3–5.
- Produces: `CommercialAuthViewModel` with `status`, `display_name`, `email`, `provider`, `finance_profile_exists`, and sanitized `error`.
- Produces: `FinanceProfileViewModel` with `page_status`, `form`, `summary`, `field_errors`, and `notice`.
- Produces: `FinanceProfileEnvelope` with `page: "finance-profile"`.
- Extends `CommercialUIState` with `login_requested`, `logout_requested`, `finance_profile_requested`, `finance_profile_saved`, and `finance_profile_back_requested`.

- [ ] **Step 1: Write failing account-action tests**

For SearchHome and AnalysisDashboard, assert anonymous users see a login button, authenticated users see their display name plus logout and personal-assets actions, and auth errors expose only the supplied friendly message.

- [ ] **Step 2: Write failing finance renderer tests**

Assert empty, populated, saving, validation-error, and storage-error states; assert numeric inputs preserve zero; submit the form and verify the exact 억/percent payload; assert back, login, and logout triggers.

- [ ] **Step 3: Write the login-required prompt test**

Render the pending analysis with an `auth_required` notice and assert the login action is keyboard accessible while search inputs and results remain present.

- [ ] **Step 4: Run frontend tests and confirm they fail**

Run from `commercial_ui/frontend`: `cmd /c npm.cmd run test`

Expected: FAIL because auth contracts, events, and finance renderer are missing.

- [ ] **Step 5: Implement shared account actions and typed contracts**

Render provider-neutral login/logout controls; Auth0 Universal Login owns the provider selection. Keep all event payloads data-only and never include credentials or owner IDs.

- [ ] **Step 6: Implement the finance profile page**

Use the existing design tokens and shared Korean currency formatter for summaries. Include explicit loading, empty/create, edit, validation, save-in-progress, and error states. Do not calculate stored debt or convert values into persistence units in React; submit UI units to Python.

- [ ] **Step 7: Route the new envelope and wire triggers**

Add the `finance-profile` branch in `src/index.tsx`; mount `AccountActions` consistently on all Commercial pages; emit the new trigger fields registered by `commercial_ui/component.py`.

- [ ] **Step 8: Run frontend checks until green**

Run from `commercial_ui/frontend`:

```powershell
cmd /c npm.cmd run typecheck
cmd /c npm.cmd run lint
cmd /c npm.cmd run test
```

Expected: all commands exit 0.

- [ ] **Step 9: Commit the Commercial frontend**

```powershell
git add commercial_ui/frontend/src
git commit -m "Add commercial login and personal assets UI"
```

### Task 7: Add safe configuration guidance and run release verification

**Files:**
- Modify: `.gitignore`
- Create: `.streamlit/secrets.toml.example`
- Modify: `README.md`
- Modify: `docs/ARCHITECTURE.md`
- Modify: `docs/COMMERCIAL_UI.md`
- Modify: `commercial_ui/README.md`
- Modify: `tests/test_runtime_metadata.py`

**Interfaces:**
- Consumes: final Auth0 provider name `auth0` and the implemented secret keys.
- Produces: a credential-free Streamlit OIDC template and setup instructions for Auth0 Universal Login plus Google, Kakao, and Naver callback/logout URLs.

- [ ] **Step 1: Write the failing configuration guard test**

Assert `.streamlit/secrets.toml` is ignored, the example contains placeholders rather than credential values, `requirements.txt` pins Authlib in the supported major range, and documentation names all three providers and the `auth0` Streamlit provider key.

- [ ] **Step 2: Run the guard test and confirm it fails**

Run: `.\.venv314\Scripts\python -m unittest tests.test_runtime_metadata -v`

Expected: FAIL until the safe template and guidance exist.

- [ ] **Step 3: Add the safe Auth0 configuration template and documentation**

Ignore the real secrets file. Document Auth0 application, allowed callback/logout URLs, provider connections, local/production separation, and the fact that actual values must never be committed. Update architecture and Commercial status without including setup credentials.

- [ ] **Step 4: Run all Python tests**

Run: `.\.venv314\Scripts\python -m unittest discover -s tests -v`

Expected: PASS, except PostgreSQL smoke tests may explicitly skip when `TEST_DATABASE_URL` is unavailable; record that skip rather than describing it as a pass.

- [ ] **Step 5: Run all frontend verification**

Run from `commercial_ui/frontend`:

```powershell
cmd /c npm.cmd run typecheck
cmd /c npm.cmd run lint
cmd /c npm.cmd run test
cmd /c npm.cmd run build
```

Expected: all commands exit 0.

- [ ] **Step 6: Run Streamlit smoke verification**

Run: `.\.venv314\Scripts\python -m streamlit run app.py`

Verify startup health in both `legacy` and `commercial` UI modes. Without Auth0 credentials, verify the app fails safely with setup guidance rather than exposing an exception or secret value.

- [ ] **Step 7: Run manual Auth0 provider smoke tests when credentials are available**

For Google, Kakao, and Naver: authenticate, confirm one internal identity mapping, create/update the current finance profile, run and save an analysis, log out, and confirm protected data is hidden. If credentials are unavailable, report this verification as pending.

- [ ] **Step 8: Review the final diff and commit documentation/configuration**

```powershell
git diff --check
git status --short
git add .gitignore .streamlit/secrets.toml.example README.md docs/ARCHITECTURE.md docs/COMMERCIAL_UI.md commercial_ui/README.md tests/test_runtime_metadata.py
git commit -m "Document commercial authentication setup"
```

- [ ] **Step 9: Push only requested commits to `origin/dev-ing`**

Run: `git push origin dev-ing`

Expected: the remote `dev-ing` branch advances without staging or committing `.env`, `cmd.txt`, or `data/app.db`.

### 2026-09-30 authentication hardening checkpoint

- The Commercial adapter now distinguishes configuration, login-start, identity, and account-resolution failures with sanitized error codes.
- Required Auth0 settings and callback/discovery URL shapes are validated before starting the redirect.
- Google, Kakao, and Naver are normalized from a verified Auth0 connection claim with subject-prefix fallback; unknown connections remain provider-neutral.
- Live provider completion remains an external release check because it requires real Auth0 configuration and provider test accounts.

## Self-Review Checklist

- [ ] Every protected workflow receives the internal user ID from verified Streamlit session context, never from React.
- [ ] No Commercial code path calls `get_latest()` for a finance profile or unscoped `list_recent()`/`get_by_id()` for saved analyses.
- [ ] Existing legacy finance and analysis repository methods remain available and unowned legacy rows stay unchanged.
- [ ] Matching email addresses do not link accounts.
- [ ] Finance creation and update keep one stable profile ID per user.
- [ ] A failed profile update preserves the stored row.
- [ ] Logout clears sensitive Commercial state and preserves only safe search criteria.
- [ ] The pending analysis runs at most once after login/profile completion.
- [ ] React receives no raw claims, tokens, secrets, or client-controlled owner IDs.
- [ ] Full verification matches `AGENTS.md`, and unavailable PostgreSQL/provider smoke tests are reported accurately.
