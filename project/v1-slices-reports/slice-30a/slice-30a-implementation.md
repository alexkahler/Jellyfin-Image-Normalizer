# Slice-30a Implementation Report

## Baseline observations
- Branch baseline at implementation start: `v1/thm-a-governance-contract-posture-recovery`.
- Baseline `HEAD` at implementation start: `7e35f1e`.
- Authoritative pre-slice dirt snapshot (captured before creating `slice-30a/` artifacts) was:
  - `?? project/v1-slices-reports/slice-30/`
- After creating Slice-30a report artifacts, expected additional untracked path:
  - `?? project/v1-slices-reports/slice-30a/`
- Pre-change anti-evasion marker in `src/jfin/cli.py`: `2:# fmt: off`.
- Pre-change `src/jfin/cli.py` LOC: `289`.
- Baseline offender expectation from approved plan: `src/jfin/cli.py`, `src/jfin/cli_runtime.py`, `src/jfin/pipeline.py`, `src/jfin/pipeline_backdrops.py`.

## Exact changes made
- Updated `src/jfin/cli.py` only.
- Removed anti-evasion formatter suppression marker (`# fmt: off`).
- Added private helper `_collect_unexpected_tokens(argv, allowed, value_flags)` to centralize repeated argument-token filtering logic.
- Added private helper `_raise_invalid_combination(command_flag, extras, stats_detail)` to centralize identical error/exit handling.
- Rewired these existing entry points to use the shared helper flow, preserving signatures and exit behavior:
  - `validate_generate_config_args(argv)`
  - `validate_restore_all_args(argv)`
  - `validate_test_jf_args(argv)`
- Applied formatter normalization with `ruff format` to keep honest formatter-compatible structure.
- No substantive changes to `src/jfin/cli_runtime.py` (no edits made).

## Provisional verification evidence
1. Formatter marker grep (`src/jfin/cli.py`):
   - Command: `rg -n "#\\s*fmt:\\s*(off|on)" src/jfin/cli.py`
   - Result: no matches (`rg` exit code `1`).
2. Honest LOC check:
   - Command: `(Get-Content src/jfin/cli.py).Length`
   - Result: `292` (meets `<=300`).
3. Targeted anti-evasion style check:
   - Command: `python -m ruff check src/jfin/cli.py --select E701,E702,E703`
   - Result: `All checks passed!`
4. Formatter compatibility check:
   - Command: `python -m ruff format --check src/jfin/cli.py`
   - Result: `1 file already formatted`.
5. Targeted CLI regression tests from plan:
   - Command: `python -m pytest -q tests/characterization/cli_contract/test_cli_contract_characterization.py tests/test_jfin.py tests/test_config.py`
   - Result: `64 passed`.
6. Provisional governance LOC offender assertion:
   - Command: `python project/scripts/verify_governance.py --check loc`
   - Result: non-zero (expected while offenders remain).
   - Parsed offender set: `src/jfin/cli_runtime.py`, `src/jfin/pipeline.py`, `src/jfin/pipeline_backdrops.py`.
   - Exact-set assertion: match true against expected remaining set.
   - Not-flagged assertion: `src/jfin/cli.py`, `src/jfin/client.py`, `src/jfin/client_http.py` are absent from offender set.
7. Scope control:
   - Command: `git diff --name-only -- src`
   - Result: only `src/jfin/cli.py` touched.

## Blocked or closable
- Slice-30a implementation scope is **closable**.
- Hard-stop conditions were not triggered for runtime scope (`src/jfin/cli_runtime.py` unchanged).

## Required open-state statement
- **A-08 and Theme A remain open after Slice-30a.**

## Explicit next slice statement
- `Slice-30b Runtime evasion remediation tranche 3b (cli_runtime.py)`
- Why: after successful Slice-30a, `cli_runtime.py` remains an expected anti-evasion offender and requires isolated, behavior-preserving remediation without scope mixing.
