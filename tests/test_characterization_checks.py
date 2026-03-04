"""Unit tests for WI-004 characterization governance checks."""

from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

import pytest
from tests._characterization_test_helpers import (
    build_valid_baseline_payload,
    build_valid_imaging_manifest,
)

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = ROOT / "project" / "scripts"


@pytest.fixture(scope="module")
def characterization_modules():
    """Import characterization checker modules from project/scripts."""
    if str(SCRIPTS_DIR) not in sys.path:
        sys.path.insert(0, str(SCRIPTS_DIR))

    for module_name in (
        "characterization_contract",
        "characterization_checks",
        "parity_contract",
    ):
        if module_name in sys.modules:
            del sys.modules[module_name]

    characterization_contract = importlib.import_module("characterization_contract")
    characterization_checks = importlib.import_module("characterization_checks")
    parity_contract = importlib.import_module("parity_contract")
    return characterization_contract, characterization_checks, parity_contract


def _escape_cell(value: str) -> str:
    return value.replace("|", "\\|")


def _render_table(columns: list[str], rows: list[dict[str, str]]) -> str:
    lines = [
        "| " + " | ".join(_escape_cell(column) for column in columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(_escape_cell(row.get(column, "")) for column in columns)
            + " |"
        )
    return "\n".join(lines) + "\n"


def _write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _owner_test_for_behavior(behavior_id: str) -> tuple[str, str]:
    function_name = f"test_{behavior_id.lower().replace('-', '_')}"
    if behavior_id.startswith("CLI-"):
        return (
            "tests/characterization/cli_contract/test_cli_contract_characterization.py",
            function_name,
        )
    if behavior_id.startswith("IMG-"):
        return (
            "tests/characterization/imaging_contract/test_imaging_contract_characterization.py",
            function_name,
        )
    if behavior_id.startswith(("API-", "PIPE-", "RST-")):
        if behavior_id.startswith("API-"):
            return (
                "tests/characterization/safety_contract/test_safety_contract_api.py",
                function_name,
            )
        if behavior_id.startswith("PIPE-"):
            return (
                "tests/characterization/safety_contract/test_safety_contract_pipeline.py",
                function_name,
            )
        return (
            "tests/characterization/safety_contract/test_safety_contract_restore.py",
            function_name,
        )
    return (
        "tests/characterization/config_contract/test_config_contract_characterization.py",
        function_name,
    )


def _write_owner_test_files(required_ids: list[str], repo_root: Path) -> None:
    cli_functions: list[str] = []
    cfg_functions: list[str] = []
    img_functions: list[str] = []
    safety_functions: list[str] = []
    for behavior_id in required_ids:
        _path, function_name = _owner_test_for_behavior(behavior_id)
        function_line = f"def {function_name}():\n    assert True\n"
        if behavior_id.startswith("CLI-"):
            cli_functions.append(function_line)
        elif behavior_id.startswith("IMG-"):
            img_functions.append(function_line)
        elif behavior_id.startswith(("API-", "PIPE-", "RST-")):
            safety_functions.append(function_line)
        else:
            cfg_functions.append(function_line)

    _write_file(
        repo_root
        / "tests/characterization/cli_contract/test_cli_contract_characterization.py",
        "\n".join(cli_functions) + "\n",
    )
    _write_file(
        repo_root
        / "tests/characterization/config_contract/test_config_contract_characterization.py",
        "\n".join(cfg_functions) + "\n",
    )
    _write_file(
        repo_root
        / "tests/characterization/imaging_contract/test_imaging_contract_characterization.py",
        "\n".join(img_functions) + "\n",
    )
    safety_api_functions = [line for line in safety_functions if "test_api_" in line]
    safety_pipeline_functions = [
        line for line in safety_functions if "test_pipe_" in line
    ]
    safety_restore_functions = [
        line for line in safety_functions if "test_rst_" in line
    ]
    _write_file(
        repo_root
        / "tests/characterization/safety_contract/test_safety_contract_api.py",
        "\n".join(safety_api_functions) + "\n",
    )
    _write_file(
        repo_root
        / "tests/characterization/safety_contract/test_safety_contract_pipeline.py",
        "\n".join(safety_pipeline_functions) + "\n",
    )
    _write_file(
        repo_root
        / "tests/characterization/safety_contract/test_safety_contract_restore.py",
        "\n".join(safety_restore_functions) + "\n",
    )


def _build_valid_parity_rows(required_ids: list[str]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for behavior_id in required_ids:
        baseline_file = (
            "tests/characterization/baselines/cli_contract_baseline.json"
            if behavior_id.startswith("CLI-")
            else (
                "tests/characterization/baselines/imaging_contract_baseline.json"
                if behavior_id.startswith("IMG-")
                else (
                    "tests/characterization/baselines/safety_contract_baseline.json"
                    if behavior_id.startswith(("API-", "PIPE-", "RST-"))
                    else "tests/characterization/baselines/config_contract_baseline.json"
                )
            )
        )
        owner_path, owner_function = _owner_test_for_behavior(behavior_id)
        rows.append(
            {
                "behavior_id": behavior_id,
                "baseline_source": f"{baseline_file}#{behavior_id}",
                "current_result": "matches-baseline",
                "status": "preserved",
                "owner_test": f"{owner_path}::{owner_function}",
                "approval_ref": "n/a",
                "notes": "seed",
                "migration_note": "-",
            }
        )
    return rows


def _write_valid_artifacts(
    tmp_path: Path,
    characterization_contract,
    parity_contract,
) -> tuple[Path, Path, Path]:
    repo_root = tmp_path
    cli_payload = build_valid_baseline_payload(
        characterization_contract.CLI_BEHAVIOR_IDS
    )
    cfg_payload = build_valid_baseline_payload(
        characterization_contract.CFG_BEHAVIOR_IDS
    )
    imaging_payload = build_valid_baseline_payload(
        characterization_contract.IMG_BEHAVIOR_IDS,
        imaging=True,
    )
    safety_payload = build_valid_baseline_payload(
        characterization_contract.SAFETY_BEHAVIOR_IDS,
        safety=True,
    )
    imaging_manifest = build_valid_imaging_manifest(
        characterization_contract.IMG_BEHAVIOR_IDS
    )
    for behavior_id in characterization_contract.IMG_BEHAVIOR_IDS:
        imaging_payload["cases"][behavior_id]["golden_key"] = (
            f"golden-{behavior_id.lower()}"
        )

    cli_baseline_path = (
        repo_root / "tests/characterization/baselines/cli_contract_baseline.json"
    )
    cfg_baseline_path = (
        repo_root / "tests/characterization/baselines/config_contract_baseline.json"
    )
    imaging_baseline_path = (
        repo_root / "tests/characterization/baselines/imaging_contract_baseline.json"
    )
    safety_baseline_path = (
        repo_root / "tests/characterization/baselines/safety_contract_baseline.json"
    )
    imaging_manifest_path = repo_root / "tests/golden/imaging/manifest.json"
    _write_file(cli_baseline_path, json.dumps(cli_payload, indent=2) + "\n")
    _write_file(cfg_baseline_path, json.dumps(cfg_payload, indent=2) + "\n")
    _write_file(imaging_baseline_path, json.dumps(imaging_payload, indent=2) + "\n")
    _write_file(safety_baseline_path, json.dumps(safety_payload, indent=2) + "\n")
    _write_file(imaging_manifest_path, json.dumps(imaging_manifest, indent=2) + "\n")

    for behavior_id in characterization_contract.IMG_BEHAVIOR_IDS:
        expected_relpath = (
            f"tests/golden/imaging/expected/{behavior_id.lower()}_expected.png"
        )
        _write_file(repo_root / expected_relpath, "binary-seed")
    _write_file(
        repo_root / "tests/golden/imaging/fixtures/realish/fixture-seed.png", "seed"
    )

    required_ids = characterization_contract.REQUIRED_CHARACTERIZATION_BEHAVIOR_IDS
    _write_owner_test_files(required_ids, repo_root)

    parity_rows = _build_valid_parity_rows(required_ids)
    parity_text = _render_table(parity_contract.REQUIRED_PARITY_COLUMNS, parity_rows)
    parity_path = repo_root / "project/parity-matrix.md"
    _write_file(parity_path, parity_text)
    return repo_root, cli_baseline_path, parity_path


def test_characterization_check_valid_pass(characterization_modules, tmp_path: Path):
    characterization_contract, characterization_checks, parity_contract = (
        characterization_modules
    )
    repo_root, _baseline_path, _parity_path = _write_valid_artifacts(
        tmp_path,
        characterization_contract,
        parity_contract,
    )

    result = characterization_checks.check_characterization_artifacts(repo_root)
    assert not result.errors
    assert not result.warnings


def test_characterization_fails_when_baseline_file_missing(
    characterization_modules,
    tmp_path: Path,
):
    characterization_contract, characterization_checks, parity_contract = (
        characterization_modules
    )
    repo_root, cli_baseline_path, _parity_path = _write_valid_artifacts(
        tmp_path,
        characterization_contract,
        parity_contract,
    )
    cli_baseline_path.unlink()

    result = characterization_checks.check_characterization_artifacts(repo_root)
    assert any("baseline file not found" in error for error in result.errors)


def test_characterization_fails_when_required_behavior_id_missing(
    characterization_modules,
    tmp_path: Path,
):
    characterization_contract, characterization_checks, parity_contract = (
        characterization_modules
    )
    repo_root, cli_baseline_path, _parity_path = _write_valid_artifacts(
        tmp_path,
        characterization_contract,
        parity_contract,
    )
    cli_payload = json.loads(cli_baseline_path.read_text(encoding="utf-8"))
    del cli_payload["cases"][characterization_contract.CLI_BEHAVIOR_IDS[0]]
    _write_file(cli_baseline_path, json.dumps(cli_payload, indent=2) + "\n")

    result = characterization_checks.check_characterization_artifacts(repo_root)
    assert any("missing required behavior_id" in error for error in result.errors)
