# Slice 47 Plan - Route Flip `run|backdrop` (`v0 -> v1`)

Date: 2026-03-09
Branch: feat/v1-overhaul
Local SHA: 9edd512aed14023389eb5bf551b3247b93874b55

## Slice Type
- route flip
- single-row governance mutation

## Route-Flip Discipline Precheck
eligible_now: row `run|backdrop` is `parity_status=ready` and currently `route=v0`.
smaller_safer_than_alternative: this is the only remaining eligible `ready+v0` row after Slice 46 progression.
readiness_evidence: readiness validator reports 2 claimed/validated rows and includes `run|backdrop`.
same_sha_status: unavailable
workflow_identity: GitHub Actions `ci.yml`
same_sha_unavailable_reason: no CI workflow run exists on GitHub for local SHA `9edd512aed14023389eb5bf551b3247b93874b55`.
residual_risk: remote required-job outcomes for this exact SHA are unavailable; progression relies on local governance pass and explicit fail-closed disclosure.
flip_unsafety_risks: absent same-SHA remote run evidence can hide CI-environment-only regressions.
rollback_path: revert `run|backdrop` route field from `v1` back to `v0` in both `project/route-fence.md` and `project/route-fence.json`.
flip_slice_smallness: exactly one row changed in exactly two governance truth files.

## In Scope
- `project/route-fence.md`
- `project/route-fence.json`
- `project/v1-slices-reports/slice-47/slice-47-plan.md`
- `project/v1-slices-reports/slice-47/slice-47-implementation.md`
- `project/v1-slices-reports/slice-47/slice-47-audit.md`

## Out of Scope
- all other route-fence rows
- parity status changes
- owner changes
- runtime code/tests/docs outside slice report

## Binary Success Condition
- Success only if `run|backdrop` route is `v1` in both route-fence artifacts, all other rows remain unchanged, governance checks pass, and same-SHA unavailability is explicitly recorded with residual risk.

## Expected Next Slice If Successful
- completion stop if no other `ready+v0` route-fence rows remain.

## Expected Next Slice If Unsuccessful
- single-row remediation for route-fence parity/consistency failure on `run|backdrop`.
