# Slice 16 Plan

## Slice Id and Title
- Slice id: `A-02`
- Slice title: `Backup LOC closure`

## Objective
Reduce `src/jfin/backup.py` from 540 LOC to `<=300` via behavior-preserving extraction while preserving restore and dry-run safety semantics.

## In-Scope / Out-of-Scope
- In scope: `src/jfin/backup.py` and one adjacent helper module for restore-heavy internals.
- Out of scope: restore semantics redesign, route-fence changes, CLI/config contract changes.

## Target Files
- `src/jfin/backup.py`
- `src/jfin/backup_restore.py` (new helper module, if needed)
- `tests/test_backup.py` only if compatibility adjustments are required
- `tests/characterization/safety_contract/test_safety_contract_restore.py` only if compatibility adjustments are required

## Public Interfaces Affected
- Public backup entry points remain signature-compatible:
  - `restore_from_backups`
  - `restore_single_item_from_backup`
  - `save_backup`
  - `should_backup_for_plan`

## Acceptance Criteria
- `src/jfin/backup.py` is `<=300` LOC.
- No touched `src/` file exceeds 300 LOC.
- Net `src/` LOC delta is `<=150` unless justified.
- Restore safety behavior remains preserved.
- `tests/test_backup.py` passes.
- `tests/characterization/safety_contract/test_safety_contract_restore.py` passes.
- `verify_governance.py --check architecture` passes.

## Exact Verification Commands
```powershell
@('src/jfin/backup.py','src/jfin/backup_restore.py') | ForEach-Object { if (Test-Path $_) { "{0}:{1}" -f $_, (Get-Content $_).Length } }
$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest -q tests/test_backup.py
$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest -q tests/characterization/safety_contract/test_safety_contract_restore.py
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check architecture
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check loc
git diff --numstat -- src
```

## Rollback Step
`git revert <A-02 commit>` and rerun the verification commands above.

## Behavior-Preservation Statement
Structural extraction only. No intended changes to restore decisions, dry-run behavior, write-gating, or public command/config semantics.

## Implementation Steps
1. Isolate restore-related logic in `backup.py` that can be moved without changing behavior.
2. Create one helper module for extracted restore internals.
3. Keep compatibility wrappers in `jfin.backup` so public APIs and monkeypatch targets remain stable.
4. Re-run targeted restore unit and characterization tests.
5. Confirm LOC closure and net `src` LOC budget compliance.

## Risks / Guardrails
- Risk: restore behavior drift in backdrop contiguous-index handling.
- Guardrail: keep existing algorithms and run restore safety characterization.
- Risk: monkeypatch-based tests break due moved symbols.
- Guardrail: preserve symbols/wrappers at `jfin.backup` module level.
- Risk: dry-run path accidentally writes.
- Guardrail: preserve dry-run short-circuit behavior exactly.

## Expected Commit Title
`a-02: backup LOC closure`
