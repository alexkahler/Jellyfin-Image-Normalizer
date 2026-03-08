# Slice 22 Plan

## Slice Id and Slice Title
- Slice id: `A-06`
- Slice title: `High-coupling closure slot 2 (adaptive) - cli.py`

## Objective
Close the remaining high-coupling LOC blocker in `src/jfin/cli.py` with a behavior-preserving structural extraction that keeps CLI semantics and runtime contracts unchanged.

## In-Scope / Out-of-Scope
- In scope: `src/jfin/cli.py` and minimum adjacent helper surface required to reduce `cli.py` to `<=300` LOC while preserving behavior.
- In scope: compatibility-preserving delegation/wrapper extraction only.
- In scope: preserving existing import paths/functions used by tests (`jfin.cli.*`).
- Out of scope: CLI redesign, flag/option semantic changes, route-fence semantic changes, route flips, config contract redesign, unrelated cleanup.

## Target Files
- `src/jfin/cli.py`
- `src/jfin/cli_runtime.py` (new helper module, if required)
- `project/v1-slices-reports/slice-22/slice-22-plan.md`
- `project/v1-slices-reports/slice-22/slice-22-audit.md` (post-implementation)

## Public Interfaces Affected
Behavior and signatures must remain compatible for:
- `parse_size_pair`
- `parse_args`
- `validate_generate_config_args`
- `validate_restore_all_args`
- `validate_test_jf_args`
- `warn_unused_cli_overrides`
- `warn_unrecommended_aspect_ratios`
- `run_preflight_check`
- `_enforce_route`
- `main`

## Acceptance Criteria
- `src/jfin/cli.py` is `<=300` LOC.
- All touched `src/` Python files are `<=300` LOC.
- Net `src/` LOC delta is `<=150` unless explicitly justified in slice artifacts.
- CLI behavior and option semantics remain compatible (validated by targeted CLI and characterization tests).
- Route enforcement behavior remains fail-closed and unchanged.
- Entry/exit behavior remains compatible (CLI owns exits; non-entry modules do not introduce new exit violations).
- `verify_governance.py --check architecture` passes.
- `verify_governance.py --check loc` is executed and shows `cli.py` no longer as blocker.
- `git diff --numstat -- src` evidence captured.
- If safe closure cannot be achieved within slice constraints, stop and split to `A-06a`/`A-06b` before merge.

## Exact Verification Commands
```powershell
@('src/jfin/cli.py','src/jfin/cli_runtime.py') | ForEach-Object { if (Test-Path $_) { "{0}:{1}" -f $_, (Get-Content $_).Length } }
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check loc
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check architecture
$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest -q tests/test_jfin.py
$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest -q tests/characterization/cli_contract/test_cli_contract_characterization.py
$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest -q tests/test_route_fence_runtime.py
git diff --numstat -- src
```

## Rollback Step
`git revert <A-06 commit>` and rerun the A-06 verification commands above.

## Behavior-Preservation Statement
This slice is a structural refactor only. CLI routing, options, dry-run/write expectations, and entrypoint exit semantics are preserved.

## Implementation Steps
1. Extract high-LOC orchestration internals from `cli.py` into a focused helper (`cli_runtime.py`) while preserving `jfin.cli` public functions as compatibility entrypoints.
2. Keep `main` and helper interactions compatibility-safe by injecting/seaming symbols that tests monkeypatch (`setup_logging`, `load_config_from_path`, `resolve_route`, `route_fence_json_path`, `run_preflight_check`, pipeline calls).
3. Ensure CLI exit behavior remains functionally equivalent and architecture-compliant.
4. Keep `cli.py` at `<=300` and helper file at `<=300` during implementation.
5. Run targeted CLI matrix and governance checks.
6. If closure requires risky semantic churn or breaches constraints, stop and document split trigger for `A-06a/A-06b`.

## Risks / Guardrails
- Risk: subtle CLI behavior drift due orchestration extraction.
- Guardrail: preserve function signatures and run targeted CLI + characterization tests.
- Risk: monkeypatch seam break in tests/harness.
- Guardrail: route runtime dependencies through `jfin.cli` compatibility surface.
- Risk: architecture guard regression from exit-flow relocation.
- Guardrail: keep exit behavior centralized in CLI entrypoint and verify with `--check architecture`.
- Risk: LOC closure not achievable safely in one slice.
- Guardrail: trigger roadmap split path `A-06a/A-06b` before merge.

## Expected Commit Title
`a-06: cli LOC closure`
