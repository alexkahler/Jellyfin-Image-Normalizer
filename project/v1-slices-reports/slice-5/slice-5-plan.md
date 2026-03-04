# Slice 5 Plan (Final Revision): WI-001 Architecture Guards for Gate Bullets 2 and 3

## Summary
1. Slice 5 implements only `v1-plan.md` Structure Validation Checklist bullets 2 and 3:
2. Bullet 2: non-CLI `sys.exit`/`SystemExit` guard, introduced as a transitional ratchet because legacy violations already exist.
3. Bullet 3: import-boundary guards for `domain` and `app/services`.
4. No runtime behavior changes in `src/jfin`.
5. As of March 4, 2026, CI already runs `python project/scripts/verify_governance.py --check all` in `.github/workflows/ci.yml`.

## Scope
1. In scope:
- Governance scripts and baseline artifact for architecture checks.
- `verify_governance` wiring for a new `architecture` selector.
- Tests for architecture checks and governance dispatch.
- Docs and slice/WI plan updates.
2. Out of scope:
- Refactoring legacy `src/jfin` modules to eliminate existing exit debt.
- Structure-gate bullets 1, 4, 5, 6.
- Track 2 CLI/config redesign and route-fence flips.

## Public Interfaces / Types
1. Add governance command:
- `python project/scripts/verify_governance.py --check architecture`
2. Add optional baseline helper:
- `python project/scripts/verify_governance.py --check architecture --print-baseline`
3. Add artifact:
- `project/architecture-baseline.json`
4. Add modules:
- `project/scripts/architecture_contract.py`
- `project/scripts/architecture_checks.py`
5. `--check all` includes `architecture`.

## Enforcement Rules (Decision Complete)

### A) Non-entry exit rule (transitional ratchet)
1. Track 1 allowed exit module list is fixed to `src/jfin/cli.py`.
2. All other Python files under `src/jfin` are subject to ratchet enforcement.
3. Detection patterns in scope:
- `sys.exit(...)`
- `raise SystemExit`
- `raise SystemExit(...)`
- `from sys import exit` (including aliases) followed by call
- `builtins.exit(...)`
- `builtins.quit(...)`
4. Detection patterns out of scope for Slice 5:
- Unqualified `exit(...)`/`quit(...)` not resolved via `sys` or `builtins`
- `os._exit(...)`
5. Ratchet behavior:
- Fail on any new violating file not in baseline.
- Fail on any counter increase for a baselined file.
- Pass on equal or lower counts.
- Emit warning on lower counts to prompt baseline shrink update.

### B) Import-boundary rules (hard fail, no boundary baseline)
1. Rules activate when v1 boundary paths exist.
2. No baseline/ratchet is used for boundaries in Slice 5.
3. V1 root is explicit constant: `V1_ROOT = "src/jfin"` for Track 1.
4. Domain guard path: `src/jfin/domain/**/*.py` when present.
5. App-services guard path: `src/jfin/app/services/**/*.py` when present.
6. Domain forbidden imports:
- `jfin.adapters`, `jfin.app`, `jfin.bootstrap`
- `requests`, `PIL`, `shutil`, `tempfile`, `glob`, `subprocess`, `socket`, `urllib`, `http.client`
7. App-services guard for Slice 5 is only:
- No imports of `jfin.adapters...` via absolute or resolved relative imports.
8. Other app-services purity constraints are deferred:
- No Slice 5 enforcement yet for CLI/config/bootstrap purity or transport-agnostic semantics.
9. Conditional activation means checks pass when those directories do not exist yet.

## Baseline Schema
1. `project/architecture-baseline.json` keys:
- `version` (int, fixed `1`)
- `v1_root` (string, fixed `src/jfin`)
- `entry_exit_modules` (list, includes `src/jfin/cli.py`)
- `non_entry_exit_allowlist` (map path -> counters)
2. Counter keys per file:
- `sys_exit_calls`
- `system_exit_raises`
- `sys_import_exit_calls`
- `builtins_exit_calls`
3. Generator/checker consistency rule:
- `--print-baseline` and ratchet enforcement both use the same counting function and same AST logic.

## Milestones

### Milestone 1: Contract and counting core
1. Files:
- `project/scripts/architecture_contract.py`
- `project/scripts/architecture_checks.py`
2. Intent:
- Define schema, constants, and shared AST counting primitives.
3. Verification:
- `PYTHONPATH=src python -m pytest -q tests/test_architecture_checks.py -k "schema or count"`

### Milestone 2: Ratchet + boundary checks
1. Files:
- `project/scripts/architecture_checks.py`
2. Intent:
- Implement ratcheted non-entry exit enforcement and conditional hard-fail boundary checks.
3. Verification:
- `PYTHONPATH=src python -m pytest -q tests/test_architecture_checks.py`

### Milestone 3: Governance CLI wiring + CI/contract guard
1. Files:
- `project/scripts/governance_checks.py`
- `project/scripts/verify_governance.py` (if parser surface expands for `--print-baseline`)
2. Intent:
- Add `architecture` check selector and include in `all`.
- Wire optional `--print-baseline`.
3. Verification:
- `PYTHONPATH=src python -m pytest -q tests/test_governance_checks.py -k architecture`
- `python project/scripts/verify_governance.py --check architecture`
- `rg -n "verify_governance.py --check all" .github/workflows/ci.yml project/scripts/governance_checks.py`
4. CI/contract rule:
- If repo no longer routes governance through `--check all`, update CI and contract artifacts in the same PR.

### Milestone 4: Baseline artifact and docs
1. Files:
- `project/architecture-baseline.json`
- `project/v1-slices-reports/slice-5/slice-5-plan.md`
- `plans/WI-001.md`
- `README.md`
- `docs/TECHNICAL_NOTES.md`
2. Intent:
- Seed baseline from `--print-baseline`.
- Document transitional ratchet, exact detection scope, and boundary enforcement scope.
3. Verification:
- `python project/scripts/verify_governance.py --check architecture`
- `python project/scripts/verify_governance.py --check all`
- `rg -n "check architecture|print-baseline|transitional ratchet|gate bullets 2 and 3" README.md docs/TECHNICAL_NOTES.md plans/WI-001.md project/v1-slices-reports/slice-5/slice-5-plan.md`

## Test Cases and Scenarios
1. Baseline schema valid path passes.
2. Baseline schema missing/invalid fields fail.
3. New non-entry violating file fails ratchet.
4. Baseline counter increase fails.
5. Baseline counter decrease passes with warning.
6. `sys.exit`, `raise SystemExit`, `from sys import exit as ...`, `builtins.exit`, `builtins.quit` are each detected.
7. Domain import of forbidden module fails.
8. App-services import of adapters via absolute import fails.
9. App-services import of adapters via relative import fails.
10. Conditional activation passes when boundary directories are absent.
11. `--print-baseline` output matches enforcement counting logic.
12. `--check all` executes architecture checks via governance path.

## Acceptance Criteria
1. Slice 5 clearly and only covers structure-gate bullets 2 and 3.
2. Non-entry exit guard blocks new debt and baseline growth while allowing debt reduction.
3. Boundary checks hard-fail immediately when boundary paths exist and violate rules.
4. App-services enforcement scope is explicitly limited to adapter-import prohibition in Slice 5.
5. Governance CI path remains enforced through `--check all`, or CI/contract are updated in same PR if drift is found.
6. No runtime behavior changes in `src/jfin`.

## Rollback
1. Revert Slice 5 commits in reverse dependency order:
- docs/plan updates
- governance wiring
- architecture checks
- architecture contract and baseline artifact
2. If urgent unblock is required, revert only architecture selector integration in governance script.

## Assumptions and Defaults
1. Track 1 v1 root is `src/jfin`.
2. `src/jfin/cli.py` is the only allowed exit-calling module.
3. Ratchet is temporary; target end-state remains zero non-entry exit violations.
4. Existing LOC gate failures remain pre-existing and out of Slice 5 scope.
