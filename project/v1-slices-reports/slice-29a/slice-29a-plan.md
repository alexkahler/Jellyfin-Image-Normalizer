# Slice 30 Plan (Slice-29a Final)

## Slice Id and Title
- Slice id: `Slice-29a`
- Slice title: `Runtime evasion remediation tranche 2a (client_http first, decomposed)`

## Objective
- Remove anti-evasion suppression from `src/jfin/client_http.py`.
- Keep honest LOC for `src/jfin/client_http.py` at `<=300`.
- Preserve behavior and safety invariants.
- Keep `A-08` open and do not progress to Slice 30+ in this slice.

## In Scope / Out of Scope
- In scope:
  - Behavior-preserving edits in `src/jfin/client_http.py`.
  - Tightly-coupled helper movement between `client_http.py` and `client.py` only if unavoidable.
- Out of scope:
  - Runtime edits outside `src/jfin/client_http.py` and unavoidable `client.py` coupling.
  - CLI/pipeline tranche work.
  - Governance redesign or route-fence changes.
  - A-08/GG-008 closure work.

## Target Files
- `src/jfin/client_http.py`
- Optional only if unavoidable: `src/jfin/client.py`
- `project/v1-slices-reports/slice-30/slice-30-plan.md`
- `project/v1-slices-reports/slice-30/slice-30-implementation.md` (post-implementation)
- `project/v1-slices-reports/slice-30/slice-30-audit.md` (post-audit)

## Public Interfaces Affected
- Preserve signatures/behavior for `src/jfin/client_http.py` functions:
  - `_http_error`
  - `_request_with_retry`
  - `get_response`
  - `head_response`
  - `get_json_payload`
  - `test_connection`
  - `post_image`
  - `delete_image`
- Preserve `JellyfinClient` call behavior into `client_http`.

## Acceptance Criteria
- No `# fmt: off/on` remains in `src/jfin/client_http.py`.
- No anti-evasion tactics are introduced (formatter suppression, semicolon packing, dense inline control-flow suites).
- `src/jfin/client_http.py` LOC is `<=300`.
- Targeted client/discovery/safety tests pass.
- `verify_governance --check loc` and `--check all` do not flag `src/jfin/client_http.py`.
- `src/jfin/client.py` may remain flagged until Slice-29b.
- Offender-set assertions pass with no unexpected offender expansion.
- Scope evidence shows only allowed runtime files touched.
- `A-08` remains open.

## Exact Verification Commands
```powershell
$ErrorActionPreference = 'Stop'
$env:PYTHONPATH = 'src'

$expectedRemaining = @(
  'src/jfin/cli.py',
  'src/jfin/cli_runtime.py',
  'src/jfin/client.py',
  'src/jfin/pipeline.py',
  'src/jfin/pipeline_backdrops.py'
)
$expectedCleared = @('src/jfin/client_http.py')
$allowedRuntimeTouches = @('src/jfin/client_http.py', 'src/jfin/client.py')

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
    throw "Expected $CheckName to stay non-zero globally until later slices."
  }

  $offenders = Get-AntiEvasionOffenders -Text $OutputText
  "[$CheckName] offenders: $($offenders -join ', ')"

  $missingExpected = $expectedRemaining | Where-Object { $_ -notin $offenders }
  if ($missingExpected.Count -gt 0) {
    throw "$CheckName missing expected remaining offenders: $($missingExpected -join ', ')"
  }

  $stillFlaggedCleared = $expectedCleared | Where-Object { $_ -in $offenders }
  if ($stillFlaggedCleared.Count -gt 0) {
    throw "$CheckName still flags cleared targets: $($stillFlaggedCleared -join ', ')"
  }

  $unexpectedExpansion = $offenders | Where-Object { $_ -notin $expectedRemaining }
  if ($unexpectedExpansion.Count -gt 0) {
    throw "$CheckName has unexpected offender expansion: $($unexpectedExpansion -join ', ')"
  }
}

# Minimum required checks for Slice-29a
$fmtHits = rg -n "#\s*fmt:\s*(off|on)" src/jfin/client_http.py src/jfin/client.py
if ($LASTEXITCODE -eq 0) {
  $fmtText = $fmtHits | Out-String
  $fmtHits
  if ($fmtText -match 'src/jfin/client_http.py') {
    throw 'Formatter suppression remains in src/jfin/client_http.py'
  }
}

.\.venv\Scripts\python.exe -m ruff check src/jfin/client_http.py src/jfin/client.py --select E701,E702,E703

$clientHttpLoc = (Get-Content src/jfin/client_http.py).Length
"client_http.py LOC=$clientHttpLoc"
if ($clientHttpLoc -gt 300) {
  throw 'src/jfin/client_http.py exceeds 300 LOC'
}

$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest -q tests/test_client.py tests/test_discovery.py tests/characterization/safety_contract/test_safety_contract_api.py

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

# AGENTS.md repo contract set
$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
.\.venv\Scripts\python.exe -m mypy src
.\.venv\Scripts\python.exe -m bandit -r src
.\.venv\Scripts\python.exe -m pip_audit

# Scope evidence
git diff --numstat -- src
$srcTouched = git diff --name-only -- src
$unexpected = $srcTouched | Where-Object { $_ -notin $allowedRuntimeTouches }
if ($unexpected) {
  throw "Out-of-scope src touches: $($unexpected -join ', ')"
}
```

## Rollback Step
- `git revert <slice-29a-commit-sha>`
- Re-run targeted pytest and governance `--check loc` / `--check all`.

## Behavior-Preservation Statement
- Behavior-preserving only.
- No changes to auth/retry/backoff/timeout/TLS/dry-run/fail-fast semantics.
- Dry-run write protections remain intact.

## Implementation Steps
1. Capture baseline evidence (fmt markers, LOC, offender set) for client files.
2. Remove formatter suppression from `src/jfin/client_http.py` using formatter-compatible structure.
3. Keep runtime changes local to `client_http.py`; only use tightly-coupled helper movement with `client.py` if unavoidable.
4. Run minimum and full verification commands.
5. Produce implementation report and independent audit report; fail closed on any unmet acceptance criteria.

## Risks / Guardrails
- Risk: behavior drift in HTTP/retry/write-gate paths.
  - Guardrail: fail closed on any targeted test regression.
- Risk: scope creep into non-allowed files.
  - Guardrail: explicit scope assertion on touched `src` files.
- Risk: dishonest LOC compliance attempt.
  - Guardrail: anti-evasion checks and offender assertions are mandatory blockers.

## Expected Commit Title
- `Slice-29a Runtime evasion remediation tranche 2a (client_http first, decomposed)`

## Split Rule
- Split immediately if substantive edits beyond `client_http.py` become necessary.
- Split immediately if LOC/behavior cannot be satisfied honestly without suppression/packing.

## Plan Review Notes
- Review round 1 accepted from planning worker and finalized in main thread.
- Assumes blocked Slice 29 evidence remains unchanged.
- Assumes governance offender output format remains parseable by regex used above.
- `src/jfin/client.py` being flagged is allowed for Slice-29a and deferred to Slice-29b.
