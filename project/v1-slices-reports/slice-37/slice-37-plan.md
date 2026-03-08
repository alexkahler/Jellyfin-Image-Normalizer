# Slice-37 Plan (v3 FINAL, implementation-ready)

Date: 2026-03-08

## Slice Id and Title
- Slice id: `Slice-37`
- Slice title: `Theme D minimal second-cell workflow-readiness coverage expansion`
- One-sentence success criterion: expand workflow coverage from one to two validated cells using existing parity-backed evidence, with no route flips, no owner-slice rewrites, and no runtime-code edits.

## 1) Pre-slice baseline state
- Branch: `v1/thm-d-workflow-readiness-coverage-expansion`
- Baseline HEAD: `ef0aa739f64c3e60b9ae2d40968943ffe78f8291`
- Starting worktree posture: clean before scaffold; active uncommitted state after scaffold creation is limited to `project/v1-slices-reports/slice-37/`.
- Authoritative baseline from current evidence:
  - Theme C closure is preserved in `WORK_ITEMS.md` (Slice-36 complete).
  - Route-fence remains fully `route=v0`; only `run|backdrop` is currently `parity status=ready`.
  - `project/workflow-coverage-index.json` currently has one cell only: `run|backdrop`.
- Required governance baseline commands already rerun:
  - `.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check readiness` -> PASS (`claimed_rows=1`, `validated_rows=1`)
  - `.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check parity` -> PASS
  - `.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check characterization` -> PASS (`Workflow sequence cells configured: 1`, `validated: 1`, `open debts: 0`)

## 2) Exact blocker targeted
- Single blocker: Theme D (`GG-004` breadth portion) remains open because workflow-readiness evidence is still single-cell after Theme C activation.

## 3) Exact in-scope / out-of-scope files
In-scope:
- `project/workflow-coverage-index.json`
- `WORK_ITEMS.md`
- `project/v1-slices-reports/slice-37/slice-37-plan.md`
- `project/v1-slices-reports/slice-37/slice-37-implementation.md`
- `project/v1-slices-reports/slice-37/slice-37-audit.md`

Out-of-scope (hard):
- `project/route-fence.md`
- `project/route-fence.json`
- `project/parity-matrix.md`
- `project/verification-contract.yml`
- `src/jfin/**` runtime code
- Any `route=v0 -> v1` change
- Any owner-slice rewrite (including placeholder-owner remediation)
- Any additional workflow expansion beyond one new cell

## 4) Why this slice is small enough
- One artifact objective: add one new workflow cell only.
- Zero runtime edits and zero route-fence/parity ownership edits.
- Direct machine-checkable pass/fail via existing counters:
  - characterization `configured_cells/validated_cells` should move from `1/1` to `2/2`,
  - readiness `claimed_rows/validated_rows` should stay `1/1`.

## 5) Behavior-preservation obligations
- Preserve Theme C activation proof (`run|backdrop` remains the only claimed-ready row).
- Preserve route posture (`route=v0` for all rows).
- Preserve route-fence ownership state (no owner-slice changes).
- Preserve runtime behavior (`src/jfin/**` untouched).
- Do not weaken readiness/characterization enforcement to manufacture pass conditions.

## 6) Honest remediation path
1. Add exactly one new workflow-coverage cell:
   - key: `restore|logo|thumb|backdrop|profile`
   - command/mode must exactly match existing route-fence row.
2. Link this cell to real existing parity + characterization evidence only:
   - `required_parity_ids`: `RST-REFUSE-001`
   - `required_owner_tests`: `tests/characterization/safety_contract/test_safety_contract_restore.py::test_rst_refuse_001_characterization`
3. Use evidence/ordering fields that exist in the anchored baseline payload:
   - `field_container`: `expected_observations.result`
   - `required_evidence_fields`: `raises`, `exit_code`
   - `ordering_container`: `expected_messages`
   - `required_ordering_tokens`: `Backup directory does not exist`
4. Keep readiness claims unchanged:
   - no route-fence edits,
   - no additional `parity status=ready` rows.
5. Re-run required governance checks and targeted tests.

## 7) Expected blocker contraction
- Before slice:
  - readiness: `claimed_rows=1`, `validated_rows=1`
  - characterization workflow: `configured_cells=1`, `validated_cells=1`
- After slice success:
  - readiness remains `claimed_rows=1`, `validated_rows=1` (Theme C preserved),
  - characterization workflow becomes `configured_cells=2`, `validated_cells=2`.
- Theme D effect: minimal multi-cell breadth evidence achieved without overreach.

## 8) Exact verification commands for audit
```powershell
$ErrorActionPreference = 'Stop'
$env:PYTHONPATH='src'

git rev-parse --abbrev-ref HEAD
git rev-parse HEAD
git status --short
git diff --name-only

rg -n "run\|backdrop|restore\|logo\|thumb\|backdrop\|profile|RST-REFUSE-001" project/workflow-coverage-index.json

.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check readiness
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check parity
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check characterization
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check architecture

.\.venv\Scripts\python.exe -m pytest -q tests/test_characterization_checks.py tests/test_characterization_checks_safety.py tests/test_readiness_checks.py tests/test_governance_readiness.py
```

If audit judges this slice as a plausible Theme D closure slice, also run:
```powershell
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check all
```

## 9) Rollback path
Pre-commit rollback:
1. `git restore --source=HEAD -- project/workflow-coverage-index.json WORK_ITEMS.md project/v1-slices-reports/slice-37/slice-37-*.md`
2. Re-run readiness/parity/characterization checks.

Post-commit rollback:
1. `git revert <slice-37-commit-sha>`
2. Re-run readiness/parity/characterization/architecture checks.

## 10) Next-slice expectation if successful
- Primary next gate: Theme D closure audit gate.
- If gate passes: Theme D closes and no additional Theme D breadth slice is needed.
- If gate fails: next slice must be remediation/decomposition only (no broad expansion).

## 11) Inherited unresolved audit remediation
- Inherited non-fatal carry-forward from Slice-36 audit:
  - architecture ratchet warning remains deferred:
    - `src/jfin/pipeline.py.system_exit_raises` exit-counter dropped below baseline.

## 12) Scope-tightening and decomposition triggers
Excluded adjacent work:
- Any additional workflow cell besides the single restore row.
- Any route-fence row edits.
- Any parity-matrix row edits.
- Any runtime-gate contract expansion.

Signals that make this slice too large:
- Need to touch multiple governance surfaces beyond workflow index + slice reports.
- Need to modify readiness/characterization validator logic.
- Need to edit runtime code or baseline payloads to satisfy the new cell.

Mandatory decomposition trigger:
- If the one-cell addition cannot validate cleanly with existing evidence links, fail-close this slice and create a dedicated remediation/decomposition slice instead of widening scope.
