"""Trace-focused safety governance tests for COV-04 characterization checks."""

from __future__ import annotations

import json
from pathlib import Path

from tests.test_characterization_checks import _write_file, _write_valid_artifacts

pytest_plugins = ("tests.test_characterization_checks",)


def _load_safety_payload(repo_root: Path) -> tuple[Path, dict]:
    """Load the safety baseline payload from a generated test repository."""
    safety_baseline = (
        repo_root / "tests/characterization/baselines/safety_contract_baseline.json"
    )
    return safety_baseline, json.loads(safety_baseline.read_text(encoding="utf-8"))


def test_characterization_fails_when_backdrop_trace_missing(
    characterization_modules,
    tmp_path: Path,
):
    """Required backdrop trace must be present for workflow trace contract checks."""
    characterization_contract, characterization_checks, parity_contract = (
        characterization_modules
    )
    repo_root, _cli_baseline_path, _parity_path = _write_valid_artifacts(
        tmp_path,
        characterization_contract,
        parity_contract,
    )
    safety_baseline, payload = _load_safety_payload(repo_root)
    expected_observations = payload["cases"]["PIPE-BACKDROP-001"][
        "expected_observations"
    ]
    expected_observations.pop("trace", None)
    _write_file(safety_baseline, json.dumps(payload, indent=2) + "\n")

    result = characterization_checks.check_characterization_artifacts(repo_root)
    assert any(
        error.startswith("workflow_coverage.contract_trace_missing")
        for error in result.errors
    )


def test_characterization_fails_when_backdrop_trace_schema_invalid(
    characterization_modules,
    tmp_path: Path,
):
    """Malformed backdrop trace should fail with trace schema taxonomy."""
    characterization_contract, characterization_checks, parity_contract = (
        characterization_modules
    )
    repo_root, _cli_baseline_path, _parity_path = _write_valid_artifacts(
        tmp_path,
        characterization_contract,
        parity_contract,
    )
    safety_baseline, payload = _load_safety_payload(repo_root)
    payload["cases"]["PIPE-BACKDROP-001"]["expected_observations"]["trace"][
        "events"
    ] = []
    _write_file(safety_baseline, json.dumps(payload, indent=2) + "\n")

    result = characterization_checks.check_characterization_artifacts(repo_root)
    assert any(
        error.startswith("workflow_coverage.contract_trace_schema")
        for error in result.errors
    )


def test_characterization_fails_when_optional_trace_schema_invalid(
    characterization_modules,
    tmp_path: Path,
):
    """Non-migrated safety rows may omit trace, but malformed optional trace is blocking."""
    characterization_contract, characterization_checks, parity_contract = (
        characterization_modules
    )
    repo_root, _cli_baseline_path, _parity_path = _write_valid_artifacts(
        tmp_path,
        characterization_contract,
        parity_contract,
    )
    safety_baseline, payload = _load_safety_payload(repo_root)
    payload["cases"]["API-DRYRUN-001"]["expected_observations"]["trace"] = {
        "events": []
    }
    _write_file(safety_baseline, json.dumps(payload, indent=2) + "\n")

    result = characterization_checks.check_characterization_artifacts(repo_root)
    assert any(
        "API-DRYRUN-001 expected_observations.trace.events must be a non-empty list."
        in error
        for error in result.errors
    )


def test_characterization_allows_non_migrated_rows_without_trace(
    characterization_modules,
    tmp_path: Path,
):
    """Rows outside PIPE-BACKDROP-001 remain trace-optional in Slice 13."""
    characterization_contract, characterization_checks, parity_contract = (
        characterization_modules
    )
    repo_root, _cli_baseline_path, _parity_path = _write_valid_artifacts(
        tmp_path,
        characterization_contract,
        parity_contract,
    )

    result = characterization_checks.check_characterization_artifacts(repo_root)
    assert not any(
        "API-DRYRUN-001 expected_observations.trace" in error for error in result.errors
    )


def test_characterization_fails_when_backdrop_trace_invariants_mismatch(
    characterization_modules,
    tmp_path: Path,
):
    """Backdrop trace invariant regressions should fail via assertion taxonomy."""
    characterization_contract, characterization_checks, parity_contract = (
        characterization_modules
    )
    repo_root, _cli_baseline_path, _parity_path = _write_valid_artifacts(
        tmp_path,
        characterization_contract,
        parity_contract,
    )
    safety_baseline, payload = _load_safety_payload(repo_root)
    trace_events = payload["cases"]["PIPE-BACKDROP-001"]["expected_observations"][
        "trace"
    ]["events"]
    trace_events[8]["details"]["target_index"] = 2
    _write_file(safety_baseline, json.dumps(payload, indent=2) + "\n")

    result = characterization_checks.check_characterization_artifacts(repo_root)
    assert any(
        error.startswith("workflow_coverage.contract_trace_assertion_failed")
        for error in result.errors
    )


def test_characterization_passes_when_backdrop_trace_and_legacy_evidence_are_valid(
    characterization_modules,
    tmp_path: Path,
):
    """Valid trace + legacy sequence evidence should pass for run|backdrop coverage."""
    characterization_contract, characterization_checks, parity_contract = (
        characterization_modules
    )
    repo_root, _cli_baseline_path, _parity_path = _write_valid_artifacts(
        tmp_path,
        characterization_contract,
        parity_contract,
    )

    result = characterization_checks.check_characterization_artifacts(repo_root)
    assert not any(
        error.startswith("workflow_coverage.contract_trace_") for error in result.errors
    )
    assert not any(
        warning.startswith("workflow_coverage.sequence_gap")
        for warning in result.warnings
    )
