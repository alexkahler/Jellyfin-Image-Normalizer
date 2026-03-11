# Slice 52 Plan v3 (Final) - Readiness Claim Activation for `config_validate|n/a`

Date: 2026-03-11
Branch: feat/v1-overhaul
Local SHA: b2c4584f432f3e94218a3110f39e3e3bef100164

## Slice ID + Title
- Slice 52 - Readiness claim activation for `config_validate|n/a` (`pending -> ready`, keep `route=v0`)

## Goal / Objective
- Activate the readiness claim for `config_validate|n/a` now that ownership (Slice 49), workflow coverage (Slice 50), and runtime-gate eligibility (Slice 51) are in place.
- Keep this slice governance-only and narrow: no runtime code changes and no route flip.

## Baseline State (Before Any Slice-52 Mutation)
- `project/route-fence.md` row for `config_validate|n/a` is currently:
  - `route=v0`
  - `owner slice=Slice-49`
  - `parity status=pending`
- Current readiness counters (`verify_governance.py --check readiness`):
  - `claimed_rows=2`
  - `validated_rows=2`

## Why This Is the Next Slice
- `WORK_ITEMS.md` explicitly marks Slice 51 next step as readiness activation for `config_validate|n/a`.
- Current `project/route-fence.*` shows `config_validate|n/a` still `pending`, which is the remaining claim-status gap for this row.

## In Scope
- `project/route-fence.md` (single-row parity-status update for `config_validate|n/a`)
- `project/route-fence.json` (matching single-row update)
- `project/v1-slices-reports/slice-52/slice-52-implementation.md`
- `project/v1-slices-reports/slice-52/slice-52-audit.md`
- `WORK_ITEMS.md` (record Slice 52 completion and next governance-cadence slice)

## Out of Scope
- Any `route` value changes (`v0 -> v1` is forbidden in this slice)
- Any `owner slice` changes
- `project/workflow-coverage-index.json`
- `project/verification-contract.yml`
- `project/parity-matrix.md`
- Any files under `src/` or `tests/` except audit evidence commands

## Binary Success Condition
- This slice is successful only if exactly one route-fence row (`config_validate|n/a`) changes `parity status` from `pending` to `ready`, while `route=v0` and `owner=Slice-49` remain unchanged, governance checks pass, and readiness counters advance from `2/2` to `3/3`.

## Acceptance Criteria
1. In both route-fence artifacts, exactly one row changes:
   - `command=config_validate`, `mode=n/a`, `parity status: pending -> ready`.
2. All row routes remain unchanged (specifically `config_validate|n/a` stays `v0`).
3. All row owners remain unchanged (specifically owner stays `Slice-49`).
4. Governance checks pass:
   - `.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check readiness`
   - `.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check parity`
   - `.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check characterization`
   - `.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check architecture`
   - `.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check all`
5. Readiness counters advance from `claimed_rows=2`, `validated_rows=2` to `claimed_rows=3`, `validated_rows=3`.
6. Implementation and audit reports are saved in slice-52 report paths with explicit evidence and behavior-preservation statement.

## Worker Responsibility Split
- Implementation worker responsibilities:
  - apply only the planned route-fence row mutation (`pending -> ready`) in markdown and JSON
  - run required governance verification commands
  - write `slice-52-implementation.md` with commands, outcomes, and preservation statement
- Audit worker responsibilities:
  - independently verify files changed and command evidence
  - validate acceptance criteria and fail-close criteria
  - write `slice-52-audit.md` with compliance classification and closure decision

## Closure-Evidence Posture (Same-SHA Discipline)
- local SHA field: `b2c4584f432f3e94218a3110f39e3e3bef100164`
- workflow identity field: `ci.yml`
- If same-SHA CI run evidence is unavailable, both implementation and audit reports must explicitly record:
  - inability to obtain same-SHA run evidence and why
  - residual-risk note for missing required-job status on exact SHA
- Reports must not imply same-SHA evidence exists when it is unavailable.

## Implementation Steps
1. Re-read `WORK_ITEMS.md` and `project/route-fence.*` to confirm current baseline and exact target row.
2. Update `project/route-fence.md` table row for `config_validate|n/a`: `pending -> ready`.
3. Apply the exact matching JSON row update in `project/route-fence.json`.
4. Run governance checks listed in acceptance criteria.
5. Capture command outcomes and counters in `slice-52-implementation.md`.
6. Complete implementation phase and hand off to audit worker.

## Post-Implementation Orchestration Steps (Non-Implementation Worker)
1. Run independent audit phase and write `slice-52-audit.md`.
2. Update `WORK_ITEMS.md` with Slice 52 status and next-slice recommendation after audit completion.

## Risks / Guardrails
- Risk: accidental route flip while editing route-fence rows.
  - Guardrail: fail-closed if any `route` field changes.
- Risk: accidental owner churn.
  - Guardrail: fail-closed if any `owner slice` field changes.
- Risk: scope creep into workflow coverage, runtime-gate policy, or parity matrix.
  - Guardrail: keep edits limited to route-fence row parity status plus reporting/docs updates.
- Risk: markdown/json drift between route-fence artifacts.
  - Guardrail: readiness/parity checks must pass before closure.

## Fail-Closed Criteria (Block / No-Close Triggers)
- Any `route` field changes in `project/route-fence.md` or `project/route-fence.json`.
- Any `owner slice` field changes in `project/route-fence.md` or `project/route-fence.json`.
- Any parity-status change to any row other than `config_validate|n/a`.
- Readiness check does not report `claimed_rows=3` and `validated_rows=3` after mutation.
- Any required governance check in Acceptance Criteria fails.
- Any additional governance artifact mutation outside the in-scope list appears in `git diff --name-only`.

## Rollback
- Revert `project/route-fence.md` and `project/route-fence.json` changes for `config_validate|n/a`.
- Keep slice report files and classify the slice as blocked with recorded failing evidence.

## Suggested Next Slice
- Slice 53: route-progression decision record for `config_validate|n/a` (decision-only, no route flip), including same-SHA CI evidence posture and explicit go/no-go gate for a later one-row `v0 -> v1` activation slice.
