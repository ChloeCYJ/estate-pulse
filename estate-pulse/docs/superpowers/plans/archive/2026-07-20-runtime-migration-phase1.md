# Runtime Migration Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move the project runtime baseline from Python 3.9 / Streamlit 1.50 / Node 20 to Python 3.14.6 / Streamlit 1.59.0 / Node 24.18.0 without introducing any Commercial UI implementation work.

**Architecture:** Keep the existing Streamlit app, repository/service/analyzer boundaries, and dependency management style. Create a new `.venv314`, pin the runtime versions, make only the minimum compatibility fixes required for Python 3.14 and Streamlit 1.59, and verify the current app behavior with the full Python test suite plus a Streamlit smoke test.

**Tech Stack:** Python 3.14.6, pip + requirements.txt, Streamlit 1.59.0, Node 24.18.0, npm.cmd, unittest

## Global Constraints

- Keep changes minimal and localized.
- Do not refactor unrelated files.
- Preserve SQLite fallback and PostgreSQL runtime support together.
- Do not modify `.venv/`, `.git/`, `.env`, `*.db`, `__pycache__/`, or `*.pyc`.
- Do not add React, Vite, `commercial_ui`, SearchHome, or any UI redesign work.
- Do not overwrite existing user changes in `AGENTS.md` or `docs/superpowers/`.
- Use `npm.cmd` / `npx.cmd` instead of PowerShell `npm` / `npx`.

---

### Task 1: Analyze Runtime Inputs and Pinpoint Compatibility Surface

**Files:**
- Modify: `docs/superpowers/plans/archive/2026-07-20-runtime-migration-phase1.md`
- Test: runtime inspection commands only

**Interfaces:**
- Consumes: existing `requirements.txt`, `app.py`, `modules/`, `.gitignore`
- Produces: a concrete list of files to update and compatibility hotspots for Tasks 2-5

- [ ] Record current runtime commands and outputs
- [ ] Inspect dependency definitions, lock files, and runtime version files
- [ ] Inspect Streamlit usage sites and smoke-test entrypoint shape

### Task 2: Add Failing Coverage for Runtime Metadata / Compatibility Contracts

**Files:**
- Create: `tests/test_runtime_metadata.py`
- Test: `tests/test_runtime_metadata.py`

**Interfaces:**
- Consumes: current repository files and version markers
- Produces: regression tests covering runtime version file presence and requirements pinning

- [ ] Write failing unittest coverage for `.python-version`, `.nvmrc`, and pinned `streamlit==1.59.0`
- [ ] Run the targeted tests to confirm they fail first

### Task 3: Implement Runtime Version Files and Dependency Pinning

**Files:**
- Create: `.python-version`
- Create: `.nvmrc`
- Modify: `requirements.txt`
- Test: `tests/test_runtime_metadata.py`

**Interfaces:**
- Consumes: Task 2 failing tests
- Produces: pinned runtime metadata for Python 3.14.6, Node 24.18.0, and Streamlit 1.59.0

- [ ] Add `.python-version` with `3.14.6`
- [ ] Add `.nvmrc` with `24.18.0`
- [ ] Change Streamlit requirement to `streamlit==1.59.0`
- [ ] Re-run targeted tests until they pass

### Task 4: Build New Python 3.14 Environment and Install Dependencies

**Files:**
- Create: `.tmp-python39-freeze.txt`
- Create: `.venv314/` (generated environment, not committed)
- Test: venv creation and pip install commands

**Interfaces:**
- Consumes: pinned runtime files and `requirements.txt`
- Produces: a working `.venv314` with all dependencies installed, or a precise blocker report

- [ ] Export comparison-only freeze from existing `.venv`
- [ ] Create `.venv314`
- [ ] Upgrade `pip`, `setuptools`, and `wheel`
- [ ] Install from the existing dependency definition file
- [ ] If install fails, stop and report exact package/version compatibility details before any broader changes

### Task 5: Apply Minimum Python 3.14 / Streamlit 1.59 Compatibility Fixes

**Files:**
- Modify: only files proven necessary by Task 4 or later verification
- Test: targeted unittest coverage for each fix

**Interfaces:**
- Consumes: `.venv314` install output and failing targeted checks
- Produces: minimal compatibility changes with focused regression coverage

- [ ] Add a failing test for each real compatibility issue found
- [ ] Verify each new test fails for the expected reason
- [ ] Implement the smallest code change that fixes the issue
- [ ] Re-run the targeted tests after each change

### Task 6: Verify Full Python Runtime Regression Suite

**Files:**
- Test: full project Python test command and import/compile checks

**Interfaces:**
- Consumes: `.venv314` and all compatibility fixes
- Produces: verified Python 3.14 + Streamlit 1.59 runtime status

- [ ] Run version verification commands from `.venv314`
- [ ] Run `compileall`
- [ ] Run the safest import smoke test supported by the current app structure
- [ ] Run the full Python test suite using the project’s actual command

### Task 7: Run Streamlit Smoke Test and Document Runtime Usage

**Files:**
- Modify: `README.md` and/or another existing runtime doc only if needed to reflect the actual new runtime procedure
- Test: Streamlit smoke test commands

**Interfaces:**
- Consumes: verified `.venv314`
- Produces: documented runtime startup procedure and smoke-test evidence

- [ ] Start the Streamlit app from `.venv314`
- [ ] Verify startup, initial HTTP response, and no app bootstrap exception
- [ ] Check major page entry at least to the level supported by available automation
- [ ] Update runtime instructions only where needed to reflect actual setup and commands
