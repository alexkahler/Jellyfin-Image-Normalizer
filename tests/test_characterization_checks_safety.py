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


def test_characterization_fails_when_workflow_index_missing(
    characterization_modules,
    tmp_path: Path,
):
    """Workflow coverage index file is required for Slice-11 checks."""
    characterization_contract, characterization_checks, parity_contract = (
        characterization_modules
    )
    repo_root, _cli_baseline_path, _parity_path = _write_valid_artifacts(
        tmp_path,
        characterization_contract,
        parity_contract,
    )
    (repo_root / "project/workflow-coverage-index.json").unlink()

    result = characterization_checks.check_characterization_artifacts(repo_root)
    assert any(
        error.startswith("workflow_coverage.contract_missing_index")
        for error in result.errors
    )


def test_characterization_fails_when_workflow_index_invalid_json(
    characterization_modules,
    tmp_path: Path,
):
    """Invalid workflow index JSON should fail with invalid-json contract taxonomy."""
    characterization_contract, characterization_checks, parity_contract = (
        characterization_modules
    )
    repo_root, _cli_baseline_path, _parity_path = _write_valid_artifacts(
        tmp_path,
        characterization_contract,
        parity_contract,
    )
    workflow_path = repo_root / "project/workflow-coverage-index.json"
    workflow_path.write_text("{ this is not valid json", encoding="utf-8")

    result = characterization_checks.check_characterization_artifacts(repo_root)
    assert any(
        error.startswith("workflow_coverage.contract_invalid_json")
        for error in result.errors
    )


def test_characterization_fails_when_workflow_index_schema_invalid(
    characterization_modules,
    tmp_path: Path,
):
    """Workflow index schema violations should fail with schema contract taxonomy."""
    characterization_contract, characterization_checks, parity_contract = (
        characterization_modules
    )
    repo_root, _cli_baseline_path, _parity_path = _write_valid_artifacts(
        tmp_path,
        characterization_contract,
        parity_contract,
    )
    workflow_path = repo_root / "project/workflow-coverage-index.json"
    payload = json.loads(workflow_path.read_text(encoding="utf-8"))
    payload["cells"] = []
    _write_file(workflow_path, json.dumps(payload, indent=2) + "\n")

    result = characterization_checks.check_characterization_artifacts(repo_root)
    assert any(
        error.startswith("workflow_coverage.contract_schema")
        for error in result.errors
    )


def test_characterization_fails_for_unknown_workflow_route_cell(
    characterization_modules,
    tmp_path: Path,
):
    """Workflow cell keys must correspond to route-fence command/mode rows."""
    characterization_contract, characterization_checks, parity_contract = (
        characterization_modules
    )
    repo_root, _cli_baseline_path, _parity_path = _write_valid_artifacts(
        tmp_path,
        characterization_contract,
        parity_contract,
    )
    workflow_path = repo_root / "project/workflow-coverage-index.json"
    payload = json.loads(workflow_path.read_text(encoding="utf-8"))
    payload["cells"] = {
        "run|unknown_mode": {
            **payload["cells"]["run|backdrop"],
            "command": "run",
            "mode": "unknown_mode",
        }
    }
    payload["cells"]["run|unknown_mode"]["future_split_debt"]["closure"]["cell"] = (
        "run|unknown_mode"
    )
    _write_file(workflow_path, json.dumps(payload, indent=2) + "\n")

    result = characterization_checks.check_characterization_artifacts(repo_root)
    assert any(
        error.startswith("workflow_coverage.contract_route_cell_missing")
        for error in result.errors
    )


def test_characterization_fails_for_missing_workflow_owner_symbol(
    characterization_modules,
    tmp_path: Path,
):
    """Workflow required_owner_tests must resolve to static owner symbols."""
    characterization_contract, characterization_checks, parity_contract = (
        characterization_modules
    )
    repo_root, _cli_baseline_path, _parity_path = _write_valid_artifacts(
        tmp_path,
        characterization_contract,
        parity_contract,
    )
    workflow_path = repo_root / "project/workflow-coverage-index.json"
    payload = json.loads(workflow_path.read_text(encoding="utf-8"))
    payload["cells"]["run|backdrop"]["required_owner_tests"] = [
        "tests/characterization/safety_contract/test_safety_contract_pipeline.py::test_missing_symbol"
    ]
    _write_file(workflow_path, json.dumps(payload, indent=2) + "\n")

    result = characterization_checks.check_characterization_artifacts(repo_root)
    assert any(
        error.startswith("workflow_coverage.contract_owner_symbol_missing")
        for error in result.errors
    )


def test_characterization_fails_for_uncollectable_workflow_owner_nodeid(
    characterization_modules,
    tmp_path: Path,
    monkeypatch,
):
    """Valid owner symbol should still fail when collect-only omits the nodeid."""
    characterization_contract, characterization_checks, parity_contract = (
        characterization_modules
    )
    repo_root, _cli_baseline_path, _parity_path = _write_valid_artifacts(
        tmp_path,
        characterization_contract,
        parity_contract,
    )

    monkeypatch.setattr(
        characterization_checks,
        "_collect_workflow_owner_nodeids",
        lambda _repo_root, _result: {
            "tests/characterization/safety_contract/test_safety_contract_pipeline.py::test_other_collectable"
        },
    )

    result = characterization_checks.check_characterization_artifacts(repo_root)
    assert any(
        error.startswith("workflow_coverage.contract_owner_nodeid_uncollectable")
        for error in result.errors
    )


def test_characterization_warns_on_count_only_backdrop_evidence_empty_container(
    characterization_modules,
    tmp_path: Path,
):
    """Empty backdrop evidence container should emit count-only warning."""
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
    case = payload["cases"]["PIPE-BACKDROP-001"]["expected_observations"]
    case["calls"] = {}
    _write_file(safety_baseline, json.dumps(payload, indent=2) + "\n")

    result = characterization_checks.check_characterization_artifacts(repo_root)
    assert any(
        warning.startswith("workflow_coverage.sequence_gap.count_only_detected")
        for warning in result.warnings
    )


def test_characterization_warns_on_count_only_backdrop_evidence_counts_only(
    characterization_modules,
    tmp_path: Path,
):
    """Counts-only backdrop evidence should emit count-only warning."""
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
    case = payload["cases"]["PIPE-BACKDROP-001"]["expected_observations"]
    case["calls"] = {"delete_calls": 2, "upload_calls": 2}
    _write_file(safety_baseline, json.dumps(payload, indent=2) + "\n")

    result = characterization_checks.check_characterization_artifacts(repo_root)
    assert any(
        warning.startswith("workflow_coverage.sequence_gap.count_only_detected")
        for warning in result.warnings
    )


def test_characterization_warns_when_required_backdrop_evidence_field_missing(
    characterization_modules,
    tmp_path: Path,
):
    """Missing required sequence field should emit deterministic warning."""
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
    calls = payload["cases"]["PIPE-BACKDROP-001"]["expected_observations"]["calls"]
    del calls["sequence.delete_index_zero_repeated"]
    _write_file(safety_baseline, json.dumps(payload, indent=2) + "\n")

    result = characterization_checks.check_characterization_artifacts(repo_root)
    assert any(
        warning.startswith("workflow_coverage.sequence_gap.missing_evidence_fields")
        and "sequence.delete_index_zero_repeated" in warning
        for warning in result.warnings
    )


def test_characterization_warns_when_required_backdrop_ordering_token_missing(
    characterization_modules,
    tmp_path: Path,
):
    """Empty ordering list should emit missing-ordering-token warning."""
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
    expected_observations = payload["cases"]["PIPE-BACKDROP-001"]["expected_observations"]
    expected_observations["ordering"] = []
    _write_file(safety_baseline, json.dumps(payload, indent=2) + "\n")

    result = characterization_checks.check_characterization_artifacts(repo_root)
    assert any(
        warning.startswith("workflow_coverage.sequence_gap.missing_ordering_tokens")
        and "delete_before_upload" in warning
        for warning in result.warnings
    )


def test_characterization_warns_when_required_backdrop_ordering_container_missing(
    characterization_modules,
    tmp_path: Path,
):
    """Missing ordering container should emit missing-ordering-token warning."""
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
    expected_observations = payload["cases"]["PIPE-BACKDROP-001"]["expected_observations"]
    expected_observations.pop("ordering", None)
    _write_file(safety_baseline, json.dumps(payload, indent=2) + "\n")

    result = characterization_checks.check_characterization_artifacts(repo_root)
    assert any(
        warning.startswith("workflow_coverage.sequence_gap.missing_ordering_tokens")
        and "delete_before_upload" in warning
        for warning in result.warnings
    )


def test_characterization_passes_when_backdrop_workflow_evidence_complete(
    characterization_modules,
    tmp_path: Path,
):
    """Valid backdrop workflow evidence should avoid workflow sequence warnings."""
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
        warning.startswith("workflow_coverage.sequence_gap")
        for warning in result.warnings
    )
