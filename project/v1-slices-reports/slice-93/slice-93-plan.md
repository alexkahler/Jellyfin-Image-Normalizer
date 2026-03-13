## Slice 92-94 Governance Hardening Plan (Docstrings, Formatting, and LOC)

### Summary
- Implement this as a 3-stage sequence: Slice 92 governance gates, Slice 93 src docstring restoration, Slice 94 LOC remediation program.
- Enforce `src=block` and `tests=warn` for docstring and formatter governance behavior.
- Use Ruff docstring rules with Google convention, and run `ruff format` automatically when check failures are detected.
- Baseline observed now: `src docstring violations=102`, `tests docstring violations=189`, `src over-300 files=0`, `tests over-300 files=11`.

### Implementation Changes
1. **Slice 92: Add stricter governance mechanics (no broad content rewrites)**
- Extend governance contract schema with a new `docstring_policy` and `format_policy`.
- `docstring_policy` defaults: `convention=google`, `src_mode=block`, `tests_mode=warn`, `src_max_violations=102`, `tests_max_violations=189`, `comments_policy=targeted_inline_comments_for_non_obvious_logic`.
- Add a new governance check `docstrings` to run Ruff `D` rules with Google convention on `src/` and `tests/`, enforcing regression ratchet (`src` blocks above baseline, `tests` warns above baseline).
- Add a new governance check `format` (or equivalent helper script) that runs `ruff format --check` separately for `src/` and `tests`; if drift is found, run `ruff format` automatically; `src` drift is blocking, `tests` drift is warning.
- Include these checks in `--check all`, and update CI quality/governance wiring plus contract sync assertions accordingly.
- Update governance docs and command references to reflect the new behavior.

2. **Slice 93: Recreate missing docstrings in `src` first (and keep files compliant)**
- Restore Google-style docstrings across `src` public callables/classes/modules and add targeted inline comments only where logic is non-obvious.
- Perform minimal structural extraction where needed to keep `src` files at or under 300 LOC while adding docstrings (high-risk files are currently near limit: `client.py`, `cli.py`, `pipeline.py`, `config_core.py`, `backup_restore.py`, `client_http.py`, `pipeline_backdrops.py`, `config.py`, `cli_runtime.py`).
- After restoration, ratchet `docstring_policy.src_max_violations` to `0` (absolute block in `src`).
- Keep tests in warn mode for docstrings at this stage.

3. **Slice 94: LOC remediation stage for all over-limit files (multi-tranche closure)**
- Start LOC remediation on over-300 files with tranche execution (Slice 94 + explicit continuation tranches, e.g., `94a+`) because single-slice closure is too large.
- Prioritize largest files first (`tests/test_pipeline.py`, `tests/test_characterization_checks.py`, `tests/test_backup.py`, etc.), splitting into smaller focused modules/helpers without behavior drift.
- End-state criterion for this stage: zero files above 300 LOC (`src` errors `0`, `tests` warnings `0`) while preserving existing safety/governance invariants.

### Public Interface / Contract Changes
- `project/verification-contract.yml`: add `docstring_policy` and `format_policy` sections and updated verification command contract for formatter fallback behavior.
- `project/scripts/governance_contract.py`: parse + schema-validate new policy sections and fixed expected values.
- `project/scripts/governance_checks.py`: add `docstrings` and `format` checks and include both in `--check all`.
- `.github/workflows/ci.yml`: path-split formatter behavior (`src` blocking, `tests` warning) with fallback formatting execution.
- `AGENTS.md`, `README.md`, and shared verification guidance: sync updated governance/verification expectations.

### Test Plan
1. Add/extend governance unit tests for parsing and schema validation of new policy keys and fixed values.
2. Add tests for `docstrings` check behavior: `src` regression => error, `tests` regression => warning, Google convention enforced.
3. Add tests for formatter fallback behavior: check failure triggers `ruff format`; `src` remains blocking, `tests` warning-only.
4. Update CLI selector tests so `--check all` includes the new checks.
5. Run full repo gates plus governance checks after each slice (`--check all` required).

### Assumptions and Defaults
- Ruff-based Google docstring enforcement is the chosen mechanism.
- “Comments” is enforced as review policy (`targeted inline comments for non-obvious logic`), not a brittle hard-lint count rule.
- Baseline-ratchet staging is required so Slice 92 can remain verifiable before Slice 93 clears `src` debt.
- Multi-tranche LOC closure is explicitly allowed for Slice 94 stage until all over-limit files are resolved.
