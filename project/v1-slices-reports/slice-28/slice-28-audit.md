# Slice 28 Audit (Independent)

## Slice Id and Title
- Slice id: `Slice-28`
- Slice title: `Runtime evasion remediation tranche 1 (config pair)`

## Audit Verdict
- **Compliant for Slice-28 scope (config pair tranche complete).**
- Fail-closed governance posture is preserved: `verify_governance --check loc` and `--check all` remain non-zero globally, as expected by the Slice-28 plan.
- Theme A / A-08 remain open at program level.

## Audit Target and Scope
- Audit target: current Slice-28 working tree changes plus authored slice artifacts.
- Authoritative inputs used:
  - `AGENTS.md`
  - `project/verification-contract.yml`
  - `WORK_ITEMS.md`
  - `project/v1-slices-reports/slice-26/slice-26-audit.md`
  - `project/v1-slices-reports/slice-27/slice-27-audit.md`
  - `project/v1-slices-reports/slice-28/slice-28-plan.md`
  - `project/v1-slices-reports/slice-28/slice-28-implementation.md`
- Scope compliance check (runtime tranche):
  - `git diff --name-only -- src` shows only:
    - `src/jfin/config.py`
    - `src/jfin/config_core.py`
- Out-of-scope confirmation:
  - No runtime edits outside the config pair were found.
  - No governance artifact edits were found in this runtime tranche.

## What Changed (Audited)
- `src/jfin/config.py`
  - Removed formatter suppression marker.
  - Formatting/structural wrapping adjustments only.
- `src/jfin/config_core.py`
  - Removed formatter suppression marker.
  - Behavior-preserving refactor of parsing/override/validation internals.
  - Added internal `TypeGuard` helpers to preserve typing checks.

## Acceptance Criteria Checklist (`slice-28-plan.md`)
- [x] `# fmt: off/on` removed from both target files.
  - Evidence: `rg -n "#\\s*fmt:\\s*(off|on)" src/jfin/config.py src/jfin/config_core.py` returned no matches.
- [x] No anti-evasion tactics introduced in target files.
  - Evidence: `python -m ruff check src/jfin/config.py src/jfin/config_core.py --select E701,E702,E703` passed.
  - Evidence: no formatter suppression markers in target pair.
- [x] Honest LOC `<=300` for each target file.
  - Evidence: `config.py LOC=300`, `config_core.py LOC=298`.
- [x] Targeted config tests pass.
  - Evidence: `pytest -q tests/test_config.py tests/characterization/config_contract/test_config_contract_characterization.py` -> `32 passed`.
- [x] `verify_governance --check loc` remains non-zero globally (expected semantics).
  - Evidence: `LOC_EXIT=1`.
- [x] `verify_governance --check all` remains non-zero globally (expected semantics).
  - Evidence: `ALL_EXIT=1`.
- [x] Slice-28-specific requirement: config pair no longer appears in anti-evasion findings for `loc/all`.
  - Evidence:
    - `LOC_HAS_CONFIG_FLAG=False`
    - `LOC_HAS_CONFIG_CORE_FLAG=False`
    - `ALL_HAS_CONFIG_FLAG=False`
    - `ALL_HAS_CONFIG_CORE_FLAG=False`
- [x] `A-08` remains open.
  - Evidence: `WORK_ITEMS.md` still marks A-08 blocked/open; Slice-28 implementation explicitly does not close A-08.

## Verification Commands and Results (Independent Auditor Run)
- `$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest -q tests/test_config.py tests/characterization/config_contract/test_config_contract_characterization.py`
  - Result: `PASS` (`32 passed`, exit `0`)
- `.\.venv\Scripts\python.exe -m ruff check src/jfin/config.py src/jfin/config_core.py --select E701,E702,E703`
  - Result: `PASS` (exit `0`)
- `.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check loc`
  - Result: `FAIL` expected (exit `1`)
  - Semantics verified: fail caused by remaining anti-evasion offenders outside slice scope; config pair not flagged.
- `.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check all`
  - Result: `FAIL` expected (exit `1`)
  - Semantics verified: aggregate fail due `loc` fail-closed posture; config pair not flagged.
- AGENTS verification contract command set:
  - `pytest -q` -> `PASS` (`360 passed`, exit `0`)
  - `ruff check .` -> `PASS` (exit `0`)
  - `ruff format --check .` -> `PASS` (exit `0`)
  - `mypy src` -> `PASS` (exit `0`)
  - `bandit -r src` -> `PASS` (exit `0`)
  - `pip_audit` -> `PASS` (no known vulnerabilities; local package skip note, exit `0`)

## LOC/Governance Contract Status (Slice-Relevant)
- Contract source: `project/verification-contract.yml` (`src_max_lines=300`, anti-evasion fail-closed rules).
- Slice-28 target pair now complies honestly with LOC cap (`300` and `298`) without suppression.
- Global governance `loc/all` remains intentionally non-zero due six remaining runtime files:
  - `src/jfin/cli.py`
  - `src/jfin/cli_runtime.py`
  - `src/jfin/client.py`
  - `src/jfin/client_http.py`
  - `src/jfin/pipeline.py`
  - `src/jfin/pipeline_backdrops.py`

## Behavior-Preservation Assessment
- Public interface list in the plan remains intact for `config.py` and `config_core.py`.
- No out-of-scope module changes were detected.
- Characterization and config tests passed in auditor run, supporting behavior preservation for this slice.
- Assessment: **behavior-preserving evidence is sufficient for Slice-28 closure.**

## Anti-Evasion Findings
- Target pair:
  - Formatter suppression removed.
  - No E701/E702/E703 packing violations.
  - Honest LOC compliance achieved.
- Remaining anti-evasion findings are outside this slice and correctly keep global `loc/all` fail-closed.

## Issues Found
1. **Program-level carry-forward (High, out-of-scope for Slice-28):** six runtime files still trigger anti-evasion suppression errors, so full governance closure is not yet possible.
2. **No Slice-28-specific noncompliance found.**

## Were Fixes Required During This Audit?
- **No.** Slice-28 scope met its acceptance criteria as implemented.

## Final Closure Recommendation
- **Close Slice-28 as compliant and complete for its stated scope.**
- Do not claim Theme A or A-08 closure from this slice.

## Exact Next Slice Recommendation
- **Slice-29 Runtime evasion remediation tranche 2 (client pair)** targeting:
  - `src/jfin/client.py`
  - `src/jfin/client_http.py`
