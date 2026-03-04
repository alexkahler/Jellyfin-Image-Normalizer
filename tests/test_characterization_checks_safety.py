"""Safety-focused governance tests for WI-005 characterization checks."""

from __future__ import annotations

import json
from pathlib import Path

from tests.test_characterization_checks import (
    _build_valid_parity_rows,
    _render_table,
    _write_file,
    _write_valid_artifacts,
)

pytest_plugins = ("tests.test_characterization_checks",)


def test_characterization_fails_when_safety_baseline_file_missing(
    characterization_modules,
    tmp_path: Path,
):
    """Missing safety baseline file should fail WI-005 characterization checks."""
    characterization_contract, characterization_checks, parity_contract = (
        characterization_modules
    )
    repo_root, _cli_baseline_path, _parity_path = _write_valid_artifacts(
        tmp_path,
        characterization_contract,
        parity_contract,
    )
    safety_baseline = (
        repo_root / "tests/characterization/baselines/safety_contract_baseline.json"
    )
    safety_baseline.unlink()

    result = characterization_checks.check_characterization_artifacts(repo_root)
    assert any("baseline file not found" in e for e in result.errors)


def test_characterization_fails_when_safety_behavior_id_missing(
    characterization_modules,
    tmp_path: Path,
):
    """Missing safety behavior IDs should fail with baseline drift errors."""
    characterization_contract, characterization_checks, parity_contract = (
        characterization_modules
    )
    repo_root, _cli_baseline_path, _parity_path = _write_valid_artifacts(
        tmp_path,
        characterization_contract,
        parity_contract,
    )
    safety_baseline = (
        repo_root / "tests/characterization/baselines/safety_contract_baseline.json"
    )
    payload = json.loads(safety_baseline.read_text(encoding="utf-8"))
    del payload["cases"][characterization_contract.SAFETY_BEHAVIOR_IDS[0]]
    _write_file(safety_baseline, json.dumps(payload, indent=2) + "\n")

    result = characterization_checks.check_characterization_artifacts(repo_root)
    assert any("missing required behavior_id" in e for e in result.errors)


def test_characterization_fails_when_safety_schema_missing_expected_observations(
    characterization_modules,
    tmp_path: Path,
):
    """Safety baseline cases must include expected_observations result mapping."""
    characterization_contract, characterization_checks, parity_contract = (
        characterization_modules
    )
    repo_root, _cli_baseline_path, _parity_path = _write_valid_artifacts(
        tmp_path,
        characterization_contract,
        parity_contract,
    )
    safety_baseline = (
        repo_root / "tests/characterization/baselines/safety_contract_baseline.json"
    )
    payload = json.loads(safety_baseline.read_text(encoding="utf-8"))
    first_behavior = characterization_contract.SAFETY_BEHAVIOR_IDS[0]
    del payload["cases"][first_behavior]["expected_observations"]
    _write_file(safety_baseline, json.dumps(payload, indent=2) + "\n")

    result = characterization_checks.check_characterization_artifacts(repo_root)
    assert any(
        "missing required object: expected_observations" in e for e in result.errors
    )


def test_characterization_fails_when_safety_parity_baseline_points_to_wrong_file(
    characterization_modules,
    tmp_path: Path,
):
    """Safety parity rows must point at the safety baseline artifact path."""
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
    target_behavior = characterization_contract.SAFETY_BEHAVIOR_IDS[0]
    target_row = next(row for row in rows if row["behavior_id"] == target_behavior)
    target_row["baseline_source"] = (
        f"tests/characterization/baselines/config_contract_baseline.json#{target_behavior}"
    )
    _write_file(
        parity_path,
        _render_table(parity_contract.REQUIRED_PARITY_COLUMNS, rows),
    )

    result = characterization_checks.check_characterization_artifacts(repo_root)
    assert any(
        "baseline anchor" in e or "path must reference one of" in e
        for e in result.errors
    )
