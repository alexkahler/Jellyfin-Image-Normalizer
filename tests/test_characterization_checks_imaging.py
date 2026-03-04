"""Imaging-focused governance tests for WI-003 characterization checks."""

from __future__ import annotations

import json
from pathlib import Path

from tests.test_characterization_checks import _write_file, _write_valid_artifacts

pytest_plugins = ("tests.test_characterization_checks",)


def test_characterization_fails_when_imaging_golden_key_missing(
    characterization_modules,
    tmp_path: Path,
):
    """Imaging baseline rows must include non-empty golden_key values."""
    characterization_contract, characterization_checks, parity_contract = (
        characterization_modules
    )
    repo_root, _cli_baseline_path, _parity_path = _write_valid_artifacts(
        tmp_path,
        characterization_contract,
        parity_contract,
    )
    baseline_path = (
        repo_root / "tests/characterization/baselines/imaging_contract_baseline.json"
    )
    payload = json.loads(baseline_path.read_text(encoding="utf-8"))
    first_behavior = characterization_contract.IMG_BEHAVIOR_IDS[0]
    del payload["cases"][first_behavior]["golden_key"]
    _write_file(baseline_path, json.dumps(payload, indent=2) + "\n")

    result = characterization_checks.check_characterization_artifacts(repo_root)
    assert any("golden_key must be a non-empty string" in e for e in result.errors)


def test_characterization_fails_when_imaging_baseline_file_missing(
    characterization_modules,
    tmp_path: Path,
):
    """Missing imaging baseline file should fail WI-003 characterization checks."""
    characterization_contract, characterization_checks, parity_contract = (
        characterization_modules
    )
    repo_root, _cli_baseline_path, _parity_path = _write_valid_artifacts(
        tmp_path,
        characterization_contract,
        parity_contract,
    )
    baseline_path = (
        repo_root / "tests/characterization/baselines/imaging_contract_baseline.json"
    )
    baseline_path.unlink()

    result = characterization_checks.check_characterization_artifacts(repo_root)
    assert any("baseline file not found" in e for e in result.errors)


def test_characterization_fails_when_img_behavior_id_missing(
    characterization_modules,
    tmp_path: Path,
):
    """Missing IMG behavior IDs should fail with an imaging baseline drift error."""
    characterization_contract, characterization_checks, parity_contract = (
        characterization_modules
    )
    repo_root, _cli_baseline_path, _parity_path = _write_valid_artifacts(
        tmp_path,
        characterization_contract,
        parity_contract,
    )
    baseline_path = (
        repo_root / "tests/characterization/baselines/imaging_contract_baseline.json"
    )
    payload = json.loads(baseline_path.read_text(encoding="utf-8"))
    del payload["cases"][characterization_contract.IMG_BEHAVIOR_IDS[0]]
    _write_file(baseline_path, json.dumps(payload, indent=2) + "\n")

    result = characterization_checks.check_characterization_artifacts(repo_root)
    assert any("missing required behavior_id" in e for e in result.errors)


def test_characterization_fails_when_manifest_entry_missing(
    characterization_modules,
    tmp_path: Path,
):
    """Imaging golden_key values must resolve to manifest case entries."""
    characterization_contract, characterization_checks, parity_contract = (
        characterization_modules
    )
    repo_root, _cli_baseline_path, _parity_path = _write_valid_artifacts(
        tmp_path,
        characterization_contract,
        parity_contract,
    )
    manifest_path = repo_root / "tests/golden/imaging/manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    first_behavior = characterization_contract.IMG_BEHAVIOR_IDS[0]
    missing_key = f"golden-{first_behavior.lower()}"
    del manifest["cases"][missing_key]
    _write_file(manifest_path, json.dumps(manifest, indent=2) + "\n")

    result = characterization_checks.check_characterization_artifacts(repo_root)
    assert any(
        "not found in tests/golden/imaging/manifest.json" in e for e in result.errors
    )


def test_characterization_fails_when_expected_artifact_missing(
    characterization_modules,
    tmp_path: Path,
):
    """Manifest expected_path entries must resolve to existing expected artifacts."""
    characterization_contract, characterization_checks, parity_contract = (
        characterization_modules
    )
    repo_root, _cli_baseline_path, _parity_path = _write_valid_artifacts(
        tmp_path,
        characterization_contract,
        parity_contract,
    )
    expected_path = (
        repo_root
        / "tests/golden/imaging/expected"
        / f"{characterization_contract.IMG_BEHAVIOR_IDS[0].lower()}_expected.png"
    )
    expected_path.unlink()

    result = characterization_checks.check_characterization_artifacts(repo_root)
    assert any("expected artifact not found" in e for e in result.errors)


def test_characterization_fails_when_tolerance_override_note_missing(
    characterization_modules,
    tmp_path: Path,
):
    """Any tolerance override should require tolerance_note in tolerant mode."""
    characterization_contract, characterization_checks, parity_contract = (
        characterization_modules
    )
    repo_root, _cli_baseline_path, _parity_path = _write_valid_artifacts(
        tmp_path,
        characterization_contract,
        parity_contract,
    )
    manifest_path = repo_root / "tests/golden/imaging/manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    first_behavior = characterization_contract.IMG_BEHAVIOR_IDS[0]
    golden_key = f"golden-{first_behavior.lower()}"
    manifest["cases"][golden_key]["compare_mode"] = "tolerant"
    manifest["cases"][golden_key]["max_mean_abs_error"] = 2.0
    manifest["cases"][golden_key]["max_diff_pixels"] = 3
    manifest["cases"][golden_key].pop("tolerance_note", None)
    _write_file(manifest_path, json.dumps(manifest, indent=2) + "\n")

    result = characterization_checks.check_characterization_artifacts(repo_root)
    assert any(
        "uses tolerance overrides and requires tolerance_note" in e
        for e in result.errors
    )


def test_characterization_fails_when_expected_budget_exceeded(
    characterization_modules,
    tmp_path: Path,
):
    """Expected artifact budget should fail when file count exceeds WI-003 limit."""
    characterization_contract, characterization_checks, parity_contract = (
        characterization_modules
    )
    repo_root, _cli_baseline_path, _parity_path = _write_valid_artifacts(
        tmp_path,
        characterization_contract,
        parity_contract,
    )
    expected_root = repo_root / "tests/golden/imaging/expected"
    for idx in range(17):
        _write_file(expected_root / f"overflow-{idx}.png", "seed")

    result = characterization_checks.check_characterization_artifacts(repo_root)
    assert any(
        "imaging expected artifact file count exceeds budget" in e
        for e in result.errors
    )


def test_characterization_fails_when_fixture_budget_exceeded(
    characterization_modules,
    tmp_path: Path,
):
    """Fixture budget should fail when real-ish fixture count exceeds WI-003 limit."""
    characterization_contract, characterization_checks, parity_contract = (
        characterization_modules
    )
    repo_root, _cli_baseline_path, _parity_path = _write_valid_artifacts(
        tmp_path,
        characterization_contract,
        parity_contract,
    )
    fixture_root = repo_root / "tests/golden/imaging/fixtures/realish"
    for idx in range(5):
        _write_file(fixture_root / f"overflow-{idx}.png", "seed")

    result = characterization_checks.check_characterization_artifacts(repo_root)
    assert any(
        "imaging fixture artifact file count exceeds budget" in e for e in result.errors
    )
