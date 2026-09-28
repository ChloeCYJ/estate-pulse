# Estate Pulse Codex Guide

## Purpose

This document defines the working procedure for Codex tasks. It does not repeat
system architecture or package setup details.

## Default Read Set

For current Commercial UI work, read:

1. `AGENTS.md`
2. `docs/ARCHITECTURE.md`
3. `docs/COMMERCIAL_UI.md`
4. `docs/superpowers/plans/active/<current-plan>.md`

Read archive docs only when the active documents do not contain the needed context.

## Task Flow

### 1. Investigate

- Read only the files needed for the requested scope.
- Inspect existing implementation before proposing changes.
- Classify the area as `Already Implemented`, `Partially Implemented`, or `Missing`.
- Check `git status --short` before edits.
- Confirm whether data described as personal is actually scoped by an authenticated user in the schema and repository queries.

### 2. Plan

- Define the smallest safe change scope.
- Reuse existing modules before adding new ones.
- Keep unrelated refactors out of scope.
- If the task has multiple distinct steps, maintain a short working plan while executing.

### 3. Implement

- Follow the repository boundaries documented in `docs/ARCHITECTURE.md`.
- Keep business logic in Python and rendering logic in the appropriate UI layer.
- Preserve existing user changes in tracked files unless the task explicitly requires updating them.
- Keep commercial navigation in `CommercialPageState`; do not add competing page-selection session keys.
- Keep authentication identity, authorization, and user-owned persistence in Python/repository layers.

### 4. Verify

- Run the commands that prove the requested outcome.
- Do not claim completion from reasoning alone.
- If something could not be verified, state that directly.
- PostgreSQL smoke tests require `TEST_DATABASE_URL` targeting a dedicated `*_test` database; report the missing environment separately from application test failures.

### 5. Report

When the user does not provide a custom format, report:

- Scope handled
- Files changed
- Commands run
- Actual results
- Known limitations or follow-up items

## Documentation Usage

- `README.md` is the start page for humans.
- `docs/ARCHITECTURE.md` is the long-lived system map.
- `docs/COMMERCIAL_UI.md` is the active UI migration context.
- `docs/REVIEW_GUIDE.md` is the review checklist.
- `docs/superpowers/plans/active/` is the current execution plan location.
- `docs/superpowers/*/archive/` is reference-only history.

## Do Not Do

- Do not read every archive document by default.
- Do not rewrite documentation wholesale unless the task explicitly asks for it.
- Do not report success without fresh verification evidence.
- Do not edit archived plans/specs to describe current behavior; update living docs and the active plan instead.
