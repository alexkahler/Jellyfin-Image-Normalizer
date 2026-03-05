# WI-003 Slice 4 Plan (Final Revision): Imaging Characterization + Goldens

## Summary
This plan locks WI-003 to the imaging boundary while preserving existing Track 1 parity IDs and governance posture.

As of **March 4, 2026**, `python project/scripts/verify_governance.py --check all` is run as a recorded gate signal, with known pre-existing `loc` failures in `src/jfin/*`. WI-003 must not introduce any new check failures.

## Decisions Locked
1. Corpus is **hybrid**: synthetic backbone + tiny self-made "real-ish" fixtures.
2. WI-003 seam is **imaging-only**:
- Allowed: `jfin.imaging` logic and `RunStats` mutation inside imaging helpers.
- Forbidden: `jfin.pipeline` and `jfin.client` ownership/assertions.
3. `IMG-*` parity anchors remain the existing five IDs.
4. Imaging baseline schema will **not** include `expected_exit_code`.
5. Tolerant golden comparison uses one primary metric:
- Primary: `max_mean_abs_error` (MAE) on decoded pixels.
- Secondary: optional `max_diff_pixels` only as an outlier guard.
6. Fixture policy:
- CC0/self-made only.
- No recognizable movie/TV promotional art.
- Provenance required.

## Repo Map Snippet
- Runtime: `src/jfin/imaging.py`, `src/jfin/pipeline.py`, `src/jfin/client.py`
- Existing IMG owners: `tests/test_imaging.py`
- Characterization harness root: `tests/characterization/`
- Governance scripts: `project/scripts/characterization_contract.py`, `project/scripts/characterization_checks.py`, `project/scripts/governance_checks.py`
- Parity artifact: `project/parity-matrix.md`

## Public Interfaces / Contract Additions
1. Add `tests/characterization/baselines/imaging_contract_baseline.json`
2. Add `tests/golden/imaging/manifest.json`
3. Add `tests/golden/imaging/expected/*`
4. Add `tests/golden/imaging/fixtures/realish/*`
5. Add `tests/golden/imaging/fixtures/PROVENANCE.md`
6. Extend characterization governance contract with IMG constants in `project/scripts/characterization_contract.py`:
- `IMG_BEHAVIOR_IDS`
- required imaging baseline file path
- required golden manifest path
- budget limits for `expected/*` and `fixtures/realish/*`

## Imaging Baseline Schema (Primary Parity Anchor)
Each `IMG-*` case entry includes:
- `expected_properties` (required):
  - `decision`
  - `size`
  - `mode`
  - `format`
  - `content_type`
- `golden_key` (required)
- `notes` (optional)

No exit-code field.

Parity mapping rule:
- `baseline_source` in `project/parity-matrix.md` points to `imaging_contract_baseline.json#IMG-...`
- baseline `golden_key` points into `manifest.json`
- manifest entry points to expected file path

## Golden Manifest Rules
1. Global metadata required:
- `python_version`
- `pillow_version`
- `generated_at`
2. Per-case required:
- `expected_path`
- `compare_mode` (`exact` or `tolerant`)
3. Tolerant mode defaults:
- `max_mean_abs_error` required, default target 2.0
- `max_diff_pixels` optional secondary guard
4. Per-case tolerance overrides require a justification note in manifest.

## Staged Plan

1. **Milestone 1: Parity seam audit and WI lock**
- Files: `plans/WI-003.md`
- Actions:
  - audit each current `IMG-*` behavior against imaging-only ownership
  - record seam contract and exceptions policy
- Verification:
  - `rg -n "IMG-SCALE-001|IMG-NOSCALE-001|IMG-LOGO-001|IMG-CROP-001|IMG-ENCODE-001" project/parity-matrix.md`
  - `rg -n "jfin\\.pipeline|jfin\\.client" tests/test_imaging.py`
- Exit criteria:
  - all five IDs explicitly mapped to imaging-owned assertions
  - no parity-ID meaning rewrite required

2. **Milestone 2: Add hybrid corpus + baseline + golden artifacts**
- Files:
  - `tests/characterization/baselines/imaging_contract_baseline.json`
  - `tests/golden/imaging/manifest.json`
  - `tests/golden/imaging/expected/*`
  - `tests/golden/imaging/fixtures/realish/*`
  - `tests/golden/imaging/fixtures/PROVENANCE.md`
- Actions:
  - add synthetic canonical cases
  - add 2-4 self-made real-ish fixtures
- Verification:
  - path/link resolution checks
  - artifact budget checks
- Exit criteria:
  - all `IMG-*` mapped with valid `golden_key`
  - provenance rules documented and satisfied

3. **Milestone 3: Add imaging characterization tests**
- Files:
  - `tests/characterization/imaging_contract/test_imaging_contract_characterization.py`
  - `tests/characterization/imaging_contract/_harness.py`
  - optional harness unit tests
- Actions:
  - assert transform properties and golden comparisons only
  - no pipeline/client assertions
- Verification:
  - `$env:PYTHONPATH='src'; python -m pytest -q tests/characterization/imaging_contract`
  - `rg -n "jfin\\.pipeline|jfin\\.client" tests/characterization/imaging_contract`
- Exit criteria:
  - all IMG cases green with seam contract enforced

4. **Milestone 4: Extend governance characterization checks**
- Files:
  - `project/scripts/characterization_contract.py`
  - `project/scripts/characterization_checks.py`
  - `tests/test_characterization_checks.py`
  - `tests/test_characterization_checks_links.py`
  - `tests/test_characterization_checks_imaging.py`
- Actions:
  - validate IMG baseline schema
  - validate parity anchor linkage
  - validate manifest key + expected file existence
  - enforce separate budgets:
    - `expected/*`: max 16 files, max 2 MiB
    - `fixtures/realish/*`: max 4 files, max 512 KiB
- Verification:
  - `$env:PYTHONPATH='src'; python -m pytest -q tests/test_characterization_checks.py tests/test_characterization_checks_links.py tests/test_characterization_checks_imaging.py`
  - `python project/scripts/verify_governance.py --check characterization`
  - `python project/scripts/verify_governance.py --check parity`
- Exit criteria:
  - positive and negative governance cases pass

5. **Milestone 5: Parity/docs/governance wording alignment**
- Files:
  - `project/parity-matrix.md`
  - `README.md`
  - `docs/TECHNICAL_NOTES.md`
  - `plans/WI-003.md`
- Actions:
  - re-point IMG rows to imaging baseline anchors and characterization owner tests
  - document WI-003 commands and artifact layout
  - document governance wording: `--check all` run with known pre-existing LOC failures; no new failures allowed
- Verification:
  - `rg -n "IMG-SCALE-001|IMG-NOSCALE-001|IMG-LOGO-001|IMG-CROP-001|IMG-ENCODE-001" project/parity-matrix.md`
  - `rg -n "imaging_contract|tests/golden/imaging|--check all|known pre-existing LOC" README.md docs/TECHNICAL_NOTES.md plans/WI-003.md`
- Exit criteria:
  - docs and artifacts are internally consistent

## Test Cases and Scenarios
1. `IMG-SCALE-001`: scale decision + dimensions.
2. `IMG-NOSCALE-001`: imaging helper no-scale behavior with uploader bypass and local stats mutation only.
3. `IMG-LOGO-001`: transparent-border and padding behavior.
4. `IMG-CROP-001`: cover+crop geometry and center behavior.
5. `IMG-ENCODE-001`: encoded format/content-type + decode validity.
6. Tolerant lossy comparisons use MAE as primary metric.
7. Governance negatives:
- missing IMG baseline file/case
- bad parity anchor
- missing `golden_key`
- missing manifest entry
- missing expected file
- expected budget overflow
- fixture budget overflow

## Acceptance Criteria
1. All five `IMG-*` rows are owned by imaging characterization tests with baseline anchors in imaging baseline JSON.
2. Imaging baseline schema excludes exit semantics and contains transform/golden linkage only.
3. No WI-003 imaging characterization test imports `jfin.pipeline` or `jfin.client`.
4. `--check characterization` validates IMG linkage and budget rules.
5. `--check parity` and imaging characterization tests pass.
6. `--check all` is run and recorded; no new failures beyond known pre-existing LOC failures.

## Risk Register (Top 5)
1. `IMG-NOSCALE-001` seam ambiguity.
- Mitigation: explicit seam contract allows imaging-helper-local stats only; forbids pipeline/client ownership.

2. Golden nondeterminism across environments.
- Mitigation: MAE-based tolerant comparison + manifest version metadata.

3. Fixture legal/compliance drift.
- Mitigation: provenance file + no recognizable media art rule.

4. Golden/fixture sprawl.
- Mitigation: enforced separate budgets in governance checks.

5. Parity baseline-source ambiguity.
- Mitigation: parity anchor fixed to imaging baseline JSON; manifest only secondary via `golden_key`.

## Rollback Plan
1. Revert WI-003 commits in reverse dependency order:
- docs/parity/WI doc
- governance checks/tests
- characterization tests/harness
- baseline/golden/fixture artifacts
2. Re-run:
- `python project/scripts/verify_governance.py --check characterization`
- `python project/scripts/verify_governance.py --check parity`
3. Confirm no runtime code change in `src/jfin/*`.

## Assumptions and Defaults
1. Slice 4 remains WI-003 per `WORK_ITEMS.md`.
2. No parity-ID semantic redefinition is performed in WI-003.
3. Default tolerant threshold is MAE 2.0 unless justified per-case.
4. Known LOC failures in `src/jfin/*` are pre-existing and tracked as baseline debt; WI-003 adds no new governance failures.
