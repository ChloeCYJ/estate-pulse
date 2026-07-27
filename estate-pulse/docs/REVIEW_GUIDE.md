# Estate Pulse Review Guide

## Purpose

Use this document to review a proposed change before approval or completion.
It focuses on scope, regressions, and proof.

## Inputs

Review against:

- the user request
- the relevant active plan
- the changed files
- the verification commands and results

Use archive documents only when active documents are missing necessary context.

## Scope Checklist

- Is the requested problem clear?
- Is the change limited to the requested scope?
- Does it avoid unrelated refactors?
- Does it preserve existing user changes outside the requested scope?

## Boundary Checklist

- Does Streamlit remain the app shell?
- Does Python keep business logic, repository access, and external API calls?
- Do repositories own SQL and persistence?
- Do analyzers own deterministic calculations?
- Does React avoid DB access, repository access, external API calls, and calculations?

## Regression Checklist

- Does the change preserve existing analysis behavior unless explicitly changed?
- Does it preserve SQLite fallback together with PostgreSQL runtime support?
- Does it keep legacy UI available when rollback is required?
- Does it avoid protected paths and direct DB-file edits?

## Documentation Checklist

- Are user-facing docs still accurate?
- Are architecture rules documented in `docs/ARCHITECTURE.md` rather than repeated elsewhere?
- Is current UI migration context documented in `docs/COMMERCIAL_UI.md`?
- Are old plans/specs preserved in archive instead of being deleted?

## Verification Checklist

- Were the commands that prove the claim actually run?
- Are failures, skips, or unverified items reported explicitly?
- Is the final report based on fresh output rather than assumption?

## Review Result Template

```text
Review Result: GO / HOLD / REJECT

Scope:

Boundary Notes:

Verification:

Risks:

Documentation Impact:
```
