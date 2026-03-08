# Slice 18 Audit - A-04

Date: 2026-03-07  
Auditor: Codex audit worker (`audit-governance-and-slice-compliance` skill, read-only behavior)

## Slice ID / Title
- Slice id: `A-04`
- Slice title: `Medium-coupling closure slot 2 (adaptive) - config.py`

## Audit Verdict
**Conditionally Compliant (A-04 scope).**

A-04 acceptance criteria are met for the targeted module split and regression checks. Track-1 Theme A closure gates remain open because global LOC governance still fails outside A-04 scope (`src/jfin/cli.py`, `src/jfin/pipeline.py`).

## What Changed
- Modified: `src/jfin/config.py`
- Added (untracked in working tree): `src/jfin/config_core.py`
- Added report artifacts (untracked):
  - `project/v1-slices-reports/slice-18/slice-18-plan.md`
  - `project/v1-slices-reports/slice-18/slice-18-audit.md`
- No changes observed in governance contract artifacts (`AGENTS.md`, `project/verification-contract.yml`, parity/route-fence files).

Observed extraction pattern:
- Config data classes, validation helpers, list/type parsing, CLI override merge, and canvas-size helpers moved from `config.py` into `config_core.py`.
- `config.py` remains API-facing facade and re-exports required symbols.

## Acceptance Checklist (A-04)
- [PASS] `src/jfin/config.py` is `<=300` LOC (`299`).
- [PASS] Adjacent helper module used and `<=300` LOC (`src/jfin/config_core.py:299`).
- [PASS] No touched `src/` file exceeds `300` LOC.
- [PASS] Net `src` LOC delta is within contract (`projected_net=-61`, including untracked helper file).
- [PASS] `tests/test_config.py` passes (`25 passed`).
- [PASS] `tests/characterization/config_contract` passes (`7 passed`).
- [PASS] `verify_governance --check architecture` passes.
- [PASS] Scope remains aligned to A-04 objective (config medium-coupling closure only).

## Verification Commands and Results
1. `@('src/jfin/config.py','src/jfin/config_core.py') | % { if (Test-Path $_) { "{0}:{1}" -f $_, (Get-Content $_).Length } }`  
   Result:
   - `src/jfin/config.py:299`
   - `src/jfin/config_core.py:299`
   Status: **PASS**

2. `$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest -q tests/test_config.py`  
   Result: `25 passed in 0.14s`  
   Status: **PASS**

3. `$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest -q tests/characterization/config_contract`  
   Result: `7 passed in 0.09s`  
   Status: **PASS**

4. `.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check architecture`  
   Result: `[PASS] architecture`  
   Status: **PASS**

5. `.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check loc`  
   Result: `[FAIL] loc` due to existing blockers:
   - `ERROR: src/jfin/cli.py has 817 lines (max 300)`
   - `ERROR: src/jfin/pipeline.py has 1059 lines (max 300)`
   Status: **FAIL (theme-level/open, not introduced by A-04)**

6. `git diff --numstat -- src`  
   Result: `44  404  src/jfin/config.py`  
   Status: **PASS (tracked diff evidence)**

Additional supporting evidence:
- `git status --short` shows untracked `src/jfin/config_core.py`.
- Combined tracked/untracked LOC math: `tracked_net=-360`, `untracked_add=299`, `projected_net=-61`.

## LOC / Governance Contract Status
- Contract sources checked: `AGENTS.md`, `project/verification-contract.yml`.
- A-04 touched-file LOC compliance: **PASS** (`config.py` and `config_core.py` both <=300).
- Global repository LOC gate (`verify_governance --check loc`): **FAIL** (pre-existing high-coupling blockers remain).
- Governance artifact drift in this slice: **Not observed**.

## Behavior-Preservation Assessment
**Pass with low residual risk.**
- Change is structural extraction/facade retention, consistent with A-04 behavior-preservation statement.
- Public config symbols remain available through `jfin.config` imports.
- Targeted config unit and characterization suites pass.
- No evidence of route-fence, dry-run safety, or API semantics changes in this slice.

Residual risk:
- Full repository verification contract command set (ruff/mypy/bandit/pip_audit/full pytest) was not rerun in this focused audit scope.

## Issues Found
### AUD-001 (High)
- Condition: `verify_governance --check loc` fails.
- Criteria: Track-1 LOC contract (`src_max_lines: 300`, block mode) from `project/verification-contract.yml` and mirrored AGENTS policy.
- Evidence: command #5 output (`src/jfin/cli.py` and `src/jfin/pipeline.py` over limit).
- Impact: Theme A GG-001 cannot close yet.
- Scope attribution: Pre-existing / outside A-04 module target.

### AUD-002 (Low)
- Condition: `git diff --numstat -- src` under-reports A-04 full surface while helper file is untracked.
- Criteria: Slice evidence should fully represent changed `src` surface for reproducible LOC proof.
- Evidence: command #6 plus `git status --short` showing untracked `src/jfin/config_core.py`.
- Impact: Minor audit evidence ambiguity.

## Fixes Required
- **For A-04 closure:** No immediate code fix required.
- **For Theme A closure:** Yes. Remaining LOC blockers (`cli.py`, `pipeline.py`) must be reduced to <=300 in subsequent slices (A-05/A-06/A-07 path), then rerun `verify_governance --check loc` and `--check all`.
- **For audit hygiene:** Ensure helper file is tracked/staged when collecting final `numstat` evidence.

## Closure Recommendation
- **Recommend closing A-04 as conditionally compliant** and proceeding to next roadmap slice under revalidation rules.
- **Do not claim GG-001 closure** at this point.
- Before Theme A final closure, require successful same-SHA evidence for all required CI jobs and passing global governance gates.
