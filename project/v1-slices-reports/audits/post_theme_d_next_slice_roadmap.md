# Post-Theme-D Next Slice Iteration Roadmap

## Planning Baseline

Current baseline for planning:
- Themes A-D: closed
- Route-fence rows: 8 total
- Ready rows: 1
- Pending rows: 7
- Route state: all `v0`
- Workflow coverage cells: 2
- Validated readiness claims: 1
- Governance posture: pass with warnings
- Known warning debt:
  - architecture ratchet drift
  - test LOC warning debt
  - same-SHA CI evidence freshness gap

Planning rule for this roadmap:
- Do not plan route flips yet.
- Prioritize ownership completion, readiness breadth, and warning-debt hygiene.
- Treat each route as a governed slice with explicit acceptance and verification.

## Roadmap Goal

Move from governance activation to controlled route-by-route readiness scaling, while preserving `route=v0` until at least two non-placeholder readiness paths are validated and governance warning noise is reduced.

## Slice 38 — Governance Hygiene and Roadmap Refresh

### Objective
Refresh stale planning artifacts and ratchet architecture governance so subsequent slices operate from a clean baseline.

### Scope
- Replace stale iteration-roadmap narrative that still frames Themes A-D as upcoming.
- Update planning baseline references to current post-Theme-D metrics.
- Ratchet `project/architecture-baseline.json` to verified observed counters.
- At minimum align `pipeline.py.system_exit_raises` with observed value.
- Re-run governance verification and record resulting warning delta.

### Acceptance
- Iteration roadmap reflects post-Theme-D reality.
- Architecture baseline drift warning is removed or explicitly re-baselined with justification.
- `--check architecture` passes without the stale-ratchet warning.
- `--check all` remains passing.

### Verification
- `python project/scripts/verify_governance.py --check architecture`
- `python project/scripts/verify_governance.py --check all`

### Exit Gate
Proceed only when governance signal quality is improved and planning artifacts no longer describe closed themes as future work.

## Slice 39 — Ownership Completion for Next Candidate Route

### Objective
Replace placeholder accountability on one next non-backdrop route-fence row with concrete owner metadata.

### Preferred candidate
Select one lower-blast-radius route first:
1. `test_connection`, or
2. `config_validate`

### Scope
- Choose one non-backdrop candidate row.
- Replace `WI-00X` placeholder with concrete owner metadata.
- Add explicit acceptance notes for that route.
- Confirm parity linkage and test ownership expectations are documented.

### Acceptance
- Selected route has no placeholder owner metadata.
- Route-fence artifact parses cleanly.
- Ownership and sequencing are explicit enough to support a readiness slice.

### Verification
- `python project/scripts/verify_governance.py --check readiness`
- `python project/scripts/verify_governance.py --check all`

### Exit Gate
Proceed only when one additional row is fully owned and no new governance debt is introduced.

## Slice 40 — Workflow Coverage Expansion for Selected Route

### Objective
Add the workflow-coverage evidence cell(s) needed to support the selected route’s readiness path.

### Scope
- Add workflow-coverage cell(s) for the selected route.
- Include required parity IDs.
- Include owner tests and evidence fields.
- Use explicit debt semantics for anything intentionally deferred.
- Keep breadth expansion narrow and auditable.

### Acceptance
- Coverage index includes the new governed cell(s).
- Characterization verification validates all configured cells.
- Open workflow-sequence debt remains zero, or any new debt is explicitly justified and bounded.

### Verification
- `python project/scripts/verify_governance.py --check characterization`
- `python project/scripts/verify_governance.py --check all`

### Exit Gate
Proceed only when configured coverage expands beyond the current 2-cell baseline without regressing closed debt posture.

## Slice 41 — Second Readiness Claim Activation

### Objective
Expand readiness from 1 validated claim path to at least 2 validated claim paths while preserving `route=v0`.

### Scope
- Activate readiness claim for the selected owned route.
- Ensure evidence is tied to route-fence and workflow coverage.
- Keep all routes at `v0`.
- Document why the route is claim-ready but not yet progression-ready.

### Acceptance
- Readiness claims increase from 1 to at least 2.
- Validated claims increase accordingly.
- No route is flipped to `v1`.
- Governance checks remain green.

### Verification
- `python project/scripts/verify_governance.py --check readiness`
- `python project/scripts/verify_governance.py --check all`

### Exit Gate
Proceed only when there are at least two validated readiness paths and route progression is still intentionally deferred.

## Slice 42 — Runtime-Gate Scope Decision Slice

### Objective
Decide whether broader characterization areas should be runtime-gated, and if so, expand them with explicit runtime-budget proof.

### Scope
- Review `characterization_runtime_gate_targets` scope.
- Evaluate whether selected new route evidence should be runtime-gated.
- If widening, add only the minimum additional target set needed.
- Record runtime budget and verification impact.

### Acceptance
- Decision is explicit: either no change with rationale, or widened scope with proof.
- Runtime-gate configuration remains intentional and auditable.
- Verification time/cost is documented.

### Verification
- `python project/scripts/verify_governance.py --check characterization`
- `python project/scripts/verify_governance.py --check all`
- targeted pytest characterization command(s), if added

### Exit Gate
Proceed only when runtime-gate scope is a deliberate policy choice rather than a leftover narrow default.

## Slice 43 — Test Maintainability Debt Reduction

### Objective
Reduce future slice friction by splitting or refactoring the highest-risk oversized test files.

### Priority targets
1. `tests/test_pipeline.py`
2. `tests/test_characterization_checks.py`

### Scope
- Split large files by behavior or governance concern.
- Preserve coverage and readability.
- Avoid mixing route-readiness work with broad behavioral changes.

### Acceptance
- At least one priority oversized file is reduced or decomposed.
- Verification remains green.
- LOC warning count trends downward or is explicitly documented if unchanged.

### Verification
- `python -m pytest`
- `python project/scripts/verify_governance.py --check loc`
- `python project/scripts/verify_governance.py --check all`

## Slice 44 — Evidence Freshness and Closure Discipline

### Objective
Make future closure audits same-SHA evidence complete.

### Scope
- Add explicit requirement to attach or record exact-SHA CI evidence when available.
- If CI evidence cannot be fetched, require documented inability and residual risk note.
- Update audit/closure checklist language accordingly.

### Acceptance
- Closure template or audit checklist requires same-SHA CI evidence handling.
- Future audits can no longer silently rely on stale or historical CI evidence.

### Verification
- audit artifact review
- governance review of updated checklist/template

## Route Progression Gate (Not Yet Planned)

A `route=v1` progression slice should not be scheduled until all of the following are true:
- at least 2 validated readiness claim paths exist
- at least 2 route-fence rows have real owners
- workflow coverage breadth is expanded beyond the current minimal baseline
- architecture ratchet warning is cleared
- runtime-gate policy is explicit
- current-SHA CI evidence expectations are defined

## Suggested Sequencing

1. Slice 38 — Governance Hygiene and Roadmap Refresh
2. Slice 39 — Ownership Completion for Next Candidate Route
3. Slice 40 — Workflow Coverage Expansion for Selected Route
4. Slice 41 — Second Readiness Claim Activation
5. Slice 42 — Runtime-Gate Scope Decision Slice
6. Slice 43 — Test Maintainability Debt Reduction
7. Slice 44 — Evidence Freshness and Closure Discipline

## Notes for Planners

- Prefer lower-blast-radius routes before heavier run-path routes.
- Treat `run|logo`, `run|thumb`, and `run|profile` as later candidates unless evidence shows they are equally cheap.
- Keep route progression decisions separate from readiness activation work.
- Avoid umbrella slices that mix ownership, coverage, readiness, and route flips in one PR.
- Continue evidence-first, fail-closed planning posture.

