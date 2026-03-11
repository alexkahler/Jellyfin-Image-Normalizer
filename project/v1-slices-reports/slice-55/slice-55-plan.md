# Slice 55 Plan v3 (Final) - One-Row Route Progression for `config_validate|n/a` (`v0 -> v1`)

Date: 2026-03-11
Branch: feat/v1-overhaul
Local SHA: 2a0e6e6669c1f92216e4516aeea9f6b21390487f

## Slice ID/title
- Slice 55
- One-row progression action for `config_validate|n/a` (`route v0 -> v1`)

## Objective
- Execute exactly one route progression action for `config_validate|n/a`: `v0 -> v1`.
- Keep `owner=Slice-49` and `parity status=ready` unchanged.
- Carry forward Slice 54 same-SHA unavailability explicitly:
- source evidence: Slice 54 recorded `same_sha_total_runs=0` for `be9fa48a618adf9ce00b090044ce797c7e5224fb`
- no same-SHA run id/url and no required-job summary (`test`, `security`, `quality`, `governance`) available
- residual risk remains and must be re-stated without implying same-SHA validation
- Planning-only constraint for this step: create this plan only; do not edit route-fence now.

## Worker responsibility split
- Implementation worker scope/actions:
- mutate exactly one route field for one row only (`config_validate|n/a: v0 -> v1`) in `project/route-fence.md` and `project/route-fence.json`
- preserve `owner` and `parity status` for that row
- run required governance verification and write `project/v1-slices-reports/slice-55/slice-55-implementation.md`
- Audit worker scope/actions:
- independently verify one-row mutation discipline, out-of-scope non-mutation, and same-SHA carry-forward language
- verify governance-check evidence and produce PASS/FAIL in `project/v1-slices-reports/slice-55/slice-55-audit.md`
- `WORK_ITEMS.md` is out of implementation/audit worker scope; orchestration-thread-only post-audit update if needed

## In-scope/out-of-scope files (tight)
- In scope for Slice 55 execution (unchanged):
- `project/route-fence.md` (single row/cell: `config_validate|n/a` route only)
- `project/route-fence.json` (matching single route-field update)
- `project/v1-slices-reports/slice-55/slice-55-plan.md`
- `project/v1-slices-reports/slice-55/slice-55-implementation.md`
- `project/v1-slices-reports/slice-55/slice-55-audit.md`
- Out of scope:
- all other rows/cells in `project/route-fence.md` and `project/route-fence.json`
- `project/parity-matrix.md`
- `project/workflow-coverage-index.json`
- `project/verification-contract.yml`
- `.github/workflows/ci.yml`
- `WORK_ITEMS.md` (orchestration-thread-only post-audit update; not implementation/audit worker scope)
- all `src/` and `tests/` files

## Acceptance criteria
- Exactly one route-fence row is progressed: `config_validate|n/a` route changes `v0 -> v1` in both `project/route-fence.md` and `project/route-fence.json`.
- `config_validate|n/a` owner and parity remain unchanged (`Slice-49`, `ready`).
- No other route-fence rows or out-of-scope files are modified.
- Slice 55 implementation and audit explicitly carry forward Slice 54 same-SHA unavailability:
- `same_sha_total_runs=0` evidence basis from Slice 54
- same-SHA run id/url unavailable
- required-job status summary unavailable for `test/security/quality/governance`
- explicit residual-risk statement and no implied same-SHA validation claim
- Governance checks pass for the resulting state (`.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check all` at minimum).

## Binary success condition
Slice 55 is PASS only if exactly one row (`config_validate|n/a`) is flipped `v0 -> v1` in both route-fence artifacts, `owner=Slice-49` and `parity=ready` remain unchanged, all out-of-scope files remain unchanged, governance checks pass, and Slice 54 same-SHA-unavailability carry-forward is explicitly recorded with residual risk and no implied same-SHA validation.

## Fail-close criteria (no-close blockers)
- Any mutation beyond the single `config_validate|n/a` route field in `project/route-fence.md` and `project/route-fence.json`.
- Any owner/parity change on `config_validate|n/a`.
- Any diff in out-of-scope files, including `WORK_ITEMS.md` within implementation/audit worker activity.
- Missing or ambiguous same-SHA carry-forward facts from Slice 54 (`same_sha_total_runs=0`, no run id/url, required-job summary unavailable, residual risk explicit).
- Governance verification failure for `.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check all`.
- Baseline mismatch at execution time (`config_validate|n/a` not `route=v0`, `owner=Slice-49`, `parity=ready`) without re-plan.

## Implementation steps
1. Confirm baseline row state before mutation: `config_validate|n/a` is `route=v0`, `owner=Slice-49`, `parity=ready`.
2. Re-read Slice 54 evidence branch and carry forward the same-SHA unavailability facts into Slice 55 implementation evidence.
3. Update `project/route-fence.md` for `config_validate|n/a` route only: `v0 -> v1`.
4. Update `project/route-fence.json` for the same row/field only: `v0 -> v1`.
5. Run governance verification: `.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check all`.
6. Write `slice-55-implementation.md` including exact file diff scope and explicit same-SHA carry-forward residual risk.

## Post-implementation orchestration steps
1. Independent audit worker reviews Slice 55 implementation evidence and writes `project/v1-slices-reports/slice-55/slice-55-audit.md` with explicit PASS/FAIL, including same-SHA carry-forward verification (`same_sha_total_runs=0`, no run id/url, required-job summary unavailable, residual risk explicit, no implied same-SHA validation).
2. If and only if audit result is PASS, orchestration thread may perform a post-audit `WORK_ITEMS.md` sequence update; `WORK_ITEMS.md` remains out of implementation/audit worker scope.

## Risks/guardrails
- Risk: same-SHA CI required-job evidence is still unavailable from Slice 54; remote CI-environment regressions for exact SHA are not proven.
- Guardrail: fail closed on evidence language; do not imply same-SHA validation exists.
- Guardrail: one-row mutation only; no owner/parity/readiness/workflow index edits in this slice.
- Guardrail: if `config_validate|n/a` is not `ready` at execution time, stop and re-plan instead of forcing a flip.
- Guardrail for this planning task: no route or governance-truth edits now, no commit, no reverts.

## Suggested next slice
- Slice 56: post-flip closure/roadmap decision slice to either:
- attempt same-SHA CI evidence recollection for new HEAD and reduce residual risk, or
- declare completion-stop for `ready+v0` progression with explicit carry-forward for remaining `pending` rows.

## Split rule
- If scope expands beyond one-row `config_validate|n/a` route progression (for example, additional route rows, parity/owner changes, workflow-index edits, or broader governance cleanup), stop and split:
- keep Slice 55 limited to the single-row `v0 -> v1` action and required reports,
- defer all extra changes to a new numbered slice.
