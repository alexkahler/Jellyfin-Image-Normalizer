## Slice 1 Plan: Governance Scaffolding (WI-001)

### Summary
Implement WI-001 from `project/v1-plan.md` as a governance-only slice (no runtime behavior changes in `src/jfin`).  
This slice will add governance artifacts, define a canonical verification contract at `project/verification-contract.yml`, and wire strict CI governance checks on the current migration branch (`feat/v1-overhaul`).

Important baseline facts discovered:
- Current local Python is `3.10.10`; test collection fails because `tomllib` is unavailable.
- Current `src/` already violates the `>300 LOC` target in multiple files.
- You explicitly chose strict immediate enforcement and confirmed we are already on a v1 migration branch.

### Repo Map Snippet (paths only)
- Entrypoints: `src/jfin/__main__.py`, `src/jfin/cli.py`
- Core runtime hotspots: `src/jfin/pipeline.py`, `src/jfin/client.py`, `src/jfin/config.py`, `src/jfin/imaging.py`, `src/jfin/backup.py`
- Tests: `tests/`
- CI: `.github/workflows/ci.yml`
- Blueprint: `project/v1-plan.md`
- New governance artifacts (this slice): `WORK_ITEMS.md`, `plans/WI_TEMPLATE.md`, `.github/PULL_REQUEST_TEMPLATE.md`, `project/verification-contract.yml`

### Scope

In scope:
1. Add governance scaffolding artifacts required by the blueprint.
2. Define canonical verification contract in `project/verification-contract.yml`.
3. Add CI governance enforcement job for:
- verification contract/CI sync
- strict `src/ >300 LOC` blocking
- test-file `>300 LOC` warning-only
- Python version consistency checks across CI/docs/contract
4. Add tests for governance check logic.
5. Update contributor-facing docs/instructions if verification workflow changes.

Out of scope:
1. Any refactor of `src/jfin/*`.
2. Any CLI/config/runtime behavior change.
3. Any parity-matrix implementation (WI-002+) beyond scaffolding references.

---

### Public Interfaces / Contract Additions
No runtime public API changes.  
New governance interface (repo-level contract):

`project/verification-contract.yml` schema (fixed keys):
1. `version` (int)
2. `python_version` (string, exact `3.13`)
3. `verification_commands` (ordered list of shell commands)
4. `required_ci_jobs` (ordered list: `test`, `security`, `quality`, `governance`)
5. `loc_policy` object:
- `src_max_lines` = `300`
- `src_mode` = `block`
- `tests_max_lines` = `300`
- `tests_mode` = `warn`

---

### Staged Implementation Plan

#### Milestone 1: Governance scaffold files
Files:
1. `WORK_ITEMS.md`
2. `plans/WI_TEMPLATE.md`
3. `.github/PULL_REQUEST_TEMPLATE.md`

Intent:
- Create the exact WI inventory and planning template from the blueprint.
- Enforce single-objective PR shape and mandatory verification/rollback metadata in PRs.

Required content decisions:
- `WORK_ITEMS.md` contains only WI-001..WI-005 entries from section 19.
- `plans/WI_TEMPLATE.md` contains exactly the 7 required fields.
- PR template sections include:
  - objective/scope (single objective)
  - behavior-preservation statement
  - parity IDs touched
  - verification commands + results
  - rollback note
  - docs/contract update checklist

Verification (targeted):
1. `rg -n "WI-001|WI-002|WI-003|WI-004|WI-005" WORK_ITEMS.md`
2. `rg -n "Objective|In-scope|Out-of-scope|Public interfaces affected|Acceptance criteria|Verification commands|Rollback step|Behavior-preservation statement" plans/WI_TEMPLATE.md`
3. `rg -n "Behavior-preservation|Parity IDs|How I verified|Rollback|docs/contract" .github/PULL_REQUEST_TEMPLATE.md`

Exit criteria:
- All three files exist with required sections and no extra work items.

---

#### Milestone 2: Canonical verification contract
Files:
1. `project/verification-contract.yml`

Intent:
- Establish single source of truth for quality/security/test commands + governance policy.

Contract command set (order fixed):
1. `PYTHONPATH=src python -m pytest`
2. `python -m ruff check .`
3. `python -m ruff format --check .`
4. `python -m mypy src`
5. `python -m bandit -r src`
6. `python -m pip_audit`

Verification (targeted):
1. `rg -n "python_version|verification_commands|required_ci_jobs|loc_policy" project/verification-contract.yml`
2. `rg -n "src_max_lines: 300|src_mode: block|tests_mode: warn" project/verification-contract.yml`

Exit criteria:
- Contract exists and fully defines enforcement parameters without ambiguity.

---

#### Milestone 3: Governance check implementation + unit tests
Files:
1. `project/scripts/verify_governance.py`
2. `tests/test_governance_checks.py`

Intent:
- Implement one script with deterministic checks:
  1. contract schema validation
  2. CI/contract sync check (commands + required jobs + PR trigger)
  3. LOC policy check (`src` block, `tests` warn)
  4. Python version consistency check (`ci.yml`, `README.md`, contract)
- Add unit tests with fixtures covering pass/fail/warn paths.

Implementation constraints:
- Use stdlib only (no new dependency such as PyYAML).
- Contract parser supports only this repo’s controlled YAML shape (documented in script docstring).
- Non-zero exit on blocking failures; zero exit with warnings for non-blocking test-file size cases.

Verification (targeted):
1. `PYTHONPATH=src python -m pytest -q tests/test_governance_checks.py`
2. `python project/scripts/verify_governance.py --check schema`
3. `python project/scripts/verify_governance.py --check ci-sync`
4. `python project/scripts/verify_governance.py --check loc`
5. `python project/scripts/verify_governance.py --check python-version`

Exit criteria:
- Tests pass in Python 3.13 environment.
- Script fails with clear message for current strict `src >300 LOC` baseline (expected).

---

#### Milestone 4: CI wiring for governance enforcement
Files:
1. `.github/workflows/ci.yml`

Intent:
- Add `governance` job to run on `pull_request` + `push` with Python `3.13`.
- Job executes `python project/scripts/verify_governance.py --check all`.
- Keep existing `test`, `security`, and `quality` jobs intact (no behavior change besides added governance gate).

Verification (targeted):
1. `python project/scripts/verify_governance.py --check ci-sync`
2. `rg -n "governance:|--check all|python-version: \"3.13\"|pull_request:" .github/workflows/ci.yml`

Exit criteria:
- CI file contains governance job and still defines `test`, `security`, `quality`.
- Governance job is enforceable on PRs.

---

#### Milestone 5: Governance-doc alignment
Files:
1. `AGENTS.md` (only if verification gate list is changed)
2. `README.md` and/or `docs/TECHNICAL_NOTES.md` (developer workflow section)

Intent:
- Prevent process drift by documenting how to run governance checks locally.

Verification (targeted):
1. `rg -n "verify_governance|verification-contract|governance" AGENTS.md README.md docs/TECHNICAL_NOTES.md`

Exit criteria:
- Contributor docs match implemented governance workflow.

---

### Test Cases and Scenarios
1. Contract schema success: all required keys present and valid types.
2. Contract schema failure: missing `required_ci_jobs` or malformed `loc_policy`.
3. CI sync failure: a contract command missing from `ci.yml`.
4. CI sync failure: missing `governance` job in workflow.
5. LOC blocking failure: a `src/*.py` file over 300 lines returns non-zero.
6. LOC warning case: a new `tests/*.py` file over 300 lines logs warning only.
7. Python consistency failure: mismatch between contract and CI/README versions.
8. Current baseline behavior: governance check fails on strict `src` LOC until later slices reduce file sizes.

---

### Risk Register (Top 5)
1. Immediate CI red status due strict LOC gate.
- Mitigation: expected/explicit for migration branch; document as intentional until decomposition slices land.
2. Drift between contract and CI commands.
- Mitigation: CI sync check blocks mismatch.
3. Fragile YAML parsing without external parser.
- Mitigation: enforce fixed contract shape and cover parser in unit tests.
4. Version mismatch confusion across docs/CI.
- Mitigation: automated consistency check + clear error messages naming mismatched files.
5. Governance slice scope creep into runtime refactor.
- Mitigation: hard out-of-scope guard; only governance files changed.

---

### Rollback Plan
1. Keep implementation split into atomic commits:
- commit A: scaffold docs/templates
- commit B: contract + governance script + tests
- commit C: CI wiring/doc alignment
2. If governance checks misfire, rollback by `git revert <commit C>` first (CI wiring only).
3. If script logic is incorrect, rollback `git revert <commit B>`.
4. If templates are problematic, rollback `git revert <commit A>`.
5. Do not use destructive history edits; use revert-only rollback.

---

### Assumptions and Defaults (Locked)
1. Slice target: `WI-001` only.
2. Verification contract source of truth: `project/verification-contract.yml`.
3. Slice depth: scaffolding plus full CI governance guards.
4. LOC policy: strict immediate blocking for `src >300` on this migration branch.
5. `tests >300` remains non-blocking warning.
6. Python baseline for governance checks: `3.13`.
7. No runtime behavior changes to Jellyfin/image processing in this slice.
