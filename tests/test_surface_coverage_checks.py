"""Unit tests for surface coverage governance checks."""

from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = ROOT / "project" / "scripts"

PARITY_COLUMNS = [
    "behavior_id",
    "baseline_source",
    "current_result",
    "status",
    "owner_test",
    "approval_ref",
    "notes",
    "migration_note",
]


@pytest.fixture(scope="module")
def surface_module():
    if str(SCRIPTS_DIR) not in sys.path:
        sys.path.insert(0, str(SCRIPTS_DIR))
    for module_name in ("surface_coverage_checks",):
        if module_name in sys.modules:
            del sys.modules[module_name]
    return importlib.import_module("surface_coverage_checks")


def _write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _render_parity_table(rows: list[dict[str, str]]) -> str:
    lines = [
        "| " + " | ".join(PARITY_COLUMNS) + " |",
        "| " + " | ".join(["---"] * len(PARITY_COLUMNS)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(row[column] for column in PARITY_COLUMNS) + " |")
    return "\n".join(lines) + "\n"


def _seed_repo(tmp_path: Path) -> dict[str, list[str]]:
    _write_file(tmp_path / "src/jfin/__init__.py", "")
    _write_file(
        tmp_path / "src/jfin/__main__.py",
        "from .cli import parse_args\n\nif __name__ == '__main__':\n    parse_args()\n",
    )
    _write_file(
        tmp_path / "src/jfin/cli.py",
        """
import argparse


def parse_args():
    parser = argparse.ArgumentParser(description="demo")
    parser.add_argument("--config", help="Path to config (default: config.toml in repo root).")
    parser.add_argument("--mode", help="Mode values include logo|thumb.")
    parser.add_argument("--silent", "-s", action="store_true", help="silent mode")
    return parser.parse_args()
""",
    )
    _write_file(
        tmp_path / "config.example.toml",
        """
[server]
jf_url = "https://demo"

[logging]
silent = true
""",
    )
    _write_file(
        tmp_path / "docs/TECHNICAL_NOTES.md",
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
    _write_file(tmp_path / "tests/proof.py", "def test_proof():\n    assert True\n")
    _write_file(
        tmp_path / "project/parity-matrix.md",
        _render_parity_table(
            [
                {
                    "behavior_id": "CLI-TEST",
                    "baseline_source": "tests/proof.py#CLI-TEST",
                    "current_result": "matches-baseline",
                    "status": "preserved",
                    "owner_test": "tests/proof.py::test_proof",
                    "approval_ref": "n/a",
                    "notes": "seed",
                    "migration_note": "-",
                },
                {
                    "behavior_id": "CFG-TEST",
                    "baseline_source": "tests/proof.py#CFG-TEST",
                    "current_result": "matches-baseline",
                    "status": "preserved",
                    "owner_test": "tests/proof.py::test_proof",
                    "approval_ref": "n/a",
                    "notes": "seed",
                    "migration_note": "-",
                },
                {
                    "behavior_id": "OBS-TEST",
                    "baseline_source": "tests/proof.py#OBS-TEST",
                    "current_result": "matches-baseline",
                    "status": "preserved",
                    "owner_test": "tests/proof.py::test_proof",
                    "approval_ref": "n/a",
                    "notes": "seed",
                    "migration_note": "-",
                },
            ]
        ),
    )

    return {
        "cli_ids": [
            "cli.root.command",
            "cli.root.option.-h",
            "cli.root.option.--help",
            "cli.root.option.--config",
            "cli.root.option.--mode",
            "cli.root.option.--silent",
            "cli.root.option.-s",
            "cli.root.mode.logo",
            "cli.root.mode.thumb",
        ],
        "cfg_ids": ["config.server.jf_url", "config.logging.silent"],
        "obs_ids": [
            "obs.summary.counters",
            "obs.summary.failure_list",
            "obs.summary.warning_error_presence",
            "obs.summary.scale_decision_reporting",
            "obs.exit_codes.major_classes",
        ],
    }


def _build_valid_index(detected_ids: dict[str, list[str]]) -> dict[str, object]:
    cli_items: list[dict[str, object]] = []
    for item_id in detected_ids["cli_ids"]:
        source_token = item_id.split(".")[-1]
        out_of_scope = item_id in {"cli.root.option.-h", "cli.root.option.--help"}
        cli_items.append(
            {
                "id": item_id,
                "command_path": "root",
                "source_token": source_token,
                "default_text": "config.toml in repo root"
                if item_id == "cli.root.option.--config"
                else "",
                "parity_ids": [] if out_of_scope else ["CLI-TEST"],
                "owner_tests": [] if out_of_scope else ["tests/proof.py::test_proof"],
                "out_of_scope": out_of_scope,
                "out_of_scope_reason": "help alias presentation only"
                if out_of_scope
                else "",
                "code_refs": ["src/jfin/cli.py:1"],
                "notes": "seed",
            }
        )

    cfg_items = [
        {
            "id": item_id,
            "parity_ids": ["CFG-TEST"],
            "owner_tests": ["tests/proof.py"],
            "out_of_scope": False,
            "out_of_scope_reason": "",
            "code_refs": ["config.example.toml:1"],
            "notes": "seed",
        }
        for item_id in detected_ids["cfg_ids"]
    ]
    obs_items = [
        {
            "id": item_id,
            "parity_ids": ["OBS-TEST"],
            "owner_tests": ["tests/proof.py::test_proof"],
            "out_of_scope": False,
            "out_of_scope_reason": "",
            "code_refs": ["docs/TECHNICAL_NOTES.md:1"],
            "notes": "seed",
        }
        for item_id in detected_ids["obs_ids"]
    ]
    return {
        "version": 1,
        "cli_items": cli_items,
        "config_items": cfg_items,
        "observability_items": obs_items,
    }


def test_surface_coverage_valid_pass(surface_module, tmp_path: Path):
    detected_ids = _seed_repo(tmp_path)
    index = _build_valid_index(detected_ids)
    _write_file(
        tmp_path / "project/surface-coverage-index.json",
        json.dumps(index, indent=2) + "\n",
    )

    report = surface_module.check_surface_coverage_artifacts(tmp_path)
    assert not report.result.errors
    assert report.unmapped_cli_items == 0
    assert report.unmapped_config_keys == 0
    assert report.unmapped_observability_items == 0
    assert report.parity_test_linkage_gaps == 0


def test_surface_coverage_fails_when_cli_item_missing(surface_module, tmp_path: Path):
    detected_ids = _seed_repo(tmp_path)
    index = _build_valid_index(detected_ids)
    index["cli_items"] = [
        item for item in index["cli_items"] if item["id"] != "cli.root.option.--mode"
    ]
    _write_file(
        tmp_path / "project/surface-coverage-index.json",
        json.dumps(index, indent=2) + "\n",
    )

    report = surface_module.check_surface_coverage_artifacts(tmp_path)
    assert any("missing CLI mappings" in error for error in report.result.errors)
    assert report.unmapped_cli_items == 1


def test_surface_coverage_fails_on_invalid_owner_symbol(surface_module, tmp_path: Path):
    detected_ids = _seed_repo(tmp_path)
    index = _build_valid_index(detected_ids)
    first_cfg = index["config_items"][0]
    first_cfg["owner_tests"] = ["tests/proof.py::missing_symbol"]
    _write_file(
        tmp_path / "project/surface-coverage-index.json",
        json.dumps(index, indent=2) + "\n",
    )

    report = surface_module.check_surface_coverage_artifacts(tmp_path)
    assert any(
        "owner_test symbol 'missing_symbol'" in error for error in report.result.errors
    )
    assert report.parity_test_linkage_gaps == 1


def test_surface_coverage_fails_when_out_of_scope_contract_is_invalid(
    surface_module,
    tmp_path: Path,
):
    detected_ids = _seed_repo(tmp_path)
    index = _build_valid_index(detected_ids)
    first_cli = index["cli_items"][0]
    first_cli["out_of_scope"] = True
    first_cli["out_of_scope_reason"] = "invalid tuple"
    _write_file(
        tmp_path / "project/surface-coverage-index.json",
        json.dumps(index, indent=2) + "\n",
    )

    report = surface_module.check_surface_coverage_artifacts(tmp_path)
    assert any(
        "out_of_scope=true requires empty parity_ids" in error
        for error in report.result.errors
    )
