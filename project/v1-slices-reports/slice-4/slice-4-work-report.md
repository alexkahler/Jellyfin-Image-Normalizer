Implemented WI-003 Slice 4 end-to-end.

**What I changed**
- Added WI plan doc: [plans/WI-003.md](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/plans/WI-003.md)
- Added imaging baseline + golden artifacts:
  - [tests/characterization/baselines/imaging_contract_baseline.json](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/tests/characterization/baselines/imaging_contract_baseline.json)
  - [tests/golden/imaging/manifest.json](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/tests/golden/imaging/manifest.json)
  - [tests/golden/imaging/fixtures/PROVENANCE.md](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/tests/golden/imaging/fixtures/PROVENANCE.md)
  - Added expected outputs and real-ish fixtures under `tests/golden/imaging/expected/` and `tests/golden/imaging/fixtures/realish/`
- Added imaging characterization suite:
  - [tests/characterization/imaging_contract/test_imaging_contract_characterization.py](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/tests/characterization/imaging_contract/test_imaging_contract_characterization.py)
  - [tests/characterization/imaging_contract/_harness.py](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/tests/characterization/imaging_contract/_harness.py)
  - [tests/characterization/imaging_contract/test_imaging_harness.py](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/tests/characterization/imaging_contract/test_imaging_harness.py)
- Extended governance characterization contract/checks for `IMG-*`, manifest linkage, and separate budgets:
  - [project/scripts/characterization_contract.py](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/project/scripts/characterization_contract.py)
  - [project/scripts/characterization_checks.py](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/project/scripts/characterization_checks.py)
- Added imaging governance negatives:
  - [tests/test_characterization_checks_imaging.py](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/tests/test_characterization_checks_imaging.py)
  - [tests/_characterization_test_helpers.py](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/tests/_characterization_test_helpers.py)
  - Updated [tests/test_characterization_checks.py](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/tests/test_characterization_checks.py)
- Repointed parity IMG rows to imaging baseline + new owner tests:
  - [project/parity-matrix.md](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/project/parity-matrix.md)
- Updated docs with WI-003 commands/artifacts and `--check all` baseline note:
  - [README.md](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/README.md)
  - [docs/TECHNICAL_NOTES.md](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/docs/TECHNICAL_NOTES.md)

**Seam + policy checks implemented**
- Imaging baseline schema has no `expected_exit_code` (transform properties + `golden_key` only).
- No `jfin.pipeline`/`jfin.client` imports in imaging characterization tests (`rg` returned no matches).
- Provenance policy includes CC0/self-made and no recognizable movie/TV art.
- Tolerant golden comparisons use MAE as primary metric, optional `max_diff_pixels` secondary.
- Budget enforcement added for both:
  - `expected/*`: max 16 files, max 2 MiB
  - `fixtures/realish/*`: max 4 files, max 512 KiB
- Current artifact sizes: `expected` = 5 files / 1844 bytes, `fixtures/realish` = 2 files / 3490 bytes.

**Verification run**
- `python -m ruff check ...` on touched Python files: passed.
- `PYTHONPATH=src python -m pytest -q tests/characterization/imaging_contract`: `8 passed`.
- `PYTHONPATH=src python -m pytest -q tests/test_characterization_checks.py tests/test_characterization_checks_links.py tests/test_characterization_checks_imaging.py`: `12 passed`.
- `PYTHONPATH=src python -m pytest -q tests/characterization -k harness`: `10 passed, 18 deselected`.
- `python project/scripts/verify_governance.py --check characterization`: pass.
- `python project/scripts/verify_governance.py --check parity`: pass.
- `python project/scripts/verify_governance.py --check all`: fails on existing LOC gate only (`src/jfin/*`), same 6 blocking LOC errors and 6 warning-level oversized test files; no new blocking failures introduced by WI-003.

**LOC/complexity discipline**
- Approx net new LOC excluding tests/docs: `+389` (all in existing governance scripts).
- Avoided adding new governance CLI selectors or new runtime modules; reused existing `--check characterization`.
- Added only one small new helper module for tests ([tests/_characterization_test_helpers.py](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/tests/_characterization_test_helpers.py)) to keep `tests/test_characterization_checks.py` under the 300-line warning threshold.

---

Implemented the follow-up fixes you flagged.

1. Python metadata consistency fixed  
- Regenerated WI-003 imaging golden outputs with `py -3.13` and updated manifest metadata to match generation env (`3.13.12` / `12.1.1`) in [manifest.json](C:/Users/akaehler/Proton Drive/alex.kahler/My files/Projects/Jellyfin Image Normalizer/tests/golden/imaging/manifest.json:4).

2. Tolerance override enforcement tightened  
- Governance now requires `tolerance_note` whenever tolerant-mode overrides are used (`max_mean_abs_error != default` **or** `max_diff_pixels` is present) in [characterization_contract.py](C:/Users/akaehler/Proton Drive/alex.kahler/My files/Projects/Jellyfin Image Normalizer/project/scripts/characterization_contract.py:355) and [characterization_contract.py](C:/Users/akaehler/Proton Drive/alex.kahler/My files/Projects/Jellyfin Image Normalizer/project/scripts/characterization_contract.py:368).

3. Added IMG-specific negative coverage  
- Missing imaging baseline file: [test_characterization_checks_imaging.py](C:/Users/akaehler/Proton Drive/alex.kahler/My files/Projects/Jellyfin Image Normalizer/tests/test_characterization_checks_imaging.py:38)  
- Missing IMG behavior key: [test_characterization_checks_imaging.py](C:/Users/akaehler/Proton Drive/alex.kahler/My files/Projects/Jellyfin Image Normalizer/tests/test_characterization_checks_imaging.py:60)  
- Missing tolerance note for override: [test_characterization_checks_imaging.py](C:/Users/akaehler/Proton Drive/alex.kahler/My files/Projects/Jellyfin Image Normalizer/tests/test_characterization_checks_imaging.py:134)

Verification run
- `pytest` targeted WI-003 suites: `23 passed`
- `pytest -k harness` in characterization tree: `10 passed`
- `verify_governance --check characterization`: `PASS`
- `verify_governance --check parity`: `PASS`
- `verify_governance --check all`: unchanged baseline failure on pre-existing LOC gate only (`6` errors in `src/jfin/*`, `6` warnings in oversized legacy test files)

LOC/complexity note (non-tests/docs)
- Approx net new LOC in non-test/docs code remains ~`+393` (governance contract/check files).
- Avoided adding new governance CLI selectors or runtime modules; reused existing `--check characterization`.
- Added one small test helper module to keep large test file size warnings under control: [tests/_characterization_test_helpers.py](C:/Users/akaehler/Proton Drive/alex.kahler/My files/Projects/Jellyfin Image Normalizer/tests/_characterization_test_helpers.py).

---

Verdict: **Almost fully compliant; all previously flagged technical gaps are now closed.**  
If you require strict file-list parity from the old audit’s `S4-REQ-015`, it remains a **scoped variance** (extra helper file + unchanged `tests/test_characterization_checks_links.py`).

**Cross-check vs prior partial findings**
1. `S4-REQ-007` (tolerance-note enforcement): **Pass now**  
- Enforcement now triggers when `max_diff_pixels` is used (not just non-default MAE) in [characterization_contract.py](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/project/scripts/characterization_contract.py:368).

2. `S4-REQ-011` (IMG-specific negatives): **Pass now**  
- Added explicit IMG baseline-file and IMG case-missing negatives plus tolerance-note negative in [test_characterization_checks_imaging.py](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/tests/test_characterization_checks_imaging.py:38), [test_characterization_checks_imaging.py](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/tests/test_characterization_checks_imaging.py:60), [test_characterization_checks_imaging.py](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/tests/test_characterization_checks_imaging.py:134).

3. Python metadata contradiction: **Pass now**  
- Manifest now records 3.13 generation metadata in [manifest.json](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/tests/golden/imaging/manifest.json:4).

**Verification rerun**
- `PYTHONPATH=src python -m pytest -q tests/test_characterization_checks.py tests/test_characterization_checks_links.py tests/test_characterization_checks_imaging.py` → **15 passed**
- `PYTHONPATH=src python -m pytest -q tests/characterization/imaging_contract` → **8 passed**
- `PYTHONPATH=src python -m pytest -q tests/characterization -k harness` → **10 passed, 18 deselected**
- `python project/scripts/verify_governance.py --check characterization` → **PASS**
- `python project/scripts/verify_governance.py --check parity` → **PASS**
- `python project/scripts/verify_governance.py --check all` → **same expected LOC-only failure profile** (6 `src` errors + 6 test warnings), no new governance failure classes.

**Remaining nuance**
- If judged against strict “entailed files exactly” audit interpretation: still partial due added [tests/_characterization_test_helpers.py](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/tests/_characterization_test_helpers.py) and unchanged `tests/test_characterization_checks_links.py`.
- If judged by functional/governance acceptance criteria: **compliant now**.