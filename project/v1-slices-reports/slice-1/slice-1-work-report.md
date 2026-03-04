Implemented WI-001 as a governance-only slice, with no edits under `src/jfin`.

**What I changed**
- Added work-item scaffolding:
  - [WORK_ITEMS.md](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/WORK_ITEMS.md#L1)
  - [WI_TEMPLATE.md](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/plans/WI_TEMPLATE.md#L1)
  - [PULL_REQUEST_TEMPLATE.md](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/.github/PULL_REQUEST_TEMPLATE.md#L1)
- Added canonical verification contract:
  - [verification-contract.yml](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/project/verification-contract.yml#L1)
- Implemented governance checks (split to keep Python files <300 LOC):
  - Contract parsing/schema: [governance_contract.py](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/project/scripts/governance_contract.py#L20)
  - CI sync/LOC/version checks + runner: [governance_checks.py](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/project/scripts/governance_checks.py#L21)
  - CLI wrapper: [verify_governance.py](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/project/scripts/verify_governance.py#L1)
- Added governance unit tests:
  - [test_governance_checks.py](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/tests/test_governance_checks.py#L132)
- Wired CI governance job:
  - [ci.yml](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/.github/workflows/ci.yml#L86)
- Updated docs for governance workflow:
  - [README.md](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/README.md#L424)
  - [TECHNICAL_NOTES.md](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/docs/TECHNICAL_NOTES.md#L162)

**Verification run**
- `PYTHONPATH=src python -m pytest -q tests/test_governance_checks.py` -> `8 passed`
- `python project/scripts/verify_governance.py --check schema` -> pass
- `python project/scripts/verify_governance.py --check ci-sync` -> pass
- `python project/scripts/verify_governance.py --check python-version` -> pass
- `python project/scripts/verify_governance.py --check all` -> fails as expected on strict LOC baseline (`src` files >300), warnings for oversized tests
- `python -m ruff check .` -> pass
- `python -m ruff format --check .` -> pass
- `python -m bandit -r src` -> pass
- `PYTHONPATH=src python -m pytest` -> fails in current env (`Python 3.10.10`) because `tomllib` missing
- `python -m mypy src` -> same `tomllib` import-not-found in current env
- `python -m pip_audit` -> fails with existing environment/package vulnerabilities (not introduced by this slice)

**LOC budget note**
- This slice adds >150 net non-test/docs LOC (mainly governance checker + contract enforcement).  
- Justification: WI-001 explicitly requires enforceable governance automation (schema, CI drift checks, LOC policy, version consistency) plus tests.
- Smaller alternative: split into two PRs:
  1. scaffolding + contract + CI wiring only,
  2. checker implementation + tests.
