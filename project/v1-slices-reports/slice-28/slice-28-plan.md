# Slice 28 Plan (v3 FINAL)

## Slice Id and Title
- Slice id: `Slice-28`
- Slice title: `Runtime evasion remediation tranche 1 (config pair)`

## Objective
- Remove anti-evasion reliance from the config pair while preserving behavior.
- Keep honest LOC at `<=300` for `src/jfin/config.py` and `src/jfin/config_core.py` without suppression or packing tactics.
- Complete only this tranche scope.
- Keep `A-08` open; no closure claim in Slice 28.

## In Scope
- Behavior-preserving structural remediation only in:
- `src/jfin/config.py`
- `src/jfin/config_core.py`
- Removal of `# fmt: off` / `# fmt: on` in the target pair.
- Small helper extraction/reordering between these two files only, if needed, to stay within LOC guardrails.

## Out of Scope
- Any change to CLI/config contract semantics (flags, precedence, defaults, validation semantics, error/exit behavior).
- Any edit outside `src/jfin/config.py` and `src/jfin/config_core.py`.
- Governance artifact changes (`project/*`, parity/route-fence docs, characterization baselines).
- Work on client/CLI/pipeline evasion files.
- Closing `A-08`.

## Target Files
- `src/jfin/config.py`
- `src/jfin/config_core.py`

## Public Interfaces Affected
- Interface change policy: no public interface changes are allowed in this slice.
- `config.py`: `default_config_path`, `generate_default_config`, `load_config_from_path`, `load_config`, `parse_operations`, `validate_config_for_mode`, `build_mode_runtime_settings`, `build_discovery_settings`, `build_jellyfin_client_from_config`
- `config_core.py`: `ModeRuntimeSettings`, `DiscoverySettings`, `ConfigError`, `parse_str_list`, `parse_item_types`, `apply_cli_overrides`, `validate_config_types`

## Acceptance Criteria
- `# fmt: off` / `# fmt: on` are removed from both target files.
- No anti-evasion tactics are introduced in target files:
- no formatter suppression
- no multi-statement semicolon packing
- no dense inline control-flow packing
- Honest LOC is `<=300` for each target file.
- Targeted config tests pass.
- `verify_governance --check loc` and `--check all` are expected to remain non-zero globally until later remediation slices.
- Slice-28-specific requirement: those outputs must no longer report anti-evasion findings for `src/jfin/config.py` or `src/jfin/config_core.py`.
- `A-08` is explicitly still open at slice close.

## Exact Verification Commands
```powershell
$env:PYTHONPATH='src'

# Targeted tests for the touched subsystem
.\.venv\Scripts\python.exe -m pytest -q tests/test_config.py tests/characterization/config_contract/test_config_contract_characterization.py

# Target-file anti-evasion checks
rg -n "#\s*fmt:\s*(off|on)" src/jfin/config.py src/jfin/config_core.py
if ($LASTEXITCODE -eq 0) { throw "Formatter suppression remains in target config pair." }

.\.venv\Scripts\python.exe -m ruff check src/jfin/config.py src/jfin/config_core.py --select E701,E702,E703

# Honest LOC checks for target files
$configLoc = (Get-Content src/jfin/config.py).Length
$configCoreLoc = (Get-Content src/jfin/config_core.py).Length
"config.py LOC=$configLoc"
"config_core.py LOC=$configCoreLoc"
if ($configLoc -gt 300 -or $configCoreLoc -gt 300) { throw "Target config pair exceeds 300 LOC." }

# Governance fail-closed context: non-zero is expected globally for now,
# but config pair must be cleared from anti-evasion findings.
$locOutput = & .\.venv\Scripts\python.exe project/scripts/verify_governance.py --check loc 2>&1
$locExit = $LASTEXITCODE
$locText = $locOutput | Out-String
$locText
if ($locText -match [regex]::Escape("src/jfin/config.py [anti_evasion.")) { throw "config.py still flagged in --check loc." }
if ($locText -match [regex]::Escape("src/jfin/config_core.py [anti_evasion.")) { throw "config_core.py still flagged in --check loc." }
if ($locExit -eq 0) { throw "Expected --check loc to remain non-zero globally until later slices." }

$allOutput = & .\.venv\Scripts\python.exe project/scripts/verify_governance.py --check all 2>&1
$allExit = $LASTEXITCODE
$allText = $allOutput | Out-String
$allText
if ($allText -match [regex]::Escape("src/jfin/config.py [anti_evasion.")) { throw "config.py still flagged in --check all." }
if ($allText -match [regex]::Escape("src/jfin/config_core.py [anti_evasion.")) { throw "config_core.py still flagged in --check all." }
if ($allExit -eq 0) { throw "Expected --check all to remain non-zero globally until later slices." }

# Repository contract command set from AGENTS.md
$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
.\.venv\Scripts\python.exe -m mypy src
.\.venv\Scripts\python.exe -m bandit -r src
.\.venv\Scripts\python.exe -m pip_audit

# Slice evidence
git diff --numstat -- src/jfin/config.py src/jfin/config_core.py
```

## Behavior-Preservation Statement
- Slice 28 is behavior-preserving only.
- No intended changes to user-visible CLI/config contract behavior.
- Existing validation, exception, and runtime-setting semantics must remain equivalent.

## Implementation Steps
1. Capture pre-change baselines for the two target files (LOC, suppression markers, and current anti-evasion findings).
2. Remove formatter suppression markers from both files.
3. Reformat and perform minimal structure cleanup needed for readable, formatter-compatible code.
4. If needed for LOC, move cohesive helper logic only between `config.py` and `config_core.py`.
5. Re-run targeted config tests after each micro-change.
6. Run anti-evasion checks and verify config-pair clearance from `--check loc` and `--check all` outputs.
7. Run AGENTS contract command set and collect slice evidence.
8. Record that `A-08` remains open and is not closed by Slice 28.

## Risks / Guardrails
- Risk: behavior drift during helper movement.
- Guardrail: no signature/contract changes; run targeted tests after each change.
- Risk: LOC overflow after suppression removal.
- Guardrail: split logic by cohesive responsibility inside the config pair only; no evasion tactics.
- Risk: scope creep into other runtime modules or governance artifacts.
- Guardrail: hard-stop on edits outside the two target files.

## Rollback
- `git revert <slice-28-commit-sha>`
- Re-run the targeted config tests and both governance checks (`--check loc`, `--check all`) to confirm restoration.

## Expected Commit Title
- `Slice-28 Runtime evasion remediation tranche 1 (config pair)`

## Explicit Split Rule
- If completion requires editing any file outside `src/jfin/config.py` and `src/jfin/config_core.py`, stop and split immediately.
- If either target file cannot be kept at honest `<=300` LOC without contract/behavior risk, stop and split by cohesive helper boundary inside the config pair rather than using any anti-evasion tactic.
