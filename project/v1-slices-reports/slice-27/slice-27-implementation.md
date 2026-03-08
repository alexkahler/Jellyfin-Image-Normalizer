# Slice 27 Implementation

## Slice Id And Title
- Slice id: `Slice-27`
- Slice title: `Anti-evasion enforcement parity in governance checks`

## Scope Executed
- Implemented anti-evasion enforcement parity in governance parser/schema/check paths.
- Kept runtime product code untouched (`src/jfin/*` unchanged).
- Preserved Theme A status posture: A-08 remains open.

## Files Changed
- `project/scripts/governance_contract.py`
- `project/scripts/governance_checks.py`
- `tests/test_governance_checks.py`
- `tests/test_characterization_checks.py`
- `tests/test_governance_docs_topology.py`
- `project/v1-slices-reports/slice-27/slice-27-plan.md`
- `project/v1-slices-reports/slice-27/slice-27-implementation.md`

## What Was Implemented
- Added required anti-evasion keys to `LocPolicy` parse/schema contract handling:
  - `anti_evasion_disallow_fmt`
  - `anti_evasion_disallow_multi_statement`
  - `anti_evasion_disallow_dense_control_flow`
  - `anti_evasion_fail_closed`
  - `anti_evasion_rationale`
  - `anti_evasion_noncompliance_rule`
  - `anti_evasion_multi_statement_max_semicolons`
  - `anti_evasion_control_flow_inline_suite_max`
- Added parser helpers for strict bool/int parsing and required-key enforcement.
- Extended schema checks to validate anti-evasion values against canonical expectations.
- Wired anti-evasion enforcement into `check_loc_policy`:
  - formatter suppression marker detection (`# fmt: off/on`)
  - semicolon packing detection
  - dense inline control-flow suite detection via AST
  - fail-closed handling for read/tokenize/parse failures
- Added/updated governance tests for:
  - anti-evasion parse-required key behavior
  - anti-evasion schema drift failures
  - anti-evasion fail-closed LOC violations
- Updated affected governance fixture contract writers to include anti-evasion keys so full repo test contract remains green.

## Verification Evidence
1. Targeted governance tests:
- `$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest -q tests/test_governance_checks.py`
- Result: `22 passed`.

2. Slice 27 required anti-evasion static signal command:
- `.\.venv\Scripts\python.exe -m ruff check src tests .github --select E701,E702,E703`
- Result: `All checks passed!`.

3. Fail-closed objective proof (`--check loc`):
- `.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check loc`
- Result: non-zero (`EXIT_CODE=1`) with anti-evasion errors on retained suppression files in `src/jfin/*`.
- Interpretation: expected fail-closed behavior achieved.

4. Fail-closed objective proof (`--check all`):
- `.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check all`
- Result: non-zero (`EXIT_CODE=1`) because `loc` now fails on anti-evasion violations; other checks pass.
- Interpretation: expected fail-closed aggregate behavior achieved.

5. Runtime surface proof:
- `git diff --numstat -- src`
- Result: empty output.

6. AGENTS verification contract command set:
- `$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest`
  - Result: `360 passed, 4 warnings`.
- `.\.venv\Scripts\python.exe -m ruff check .`
  - Result: pass.
- `.\.venv\Scripts\python.exe -m ruff format --check .`
  - Result: `77 files already formatted`.
- `.\.venv\Scripts\python.exe -m mypy src`
  - Result: pass.
- `.\.venv\Scripts\python.exe -m bandit -r src`
  - Result: pass (no issues).
- `.\.venv\Scripts\python.exe -m pip_audit`
  - Result: pass (no known vulnerabilities).

## Behavior-Preservation Assessment
- No runtime behavior changes introduced under `src/`.
- Slice effect is governance enforcement posture only.

## Slice 27 Closure Status
- Slice objective status: **complete**.
- Rationale: anti-evasion contract codification is now enforced in governance parser/schema/check path with fail-closed evidence.
- Theme A status: **still open** (runtime remediation slices and A-08 same-SHA proof remain).
- Exact next slice recommendation: `Slice-28 Runtime evasion remediation tranche 1 (config pair)`.
