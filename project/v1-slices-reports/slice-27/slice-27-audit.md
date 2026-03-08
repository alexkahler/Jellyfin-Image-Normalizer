# Slice 27 Audit

## Slice Id and Title
- Slice id: `Slice-27`
- Slice title: `Anti-evasion enforcement parity in governance checks`

## Audit Verdict
- **Compliant (slice objective complete).**
- `verify_governance --check loc` and `--check all` failing closed is expected positive evidence for this slice when failures are anti-evasion runtime violations.
- Theme A and A-08 are still open; this audit only closes Slice 27 scope.

## What Changed (Audited Surface)
- `project/scripts/governance_contract.py`
- `project/scripts/governance_checks.py`
- `tests/test_governance_checks.py`
- `tests/test_characterization_checks.py`
- `tests/test_governance_docs_topology.py`
- `project/v1-slices-reports/slice-27/slice-27-plan.md`
- `project/v1-slices-reports/slice-27/slice-27-implementation.md`

## Acceptance Checklist
- [x] Parser/schema enforce anti-evasion keys under `loc_policy`.
- [x] `check_loc_policy` enforces anti-evasion rules and fail-closed behavior.
- [x] `--check loc` fails closed on retained anti-evasion runtime violations (expected).
- [x] `--check all` fails closed for the same anti-evasion reason (expected).
- [x] Governance unit tests for this slice pass.
- [x] `git diff --numstat -- src` is empty (no runtime edits).
- [x] Scope remains governance parser/schema/check/tests only.

## Verification Commands and Results

### Auditor-ran (independent evidence)
1. `$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest -q tests/test_governance_checks.py`
- Result: `22 passed in 0.83s` (`EXIT_CODE=0`)

2. `.\.venv\Scripts\python.exe -m ruff check src tests .github --select E701,E702,E703`
- Result: `All checks passed!` (`EXIT_CODE=0`)

3. `.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check loc`
- Result: `FAIL` (`EXIT_CODE=1`) with anti-evasion `fmt_suppression` errors on retained `src/jfin/*` files; test LOC overflow warnings also present.
- Interpretation: expected Slice 27 fail-closed proof.

4. `.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check all`
- Result: `FAIL` (`EXIT_CODE=1`) because `loc` fails for anti-evasion; other governance checks reported `PASS` in this run.
- Interpretation: expected Slice 27 fail-closed aggregate proof.

5. `git diff --numstat -- src`
- Result: empty output.

### Existing implementation evidence (not re-run in this audit)
1. Full AGENTS contract suite reported as passing in `slice-27-implementation.md`:
- `pytest`, `ruff check .`, `ruff format --check .`, `mypy src`, `bandit -r src`, `pip_audit`.

## LOC/Governance Contract Status for Slice 27
- `project/verification-contract.yml` anti-evasion keys are treated as enforced contract inputs.
- Governance parser/schema/check path now validates anti-evasion key presence and canonical values.
- Current repo remains intentionally fail-closed on LOC due retained anti-evasion runtime violations; this is compliant with Slice 27 closure criteria.

## Behavior-Preservation Assessment
- `src/` runtime code was not modified (`git diff --numstat -- src` empty).
- Observed changes are governance enforcement and governance tests only.
- Runtime safety invariants were not altered by this slice surface.

## Anti-Evasion Findings
- `verify_governance --check loc` reports anti-evasion formatter suppression violations in:
- `src/jfin/cli.py`
- `src/jfin/cli_runtime.py`
- `src/jfin/client.py`
- `src/jfin/client_http.py`
- `src/jfin/config.py`
- `src/jfin/config_core.py`
- `src/jfin/pipeline.py`
- `src/jfin/pipeline_backdrops.py`
- These retained violations are expected and confirm fail-closed wiring is active.

## Issues Found
- No unexpected Slice 27 implementation defects were identified in audited governance parser/schema/check/tests scope.
- Known carry-forward condition remains: retained runtime anti-evasion violations block `loc/all` by design until remediation slices.
- Program-level status remains open in `WORK_ITEMS.md` (A-08 still blocked/open).

## Were Fixes Required?
- **No fixes required for Slice 27 closure** based on plan criteria and collected evidence.
- Runtime anti-evasion remediation is still required for later slices, not this audit slice.

## Final Closure Recommendation
- **Close Slice 27 as complete and compliant with its plan objective.**
- Do not claim Theme A closure from this slice; retain A-08 open posture.

## Exact Next Slice Recommendation
- `Slice-28 Runtime evasion remediation tranche 1 (config pair)`
