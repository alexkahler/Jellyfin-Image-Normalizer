# Slice 26 Plan (v3 FINAL)

## Slice Id and Title
- Slice id: `Slice-26`
- Slice title: `Anti-evasion governance codification + honest LOC rebaseline (A-08 remains open)`

## Objective
- Codify anti-evasion governance rules in Slice 26 now (`project/verification-contract.yml` + `verify_governance --check loc` enforcement + AGENTS mirror).
- Identify and document all current suppression/evasion findings.
- Remove suppression/evasion in-slice where safe and bounded; otherwise neutralize as invalid for LOC compliance and carry as explicit blockers.
- Produce honest LOC truth outputs and select the exact next slice after 26 by explicit rule.

## Non-Goals
- No A-08 / GG-008 closure claim in Slice 26.
- No false clean closure while suppression/evasion remains unresolved.
- No broad redesign beyond this governance + bounded remediation objective.

## Historical Status Alignment
- `Slice 25` is treated as superseded/noncompliant historical work because LOC-evasion tactics are now explicitly disallowed.
- `Slice 24` remains the historical A-08 evidence record; Slice 26 does not replace it.
- A-08 remains open regardless of Slice 26 outcome.

## Authoritative Inputs Used
- `project/v1-slices-reports/audits/track-1-theme-a-iteration-roadmap.md`
- `project/v1-plan.md`
- `AGENTS.md`
- `project/verification-contract.yml`
- `WORK_ITEMS.md`
- `project/v1-slices-reports/slice-24/slice-24-plan.md`
- `project/v1-slices-reports/slice-24/slice-24-audit.md`
- `project/v1-slices-reports/slice-24/a08-ci-evidence.json`

## Anti-Evasion Codification in Slice 26 (Required Now)
- Primary contract source: `project/verification-contract.yml`.
- Enforcement path: `project/scripts/verify_governance.py` (`--check loc`).
- Human mirror: `AGENTS.md` must reflect the codified rule.
- Rule posture:
  - `# fmt: off` / `# fmt: on` cannot be used to claim LOC compliance.
  - Multi-statement line packing cannot be used to claim LOC compliance.
  - Dense control-flow packing cannot be used to claim LOC compliance.
  - Fail-closed: if honest LOC cannot be established, Slice 26 is `blocked`.

## Known Current Suppression Presence (must be handled in Slice 26)
Current known baseline findings from required grep:
- `src/jfin/cli.py`
- `src/jfin/cli_runtime.py`
- `src/jfin/client.py`
- `src/jfin/client_http.py`
- `src/jfin/config.py`
- `src/jfin/config_core.py`
- `src/jfin/pipeline.py`
- `src/jfin/pipeline_backdrops.py`

Required handling in Slice 26 for each finding:
- path A (preferred): remove in-slice if safe, bounded, and verifiable within this slice.
- path B (allowed fallback): neutralize for LOC compliance (mark invalid for compliance accounting), document as blocker, and carry explicitly into Slice 27+ roadmap.

## Slice 26 Execution Sequence (implementation-ready)

### Step 1: Baseline evidence collection (run exact required minimum commands)
```powershell
git grep -n "# fmt: off\|# fmt: on" -- src tests .github
Get-ChildItem src -Recurse -Filter *.py | % { "{0}:{1}" -f $_.FullName, (Get-Content $_.FullName).Length }
\.venv\Scripts\python.exe project/scripts/verify_governance.py --check loc
\.venv\Scripts\python.exe project/scripts/verify_governance.py --check architecture
\.venv\Scripts\python.exe project/scripts/verify_governance.py --check all
\.venv\Scripts\python.exe -m ruff format --check .
git diff --numstat -- src
```

### Step 2: Codify anti-evasion governance rules in-slice
- Update `project/verification-contract.yml` with explicit anti-evasion contract fields.
- Update `project/scripts/verify_governance.py` LOC check behavior to enforce contract.
- Update `AGENTS.md` to mirror the codified rule (no contradiction with contract).

### Step 3: Re-run exact required minimum commands after codification
- Re-run the Step 1 command list verbatim and capture before/after evidence deltas.

### Step 4: Handle each suppression/evasion finding
- For each finding: choose `removed_in_slice` or `neutralized_as_blocker`.
- If any runtime `src/` file is edited while removing suppression/evasion, run narrowest targeted tests (next section).
- If safe removal is not possible, keep finding as explicit blocker and stop closure claims.

## Conditional Targeted Tests Rule (only when runtime `src/` files are edited)

Discovery rule:
- Determine touched runtime files: `git diff --name-only -- src/jfin/*.py`.
- Run the smallest matching set only:
  - `config/config_core`:
    - `\.venv\Scripts\python.exe -m pytest -q tests/test_config.py tests/characterization/config_contract/test_config_contract_characterization.py`
  - `client/client_http`:
    - `\.venv\Scripts\python.exe -m pytest -q tests/test_client.py tests/test_discovery.py tests/characterization/safety_contract/test_safety_contract_api.py`
  - `cli/cli_runtime`:
    - `\.venv\Scripts\python.exe -m pytest -q tests/test_jfin.py tests/characterization/cli_contract/test_cli_contract_characterization.py tests/test_route_fence_runtime.py`
  - `pipeline/pipeline_backdrops`:
    - `\.venv\Scripts\python.exe -m pytest -q tests/test_pipeline.py tests/characterization/safety_contract/test_safety_contract_pipeline.py`
  - `backup/backup_restore`:
    - `\.venv\Scripts\python.exe -m pytest -q tests/test_backup.py tests/characterization/safety_contract/test_safety_contract_restore.py`
- If no runtime files changed, skip targeted tests.

## Honest LOC Rebaseline Method (suppression invalid)
- Capture raw LOC per `src/**/*.py`.
- Build evasion inventory (`fmt` suppression, packed statements, dense control-flow packing).
- Compute honest LOC posture with evasion invalidated for compliance decisions.
- Any file compliant only under evasion is marked `noncompliant_true`.

## Required Concrete Outputs from Slice 26

1. `suppression_introduced_or_retained: yes|no`
2. `evasion_files` table:
   - columns: `file`, `evasion_type`, `finding_source`, `slice_26_action`, `current_status`
3. `true_noncompliant_files` table:
   - columns: `file`, `raw_loc`, `honest_loc`, `limit`, `status`
4. `next_slice_after_26: Slice-XX <title>`

### Explicit Question Answers (Required)
Answer these using exact mission wording and required format:

1. `whether suppression introduced/retained`
   - Format: `whether suppression introduced/retained: yes|no`
2. `which files rely on evasion`
   - Format: `which files rely on evasion: [comma-separated file list]`
3. `true noncompliant files after disallowing evasion`
   - Format: `true noncompliant files after disallowing evasion: [file=honest_loc, ...]`
4. `exact next slice after 26`
   - Format: `exact next slice after 26: Slice-XX <title>`

## Blocked vs Clean Closure Policy
- Mark Slice 26 `blocked` and stop if any of these hold:
  - anti-evasion codification is incomplete,
  - a suppression/evasion finding cannot be safely removed and is not explicitly neutralized as blocker,
  - required minimum commands fail,
  - outputs above are missing/incomplete.
- Blocked evidence must include:
  - command outputs from required minimum list,
  - `evasion_files` table,
  - `true_noncompliant_files` table,
  - explicit blocker carry-forward into Slice 27+ roadmap.
- Clean Slice 26 closure requires complete codification + complete outputs + explicit next-slice selection.
- A-08 remains open; no closure claim in this slice.

## Next-Slice Decision Rule (explicit default)
- Default next slice from this plan: `Slice 27 - Runtime evasion remediation tranche 1 (smallest blocker)`.
- Only choose a different next slice if Slice 26 outputs prove a smaller blocker group than the default target.
- Selection method: smallest blocker-first by `true_noncompliant_files` scope and verification blast radius.

## Ordered Slice 27+ Roadmap (after Slice 26 codification)

| Slice id / title | Objective | Target files | Why next | Expected verification command patterns | Evidence-only vs implementation | Split condition |
| --- | --- | --- | --- | --- | --- | --- |
| `Slice 27 - Runtime evasion remediation tranche 1 (smallest blocker)` | Remove/neutralize evasion in the smallest blocker group from Slice 26 outputs (default target: config pair) | Default: `src/jfin/config.py`, `src/jfin/config_core.py` unless Slice 26 outputs identify a smaller group | Fastest bounded progress after codification | Required minimum command list + targeted config test set + `git diff --numstat -- src` | Implementation | If >2 runtime files needed, split by file pair immediately |
| `Slice 28 - Runtime evasion remediation tranche 2` | Resolve next smallest blocker group | Expected next pair: `src/jfin/client.py`, `src/jfin/client_http.py` (or smaller proven group) | Continue low-to-medium coupling remediation | Required minimum command list + targeted client test set + `git diff --numstat -- src` | Implementation | If scope touches unrelated subsystem, split and stop |
| `Slice 29 - Runtime evasion remediation tranche 3` | Resolve CLI blocker group | `src/jfin/cli.py`, `src/jfin/cli_runtime.py` (if still flagged) | Entry-path cleanup after medium modules | Required minimum command list + targeted CLI test set + `git diff --numstat -- src` | Implementation | If pipeline behavior is pulled in, split CLI-only first |
| `Slice 30 - Runtime evasion remediation tranche 4` | Resolve pipeline blocker group in smallest safe order | `src/jfin/pipeline_backdrops.py`, `src/jfin/pipeline.py` (order by smaller overage first) | Highest-coupling group last | Required minimum command list + targeted pipeline test set + `git diff --numstat -- src` | Implementation | Split per file if LOC/time budget exceeded |
| `Slice 31 - Honest GG-001 revalidation` | Prove honest LOC posture under codified rules | Governance evidence artifacts + `WORK_ITEMS.md` sync (if needed) | Required checkpoint before any A-08 retry | Required minimum command list | Evidence-only | If any true noncompliance remains, mark blocked and open smallest remediation slice |
| `Slice 32 - Return to A-08 same-SHA proof` | Retry A-08 evidence gate only after honest GG-001 clean | `project/v1-slices-reports/slice-24/slice-24-audit.md`, `project/v1-slices-reports/slice-24/a08-ci-evidence.json`, `WORK_ITEMS.md` | Historical A-08 closure path resumes only after posture recovery | `git rev-parse HEAD`; `\.venv\Scripts\python.exe project/scripts/verify_governance.py --check all`; CI required-job evidence commands | Evidence-only | If any required CI job is not `success`, fail closed and open remediation |

## Assumptions / Open Gaps
- Dense control-flow packing detector thresholds may require a small follow-up refinement if false positives appear.
