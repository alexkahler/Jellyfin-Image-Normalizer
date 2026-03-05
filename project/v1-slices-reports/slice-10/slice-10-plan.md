## Slice 10 Plan: COV-01b Runtime Characterization Gate (Warn Ratchet, Tightened)

### Summary
1. Add COV-01b runtime characterization governance for `tests/characterization/safety_contract` only.
2. Keep Slice 10 in warn mode by behavior, with explicit merge policy: runtime execution must be green; mapping-coverage gaps are non-blocking informational output.
3. Preserve scope: governance/runtime-check wiring + CI reliability hardening; no route flips and no runtime feature behavior changes.

### Key Changes
1. Contract/interface changes:
- Add `characterization_runtime_gate_targets` to `project/verification-contract.yml` (initial: `tests/characterization/safety_contract`).
- Add `characterization_runtime_gate_budget_seconds` (initial: `180`).
- Update `project/scripts/governance_contract.py` parse/schema checks for these keys.

2. Runtime gate behavior in characterization checks:
- Implement in `project/scripts/characterization_checks.py` using `sys.executable`, `cwd=repo_root`, and `env={**os.environ, "PYTHONPATH": "src"}`.
- Run collect + runtime in single-target-group flow:
  - `pytest --collect-only -q <targets...>` for mapping.
  - `pytest -q --maxfail=1 <targets...>` for execution.
- Budget semantics: one end-to-end wall-clock budget for collect+run total.
- Timeout semantics: global deadline `budget + 15s`; timeout takes precedence over budget-exceeded.
- Report taxonomy:
  - warnings: `runtime_gate.target_invalid`, `runtime_gate.execution_failed`, `runtime_gate.timeout`, `runtime_gate.budget_exceeded`
  - info: `runtime_gate.parity_mapping_empty`

3. Deterministic parity mapping rules:
- Normalize both parity `owner_test` and collect-only nodeids to repo-relative POSIX nodeid strings.
- Mapping definition: in-scope parity IDs are the intersection of normalized owner nodeids and collected nodeids for configured targets.
- Include mapped parity IDs in runtime-failure output for actionability.

4. Governance output and exit behavior:
- Extend `project/scripts/governance_checks.py` output with runtime-gate counters/status and elapsed vs budget.
- Explicit status line: `Characterization runtime gate OK|NOT OK (warn)`.
- Slice 10 behavior: runtime-gate warnings do not change process exit code by themselves.

5. CI hardening (minimal, in-scope):
- Update `.github/workflows/ci.yml` governance job to install dependencies required for runtime pytest execution before `verify_governance.py --check all`.
- Add minimal CI-sync validation/test coverage that governance job includes an install step with pytest availability.

6. Slice artifacts:
- Update `project/v1-slices-reports/slice-10/slice-10-plan.md`.
- Update `WORK_ITEMS.md` with Slice 10 COV-01b tracking note.

### Test Plan
1. Contract tests:
- pass/fail for new runtime keys (missing keys, invalid targets, non-positive budget).

2. Runtime gate tests:
- pass path for safety target.
- execution failure warning path.
- timeout warning path.
- completed-over-budget warning path.
- timeout-precedence-over-budget test.
- nodeid normalization/intersection test.
- parity-mapping-empty emits info (not warning/error).

3. Governance behavior tests:
- output includes runtime gate section and explicit `OK|NOT OK (warn)` line.
- warn-only runtime outcomes do not force nonzero exit code.
- CI-sync test fails when governance job lacks dependency install step.

4. Verification commands:
- targeted pytest for new governance/runtime tests.
- `PYTHONPATH=src ./.venv/bin/python project/scripts/verify_governance.py --check characterization`
- `PYTHONPATH=src ./.venv/bin/python project/scripts/verify_governance.py --check all` (expected remaining blockers: known pre-existing `src/` LOC only, assuming COV-01a stability holds).

### Acceptance and Ratchet
1. Slice 10 merge criteria:
- runtime gate runs every characterization check and reports deterministic runtime status.
- no runtime execution warnings (`execution_failed`, `timeout`, `budget_exceeded`, `target_invalid`) on baseline run.
- informational `parity_mapping_empty` allowed only with explicit slice-report rationale.

2. Slice 11 ratchet-to-block criteria:
- promote runtime gate to blocking only after 3 consecutive CI governance runs with runtime execution status `OK`, no runtime warnings, and documented runtime budget compliance.

### Assumptions
1. COV-01a collectability hardening remains green and stable.
2. Safety-contract suite is the only Slice 10 runtime target.
3. No route-fence row flips are planned in Slice 10.
