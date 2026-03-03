"""Additional linkage-focused tests for WI-004 characterization governance checks."""

from __future__ import annotations

from pathlib import Path

from tests.test_characterization_checks import (
    _build_valid_parity_rows,
    _render_table,
    _write_file,
    _write_valid_artifacts,
)

pytest_plugins = ("tests.test_characterization_checks",)


def test_characterization_fails_when_baseline_anchor_missing(
    characterization_modules,
    tmp_path: Path,
):
    """Parity baseline_source anchors must resolve to baseline case keys."""
    characterization_contract, characterization_checks, parity_contract = (
        characterization_modules
    )
    repo_root, _cli_baseline_path, parity_path = _write_valid_artifacts(
        tmp_path,
        characterization_contract,
        parity_contract,
    )
    rows = _build_valid_parity_rows(
        characterization_contract.REQUIRED_CHARACTERIZATION_BEHAVIOR_IDS
    )
    rows[0]["baseline_source"] = (
        "tests/characterization/baselines/cli_contract_baseline.json#MISSING-ID"
    )
    _write_file(
        parity_path,
        _render_table(parity_contract.REQUIRED_PARITY_COLUMNS, rows),
    )
    result = characterization_checks.check_characterization_artifacts(repo_root)
    assert any(
        "baseline_source anchor must match behavior_id" in e for e in result.errors
    )


def test_characterization_fails_when_owner_test_function_missing(
    characterization_modules,
    tmp_path: Path,
):
    """Owner test function references must resolve in the referenced test file."""
    characterization_contract, characterization_checks, parity_contract = (
        characterization_modules
    )
    repo_root, _cli_baseline_path, parity_path = _write_valid_artifacts(
        tmp_path,
        characterization_contract,
        parity_contract,
    )
    rows = _build_valid_parity_rows(
        characterization_contract.REQUIRED_CHARACTERIZATION_BEHAVIOR_IDS
    )
    rows[0]["owner_test"] = (
        "tests/characterization/cli_contract/test_cli_contract_characterization.py::"
        "test_missing_function"
    )
    _write_file(
        parity_path,
        _render_table(parity_contract.REQUIRED_PARITY_COLUMNS, rows),
    )
    result = characterization_checks.check_characterization_artifacts(repo_root)
    assert any(
        "owner_test function 'test_missing_function' not found" in e
        for e in result.errors
    )


def test_characterization_fails_when_owner_test_file_missing(
    characterization_modules,
    tmp_path: Path,
):
    """Owner test file references must resolve to an existing file path."""
    characterization_contract, characterization_checks, parity_contract = (
        characterization_modules
    )
    repo_root, _cli_baseline_path, parity_path = _write_valid_artifacts(
        tmp_path,
        characterization_contract,
        parity_contract,
    )
    rows = _build_valid_parity_rows(
        characterization_contract.REQUIRED_CHARACTERIZATION_BEHAVIOR_IDS
    )
    rows[0]["owner_test"] = (
        "tests/characterization/cli_contract/test_missing_file.py::test_case"
    )
    _write_file(
        parity_path,
        _render_table(parity_contract.REQUIRED_PARITY_COLUMNS, rows),
    )
    result = characterization_checks.check_characterization_artifacts(repo_root)
    assert any("owner_test file not found" in e for e in result.errors)


def test_characterization_fails_when_owner_test_is_outside_characterization_tree(
    characterization_modules,
    tmp_path: Path,
):
    """Owner test references must remain under tests/characterization/."""
    characterization_contract, characterization_checks, parity_contract = (
        characterization_modules
    )
    repo_root, _cli_baseline_path, parity_path = _write_valid_artifacts(
        tmp_path,
        characterization_contract,
        parity_contract,
    )
    rows = _build_valid_parity_rows(
        characterization_contract.REQUIRED_CHARACTERIZATION_BEHAVIOR_IDS
    )
    rows[0]["owner_test"] = "tests/test_jfin.py::test_some_case"
    _write_file(
        parity_path,
        _render_table(parity_contract.REQUIRED_PARITY_COLUMNS, rows),
    )
    result = characterization_checks.check_characterization_artifacts(repo_root)
    assert any(
        "owner_test path must be under tests/characterization/" in e
        for e in result.errors
    )
