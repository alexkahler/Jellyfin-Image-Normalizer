# Slice-35 Plan (v3 FINAL, implementation-ready)

Date: 2026-03-08

## Slice Id and Title
- Slice id: `Slice-35`
- Slice title: `Theme C1 run|backdrop ownership accountability normalization`
- Plan posture: implementation-ready planning artifact
- One-sentence success criterion: canonical `run|backdrop` ownership is real (`Slice-35`) and claimed-ready rows are machine-blocked from placeholder ownership.

## 1) Pre-slice baseline state
- Branch: `v1/thm-c-route-readiness-activation-accountability`
- HEAD at planning capture: `e52a4498dbb9dea5d64356399a8458483f612c71`
- Governance baseline:
  - `verify_governance.py --check readiness`: PASS with `claimed_rows=0`, `validated_rows=0`
  - `verify_governance.py --check parity`: PASS
  - `verify_governance.py --check characterization`: PASS, `workflow sequence open debts=0`
- Theme B closure baseline remains intact:
  - `project/workflow-coverage-index.json` keeps only `run|backdrop`
  - `future_split_debt.id=DEBT-BACKDROP-ID-SPLIT-001`
  - `future_split_debt.status=closed`
- Intended claim-path baseline in route-fence artifacts:
  - `run|backdrop`: `route=v0`, `owner slice=WI-00X`, `parity status=pending` (markdown + JSON mirror)

## 2) Exact blocker targeted
- Targeted blocker (single): Theme C1 accountability blocker (`GG-002`) on intended claim path `run|backdrop`.
- Problem: ownership is placeholder (`WI-00X`) and not accountable enough for upcoming real readiness activation.

## 3) Exact in-scope / out-of-scope files
In-scope files:
- `project/route-fence.md`
- `project/route-fence.json`
- `project/scripts/readiness_checks.py`
- `tests/_readiness_test_helpers.py`
- `tests/test_readiness_checks.py`
- `project/v1-slices-reports/slice-35/slice-35-plan.md`
- `project/v1-slices-reports/slice-35/slice-35-implementation.md`
- `project/v1-slices-reports/slice-35/slice-35-audit.md`

Out-of-scope (hard):
- `project/workflow-coverage-index.json`
- `project/parity-matrix.md`
- Any `route=v0 -> v1` flip
- Any canonical `parity status=pending -> ready` activation
- Ownership edits for rows other than `run|backdrop`
- Theme D readiness breadth expansion
- Any `src/jfin/**` runtime behavior edits

## 4) Why this slice is small enough to avoid context rot
- One objective and one route row (`run|backdrop`) only.
- Accountability-only normalization plus validator guardrail, no activation.
- Bounded code surface: one validator path and targeted readiness tests/helpers.

## 5) Behavior-preservation obligations
- Preserve runtime behavior and safety invariants (`src/jfin/**` untouched).
- Preserve Theme B closure posture (no debt reopening; no workflow index changes).
- Preserve non-activation posture (`route=v0`, `parity status=pending` canonical).
- Do not weaken readiness enforcement; only add ownership-accountability blocking for claimed-ready rows.

## 6) Honest remediation path
1. Update canonical `run|backdrop` owner claim in `project/route-fence.md`:
   - `owner slice: WI-00X -> Slice-35`
2. Keep `project/route-fence.json` synchronized with the same exact owner value.
3. Add readiness semantic guard in `project/scripts/readiness_checks.py`:
   - when a row claims readiness (`parity status=ready` or `route=v1`), placeholder owner values are invalid (at minimum `WI-00X`).
4. Add targeted readiness tests proving:
   - claimed-ready + placeholder owner fails,
   - claimed-ready + non-placeholder owner passes when other proof links remain valid,
   - canonical artifacts for this slice remain non-activated.

## 7) Expected blocker contraction
- Before: intended claim-path ownership is placeholder and weakly accountable.
- After: intended claim-path ownership is explicit (`Slice-35`) and placeholder owners are machine-rejected for claimed-ready rows.
- Theme C status after this slice (expected): OPEN (C2 activation still required).

## 8) Exact verification commands for audit worker
```powershell
$ErrorActionPreference = 'Stop'
$env:PYTHONPATH='src'

git rev-parse --abbrev-ref HEAD
git status --short
git diff --name-only

rg -n "\| run \| backdrop \|" project/route-fence.md
rg -n "owner slice|parity status|WI-00X|Slice-35" project/route-fence.md
rg -n '"command": "run"|"mode": "backdrop"|"owner_slice"|"parity_status"|"Slice-35"' project/route-fence.json
rg -n "placeholder|owner|claimed_ready" project/scripts/readiness_checks.py tests/test_readiness_checks.py tests/_readiness_test_helpers.py

.\.venv\Scripts\python.exe -m pytest -q tests/test_readiness_checks.py

.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check readiness
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check parity
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check characterization
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check architecture
```

## 9) Rollback path
Pre-commit rollback:
1. `git restore --source=HEAD -- project/route-fence.md project/route-fence.json project/scripts/readiness_checks.py tests/_readiness_test_helpers.py tests/test_readiness_checks.py`
2. Re-run:
   - `.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check readiness`
   - `.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check parity`

Post-commit rollback:
1. `git revert <slice-35-commit-sha>`
2. Re-run readiness/parity/characterization/architecture checks listed above.

## 10) Exact next-slice expectation if successful
- Next slice: `Slice-36 (Theme C2)`.
- Exact objective: activate first canonical readiness claim on intended path by setting `run|backdrop parity status=ready` with `route=v0` unchanged.
- Expected C2 proof: `verify_governance.py --check readiness` reports `claimed_rows > 0` and `validated_rows > 0`.

## 11) Inherited unresolved audit remediation
- None blocking inherited from Slice-34 audit.
- Carry-forward informational debt only:
  - architecture ratchet warning (existing)
  - tests LOC warnings (existing)

## 12) Scope-tightening and decomposition signals
Excluded adjacent work:
- Ownership normalization for all route rows.
- Any route-fence activation or route flips.
- Any workflow/parity breadth expansion.

Too-large signals:
- Need to edit governance systems beyond route-fence + readiness semantics.
- Need to touch runtime modules or characterization baselines.

Mandatory decomposition trigger:
- If ownership-accountability enforcement requires broad validator redesign, fail-close this slice and make next slice a decomposition/remediation slice instead of forcing implementation.
