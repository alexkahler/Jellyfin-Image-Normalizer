**Slice 6 Governance Audit Report (Delta-Only)**
Audit date: March 4, 2026  
Verdict: **Compliant with caveats**

**Direct Answers**
1. Gaps in implementation: **No blocking WI-005 implementation gaps found**.
2. Contradictions: **One documentation contradiction** (details in Findings #1).
3. Oversights: **One scope/documentation attribution oversight** (`project/v1-plan.md` delta handling).
4. Governance accidentally changed: **No accidental executable-governance change detected**; one governance-document delta exists.
5. Do changed files correspond to Slice 6 plan: **Yes, mostly**; one file is attribution-ambiguous (`project/v1-plan.md`).

**Section 2: Requirement Traceability**

| Requirement | Expected Artifact | Observed Evidence | Status |
|---|---|---|---|
| Add parity IDs `API-DRYRUN-002`, `RST-REFUSE-001`, `RST-PATH-001` | Parity contract + matrix rows | [`project/scripts/parity_contract.py:46`](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/project/scripts/parity_contract.py:46), [`project/scripts/parity_contract.py:68`](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/project/scripts/parity_contract.py:68), [`project/parity-matrix.md:23`](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/project/parity-matrix.md:23), [`project/parity-matrix.md:45`](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/project/parity-matrix.md:45) | Pass |
| Add safety baseline | `safety_contract_baseline.json` with WI-005 cases | [`tests/characterization/baselines/safety_contract_baseline.json:19`](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/tests/characterization/baselines/safety_contract_baseline.json:19), [`...:122`](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/tests/characterization/baselines/safety_contract_baseline.json:122), [`...:138`](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/tests/characterization/baselines/safety_contract_baseline.json:138) | Pass |
| Add safety characterization harness/tests | `_harness.py` + API/Pipeline/Restore tests | [`tests/characterization/safety_contract/_harness.py:13`](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/tests/characterization/safety_contract/_harness.py:13), [`test_safety_contract_api.py:61`](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/tests/characterization/safety_contract/test_safety_contract_api.py:61), [`test_safety_contract_pipeline.py:53`](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/tests/characterization/safety_contract/test_safety_contract_pipeline.py:53), [`test_safety_contract_restore.py:102`](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/tests/characterization/safety_contract/test_safety_contract_restore.py:102) | Pass |
| Extend governance schema/link checks | Safety IDs + safety schema validation + required baseline linkage | [`project/scripts/characterization_contract.py:34`](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/project/scripts/characterization_contract.py:34), [`...:67`](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/project/scripts/characterization_contract.py:67), [`...:296`](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/project/scripts/characterization_contract.py:296), [`project/scripts/characterization_checks.py:32`](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/project/scripts/characterization_checks.py:32) | Pass |
| Re-link safety parity rows to characterization owners | API/PIPE/RST rows point to safety baseline + safety tests | [`project/parity-matrix.md:22`](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/project/parity-matrix.md:22), [`...:36`](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/project/parity-matrix.md:36), [`...:43`](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/project/parity-matrix.md:43) | Pass |
| Governance check path enforces WI-005 | `--check characterization` catches safety drift | [`tests/test_characterization_checks_safety.py:18`](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/tests/test_characterization_checks_safety.py:18), [`...:40`](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/tests/test_characterization_checks_safety.py:40), [`...:91`](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/tests/test_characterization_checks_safety.py:91) | Pass |
| Seeded unit tests remain guardrails | Existing seeded tests still present and pass in targeted runs | [`tests/test_client.py:128`](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/tests/test_client.py:128), [`tests/test_pipeline.py:134`](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/tests/test_pipeline.py:134), [`tests/test_backup.py:340`](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/tests/test_backup.py:340) | Pass |
| Out-of-scope runtime refactor avoidance | No `src/jfin/*` delta | `git diff --name-only -- src/jfin` returned empty | Pass |

**Section 3: Findings (Ordered by Severity)**
1. **Medium**: Attribution contradiction around `project/v1-plan.md`.  
Evidence: WI-005-related additions appear in [`project/v1-plan.md:388`](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/project/v1-plan.md:388) and [`project/v1-plan.md:536`](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/project/v1-plan.md:536), while report text says pre-existing unrelated modification was left untouched at [`slice-6-work-report.md:45`](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/project/v1-slices-reports/slice-6/slice-6-work-report.md:45).  
Impact: governance-document scope/accounting ambiguity.
2. **Low**: `--check all` is not green in current tree due pre-existing LOC gate failures in oversized `src/jfin/*` modules (not Slice 6 deltas).  
Impact: repository-wide governance gate remains failing, but this is pre-existing under delta-only scoring.

**Section 4: Changed-File Conformance**

| File | Classification | Result |
|---|---|---|
| `project/parity-matrix.md` | Entailed | In-scope WI-005 parity relink/ID coverage |
| `project/scripts/parity_contract.py` | Entailed | In-scope required behavior IDs update |
| `project/scripts/characterization_contract.py` | Entailed | In-scope safety schema + baseline contract |
| `project/scripts/characterization_checks.py` | Entailed | In-scope characterization governance extension |
| `tests/characterization/baselines/safety_contract_baseline.json` | Entailed | Required new baseline artifact |
| `tests/characterization/safety_contract/_harness.py` | Entailed | Required harness |
| `tests/characterization/safety_contract/test_safety_contract_api.py` | Entailed | Required owner test |
| `tests/characterization/safety_contract/test_safety_contract_pipeline.py` | Entailed | Required owner test |
| `tests/characterization/safety_contract/test_safety_contract_restore.py` | Entailed | Required owner test |
| `tests/_characterization_test_helpers.py` | Entailed | Governance scaffolding support |
| `tests/test_characterization_checks.py` | Entailed | Governance scaffolding support |
| `tests/test_characterization_checks_safety.py` | Entailed | Required safety governance tests |
| `plans/WI-005.md` | Supporting | WI documentation alignment |
| `project/v1-slices-reports/slice-6/slice-6-plan.md` | Supporting | Slice planning artifact |
| `project/v1-slices-reports/slice-6/slice-6-work-report.md` | Supporting | Slice reporting artifact |
| `README.md` | Supporting | Docs sync |
| `docs/TECHNICAL_NOTES.md` | Supporting | Docs sync |
| `project/v1-plan.md` | **Extra / attribution needed** | Governance-document delta not explicitly scoped in Slice 6 in-scope list |

**Section 5: Verification Command Ledger**

| Command | Observed Result | Classification |
|---|---|---|
| `PYTHONPATH=src python -m pytest -q tests/characterization/safety_contract` | `7 passed, 2 skipped` | Pass (env caveat only) |
| `PYTHONPATH=src python -m pytest -q tests/test_characterization_checks.py tests/test_characterization_checks_links.py tests/test_characterization_checks_imaging.py tests/test_characterization_checks_safety.py` | `19 passed` | Pass |
| `PYTHONPATH=src python -m pytest -q tests/test_client.py -k "dry_run or delete_image or set_user_profile_image"` | `8 passed, 8 deselected` | Pass |
| `PYTHONPATH=src python -m pytest -q tests/test_backup.py -k "restore or dry_run"` | `20 passed, 29 deselected` | Pass |
| `python project/scripts/verify_governance.py --check characterization` | `[PASS] characterization` | Pass |
| `python project/scripts/verify_governance.py --check parity` | `[PASS] parity` | Pass |
| `python project/scripts/verify_governance.py --check all` | Fails on LOC gate (`src/jfin/*` > 300 LOC) | **Pre-existing failure** (not Slice 6 delta) |

**Section 6: Pre-Existing Issues Ledger (Delta-Only Separation)**
1. Local interpreter is Python 3.10.10; pipeline safety tests include skip guards for missing `tomllib` on <3.11.
2. `verify_governance --check all` fails due pre-existing LOC gate violations in `src/jfin/*` and existing oversized test warnings.
3. These do not indicate a Slice 6 behavior-regression delta in current evidence.

No repository files were modified during this audit.