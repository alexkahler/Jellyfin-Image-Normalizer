## Slice 14: COV-05 Blueprint Topology Drift Guard (Final)

### Summary
1. Fix the known suite-topology drift in `project/v1-plan.md`.
2. Add a minimal, blocking governance doc-contract check in `project/scripts/governance_checks.py`.
3. Keep scope docs/governance-only; no characterization-domain semantic changes.

### Implementation Changes
1. Update the `### Characterization suites` list in `project/v1-plan.md` to the canonical set:
`tests/characterization/cli_contract/`, `tests/characterization/config_contract/`, `tests/characterization/imaging_contract/`, `tests/characterization/safety_contract/`.
2. Keep `docs/TECHNICAL_NOTES.md` as canonical narrative text; only make wording edits if needed for exact agreement.
3. Keep `restore_contract` as migration-note alias only, not canonical topology.
4. Implement `check_docs_topology_contract(repo_root)` in `project/scripts/governance_checks.py`.
5. Use one blocking error prefix only: `docs_topology.contract: ...`.
6. Enforce robust, bounded extraction (format-tolerant, not free-form grepping):
   - parse only the `### Characterization suites` section block in `v1-plan.md`,
   - parse only the "Characterization suites live in ..." statement in `TECHNICAL_NOTES.md`,
   - normalize path tokens (slashes, trailing `/`, punctuation/backticks), compare sets (order-insensitive).
7. In the same check, assert required directories exist on disk:
`tests/characterization/cli_contract/`, `config_contract/`, `imaging_contract/`, `safety_contract/`, and `tests/characterization/baselines/`.
8. Wire this check into `--check characterization` in governance aggregation flow.
9. Add/update planning artifacts only as tracking/admin:
`WORK_ITEMS.md`, `plans/Slice-14.md`, `project/v1-slices-reports/slice-14/slice-14-plan.md`.

### End-State Acceptance
Governance must fail when either `project/v1-plan.md` or `docs/TECHNICAL_NOTES.md` disagrees with the canonical suite set, and must also fail when any canonical suite/baseline directory is missing on disk.

### Test Plan
1. Add `tests/test_governance_docs_topology.py` with pass/fail cases for:
   - canonical docs agreement,
   - `v1-plan.md` legacy suite drift,
   - `TECHNICAL_NOTES.md` suite drift,
   - missing required directories,
   - formatting-tolerance (spacing/order/punctuation changes that should still pass).
2. Add integration assertion that `run_selected_checks("characterization", ...)` reports/fails on docs-topology drift.
3. Run:
`$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest -q tests/test_governance_docs_topology.py tests/test_governance_checks.py`
`$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe project/scripts/verify_governance.py --check characterization`
`$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe project/scripts/verify_governance.py --check all` (expect only pre-existing LOC blockers/warnings)
plus full verification-contract command set.

### Assumptions and Non-Goals
1. Canonical suite set is fixed to the four current Track-1 suite directories above.
2. README topology guarding is intentionally out of scope for Slice 14.
3. No changes to COV-01b runtime gate, COV-02 workflow coverage, COV-03 readiness semantics, or COV-04 trace contract behavior.
