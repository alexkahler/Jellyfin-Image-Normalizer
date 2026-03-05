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


def _write_verification_contract(repo_root: Path) -> None:
    """Write the canonical verification-contract payload for test repos."""
    _write_file(
        repo_root / "project/verification-contract.yml",
        "\n".join(
            [
                "version: 1",
                'python_version: "3.13"',
                "verification_commands:",
                "  - PYTHONPATH=src ./.venv/bin/python -m pytest",
                "  - ./.venv/bin/python -m ruff check .",
                "  - ./.venv/bin/python -m ruff format --check .",
                "  - ./.venv/bin/python -m mypy src",
                "  - ./.venv/bin/python -m bandit -r src",
                "  - ./.venv/bin/python -m pip_audit",
                "required_ci_jobs:",
                "  - test",
                "  - security",
                "  - quality",
                "  - governance",
                "characterization_runtime_gate_targets:",
                "  - tests/characterization/safety_contract",
                "characterization_runtime_gate_budget_seconds: 180",
                "loc_policy:",
                "  src_max_lines: 300",
                "  src_mode: block",
                "  tests_max_lines: 300",
                "  tests_mode: warn",
            ]
        )
        + "\n",
    )


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


def _write_surface_artifacts(
    repo_root: Path,
    characterization_contract,
) -> None:
    _write_file(repo_root / "src/jfin/__init__.py", "")
    _write_file(
        repo_root / "src/jfin/__main__.py",
        "from .cli import parse_args\n\nif __name__ == '__main__':\n    parse_args()\n",
    )
    _write_file(
        repo_root / "src/jfin/cli.py",
        """
import argparse


def parse_args():
    parser = argparse.ArgumentParser(description="seed")
    parser.add_argument("--config", help="Path to config (default: config.toml in repo root).")
    parser.add_argument("--mode", help="Mode values include logo|thumb|backdrop|profile.")
    parser.add_argument("--silent", "-s", action="store_true", help="silent mode")
    return parser.parse_args()
""",
    )
    _write_file(
        repo_root / "config.example.toml",
        """
[server]
jf_url = "https://demo"

[logging]
silent = true
""",
    )
    _write_file(
        repo_root / "docs/TECHNICAL_NOTES.md",
        """
## Runtime Flow (High Level)
9) Always log scale decisions, API failures, and run summary before exit.

## Logging, State, and Metrics
- RunStats counts images_found/processed/success/skipped/warning/error and failed items.
- Presence/absence of warning/error classes should remain user-visible.
- Exit behavior: major classes are success, validation failure, and runtime failure.
- upscaled_images and downscaled_images feed summary output.
""",
    )

    cli_behavior = characterization_contract.CLI_BEHAVIOR_IDS[0]
    cfg_behavior = characterization_contract.CFG_BEHAVIOR_IDS[0]
    obs_behavior = characterization_contract.CLI_BEHAVIOR_IDS[1]

    cli_owner_path, cli_owner_fn = _owner_test_for_behavior(cli_behavior)
    cfg_owner_path, cfg_owner_fn = _owner_test_for_behavior(cfg_behavior)
    obs_owner_path, obs_owner_fn = _owner_test_for_behavior(obs_behavior)

    surface_index = {
        "version": 1,
        "cli_items": [
            {
                "id": "cli.root.command",
                "command_path": "root",
                "source_token": "command:root",
                "default_text": "",
                "parity_ids": [obs_behavior],
                "owner_tests": [f"{obs_owner_path}::{obs_owner_fn}"],
                "out_of_scope": False,
                "out_of_scope_reason": "",
                "code_refs": ["src/jfin/cli.py:1"],
                "notes": "seed",
            },
            {
                "id": "cli.root.option.-h",
                "command_path": "root",
                "source_token": "-h",
                "default_text": "",
                "parity_ids": [],
                "owner_tests": [],
                "out_of_scope": True,
                "out_of_scope_reason": "help alias formatting",
                "code_refs": ["src/jfin/cli.py:1"],
                "notes": "seed",
            },
            {
                "id": "cli.root.option.--help",
                "command_path": "root",
                "source_token": "--help",
                "default_text": "",
                "parity_ids": [],
                "owner_tests": [],
                "out_of_scope": True,
                "out_of_scope_reason": "help alias formatting",
                "code_refs": ["src/jfin/cli.py:1"],
                "notes": "seed",
            },
            {
                "id": "cli.root.option.--config",
                "command_path": "root",
                "source_token": "--config",
                "default_text": "config.toml in repo root",
                "parity_ids": [cfg_behavior],
                "owner_tests": [f"{cfg_owner_path}::{cfg_owner_fn}"],
                "out_of_scope": False,
                "out_of_scope_reason": "",
                "code_refs": ["src/jfin/cli.py:1"],
                "notes": "seed",
            },
            {
                "id": "cli.root.option.--mode",
                "command_path": "root",
                "source_token": "--mode",
                "default_text": "",
                "parity_ids": [cli_behavior],
                "owner_tests": [f"{cli_owner_path}::{cli_owner_fn}"],
                "out_of_scope": False,
                "out_of_scope_reason": "",
                "code_refs": ["src/jfin/cli.py:1"],
                "notes": "seed",
            },
            {
                "id": "cli.root.option.--silent",
                "command_path": "root",
                "source_token": "--silent",
                "default_text": "",
                "parity_ids": [obs_behavior],
                "owner_tests": [f"{obs_owner_path}::{obs_owner_fn}"],
                "out_of_scope": False,
                "out_of_scope_reason": "",
                "code_refs": ["src/jfin/cli.py:1"],
                "notes": "seed",
            },
            {
                "id": "cli.root.option.-s",
                "command_path": "root",
                "source_token": "-s",
                "default_text": "",
                "parity_ids": [obs_behavior],
                "owner_tests": [f"{obs_owner_path}::{obs_owner_fn}"],
                "out_of_scope": False,
                "out_of_scope_reason": "",
                "code_refs": ["src/jfin/cli.py:1"],
                "notes": "seed",
            },
            {
                "id": "cli.root.mode.backdrop",
                "command_path": "root",
                "source_token": "backdrop",
                "default_text": "",
                "parity_ids": [cli_behavior],
                "owner_tests": [f"{cli_owner_path}::{cli_owner_fn}"],
                "out_of_scope": False,
                "out_of_scope_reason": "",
                "code_refs": ["src/jfin/cli.py:1"],
                "notes": "seed",
            },
            {
                "id": "cli.root.mode.logo",
                "command_path": "root",
                "source_token": "logo",
                "default_text": "",
                "parity_ids": [cli_behavior],
                "owner_tests": [f"{cli_owner_path}::{cli_owner_fn}"],
                "out_of_scope": False,
                "out_of_scope_reason": "",
                "code_refs": ["src/jfin/cli.py:1"],
                "notes": "seed",
            },
            {
                "id": "cli.root.mode.profile",
                "command_path": "root",
                "source_token": "profile",
                "default_text": "",
                "parity_ids": [cli_behavior],
                "owner_tests": [f"{cli_owner_path}::{cli_owner_fn}"],
                "out_of_scope": False,
                "out_of_scope_reason": "",
                "code_refs": ["src/jfin/cli.py:1"],
                "notes": "seed",
            },
            {
                "id": "cli.root.mode.thumb",
                "command_path": "root",
                "source_token": "thumb",
                "default_text": "",
                "parity_ids": [cli_behavior],
                "owner_tests": [f"{cli_owner_path}::{cli_owner_fn}"],
                "out_of_scope": False,
                "out_of_scope_reason": "",
                "code_refs": ["src/jfin/cli.py:1"],
                "notes": "seed",
            },
        ],
        "config_items": [
            {
                "id": "config.server.jf_url",
                "parity_ids": [cfg_behavior],
                "owner_tests": [f"{cfg_owner_path}::{cfg_owner_fn}"],
                "out_of_scope": False,
                "out_of_scope_reason": "",
                "code_refs": ["config.example.toml:2"],
                "notes": "seed",
            },
            {
                "id": "config.logging.silent",
                "parity_ids": [cfg_behavior],
                "owner_tests": [f"{cfg_owner_path}::{cfg_owner_fn}"],
                "out_of_scope": False,
                "out_of_scope_reason": "",
                "code_refs": ["config.example.toml:5"],
                "notes": "seed",
            },
        ],
        "observability_items": [
            {
                "id": "obs.summary.counters",
                "parity_ids": [obs_behavior],
                "owner_tests": [f"{obs_owner_path}::{obs_owner_fn}"],
                "out_of_scope": False,
                "out_of_scope_reason": "",
                "code_refs": ["docs/TECHNICAL_NOTES.md:6"],
                "notes": "seed",
            },
            {
                "id": "obs.summary.failure_list",
                "parity_ids": [obs_behavior],
                "owner_tests": [f"{obs_owner_path}::{obs_owner_fn}"],
                "out_of_scope": False,
                "out_of_scope_reason": "",
                "code_refs": ["docs/TECHNICAL_NOTES.md:6"],
                "notes": "seed",
            },
            {
                "id": "obs.summary.warning_error_presence",
                "parity_ids": [obs_behavior],
                "owner_tests": [f"{obs_owner_path}::{obs_owner_fn}"],
                "out_of_scope": False,
                "out_of_scope_reason": "",
                "code_refs": ["docs/TECHNICAL_NOTES.md:7"],
                "notes": "seed",
            },
            {
                "id": "obs.summary.scale_decision_reporting",
                "parity_ids": [obs_behavior],
                "owner_tests": [f"{obs_owner_path}::{obs_owner_fn}"],
                "out_of_scope": False,
                "out_of_scope_reason": "",
                "code_refs": ["docs/TECHNICAL_NOTES.md:3"],
                "notes": "seed",
            },
            {
                "id": "obs.exit_codes.major_classes",
                "parity_ids": [obs_behavior],
                "owner_tests": [f"{obs_owner_path}::{obs_owner_fn}"],
                "out_of_scope": False,
                "out_of_scope_reason": "",
                "code_refs": ["docs/TECHNICAL_NOTES.md:8"],
                "notes": "seed",
            },
        ],
    }
    _write_file(
        repo_root / "project/surface-coverage-index.json",
        json.dumps(surface_index, indent=2) + "\n",
    )


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
    _write_verification_contract(repo_root)
    _write_surface_artifacts(repo_root, characterization_contract)
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
    collectability_report = getattr(result, "collectability_report", None)
    assert collectability_report is not None
    assert collectability_report.unresolved_owner_nodeids == 0


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


def test_characterization_collectability_fails_for_non_collectable_nodeid(
    characterization_modules,
    tmp_path: Path,
):
    """Owner test symbols that exist but are not pytest-collectable must fail."""
    characterization_contract, characterization_checks, parity_contract = (
        characterization_modules
    )
    repo_root, _cli_baseline_path, parity_path = _write_valid_artifacts(
        tmp_path,
        characterization_contract,
        parity_contract,
    )
    behavior_id = characterization_contract.CLI_BEHAVIOR_IDS[0]
    owner_path, _owner_fn = _owner_test_for_behavior(behavior_id)
    owner_file = repo_root / owner_path
    owner_file.write_text(
        owner_file.read_text(encoding="utf-8")
        + "\n\ndef helper_not_a_pytest_case():\n    return True\n",
        encoding="utf-8",
    )
    rows = _build_valid_parity_rows(
        characterization_contract.REQUIRED_CHARACTERIZATION_BEHAVIOR_IDS
    )
    target_row = next(row for row in rows if row["behavior_id"] == behavior_id)
    target_row["owner_test"] = f"{owner_path}::helper_not_a_pytest_case"
    _write_file(
        parity_path,
        _render_table(parity_contract.REQUIRED_PARITY_COLUMNS, rows),
    )

    result = characterization_checks.check_characterization_artifacts(repo_root)
    assert any(
        "collectability.collect_only_unresolved" in error and behavior_id in error
        for error in result.errors
    )


def test_characterization_collectability_fails_when_contract_context_missing(
    characterization_modules,
    tmp_path: Path,
):
    """Collectability must fail deterministically when contract context is invalid."""
    characterization_contract, characterization_checks, parity_contract = (
        characterization_modules
    )
    repo_root, _cli_baseline_path, _parity_path = _write_valid_artifacts(
        tmp_path,
        characterization_contract,
        parity_contract,
    )
    _write_file(
        repo_root / "project/verification-contract.yml",
        "version: 1\n",
    )

    result = characterization_checks.check_characterization_artifacts(repo_root)
    assert any(
        "collectability.contract_context_missing" in error for error in result.errors
    )
