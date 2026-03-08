# Slice 18 Plan

## Slice Id and Title
- Slice id: `A-04`
- Slice title: `Medium-coupling closure slot 2 (adaptive) - config.py`

## Objective
Reduce `src/jfin/config.py` to `<=300` LOC with behavior-preserving extraction only.

## Adaptive Revalidation Basis
- Prior touched module (`client.py`) is now `<=300`.
- Remaining medium-tier blocker is `config.py` (`659`), so A-04 targets `config.py`.

## In-Scope / Out-of-Scope
- In scope: `src/jfin/config.py` and at most one adjacent helper module.
- Out of scope: CLI/config behavior redesign, route-fence changes, high-coupling module work.

## Target Files
- `src/jfin/config.py`
- `src/jfin/config_core.py` (new helper module, if needed)

## Public Interfaces Affected
- Keep `jfin.config` public symbols/signatures behavior-compatible:
  - `ConfigError`, `ModeRuntimeSettings`, `DiscoverySettings`
  - config loading/validation/operation parsing/build helpers

## Acceptance Criteria
- `src/jfin/config.py` is `<=300` LOC.
- No touched `src/` file exceeds 300 LOC.
- Net `src` LOC delta is `<=150` unless justified.
- `tests/test_config.py` passes.
- `tests/characterization/config_contract` passes.
- `verify_governance --check architecture` passes.

## Exact Verification Commands
```powershell
@('src/jfin/config.py','src/jfin/config_core.py') | ForEach-Object { if (Test-Path $_) { "{0}:{1}" -f $_, (Get-Content $_).Length } }
$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest -q tests/test_config.py
$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest -q tests/characterization/config_contract
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check architecture
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check loc
git diff --numstat -- src
```

## Rollback Step
`git revert <A-04 commit>` and rerun verification commands.

## Behavior-Preservation Statement
Structural extraction only; preserve config precedence, validation outcomes, and CLI/config contract semantics.

## Implementation Steps
1. Extract internal/pure config logic into one helper module.
2. Keep `config.py` as compatibility facade with unchanged public API signatures.
3. Preserve exit-bearing compatibility paths where needed for architecture guard behavior.
4. Run config unit + characterization matrix and governance checks.
5. Confirm LOC and net `src` delta constraints.

## Risks / Guardrails
- Risk: config validation/precedence drift.
- Guardrail: direct-lift extraction + config contract tests.
- Risk: interface break on imports.
- Guardrail: retain/re-export public symbols from `jfin.config`.

## Expected Commit Title
`a-04: config LOC closure`
