# Slice 26 Implementation (Worker 2)

## Scope
- Branch: `v1/thm-a-governance-contract-posture-recovery`
- Plan executed: `project/v1-slices-reports/slice-26/slice-26-plan.md` (v3 FINAL)
- Owned artifacts touched:
  - `project/verification-contract.yml`
  - `AGENTS.md`
  - `project/v1-slices-reports/slice-26/slice-26-implementation.md` (this file)
- Audit artifact intentionally not edited: `slice-26-audit.md`

## Anti-Evasion Governance Codification Update
### Contract codification (`project/verification-contract.yml`)
Added explicit anti-evasion rule text under `loc_policy` with rationale and noncompliance posture:
- `anti_evasion_rationale: honest_loc_required_for_maintainability`
- `anti_evasion_noncompliance_rule: suppression_or_packing_invalidates_loc_claim`

Existing anti-evasion keys retained as contract values:
- `anti_evasion_disallow_fmt: true`
- `anti_evasion_disallow_multi_statement: true`
- `anti_evasion_disallow_dense_control_flow: true`
- `anti_evasion_fail_closed: true`
- `anti_evasion_multi_statement_max_semicolons: 0`
- `anti_evasion_control_flow_inline_suite_max: 0`

### Human mirror codification (`AGENTS.md`)
Added explicit anti-evasion governance text in `LOC and Complexity Guardrails`:
- `# fmt: off/# fmt: on` cannot be used for LOC compliance claims.
- Semicolon packing and dense inline control-flow packing cannot be used for LOC compliance claims.
- Fail-closed posture if honest LOC cannot be established.
- Rationale: LOC maintainability limits are only meaningful with honest, formatter-compatible structure.

## Required Command Evidence
All required commands were run before and after codification; results were unchanged.

### 1) `git grep -n "# fmt: off\|# fmt: on" -- src tests .github`
Output:
```text
src/jfin/cli.py:2:# fmt: off
src/jfin/cli_runtime.py:1:# fmt: off
src/jfin/client.py:1:# fmt: off
src/jfin/client_http.py:1:# fmt: off
src/jfin/config.py:1:# fmt: off
src/jfin/config_core.py:1:# fmt: off
src/jfin/pipeline.py:1:# fmt: off
src/jfin/pipeline_backdrops.py:1:# fmt: off
```

### 2) `Get-ChildItem src -Recurse -Filter *.py | % { "{0}:{1}" -f $_.FullName, (Get-Content $_.FullName).Length }`
Output:
```text
C:\Users\akaehler\Proton Drive\alex.kahler\My files\Projects\Jellyfin Image Normalizer\src\jfin\backup.py:287
C:\Users\akaehler\Proton Drive\alex.kahler\My files\Projects\Jellyfin Image Normalizer\src\jfin\backup_restore.py:295
C:\Users\akaehler\Proton Drive\alex.kahler\My files\Projects\Jellyfin Image Normalizer\src\jfin\cli.py:289
C:\Users\akaehler\Proton Drive\alex.kahler\My files\Projects\Jellyfin Image Normalizer\src\jfin\client.py:291
C:\Users\akaehler\Proton Drive\alex.kahler\My files\Projects\Jellyfin Image Normalizer\src\jfin\client_http.py:221
C:\Users\akaehler\Proton Drive\alex.kahler\My files\Projects\Jellyfin Image Normalizer\src\jfin\cli_runtime.py:288
C:\Users\akaehler\Proton Drive\alex.kahler\My files\Projects\Jellyfin Image Normalizer\src\jfin\config.py:300
C:\Users\akaehler\Proton Drive\alex.kahler\My files\Projects\Jellyfin Image Normalizer\src\jfin\config_core.py:300
C:\Users\akaehler\Proton Drive\alex.kahler\My files\Projects\Jellyfin Image Normalizer\src\jfin\constants.py:247
C:\Users\akaehler\Proton Drive\alex.kahler\My files\Projects\Jellyfin Image Normalizer\src\jfin\discovery.py:266
C:\Users\akaehler\Proton Drive\alex.kahler\My files\Projects\Jellyfin Image Normalizer\src\jfin\imaging.py:194
C:\Users\akaehler\Proton Drive\alex.kahler\My files\Projects\Jellyfin Image Normalizer\src\jfin\imaging_ops.py:249
C:\Users\akaehler\Proton Drive\alex.kahler\My files\Projects\Jellyfin Image Normalizer\src\jfin\logging_utils.py:176
C:\Users\akaehler\Proton Drive\alex.kahler\My files\Projects\Jellyfin Image Normalizer\src\jfin\pipeline.py:285
C:\Users\akaehler\Proton Drive\alex.kahler\My files\Projects\Jellyfin Image Normalizer\src\jfin\pipeline_backdrops.py:300
C:\Users\akaehler\Proton Drive\alex.kahler\My files\Projects\Jellyfin Image Normalizer\src\jfin\pipeline_image_normalization.py:184
C:\Users\akaehler\Proton Drive\alex.kahler\My files\Projects\Jellyfin Image Normalizer\src\jfin\pipeline_image_payload.py:102
C:\Users\akaehler\Proton Drive\alex.kahler\My files\Projects\Jellyfin Image Normalizer\src\jfin\pipeline_orchestration.py:203
C:\Users\akaehler\Proton Drive\alex.kahler\My files\Projects\Jellyfin Image Normalizer\src\jfin\pipeline_profiles.py:240
C:\Users\akaehler\Proton Drive\alex.kahler\My files\Projects\Jellyfin Image Normalizer\src\jfin\route_fence.py:143
C:\Users\akaehler\Proton Drive\alex.kahler\My files\Projects\Jellyfin Image Normalizer\src\jfin\state.py:89
C:\Users\akaehler\Proton Drive\alex.kahler\My files\Projects\Jellyfin Image Normalizer\src\jfin\__init__.py:13
C:\Users\akaehler\Proton Drive\alex.kahler\My files\Projects\Jellyfin Image Normalizer\src\jfin\__main__.py:5
```

### 3) `.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check loc`
Concise result:
- `[PASS] loc`
- Warnings: 9 test files above `tests_max_lines` (warn-only policy)
- Final line: `Governance checks passed with 9 warning(s).`

### 4) `.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check architecture`
Concise result:
- `[PASS] architecture`
- Warning: `architecture: exit counter dropped below baseline for src/jfin/pipeline.py.system_exit_raises: observed 2, baseline 5. Update project/architecture-baseline.json to ratchet downward.`
- Final line: `Governance checks passed with 1 warning(s).`

### 5) `.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check all`
Concise result:
- All checks PASS: `schema`, `ci-sync`, `loc`, `python-version`, `architecture`, `parity`, `characterization`, `readiness`
- Warnings:
  - 9 LOC warnings for oversized test files (warn mode)
  - 1 architecture baseline warning (pipeline exit counter)
- Final line: `Governance checks passed with 10 warning(s).`

### 6) `.\.venv\Scripts\python.exe -m ruff format --check .`
Output:
```text
77 files already formatted
```

### 7) `git diff --numstat -- src`
Output:
```text
(no output)
```

## Honest LOC Rebaseline (Suppression Invalid)
### Method (defensible)
- Raw LOC source: required `Get-ChildItem ... Length` output above.
- Suppression inventory source: required `git grep` output above.
- Honest LOC computation for suppression files: temporary formatter probe.
  - For each suppression file, remove `# fmt: off/# fmt: on` in a temp copy.
  - Run `ruff format` on temp copy.
  - Count resulting lines as `honest_loc`.
- Compliance decision rule in this slice: anti-evasion fail-closed posture from contract + AGENTS mirror.

### Evasion files
| file | evasion_type | finding_source | slice_26_action | current_status |
| --- | --- | --- | --- | --- |
| `src/jfin/cli.py` | `fmt_suppression` | `git grep -n "# fmt: off\|# fmt: on" -- src tests .github` | `neutralized_as_blocker` | `retained_noncompliant` |
| `src/jfin/cli_runtime.py` | `fmt_suppression` | same command | `neutralized_as_blocker` | `retained_noncompliant` |
| `src/jfin/client.py` | `fmt_suppression` | same command | `neutralized_as_blocker` | `retained_noncompliant` |
| `src/jfin/client_http.py` | `fmt_suppression` | same command | `neutralized_as_blocker` | `retained_noncompliant` |
| `src/jfin/config.py` | `fmt_suppression` | same command | `neutralized_as_blocker` | `retained_noncompliant` |
| `src/jfin/config_core.py` | `fmt_suppression` | same command | `neutralized_as_blocker` | `retained_noncompliant` |
| `src/jfin/pipeline.py` | `fmt_suppression` | same command | `neutralized_as_blocker` | `retained_noncompliant` |
| `src/jfin/pipeline_backdrops.py` | `fmt_suppression` | same command | `neutralized_as_blocker` | `retained_noncompliant` |

### True noncompliant files (after disallowing evasion)
| file | raw_loc | honest_loc | limit | status |
| --- | ---: | ---: | ---: | --- |
| `src/jfin/cli.py` | 289 | 315 | 300 | `noncompliant_true` |
| `src/jfin/cli_runtime.py` | 288 | 449 | 300 | `noncompliant_true` |
| `src/jfin/client.py` | 291 | 382 | 300 | `noncompliant_true` |
| `src/jfin/client_http.py` | 221 | 317 | 300 | `noncompliant_true` |
| `src/jfin/config.py` | 300 | 301 | 300 | `noncompliant_true` |
| `src/jfin/config_core.py` | 300 | 319 | 300 | `noncompliant_true` |
| `src/jfin/pipeline.py` | 285 | 302 | 300 | `noncompliant_true` |
| `src/jfin/pipeline_backdrops.py` | 300 | 302 | 300 | `noncompliant_true` |

## Explicit Required Answers
whether suppression introduced/retained: yes
which files rely on evasion: [src/jfin/cli.py, src/jfin/cli_runtime.py, src/jfin/client.py, src/jfin/client_http.py, src/jfin/config.py, src/jfin/config_core.py, src/jfin/pipeline.py, src/jfin/pipeline_backdrops.py]
true noncompliant files after disallowing evasion: [src/jfin/cli.py=315, src/jfin/cli_runtime.py=449, src/jfin/client.py=382, src/jfin/client_http.py=317, src/jfin/config.py=301, src/jfin/config_core.py=319, src/jfin/pipeline.py=302, src/jfin/pipeline_backdrops.py=302]
exact next slice after 26: Slice-27 Anti-evasion enforcement parity in governance checks

## Slice 27+ Ordered Roadmap (small, context-stable)
1. Slice-27 Anti-evasion enforcement parity in governance checks
   - Scope: `project/scripts/governance_contract.py`, `project/scripts/governance_checks.py`, governance tests
   - Objective: parser/schema/`--check loc` anti-evasion fail-closed enforcement.
2. Slice-28 Runtime evasion remediation tranche 1 (smallest blocker)
   - Target default smallest coupled pair: `src/jfin/config.py`, `src/jfin/config_core.py`
   - Remove fmt suppression, hold honest LOC <=300, run required command set + targeted config tests.
3. Slice-29 Runtime evasion remediation tranche 2
   - Target next smallest blocker group: `src/jfin/client.py`, `src/jfin/client_http.py`
   - Same verification pattern + targeted client tests.
4. Slice-30 Runtime evasion remediation tranche 3
   - Target CLI group: `src/jfin/cli.py`, `src/jfin/cli_runtime.py`
   - Same verification pattern + targeted CLI tests.
5. Slice-31 Runtime evasion remediation tranche 4
   - Target pipeline group: `src/jfin/pipeline.py`, `src/jfin/pipeline_backdrops.py`
   - Same verification pattern + targeted pipeline tests.
6. Slice-32 Honest GG-001 revalidation
   - Re-run governance evidence under anti-evasion posture and confirm true LOC clean.
7. Slice-33 Return to A-08 same-SHA proof
   - Attempt A-08 proof only after honest LOC posture is clean.

## Slice 26 Outcome
- Cleanly closable for Slice 26 objective: **yes**.
- Rationale: anti-evasion contract codification + AGENTS mirror + required evidence + explicit blocker carry-forward are complete.
- A-08 closure: **not attempted** (remains open by plan).
