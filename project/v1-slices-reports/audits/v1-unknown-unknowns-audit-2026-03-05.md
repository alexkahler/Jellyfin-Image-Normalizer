# V1 Unknown-Unknowns Audit Report (Current Branch + Working Tree)

Audit timestamp: 2026-03-05 17:29:00 +01:00  
Audit scope: `feat/v1-overhaul` branch + working tree (including untracked files)  
HEAD: `1e2ed84db7c18848821e5e194290f1670673100b`  
Comparison base for migration surface inventory: `origin/main` merge-base `5ae2d179452a0b9635f1965802ae564e11d90a6d`

## 1) Executive Summary

Overall status: **Conditionally Compliant (governance artifacts), Noncompliant (full verification contract)**.

Top risks:
1. **High**: Backdrop parity ownership (`PIPE-BACKDROP-001`) under-specifies critical sequencing invariants, creating a coverage illusion.
2. **Medium**: Route-fence `parity_status` readiness is schema-validated but not semantically validated against parity evidence.
3. **Medium**: `project/v1-plan.md` characterization suite paths drift from current canonical structure and can mislead future route-flip planning.

Immediate blockers:
1. **Blocker**: `project/scripts/verify_governance.py --check all` fails on `src/` LOC blockers (`src_max_lines: 300` contract).
2. **Blocker**: Full verification-contract `pytest` command fails (`9 failed, 282 passed`), mostly characterization message-capture assertions.

## 2) Audit Target And Scope

- Target branch: `feat/v1-overhaul` (`HEAD` at `1e2ed84`).
- Working tree state: clean tracked files, **one untracked file** (`REPO_MAP.md`).
- Changed migration surface vs `origin/main` base:
  - `121 files changed`, `86334 insertions`, `312 deletions`.
  - Grouped paths: `src:4`, `tests:40`, `project:42`, `docs:8`, `ci:2`, `plans:8`, `.agents:12`, root files: `5`.

Out-of-scope clarifications:
- No live Jellyfin server integration/e2e verification was performed.
- Route-fence rows remain `v0`; this audit evaluates readiness/governance consistency, not active v1 runtime execution.

## 3) Evidence Collected

### 3.1 Verification Evidence

Planned command set (requested):
- `PYTHONPATH=src .\.venv\Scripts\python.exe project/scripts/verify_governance.py --check parity` -> **PASS**
- `PYTHONPATH=src .\.venv\Scripts\python.exe project/scripts/verify_governance.py --check characterization` -> **PASS** (`unmapped_cli=0`, `unmapped_config=0`, `unmapped_observability=0`, `parity_test_linkage_gaps=0`)
- `PYTHONPATH=src .\.venv\Scripts\python.exe project/scripts/verify_governance.py --check all` -> **FAIL** (LOC blockers only; other subchecks pass)
- `PYTHONPATH=src .\.venv\Scripts\python.exe -m pytest -q tests/characterization/safety_contract/test_safety_contract_pipeline.py -k "backdrop or dryrun"` -> **2 passed**
- `PYTHONPATH=src .\.venv\Scripts\python.exe -m pytest -q tests/test_pipeline.py -k "normalize_item_backdrops_api or process_single_item_backdrop"` -> **11 passed, 13 deselected**
- `PYTHONPATH=src .\.venv\Scripts\python.exe -m pytest -q tests/characterization/safety_contract/test_safety_contract_restore.py tests/test_backup.py -k "backdrop or restore"` -> **29 passed, 24 deselected**

Additional full verification-contract run (for thoroughness):
- `PYTHONPATH=src .\.venv\Scripts\python.exe -m pytest` -> **FAIL** (`9 failed, 282 passed, 3 warnings`)
- `.\.venv\Scripts\python.exe -m ruff check .` -> **PASS**
- `.\.venv\Scripts\python.exe -m ruff format --check .` -> **PASS** (`57 files already formatted`)
- `.\.venv\Scripts\python.exe -m mypy src` -> **PASS**
- `.\.venv\Scripts\python.exe -m bandit -r src` -> **PASS**
- `.\.venv\Scripts\python.exe -m pip_audit` -> **PASS** (local `jfin` skipped as non-PyPI)

### 3.2 Key Artifacts Inspected

- Migration blueprint: `project/v1-plan.md` (`248`, `275`, `467`, `507`)
- Runtime behavior notes: `docs/TECHNICAL_NOTES.md` (`94`, `103-108`, `173-174`, `179`)
- Backdrop runtime flow: `src/jfin/pipeline.py` (`412`, `485`, `571`, `581`, `591`, `611`, `631`, `652`)
- Restore contiguous backdrop semantics: `src/jfin/backup.py` (`310`, `320-323`, `355-360`, `365`, `390-392`)
- Parity ownership: `project/parity-matrix.md` (`22`, `38`, `43`, `44`)
- Safety baseline: `tests/characterization/baselines/safety_contract_baseline.json` (`48`, `65-87`, `88-121`)
- Safety characterization tests: `tests/characterization/safety_contract/test_safety_contract_pipeline.py` (`154-159`, `229-245`)
- Unit-depth backdrop tests: `tests/test_pipeline.py` (`481-488`, `689-713`, `704`, `734`, `793`)
- Route-fence artifacts: `project/route-fence.md` (`8-15`), `project/route-fence.json` (`rows[].parity_status`)
- Route-fence runtime enforcement: `src/jfin/cli.py` (`492`, `531`, `593`, `612`, `655`), `src/jfin/route_fence.py` (`14-23`)
- Governance enforcement logic: `project/scripts/parity_checks.py` (`125`, `144`, `158`, `193`, `241`, `282`, `307`)
- Characterization schema depth constraints: `project/scripts/characterization_contract.py` (`267-293`, `308-358`)

## 4) Compliance Checklist

- Verification contract & CI jobs: **PASS (artifact checks)**  
  Evidence: `verify_governance --check ci-sync` passed; CI contains required jobs/commands and governance entrypoint.
- Governance checks (`--check parity`, `--check characterization`): **PASS**
- Governance aggregate (`--check all`): **FAIL (LOC-only)**
- LOC policy (`src_max_lines:300 block`, `tests_max_lines:300 warn`): **FAIL (known baseline blockers remain)**
- Parity matrix schema/linkage: **PASS**
- Characterization/golden governance linkage: **PASS**
- Route-fence discipline (all routes still `v0`, runtime fail-closed): **PASS with caveat**
  Caveat: readiness semantics for `parity_status` are not validated beyond schema/sync.
- Slice-plan discipline (`one objective`, `<10 min verification`, rollback): **PARTIAL / NOT DIRECTLY APPLICABLE**  
  Reason: audited target is whole branch + working tree, not a single slice PR.

## 5) Backdrop Order-of-Operations Capture Verdict

Verdict: **Partially captured**.

The core backdrop flow is implemented and strongly covered by unit tests, but parity-owned characterization (`PIPE-BACKDROP-001`) captures only a subset (delete-before-upload + staging retention). This leaves high-value sequencing checks outside parity ownership.

### Backdrop Invariant Matrix

| Invariant | Plan/Docs | Runtime | Parity-owned characterization | Additional tests | Coverage state |
| --- | --- | --- | --- | --- | --- |
| Fetch all indices `0..n-1` | `docs/TECHNICAL_NOTES.md:104` | `src/jfin/pipeline.py:412`, `:427` | No explicit index-sequence assertion in `PIPE-BACKDROP-001` (`test_safety_contract_pipeline.py:229-245`) | Explicitly asserted (`tests/test_pipeline.py:484`, `:677-682`) | **Documented + tested, parity-owned assertion weak** |
| Normalize by source index | `docs/TECHNICAL_NOTES.md:105` | `src/jfin/pipeline.py:490-542` | Not asserted as source-index mapping in baseline/test | Explicitly asserted (`tests/test_pipeline.py:485`, `:684-687`) | **Documented + tested, parity-owned assertion weak** |
| Delete originals via repeated index `0` | `docs/TECHNICAL_NOTES.md:106` | `src/jfin/pipeline.py:581` | Count asserted, index semantics not asserted (`safety_contract_baseline.json:72-74`) | Index semantics asserted (`tests/test_pipeline.py:689-702`) | **Documented + tested, parity-owned assertion weak** |
| 404 verification before upload | `docs/TECHNICAL_NOTES.md:106` | `src/jfin/pipeline.py:591-603` | Not asserted in `PIPE-BACKDROP-001` baseline/test | Asserted (`tests/test_pipeline.py:704-707`) | **Tested but not parity-owned** |
| Re-upload dense `0..n-1` preserving order | `docs/TECHNICAL_NOTES.md:107` | `src/jfin/pipeline.py:621-631` | Upload count and delete-before-upload asserted, dense index/order not asserted | Explicit dense/order assertions (`tests/test_pipeline.py:709-721`, `:725-731`) | **Documented + tested, parity-owned assertion weak** |
| Staging retained on partial upload failure | `docs/TECHNICAL_NOTES.md:108` | `src/jfin/pipeline.py:655-657` | Explicitly asserted (`safety_contract_baseline.json:80`, `test_safety_contract_pipeline.py:239`) | Also covered (`tests/test_pipeline.py:793-868`) | **Documented + tested + parity-owned** |
| Dry-run non-destructive behavior | `project/v1-plan.md:467`, `docs/TECHNICAL_NOTES.md:134` | `src/jfin/pipeline.py:572-619` + adapter gate | Covered by `PIPE-DRYRUN-001` and `API-DRYRUN-001` (`parity-matrix.md:22`, `:36`) | Unit dry-run backdrop test (`tests/test_pipeline.py:734`) | **Documented + tested + parity-owned** |
| Restore contiguous-index semantics | `project/v1-plan.md:467`, `src/jfin/backup.py:320-323` | `src/jfin/backup.py:348-375` | Covered by `RST-BULK-001`/`RST-SINGLE-001` (`parity-matrix.md:43-44`) | Additional restore tests in `tests/test_backup.py` | **Documented + tested + parity-owned** |

## 6) Findings (Detailed)

### UU-001
- Severity: **Blocker**
- Condition: Full verification-contract command `PYTHONPATH=src .\.venv\Scripts\python.exe -m pytest` fails with 9 failures.
- Criteria: `project/verification-contract.yml` requires full pytest pass.
- Evidence:
  - Command result: `9 failed, 282 passed, 3 warnings`.
  - Failures include:
    - `tests/characterization/cli_contract/test_cli_contract_characterization.py` (6 failures)
    - `tests/characterization/safety_contract/test_safety_contract_api.py` (2 failures)
    - `tests/characterization/safety_contract/test_safety_contract_restore.py::test_rst_refuse_001_characterization` (1 failure)
- Impact: Contract-level test gate is not green; branch cannot be represented as fully verification-compliant.
- Recommended remediation:
  - Fix message-capture/expectation drift in characterization harness/tests.
  - Re-run full verification contract command set end-to-end.
  - Skill: `verification-gates-and-diff-discipline`.

### UU-002
- Severity: **Blocker**
- Condition: `verify_governance.py --check all` fails LOC blocker for `src/` files.
- Criteria: `project/verification-contract.yml` `src_max_lines: 300` with `src_mode: block`.
- Evidence:
  - Errors for `src/jfin/backup.py`, `cli.py`, `client.py`, `config.py`, `imaging.py`, `pipeline.py`.
- Impact: Track-1 hard LOC governance gate remains noncompliant.
- Recommended remediation:
  - Execute ratcheted decomposition slices focused on one module per objective.
  - Preserve behavior via existing characterization + parity before each split.
  - Skill: `loc-and-complexity-discipline`, `safe-refactor-python-modules`.

### UU-003
- Severity: **High**
- Condition: `PIPE-BACKDROP-001` parity ownership does not assert several critical backdrop transaction invariants (404 verification, dense upload index mapping, source-index mapping).
- Criteria:
  - `project/v1-plan.md:467` requires backdrop transaction parity over stage/normalize/delete/upload/finalize.
  - `project/v1-plan.md:248` treats backdrop transaction/recovery parity as gate.
- Evidence:
  - Parity owner row: `project/parity-matrix.md:38`.
  - Baseline payload emphasizes counts/order token/staging only: `safety_contract_baseline.json:65-87`.
  - Characterization observed assertions are limited to `delete_calls`, `upload_calls`, `staging_retained`, `delete_before_upload`: `test_safety_contract_pipeline.py:229-245`.
  - Stronger assertions exist only in non-parity-owned unit tests: `tests/test_pipeline.py:481-731`.
- Impact: Regression in critical sequencing behavior could evade parity governance while still passing owner characterization.
- Recommended remediation:
  - Expand `PIPE-BACKDROP-*` characterization to include explicit sequence/index/404 assertions.
  - Optionally split into additional behavior IDs for better ownership granularity.
  - Skill: `verification-gates-and-diff-discipline`.

### UU-004
- Severity: **Medium**
- Condition: Route-fence readiness metadata (`parity_status`) is validated only for schema/sync, not semantic readiness linkage to parity evidence.
- Criteria: Track-1 strangler discipline expects route flips only when parity is demonstrably green (`project/v1-plan.md:275`).
- Evidence:
  - All rows remain `pending`: `project/route-fence.md:8-15`, `project/route-fence.json` rows.
  - Governance checks validate field presence/sync but not readiness semantics: `project/scripts/parity_checks.py:125`, `:241`, `:282`.
- Impact: Future flip decisions can rely on manually maintained metadata without machine-checked parity linkage.
- Recommended remediation:
  - Add route-row-to-parity-ID readiness policy check in governance scripts.
  - Skill: `verification-gates-and-diff-discipline`.

### UU-005
- Severity: **Medium**
- Condition: Blueprint characterization suite paths drift from current canonical safety-contract layout.
- Criteria: Governance docs should remain contract-accurate and non-contradictory.
- Evidence:
  - Blueprint lists `workflows`, `restore_contract`, `observability`: `project/v1-plan.md:309-311`.
  - Canonical notes point to `safety_contract` and explain restore alias as migration note: `docs/TECHNICAL_NOTES.md:173-174`, `:179`.
- Impact: Auditors/implementers can target wrong contract locations or mis-scope future parity ownership.
- Recommended remediation:
  - Normalize path terminology in `project/v1-plan.md` to current canonical contract layout.
  - Skill: `docs-self-healing-update-loop`.

### UU-006
- Severity: **Low**
- Condition: Safety baseline schema supports scalar maps + tokenized `ordering` only; this constrains expression of richer call-trace invariants.
- Criteria: Unknown-unknown reduction favors explicit and granular invariant capture for safety-critical flows.
- Evidence:
  - Scalar mapping restrictions: `project/scripts/characterization_contract.py:267-293`.
  - Safety `ordering` modeled as `list[str]` tokens: `project/scripts/characterization_contract.py:351-358`.
- Impact: Some deep sequencing semantics may be represented indirectly or moved to non-parity unit tests.
- Recommended remediation:
  - Either enrich schema for structured call traces or codify a policy requiring parity rows to reference both characterization and critical unit tests for complex transactions.
  - Skill: `verification-gates-and-diff-discipline`.

## 7) Unknown-Unknown Register (Residual)

| Risk ID | Residual unknown | Current containment | Residual risk |
| --- | --- | --- | --- |
| UUR-001 | 404 verification step could regress without parity-owner failure | Covered in unit tests, not in parity-owner characterization | Medium |
| UUR-002 | Backdrop dense re-upload ordering/index mapping drift | Strong unit tests; weak parity-owner assertions | Medium |
| UUR-003 | Route-fence readiness metadata may diverge from true parity readiness | Schema/sync checks only | Medium |
| UUR-004 | Baseline message-capture behavior drift affects characterization reliability | Full pytest currently exposes failures | High until fixed |

## 8) Prioritized Remediation Plan

1. Restore contract green baseline:
   - Fix 9 failing characterization tests (`CLI-*`, `API-DRYRUN-*`, `RST-REFUSE-001` message assertions).
   - Re-run: `PYTHONPATH=src .\.venv\Scripts\python.exe -m pytest`.
2. Close backdrop parity-depth gap:
   - Expand `PIPE-BACKDROP-*` baseline/test coverage for index mapping + 404 verification + dense ordering.
   - Re-run:
     - `PYTHONPATH=src .\.venv\Scripts\python.exe -m pytest -q tests/characterization/safety_contract/test_safety_contract_pipeline.py -k "backdrop"`
     - `PYTHONPATH=src .\.venv\Scripts\python.exe project/scripts/verify_governance.py --check characterization`
3. Add route-fence semantic readiness guard:
   - Extend governance check logic to validate route readiness metadata against parity evidence.
   - Re-run:
     - `PYTHONPATH=src .\.venv\Scripts\python.exe project/scripts/verify_governance.py --check parity`
4. Resolve doc topology drift:
   - Align `project/v1-plan.md` characterization paths with current canonical contracts.
   - Re-run:
     - `PYTHONPATH=src .\.venv\Scripts\python.exe project/scripts/verify_governance.py --check characterization`
5. Continue LOC ratchet decomposition:
   - Split oversized `src/jfin/*` modules slice-by-slice with parity safeguards.
   - Re-run:
     - `PYTHONPATH=src .\.venv\Scripts\python.exe project/scripts/verify_governance.py --check all`

## 9) Audit Limitations

1. This audit is static/unit/governance based; no live Jellyfin API integration run was executed.
2. Branch-wide scope (not a single slice PR) makes slice-policy checks (`one objective`, `<10 min`) informational rather than strict pass/fail.
3. Baseline includes known historical governance debt (LOC blockers); this report separates those from newly identified unknown-unknown risks.

## 10) Final Attestation

The current v1 migration state is **not fully verification-contract compliant** (full pytest failures + LOC blockers), but governance artifact integrity for parity/characterization/route-fence sync is currently intact.  
Backdrop order-of-operations behavior is implemented and well unit-tested, yet **only partially captured by parity-owned characterization**, which is the primary unknown-unknown risk to close before route-flip work.

