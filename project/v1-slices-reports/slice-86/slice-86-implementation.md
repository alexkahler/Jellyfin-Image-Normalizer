# Slice 86 Implementation Report

Date: 2026-03-12
Plan source: `project/v1-slices-reports/slice-86/slice-86-plan.md` (v3 final)

## Scope executed
- Objective: remediate CI regression where `--generate-config` fail-closed because `config_init|n/a` resolves to `route=v1`.
- Runtime fix file touched: `src/jfin/cli.py`
- Test update file touched: `tests/test_route_fence_runtime.py`
- No route-fence/parity/workflow/verification-contract/CI file mutation.

## Root-cause reproduction (pre-fix)
Reproduced with:
```powershell
$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest -q tests/test_jfin.py::test_main_exit_code_classes tests/test_route_fence_runtime.py::test_generate_config_succeeds_when_route_fence_is_v0 tests/test_route_fence_runtime.py::test_generate_config_fails_closed_when_route_declares_v1
```
Observed failure excerpt:
```text
route-fence dispatch blocked: command='config_init' mode='n/a' declares route='v1' but v1 runtime path is not implemented in this build.
```

## Code changes
1. `src/jfin/cli.py`
   - Added explicit v1 runtime-support allowlist:
     - `_V1_RUNTIME_IMPLEMENTED_ROUTE_KEYS = {("config_init", "n/a")}`
   - Updated `_enforce_route`:
     - allow `route=="v0"` unchanged
     - allow `route=="v1"` only for keys in `_V1_RUNTIME_IMPLEMENTED_ROUTE_KEYS`
     - keep fail-closed block for all other `v1` keys.

2. `tests/test_route_fence_runtime.py`
   - Made `test_generate_config_succeeds_when_route_fence_is_v0` deterministic by mocking `resolve_route -> "v0"`.
   - Replaced pre-implementation expectation test with:
     - `test_generate_config_succeeds_when_route_declares_v1_for_config_init`
   - Added guard test:
     - `test_enforce_route_fails_closed_for_unimplemented_v1_key`

## Post-fix verification
Targeted regressions:
```powershell
$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest -q tests/test_jfin.py::test_main_exit_code_classes tests/test_route_fence_runtime.py tests/characterization/cli_contract/test_cli_contract_characterization.py::test_cli_generate_config_blocks_operational_flags
```
Result:
```text
12 passed in 1.23s
```

Governance checks:
```powershell
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check readiness
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check parity
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check all
```
Result summary:
- readiness: PASS (`Route readiness claims: 5`, `validated: 5`)
- parity: PASS
- all: PASS (existing non-blocking LOC warnings unchanged)

## Diff-scope proof
Working diff before audit/update steps:
```text
src/jfin/cli.py
tests/test_route_fence_runtime.py
project/v1-slices-reports/slice-86/slice-86-plan.md
```
Forbidden-surface diff check:
- `project/route-fence.md`: unchanged
- `project/route-fence.json`: unchanged
- `project/parity-matrix.md`: unchanged
- `project/workflow-coverage-index.json`: unchanged
- `project/verification-contract.yml`: unchanged
- `.github/workflows/ci.yml`: unchanged

## Final implementation verdict
final_implementation_verdict: PASS
final_implementation_blockers: none
