# Slice-07

## 1. Objective
Implement a machine-checkable Surface Coverage Gate that enforces complete Track 1 coverage mapping for CLI help-visible surface, `config.example.toml` keys, and Track 1 observability contract items, with deterministic unmapped reporting under governance.

## 2. In-scope / Out-of-scope
In-scope: `project/surface-coverage-index.json`, surface detection/validation in governance scripts, characterization-gate integration, unmapped/report counters, parity rows and tests for `OBS-SUMLOG-001`, `CFG-SCALEFLAGS-001`, and `OBS-EXITCODE-001`, and Slice 7 docs/report updates.
Out-of-scope: route-fence flips, Track 2 CLI/config redesign, additional mapping artifacts for the same surface, and unrelated runtime refactors in `src/jfin`.

## 3. Public interfaces affected
- `project/surface-coverage-index.json`
- `./.venv/bin/python project/scripts/verify_governance.py --check characterization`
- `./.venv/bin/python project/scripts/verify_governance.py --check all`
- `project/parity-matrix.md`

## 4. Acceptance criteria
- Surface Coverage Gate runs in characterization checks and transitively in `--check all`.
- Governance output includes:
  - `Remaining unmapped CLI items: <n>`
  - `Remaining unmapped config keys: <n>`
  - `Remaining unmapped observability items: <n>`
  - `Remaining parity/test linkage gaps: <n>`
- At completion, unmapped counts are zero for CLI/config/observability contract items.
- All mapped parity IDs exist in `project/parity-matrix.md`.
- All mapped owner tests resolve to existing files; `path::symbol` references also resolve symbol names.
- New parity rows and tests exist for `OBS-SUMLOG-001`, `CFG-SCALEFLAGS-001`, and `OBS-EXITCODE-001`.

## 5. Verification commands (<10 min)
- `PYTHONPATH=src ./.venv/bin/python -m pytest -q tests/test_surface_coverage_checks.py`
- `PYTHONPATH=src ./.venv/bin/python -m pytest -q tests/test_characterization_checks.py tests/test_characterization_checks_links.py tests/test_characterization_checks_imaging.py tests/test_characterization_checks_safety.py`
- `PYTHONPATH=src ./.venv/bin/python -m pytest -q tests/test_parity_checks.py tests/test_governance_checks.py`
- `PYTHONPATH=src ./.venv/bin/python -m pytest -q tests/test_logging_utils.py`
- `PYTHONPATH=src ./.venv/bin/python -m pytest -q tests/test_imaging.py -k "no_scale or no_upscale or no_downscale"`
- `PYTHONPATH=src ./.venv/bin/python -m pytest -q tests/test_jfin.py -k "exit_code or generate_config or restore_all or test_jf"`
- `./.venv/bin/python project/scripts/verify_governance.py --check characterization`
- `./.venv/bin/python project/scripts/verify_governance.py --check all`

## 6. Rollback step
Revert Slice 7 commits in reverse dependency order with `git revert`: docs/report updates, parity row/test updates, characterization integration changes, then surface coverage checker/index artifacts.

## 7. Behavior-preservation statement
Preserved by default. Slice 7 adds governance enforcement and test-backed parity rows for previously unmapped behavior classes without intentional runtime behavior breaks.
