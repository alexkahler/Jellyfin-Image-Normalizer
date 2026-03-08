# Slice-30 Plan (Final)

## Slice Id and Title
- Slice id: `Slice-30`
- Slice title: `Runtime evasion remediation tranche 3 (CLI pair)`

## Objective
- Remove anti-evasion suppression from `src/jfin/cli.py` and `src/jfin/cli_runtime.py`.
- Keep honest LOC `<=300` for both files.
- Preserve behavior with no CLI/config contract redesign.
- Keep `A-08` open.

## In Scope / Out of Scope
- In scope:
  - behavior-preserving structural remediation in `src/jfin/cli.py` and `src/jfin/cli_runtime.py`.
  - formatter-compatible restructuring required after suppression removal.
- Out of scope:
  - route flips, route-fence changes, governance redesign, CLI/config semantic redesign, A-08/GG-008 closure work.
  - runtime edits outside the CLI pair; if unavoidable, split the slice.

## Target Files
- `src/jfin/cli.py`
- `src/jfin/cli_runtime.py`
- `project/v1-slices-reports/slice-30/slice-30-plan.md`
- `project/v1-slices-reports/slice-30/slice-30-implementation.md` (post-implementation)
- `project/v1-slices-reports/slice-30/slice-30-audit.md` (post-audit)

## Public Interfaces Affected
- Preserve behavior/signatures for CLI entry flow in `src/jfin/cli.py` and dispatch/runtime helpers in `src/jfin/cli_runtime.py`.
- Preserve current flag handling, validation behavior, and existing exit semantics.
- Preserve dry-run/write safety behavior and API-first execution posture.

## Acceptance Criteria
- No `# fmt: off/on` remains in `src/jfin/cli.py` and `src/jfin/cli_runtime.py`.
- No anti-evasion tactics are introduced (no formatter suppression, semicolon packing, dense inline control-flow suites).
- Honest LOC `<=300` for both CLI files.
- CLI-focused targeted tests pass.
- `verify_governance --check loc` and `--check all` no longer flag `src/jfin/cli.py` or `src/jfin/cli_runtime.py`.
- Offender-set contraction after Slice-30 is exact to pipeline pair only:
  - `src/jfin/pipeline.py`
  - `src/jfin/pipeline_backdrops.py`
- `A-08` remains open.

## Exact Verification Commands
```powershell
$ErrorActionPreference = 'Stop'
$env:PYTHONPATH = 'src'

$expectedRemaining = @(
  'src/jfin/pipeline.py',
  'src/jfin/pipeline_backdrops.py'
)

$expectedCleared = @(
  'src/jfin/client.py',
  'src/jfin/client_http.py',
  'src/jfin/cli.py',
  'src/jfin/cli_runtime.py'
)

$allowedRuntimeTouches = @(
  'src/jfin/cli.py',
  'src/jfin/cli_runtime.py'
)

function Get-AntiEvasionOffenders {
  param([string]$Text)
  [regex]::Matches($Text, 'src/jfin/[A-Za-z0-9_]+\.py(?=\s+\[anti_evasion\.)') |
    ForEach-Object { $_.Value } |
    Sort-Object -Unique
}

function Assert-OffenderSet {
  param(
    [string]$CheckName,
    [int]$ExitCode,
    [string]$OutputText
  )

  if ($ExitCode -eq 0) {
    throw "Expected $CheckName to remain non-zero globally until later slices."
  }

  $offenders = Get-AntiEvasionOffenders -Text $OutputText
  "[$CheckName] offenders: $($offenders -join ', ')"

  $stillFlaggedCleared = $expectedCleared | Where-Object { $_ -in $offenders }
  if ($stillFlaggedCleared.Count -gt 0) {
    throw "$CheckName still flags cleared targets: $($stillFlaggedCleared -join ', ')"
  }

  $missingExpected = $expectedRemaining | Where-Object { $_ -notin $offenders }
  if ($missingExpected.Count -gt 0) {
    throw "$CheckName missing expected remaining offenders: $($missingExpected -join ', ')"
  }

  $unexpectedExpansion = $offenders | Where-Object { $_ -notin $expectedRemaining }
  if ($unexpectedExpansion.Count -gt 0) {
    throw "$CheckName has unexpected offender expansion: $($unexpectedExpansion -join ', ')"
  }
}

# 1) Suppression marker scan
$fmtHits = rg -n "#\s*fmt:\s*(off|on)" src/jfin/cli.py src/jfin/cli_runtime.py
if ($LASTEXITCODE -eq 0) {
  $fmtHits
  throw 'Formatter suppression remains in CLI pair.'
}

# 2) Honest LOC checks
$cliLoc = (Get-Content src/jfin/cli.py).Length
$cliRuntimeLoc = (Get-Content src/jfin/cli_runtime.py).Length
"cli.py LOC=$cliLoc"
"cli_runtime.py LOC=$cliRuntimeLoc"
if ($cliLoc -gt 300 -or $cliRuntimeLoc -gt 300) {
  throw 'CLI pair exceeds 300 LOC.'
}

# 3) Anti-packing lint checks
.\.venv\Scripts\python.exe -m ruff check src/jfin/cli.py src/jfin/cli_runtime.py --select E701,E702,E703

# 4) Targeted CLI regression checks
$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest -q `
  tests/characterization/cli_contract/test_cli_contract_characterization.py `
  tests/test_jfin.py `
  tests/test_config.py

# 5) Governance checks with offender assertions
$locOutput = & .\.venv\Scripts\python.exe project/scripts/verify_governance.py --check loc 2>&1
$locExit = $LASTEXITCODE
$locText = $locOutput | Out-String
$locText
Assert-OffenderSet -CheckName '--check loc' -ExitCode $locExit -OutputText $locText

$allOutput = & .\.venv\Scripts\python.exe project/scripts/verify_governance.py --check all 2>&1
$allExit = $LASTEXITCODE
$allText = $allOutput | Out-String
$allText
Assert-OffenderSet -CheckName '--check all' -ExitCode $allExit -OutputText $allText

# 6) AGENTS contract command set
$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
.\.venv\Scripts\python.exe -m mypy src
.\.venv\Scripts\python.exe -m bandit -r src
.\.venv\Scripts\python.exe -m pip_audit

# 7) Scope evidence
git diff --numstat -- src
$srcTouched = git diff --name-only -- src
$unexpected = $srcTouched | Where-Object { $_ -notin $allowedRuntimeTouches }
if ($unexpected) {
  throw "Out-of-scope src touches: $($unexpected -join ', ')"
}
```

## Rollback Step
- `git revert <slice-30-commit-sha>`
- Re-run targeted CLI tests and governance `--check loc` / `--check all`.

## Behavior-Preservation Statement
- Slice-30 is behavior-preserving only.
- No intended CLI flag/contract/default/precedence redesign.
- No intended change to safety invariants.

## Implementation Steps
1. Capture baseline evidence (suppression scan, LOC, offender set).
2. Remove suppression markers from CLI pair.
3. Apply minimal formatter-compatible restructuring to keep both files honestly `<=300`.
4. Run targeted CLI tests after each micro-change.
5. Run governance checks and enforce offender-set assertions.
6. Run AGENTS contract command set.
7. Produce implementation and audit artifacts.

## Risks / Guardrails
- Risk: CLI behavior drift during structural decomposition.
  - Guardrail: preserve public CLI behavior and verify with targeted CLI characterization/tests.
- Risk: LOC exceeds 300 after formatter compliance.
  - Guardrail: split by cohesive boundary; do not use suppression/packing.
- Risk: scope creep into non-CLI runtime files.
  - Guardrail: hard-stop and split if additional runtime files are required.

## Expected Commit Title
- `Slice-30 Runtime evasion remediation tranche 3 (CLI pair)`

## Split Rule
- If either CLI file cannot be kept at honest `<=300` without behavior risk, split before broadening edits.
- If any runtime file outside CLI pair is required, stop and open a decomposition slice rather than forcing completion.

## Plan Review Notes
- Planning worker draft accepted with final local normalization.
- Assumes Slice-29a and Slice-29b remain closed/compliant and pushed.
- Assumes pipeline pair remains the only expected anti-evasion offender set after successful Slice-30 closure.
