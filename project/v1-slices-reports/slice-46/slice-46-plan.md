# Slice 46 Plan - Route Flip `test_connection|n/a` (`v0 -> v1`)

Date: 2026-03-09
Branch: feat/v1-overhaul
Local SHA: 9edd512aed14023389eb5bf551b3247b93874b55

## Slice Type
- route flip
- single-row governance mutation

## Route-Flip Discipline Precheck
eligible_now: row `test_connection|n/a` is `parity_status=ready` and currently `route=v0`.
smaller_safer_than_alternative: this row is narrower than `run|backdrop` because it has no media-mode branching and lower workflow surface.
readiness_evidence: readiness validator reports 2 claimed/validated rows and includes `test_connection|n/a`.
same_sha_status: unavailable
workflow_identity: GitHub Actions `ci.yml`
same_sha_unavailable_reason: no CI workflow run exists on GitHub for local SHA `9edd512aed14023389eb5bf551b3247b93874b55`.
residual_risk: remote required-job outcomes for this exact SHA are unavailable; progression relies on local governance pass and explicit fail-closed disclosure.
flip_unsafety_risks: lack of same-SHA remote run coverage can hide branch-protection-level regressions.
rollback_path: revert `test_connection|n/a` route field from `v1` back to `v0` in both `project/route-fence.md` and `project/route-fence.json`.
flip_slice_smallness: exactly one row changed in exactly two governance truth files.

## In Scope
- `project/route-fence.md`
- `project/route-fence.json`
- `project/v1-slices-reports/slice-46/slice-46-plan.md`
- `project/v1-slices-reports/slice-46/slice-46-implementation.md`
- `project/v1-slices-reports/slice-46/slice-46-audit.md`

## Out of Scope
- all other route-fence rows
- parity status changes
- owner changes
- runtime code/tests/docs outside slice report

## Binary Success Condition
- Success only if `test_connection|n/a` route is `v1` in both route-fence artifacts, all other rows remain unchanged, governance checks pass, and same-SHA unavailability is explicitly recorded with residual risk.

## Expected Next Slice If Successful
- one-row route flip for `run|backdrop` (`v0 -> v1`).

## Expected Next Slice If Unsuccessful
- single-row remediation for route-fence parity/consistency failure on `test_connection|n/a`.
