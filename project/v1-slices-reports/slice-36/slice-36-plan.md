# Slice-36 Plan (v3 FINAL, implementation-ready)

Date: 2026-03-08

## Slice Id and Title
- Slice id: `Slice-36`
- Slice title: `Theme C2 canonical first-claim activation on run|backdrop`
- Plan posture: implementation-ready planning artifact.
- One-sentence success criterion: canonical readiness becomes non-vacuous on the intended path (`claimed_rows=1`, `validated_rows=1`) with `route=v0` unchanged.

## 1) Pre-slice baseline state
- Branch: `v1/thm-c-route-readiness-activation-accountability`
- Baseline head at planning capture: `901508c`
- Governance baseline:
  - `verify_governance.py --check readiness`: PASS with `claimed_rows=0`, `validated_rows=0`
  - `verify_governance.py --check parity`: PASS
  - `verify_governance.py --check characterization`: PASS
- Theme B closure remains preserved:
  - `project/workflow-coverage-index.json` keeps `run|backdrop` debt closed (`DEBT-BACKDROP-ID-SPLIT-001`).
- Theme C1 accountability is in place:
  - canonical `run|backdrop.owner slice=Slice-35`
  - claimed-ready placeholder owners are machine-blocked in readiness checks.

## 2) Exact blocker targeted
- Targeted blocker (single): Theme C2 activation blocker (`GG-003`) for intended claim path `run|backdrop`.
- Problem: canonical readiness validation is still vacuous (`claimed_rows=0`, `validated_rows=0`).

## 3) Exact in-scope / out-of-scope files
In-scope:
- `project/route-fence.md`
- `project/route-fence.json`
- `tests/test_readiness_runtime_overlay.py` (inherited mandatory readiness test remediation from Slice-35 owner-placeholder enforcement)
- `WORK_ITEMS.md`
- `project/v1-slices-reports/slice-36/slice-36-plan.md`
- `project/v1-slices-reports/slice-36/slice-36-implementation.md`
- `project/v1-slices-reports/slice-36/slice-36-audit.md`

Out-of-scope (hard):
- `project/workflow-coverage-index.json`
- `project/parity-matrix.md`
- Any `route=v0 -> v1` flip
- Any ownership edits outside existing `run|backdrop=Slice-35`
- Any Theme D breadth expansion (no additional workflow cells)
- Any runtime edits under `src/jfin/**`

## 4) Why this slice is small enough
- One row change only (`run|backdrop parity status: pending -> ready`) with JSON sync.
- No validator redesign, no workflow/parity topology changes.
- Verification directly answers one gate question: did canonical readiness become non-vacuous?

## 5) Behavior-preservation obligations
- Preserve runtime behavior (`src/jfin/**` untouched).
- Preserve Theme B closure posture.
- Preserve route safety discipline: keep canonical `route=v0`.
- Preserve scope discipline: no Theme D expansion.

## 6) Honest remediation path
1. Update canonical route-fence markdown row:
   - `run|backdrop parity status: pending -> ready`
   - keep `route=v0`
   - keep `owner slice=Slice-35`.
2. Synchronize `project/route-fence.json` to match markdown exactly.
3. Run readiness/parity/characterization/architecture checks plus targeted regression tests.
4. Confirm canonical readiness reports `claimed_rows=1` and `validated_rows=1`.

## 7) Expected blocker contraction
- Before: canonical readiness is vacuous (`0/0`).
- After: canonical readiness evaluates at least one real claim candidate (`1/1`) on intended path.
- Theme C expected status after success: `CLOSED` (Theme B preserved, intended path activated, real claim evaluated with machine-checked accountability).

## 8) Exact verification commands for audit
```powershell
$ErrorActionPreference = 'Stop'
$env:PYTHONPATH='src'

git rev-parse --abbrev-ref HEAD
git status --short
git diff --name-only

rg -n "\| run \| backdrop \|" project/route-fence.md
rg -n "\"command\": \"run\"|\"mode\": \"backdrop\"|\"route\"|\"owner_slice\"|\"parity_status\"" project/route-fence.json

.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check readiness
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check parity
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check characterization
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check architecture
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check all

.\.venv\Scripts\python.exe -m pytest -q tests/test_readiness_checks.py tests/test_readiness_runtime_overlay.py tests/test_governance_readiness.py tests/test_parity_checks.py
```

## 9) Rollback path
Pre-commit rollback:
1. `git restore --source=HEAD -- project/route-fence.md project/route-fence.json WORK_ITEMS.md project/v1-slices-reports/slice-36/slice-36-*.md`
2. Re-run readiness/parity checks.

Post-commit rollback:
1. `git revert <slice-36-commit-sha>`
2. Re-run readiness/parity/characterization/architecture checks.

## 10) Next-slice expectation if successful
- No next Theme C slice expected.
- Next gate transitions to Theme D planning only if explicitly authorized by authoritative artifacts.

## 11) Inherited unresolved remediation
- Mandatory inherited remediation:
  - align readiness runtime-overlay claimed-ready tests with Slice-35 owner-placeholder enforcement (`tests/test_readiness_runtime_overlay.py`).
- Non-fatal carry-forward warning:
  - architecture ratchet warning in `src/jfin/pipeline.py.system_exit_raises`.

## 12) Scope-tightening and decomposition triggers
Excluded adjacent work:
- Activating additional route rows.
- Any route flip to `v1`.
- Any coverage expansion across additional workflow cells.

Too-large signals:
- Need to modify workflow coverage/parity contracts to make activation pass.
- Need to change runtime code or broaden runtime gate targets.

Mandatory decomposition trigger:
- If canonical activation fails due broader coupling outside route-fence row sync, fail-close and create a decomposition/remediation slice instead of forcing Theme C closure.
