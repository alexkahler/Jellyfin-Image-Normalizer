"""Focused schema-negative tests for architecture baseline contract parsing."""

from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = ROOT / "project" / "scripts"


@pytest.fixture(scope="module")
def architecture_contract():
    """Load architecture_contract from project/scripts for schema tests."""
    if str(SCRIPTS_DIR) not in sys.path:
        sys.path.insert(0, str(SCRIPTS_DIR))
    if "architecture_contract" in sys.modules:
        del sys.modules["architecture_contract"]
    return importlib.import_module("architecture_contract")


def _write_baseline(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _valid_payload(contract_module) -> dict[str, object]:
    return {
        "version": contract_module.BASELINE_VERSION,
        "v1_root": contract_module.V1_ROOT,
        "entry_exit_modules": list(contract_module.DEFAULT_ENTRY_EXIT_MODULES),
        "non_entry_exit_allowlist": {},
    }


def test_baseline_rejects_extra_entry_exit_module(
    architecture_contract, tmp_path: Path
):
    """entry_exit_modules must remain fixed to the Track 1 CLI entry module."""
    payload = _valid_payload(architecture_contract)
    payload["entry_exit_modules"] = [
        "src/jfin/cli.py",
        "src/jfin/config.py",
    ]
    baseline_path = tmp_path / "project" / "architecture-baseline.json"
    _write_baseline(baseline_path, payload)

    with pytest.raises(
        architecture_contract.ArchitectureContractError,
        match="entry_exit_modules must be exactly",
    ):
        architecture_contract.load_architecture_baseline(baseline_path)


def test_baseline_rejects_missing_cli_entry(architecture_contract, tmp_path: Path):
    """entry_exit_modules should fail when the fixed CLI entry is not present."""
    payload = _valid_payload(architecture_contract)
    payload["entry_exit_modules"] = ["src/jfin/config.py"]
    baseline_path = tmp_path / "project" / "architecture-baseline.json"
    _write_baseline(baseline_path, payload)

    with pytest.raises(
        architecture_contract.ArchitectureContractError,
        match="entry_exit_modules must be exactly",
    ):
        architecture_contract.load_architecture_baseline(baseline_path)


def test_baseline_rejects_negative_counter_values(
    architecture_contract, tmp_path: Path
):
    """Counters must be non-negative integers."""
    payload = _valid_payload(architecture_contract)
    payload["non_entry_exit_allowlist"] = {
        "src/jfin/config.py": {
            "sys_exit_calls": -1,
            "system_exit_raises": 0,
            "sys_import_exit_calls": 0,
            "builtins_exit_calls": 0,
        }
    }
    baseline_path = tmp_path / "project" / "architecture-baseline.json"
    _write_baseline(baseline_path, payload)

    with pytest.raises(
        architecture_contract.ArchitectureContractError,
        match="non-negative integer",
    ):
        architecture_contract.load_architecture_baseline(baseline_path)


def test_baseline_rejects_unknown_counter_keys(architecture_contract, tmp_path: Path):
    """Counter mappings should fail when unexpected keys are present."""
    payload = _valid_payload(architecture_contract)
    payload["non_entry_exit_allowlist"] = {
        "src/jfin/config.py": {
            "sys_exit_calls": 0,
            "system_exit_raises": 0,
            "sys_import_exit_calls": 0,
            "builtins_exit_calls": 0,
            "unknown_counter": 1,
        }
    }
    baseline_path = tmp_path / "project" / "architecture-baseline.json"
    _write_baseline(baseline_path, payload)

    with pytest.raises(
        architecture_contract.ArchitectureContractError,
        match="unknown keys",
    ):
        architecture_contract.load_architecture_baseline(baseline_path)
