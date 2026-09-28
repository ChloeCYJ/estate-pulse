# Commercial SNS Authentication and Personal Assets Design

**Date:** 2026-09-28
**Status:** Approved conversational design

## 1. Purpose

Add SNS login and sign-up to Commercial mode and connect the existing personal finance profile feature to the authenticated user. Users may search without signing in, but analysis execution, result persistence, and personal asset management require authentication.

Success means:

- users can authenticate through Google, Kakao, or Naver;
- each authenticated user has at most one current personal finance profile;
- analysis always uses the authenticated user's profile;
- one user cannot read or change another user's data;
- the legacy UI and existing unowned finance data remain available for rollback and are not silently assigned to a user.

## 2. Scope

### Included

- Auth0 as the external authentication broker;
- Streamlit authentication through Auth0 using OIDC;
- Google, Kakao, and Naver connections presented by Auth0 Universal Login;
- internal application users separated from external identities;
- first-login user provisioning and returning-user lookup;
- login-gated analysis, saved results, and personal asset management;
- creation and update of one current finance profile per user;
- additive migration of the existing finance profile storage;
- Commercial UI loading, empty, cancellation, and error states;
- automated tests and provider smoke-test guidance.

### Excluded from the first release

- account-linking UI;
- automatic linking based on matching email addresses;
- membership withdrawal and data deletion workflow;
- multiple saved asset scenarios or finance-profile history;
- changes to the legacy UI's current data behavior.

The data model must permit a later verified account-linking flow without redesigning user-owned records.

## 3. Authentication Architecture

Streamlit owns authentication, routing, and session state. It connects to Auth0 with OIDC. Auth0 brokers the Google, Kakao, and Naver provider flows and returns a verified identity to Streamlit.

An `AuthService` converts the verified OIDC identity into an internal application user. On first login it creates the internal user and identity mapping in one workflow; on later logins it resolves the existing mapping. Email is display/contact data only and is never used as the account ownership key.

React receives only a JSON-serializable authentication ViewModel, such as login state, display name, and whether a finance profile exists. React never receives provider credentials, raw tokens, DB access, or authorization responsibility.

The initial release does not expose account linking. Separate Auth0 subjects remain separate application accounts even when their email values match. A future verified linking flow may attach more than one external identity to the same internal user.

## 4. Data Model

### `app_user`

Represents the stable internal owner of application data.

Required concepts:

- internal immutable ID;
- display name and email as optional provider-derived attributes;
- active status;
- created and updated timestamps.

### `auth_identity`

Maps an external authenticated identity to an internal user.

Required concepts:

- internal user ID;
- OIDC issuer;
- OIDC subject;
- provider/connection label for display and diagnostics;
- created and last-login timestamps;
- a unique constraint on `(issuer, subject)`.

No automatic merge occurs when two identities report the same email.

### `user_finance_profile`

The existing finance profile remains the source for personal asset values. Add an owner reference with these rules:

- `user_id` is nullable only so existing legacy rows can remain unowned;
- every new Commercial write must supply the authenticated internal user ID;
- a unique constraint or equivalent partial unique index permits at most one owned profile per user;
- Commercial repository methods require a user ID and never fall back to the latest global row;
- legacy rows with no owner are not returned to Commercial mode and are not automatically migrated to the first user who signs in.

The migration is additive. It must not delete or rewrite existing finance-profile values.

### `analysis_result`

Saved Commercial analyses are user-owned data and require the same isolation boundary:

- add a nullable `user_id` so existing legacy rows remain intact;
- every new Commercial save records the authenticated internal user ID;
- Commercial recent-history and detail queries require `user_id` and never return another user's or an unowned legacy row;
- legacy analysis queries remain explicitly separate where rollback behavior requires them.

## 5. Component Responsibilities

- **Streamlit app shell:** invokes login/logout, owns the verified session, preserves safe pending navigation, and provides authenticated context to services.
- **Auth service:** normalizes verified identity claims and provisions or resolves the internal user.
- **User and identity repositories:** own user/identity persistence and uniqueness queries.
- **Finance profile repository:** exposes user-scoped create, get, and update operations while preserving explicitly separate legacy operations where required.
- **Analysis repository:** scopes Commercial save, recent-history, and detail access by internal user ID while preserving explicitly separate legacy operations where required.
- **Commercial workflow services:** require authenticated user context for protected operations and pass the internal user ID to repositories.
- **Python adapters:** build authentication and finance-profile ViewModels.
- **React Commercial UI:** renders login state, access prompts, profile forms, and loading/empty/error states; it does not make authorization decisions.

## 6. User Flow

### Public search

1. A guest enters search conditions and views property search results.
2. Search state remains in the Streamlit session.
3. Selecting analysis, result saving, or personal assets displays a login requirement.

### Login and return

1. The user selects login and is redirected to Auth0 Universal Login.
2. Auth0 offers Google, Kakao, and Naver.
3. After successful authentication, Streamlit resolves the internal user.
4. The user returns to the pending Commercial task with their safe search conditions preserved.
5. Login cancellation or failure returns the user to search with a retry message and without losing safe search state.

### Personal assets and analysis

1. A signed-in user with no finance profile sees the existing finance input experience in an empty state.
2. Saving creates the user's single current profile.
3. A returning user edits the same profile; the operation updates rather than appends another profile.
4. Analysis resolves the profile exclusively by the authenticated internal user ID.
5. Missing profile data blocks analysis and directs the user to complete the profile.
6. Logout clears authenticated and sensitive in-memory UI state but does not delete persisted user data.

## 7. Authorization and Security

- Secrets and provider credentials live only in Streamlit secrets or deployment environment configuration and are never committed.
- Raw authentication tokens are not stored in the application DB, written to logs, or sent to React.
- Protected services obtain the internal user ID from verified server-side session context, never from a client-supplied owner ID.
- Every profile read and mutation includes owner scope in the repository query.
- Auth identity uniqueness and one-profile-per-user constraints are enforced in the DB as well as in service validation.
- Authentication failures must not create partial internal users or identities.
- Finance-profile validation completes before persistence; a failed update preserves the previously stored profile.
- Logs may contain internal correlation identifiers but must not include tokens or full sensitive financial payloads.

## 8. Error and UI States

Commercial UI must explicitly represent:

- authentication loading and redirect initiation;
- login cancelled or failed, with retry;
- authenticated user provisioning failure;
- no finance profile, with a clear create action;
- finance profile loading and save-in-progress;
- validation failure with field-level guidance;
- storage failure with the prior value preserved;
- partial downstream analysis data without losing the authenticated context;
- expired session, returning the user to login while retaining only safe search criteria.

Messages must not expose provider tokens, database details, or raw exception text.

## 9. Compatibility and Rollback

- The legacy UI remains available under the existing rollback path.
- Existing unowned finance rows remain intact and are ignored by Commercial user-scoped queries.
- Existing unowned analysis rows remain intact and are ignored by Commercial user-scoped queries.
- Commercial mode must stop using `get_latest()` or any equivalent global-latest fallback for analysis.
- Schema initialization and migrations must support the project's configured database implementations.
- Disabling the Commercial feature flag must restore the prior user-visible path without requiring destructive data rollback.

## 10. Verification

Automated coverage must include:

- first login creates one internal user and identity;
- repeated login reuses the same internal user;
- different subjects with matching email remain separate;
- identity uniqueness is enforced;
- a user can create and update exactly one current finance profile;
- cross-user profile reads and writes are rejected or return no data;
- analysis receives only the signed-in user's profile;
- analysis is blocked when the user is unauthenticated or has no profile;
- safe search state resumes after successful login;
- authentication cancellation and failure preserve public search usability;
- legacy behavior remains covered by regression tests;
- secrets and raw tokens do not appear in serialized frontend payloads.

Required project verification remains:

```powershell
.\.venv314\Scripts\python -m unittest discover -s tests -v
```

From `commercial_ui/frontend`:

```powershell
cmd /c npm.cmd run typecheck
cmd /c npm.cmd run lint
cmd /c npm.cmd run test
cmd /c npm.cmd run build
```

Run the Streamlit smoke command and manually verify each configured provider in the development Auth0 tenant. Provider smoke tests require registered callback/logout URLs for the actual development origin.

## 11. External Configuration

Implementation depends on configuration outside this repository:

- an Auth0 application for the Streamlit OIDC client;
- Google, Kakao, and Naver connections enabled in Auth0;
- provider applications with callback URLs registered for the Auth0 tenant;
- Streamlit OIDC redirect and logout URLs registered in Auth0;
- development and production credentials stored separately.

Repository documentation must list required secret names and setup steps without including credential values.

## 12. Reference Documentation

- [Streamlit `st.login`](https://docs.streamlit.io/develop/api-reference/user/st.login)
- [Auth0 custom OAuth 2.0 social connections](https://auth0.com/docs/authenticate/identity-providers/social-identity-providers/oauth2)
- [Google OpenID Connect](https://developers.google.com/identity/openid-connect/reference)
- [Kakao Login OpenID Connect](https://developers.kakao.com/docs/ko/kakaologin/utilize)
- [Naver Login API](https://developers.naver.com/docs/login/api/api.md)
