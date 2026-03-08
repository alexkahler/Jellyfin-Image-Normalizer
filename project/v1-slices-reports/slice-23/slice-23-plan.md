# Slice 23 Plan

## Slice Id and Title
- Slice id: `A-07`
- Slice title: `Residual blocker closure + GG-001 gate`

## Objective
Close the residual GG-001 governance posture for Theme A by validating and recording current closure evidence (`src` LOC compliance + governance gate pass) with minimum/no runtime code change.

## In-Scope / Out-of-Scope
- In scope: evidence-first A-07 closure work, current-state revalidation, slice artifacts, and narrow governance-status synchronization.
- In scope: minimal updates needed to record closure status (for example, `WORK_ITEMS.md` status line updates).
- Out of scope: new decomposition/refactor work, route-fence changes, route flips, CLI/config semantic changes, architecture redesign, reopening closed LOC slices without fresh regression evidence.

## Target Files
- `project/v1-slices-reports/slice-23/slice-23-plan.md`
- `project/v1-slices-reports/slice-23/slice-23-audit.md`
- `WORK_ITEMS.md` (status synchronization only, if needed)

## Public Interfaces Affected
- None expected.
- All runtime public interfaces under `src/jfin/` must remain behavior-identical.

## Acceptance Criteria
- All Python files under `src/` are `<=300` LOC at verification time.
- `.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check loc` passes (warnings allowed per contract policy where non-blocking).
- `.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check architecture` passes.
- `.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check all` passes.
- Known architecture ratchet warning (`pipeline.py.system_exit_raises`) is treated as non-blocking unless it escalates to failure in fresh verification.
- No behavior-changing runtime code edits are introduced.
- Slice audit explicitly records GG-001 closure recommendation based on command evidence.

## Exact Verification Commands
```powershell
Get-ChildItem src -Recurse -Filter *.py | ForEach-Object { "{0}:{1}" -f $_.FullName, (Get-Content $_.FullName).Length }
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check loc
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check architecture
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check all
git diff --numstat -- src
```
If any non-governance file is touched during A-07, add only narrowly relevant targeted pytest commands for those touched areas.

## Rollback Step
`git revert <A-07 commit>` and rerun the A-07 verification commands above.

## Behavior-Preservation Statement
A-07 is a governance closure/evidence slice. No intended runtime behavior change; CLI/config/route and safety semantics remain preserved.

## Implementation Steps
1. Re-run A-07 entry/closure gates from current HEAD (`loc`, `architecture`, `all`) and capture exact outputs.
2. Confirm no new `src` LOC blockers and no new architecture failures.
3. Keep runtime code unchanged unless a fresh failing gate proves narrow remediation is required.
4. Update only required closure artifacts (slice plan/audit, optional `WORK_ITEMS.md` status sync).
5. Produce A-07 audit report with explicit verdict on GG-001 closure readiness.
6. If any gate fails, stop A-07 closure, document blocked state and required remediation; do not proceed to A-08.

## Risks / Guardrails
- Risk: stale evidence or relying on prior-run outputs.
- Guardrail: run all A-07 closure commands fresh in this slice.
- Risk: over-scoping into unnecessary refactor.
- Guardrail: evidence-first scope; runtime changes only if required by current failing gate.
- Risk: treating warning as failure (or failure as warning).
- Guardrail: classify strictly by current command exit status and roadmap policy.
- Risk: accidental reopening of closed slices.
- Guardrail: no reopen unless fresh regression is proven by current verification.

## Expected Commit Title
`a-07: residual blocker closure + gg-001 gate`
