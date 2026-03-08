# Slice-29b Plan (Final)

## Slice Id and Title
- Slice id: `Slice-29b`
- Slice title: `Runtime evasion remediation tranche 2b (client.py)`

## Objective
- Clear anti-evasion suppression from `src/jfin/client.py`.
- Keep honest LOC for `src/jfin/client.py` at `<=300`.
- Preserve behavior and safety invariants.
- Keep `A-08` open and do not progress to Slice 30+ in this slice.

## In Scope / Out of Scope
- In scope:
  - Behavior-preserving edits in `src/jfin/client.py`.
  - Tightly-coupled helper movement with `src/jfin/client_http.py` only if unavoidable.
  - Optional extraction to one tightly-coupled helper module if required to satisfy honest formatted LOC.
- Out of scope:
  - CLI/pipeline remediation slices.
  - Governance/route-fence redesign.
  - Any behavior change to auth/retry/backoff/timeout/TLS/dry-run/fail-fast semantics.
  - A-08/GG-008 closure work.

## Target Files
- `src/jfin/client.py`
- Optional only if unavoidable: `src/jfin/client_http.py`
- Optional only if unavoidable: `src/jfin/client_image_ops.py`
- `project/v1-slices-reports/slice-29b/slice-29b-plan.md`
- `project/v1-slices-reports/slice-29b/slice-29b-implementation.md` (post-implementation)
- `project/v1-slices-reports/slice-29b/slice-29b-audit.md` (post-audit)

## Public Interfaces Affected
- No public interface changes allowed.
- Preserve signatures and behavior for `JellyfinClient` methods, especially:
  - `_headers`, `_get`, `_get_json`, `_head`, `_writes_allowed`, `_guess_content_type`
  - `test_connection`, `list_users`, `list_media_folders`, `query_items`, `get_item`
  - `get_item_image`, `get_item_image_head`, `get_user_image`
  - `_post_image`, `set_item_image_bytes`, `set_item_image`, `set_user_image_bytes`
  - `delete_image`, `set_user_profile_image`

## Acceptance Criteria
- No `# fmt: off/on` remains in either `src/jfin/client.py` or `src/jfin/client_http.py`.
- No anti-evasion tactics are introduced (formatter suppression, semicolon packing, dense inline control-flow suites).
- Honest LOC for `src/jfin/client.py` is `<=300`.
- Targeted client/discovery/safety tests pass.
- `verify_governance --check loc` and `--check all` do not flag either `src/jfin/client.py` or `src/jfin/client_http.py`.
- Offender-set assertions pass with no unexpected expansion.
- Scope evidence shows only allowed runtime files touched.
- `A-08` remains open.

## Exact Verification Commands
```powershell
$ErrorActionPreference = 'Stop'
$env:PYTHONPATH = 'src'

$expectedRemaining = @(
  'src/jfin/cli.py',
  'src/jfin/cli_runtime.py',
  'src/jfin/pipeline.py',
  'src/jfin/pipeline_backdrops.py'
)
$expectedCleared = @('src/jfin/client.py', 'src/jfin/client_http.py')
$allowedRuntimeTouches = @('src/jfin/client.py', 'src/jfin/client_http.py', 'src/jfin/client_image_ops.py')

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

# Minimum required checks for Slice-29b
$fmtHits = rg -n "#\s*fmt:\s*(off|on)" src/jfin/client.py src/jfin/client_http.py
if ($LASTEXITCODE -eq 0) {
  $fmtHits
  throw 'Formatter suppression remains in client pair.'
}

$clientLoc = (Get-Content src/jfin/client.py).Length
"client.py LOC=$clientLoc"
if ($clientLoc -gt 300) {
  throw 'src/jfin/client.py exceeds 300 LOC'
}

.\.venv\Scripts\python.exe -m ruff check src/jfin/client.py src/jfin/client_http.py --select E701,E702,E703

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
- `git revert <slice-29b-commit-sha>`
- Re-run targeted pytest and governance `--check loc` / `--check all`.

## Behavior-Preservation Statement
- Behavior-preserving only.
- No intended changes to runtime semantics or safety invariants.
- Dry-run write protections remain intact.

## Implementation Steps
1. Capture baseline evidence (fmt markers, LOC, offender set) for client pair.
2. Remove formatter suppression from `src/jfin/client.py` using formatter-compatible structure.
3. Keep runtime changes local to `client.py`; only edit `client_http.py` if unavoidable for behavior-preserving coupling.
4. Run minimum and full verification commands.
5. Produce implementation report and independent audit report.

## Risks / Guardrails
- Risk: behavior drift in client request/response handling.
  - Guardrail: keep edits structural only and run targeted safety tests.
- Risk: honest LOC for `client.py` exceeded after formatting.
  - Guardrail: small local extraction only; no evasion tactics.
- Risk: scope creep.
  - Guardrail: explicit scope assertion against touched `src` files.

## Expected Commit Title
- `Slice-29b Runtime evasion remediation tranche 2b (client.py)`

## Split Rule
- Split immediately if substantive runtime edits beyond `client.py` (or unavoidable tight coupling with `client_http.py` / a single helper extraction module) are required.
- If honest `<=300` LOC cannot be achieved without behavior risk, stop and mark blocked rather than widening scope.

## Plan Review Notes
- Planning worker draft required two revisions to align with the exact Slice-29b objective and command set.
- Final plan enforces fail-closed offender-set assertions: both client files must clear anti-evasion findings.
- `A-08` remains open and unchanged by this slice.
