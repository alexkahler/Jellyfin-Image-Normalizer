# Slice-33 Plan

## Slice Id and Title
- Slice id: `Slice-33`
- Slice title: `A-08 same-SHA CI proof + Theme A closure gate`

## Objective
- Close GG-008 using canonical same-SHA CI proof for required jobs.
- Close Theme A only if both closure conditions are met:
  - GG-001: `verify_governance --check all` passes.
  - GG-008: same SHA CI run for workflow `CI` (`.github/workflows/ci.yml`) has required jobs `test`, `security`, `quality`, `governance` all `success`.

## Scope
- In scope:
  - Evidence retrieval and validation.
  - Slice-33 reporting artifacts.
  - Theme A closure status synchronization in roadmap/work items.
- Out of scope:
  - Runtime feature/refactor changes.
  - Route-fence semantics changes.

## Acceptance Criteria
- `git rev-parse HEAD` SHA captured.
- Local `verify_governance --check all` passes on that SHA.
- CI run exists for same SHA, workflow `CI`, path `.github/workflows/ci.yml`.
- Required jobs all `success`: `test`, `security`, `quality`, `governance`.
- Evidence includes run URL, run ID, workflow identity, head SHA, per-job conclusions.
- If any element missing/ambiguous, mark insufficient evidence and keep Theme A open.
