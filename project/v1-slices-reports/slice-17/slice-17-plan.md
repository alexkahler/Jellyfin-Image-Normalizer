# Slice 17 Plan

## Slice Id and Title
- Slice id: `A-03`
- Slice title: `Medium-coupling LOC closure slot 1 (adaptive) - client.py`

## Objective
Reduce `src/jfin/client.py` to `<=300` LOC via behavior-preserving extraction while preserving API client safety semantics.

## Adaptive Revalidation Basis
- Prior touched module check: `backup.py` is now `<=300`, so continuation rule does not apply.
- Medium-tier candidates after revalidation: `client.py:722`, `config.py:659`.
- Selected target for A-03: `client.py` (higher overage first per roadmap rule).

## In-Scope / Out-of-Scope
- In scope: `src/jfin/client.py` plus at most one adjacent helper module.
- Out of scope: `config.py`, CLI/config semantics redesign, route-fence changes, behavior changes.

## Target Files
- `src/jfin/client.py`
- `src/jfin/client_http.py` (new helper module, if needed)
- Tests only if strictly required for compatibility

## Public Interfaces Affected
- `JellyfinClient` public constructor fields and method signatures remain compatible.
- Preserve monkeypatch seams used by current tests (`_get_json`, `_headers`, `_writes_allowed`, etc.).

## Acceptance Criteria
- `src/jfin/client.py` is `<=300` LOC.
- No touched `src/` file exceeds 300 LOC.
- Net `src` LOC delta is `<=150` unless justified.
- `tests/test_client.py` passes.
- `tests/test_discovery.py` passes.
- `tests/characterization/safety_contract/test_safety_contract_api.py` passes.
- `verify_governance --check architecture` passes.

## Exact Verification Commands
```powershell
@('src/jfin/client.py','src/jfin/client_http.py') | ForEach-Object { if (Test-Path $_) { "{0}:{1}" -f $_, (Get-Content $_).Length } }
$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest -q tests/test_client.py
$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest -q tests/test_discovery.py
$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest -q tests/characterization/safety_contract/test_safety_contract_api.py
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check architecture
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check loc
git diff --numstat -- src
```

## Rollback Step
`git revert <A-03 commit>` and rerun the verification commands above.

## Behavior-Preservation Statement
Structural extraction only; preserve auth header shape, retry/backoff flow, timeout/TLS usage, and dry-run/write gates.

## Implementation Steps
1. Extract private HTTP/retry/write internals into one helper module.
2. Keep `JellyfinClient` public methods/signatures stable as wrappers.
3. Preserve monkeypatch compatibility for current tests.
4. Run module-specific matrix and governance checks.
5. Confirm LOC and net `src` delta constraints.

## Risks / Guardrails
- Risk: retry/backoff or dry-run semantic drift.
- Guardrail: preserve flow order and run safety + client regression suites.
- Risk: interface break from moved internals.
- Guardrail: keep wrappers and method signatures unchanged.

## Expected Commit Title
`a-03: client LOC closure`
