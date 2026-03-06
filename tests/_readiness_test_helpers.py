"""Shared helpers for COV-03 readiness governance tests."""

from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

import pytest

from tests.test_characterization_checks import (
    _render_table,
    _write_file,
    _write_valid_artifacts,
)

pytest_plugins = ("tests.test_characterization_checks",)

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = ROOT / "project" / "scripts"


@pytest.fixture(scope="module")
def readiness_modules(characterization_modules):
    """Load readiness and parity modules from project/scripts."""
    if str(SCRIPTS_DIR) not in sys.path:
        sys.path.insert(0, str(SCRIPTS_DIR))

    for module_name in ("readiness_checks", "parity_checks"):
        if module_name in sys.modules:
            del sys.modules[module_name]

    readiness_checks = importlib.import_module("readiness_checks")
    parity_checks = importlib.import_module("parity_checks")
    return (*characterization_modules, readiness_checks, parity_checks)


def sync_route_fence_json(repo_root: Path, parity_contract) -> None:
    """Rebuild route-fence JSON from canonical markdown rows."""
    table = parity_contract.load_marked_route_fence_table(
        repo_root / "project/route-fence.md"
    )
    payload = {
        "version": parity_contract.ROUTE_FENCE_JSON_VERSION,
        "rows": [
            {
                "command": row["command"].strip(),
                "mode": row["mode"].strip(),
                "route": row["route(v0|v1)"].strip().lower(),
                "owner_slice": row["owner slice"].strip(),
                "parity_status": row["parity status"].strip(),
            }
            for row in table.rows
        ],
    }
    _write_file(
        repo_root / "project/route-fence.json",
        json.dumps(payload, indent=2) + "\n",
    )


def set_route_row(
    repo_root: Path,
    parity_contract,
    *,
    command: str,
    mode: str,
    route: str | None = None,
    parity_status: str | None = None,
) -> None:
    """Update one route-fence row in markdown and keep JSON synchronized."""
    table = parity_contract.load_marked_route_fence_table(
        repo_root / "project/route-fence.md"
    )
    for row in table.rows:
        if row["command"] == command and row["mode"] == mode:
            if route is not None:
                row["route(v0|v1)"] = route
            if parity_status is not None:
                row["parity status"] = parity_status
            break
    else:  # pragma: no cover - helper guard
        raise AssertionError(f"route row not found: {command}|{mode}")

    route_table_body = _render_table(
        parity_contract.REQUIRED_ROUTE_FENCE_COLUMNS, table.rows
    )
    route_table = (
        f"{parity_contract.ROUTE_FENCE_MARKER_START}\n"
        f"{route_table_body}"
        f"{parity_contract.ROUTE_FENCE_MARKER_END}\n"
    )
    _write_file(repo_root / "project/route-fence.md", route_table)
    sync_route_fence_json(repo_root, parity_contract)


def set_workflow_cell(
    repo_root: Path,
    *,
    parity_ids: list[str] | None = None,
    owner_tests: list[str] | None = None,
    debt_status: str | None = None,
) -> None:
    """Patch run|backdrop workflow index fields used by readiness checks."""
    workflow_path = repo_root / "project/workflow-coverage-index.json"
    payload = json.loads(workflow_path.read_text(encoding="utf-8"))
    cell = payload["cells"]["run|backdrop"]
    if parity_ids is not None:
        cell["required_parity_ids"] = parity_ids
    if owner_tests is not None:
        cell["required_owner_tests"] = owner_tests
    if debt_status is not None:
        cell["future_split_debt"]["status"] = debt_status
    _write_file(workflow_path, json.dumps(payload, indent=2) + "\n")


def set_parity_row(
    repo_root: Path, parity_contract, behavior_id: str, **updates: str
) -> None:
    """Patch one parity row and persist parity-matrix markdown."""
    parity_path = repo_root / "project/parity-matrix.md"
    table = parity_contract.load_markdown_table(
        parity_path,
        parity_contract.REQUIRED_PARITY_COLUMNS,
        "parity-matrix",
    )
    for row in table.rows:
        if row["behavior_id"] == behavior_id:
            for key, value in updates.items():
                row[key] = value
            break
    else:  # pragma: no cover - helper guard
        raise AssertionError(f"parity row not found: {behavior_id}")

    _write_file(
        repo_root / "project/parity-matrix.md", _render_table(table.columns, table.rows)
    )


def runtime_report(
    characterization_checks,
    *,
    mapped_parity_ids: tuple[str, ...] = ("PIPE-BACKDROP-001",),
    diagnostics: tuple | None = None,
):
    """Build a deterministic runtime gate report for monkeypatching."""
    runtime_diagnostics = diagnostics or ()
    return characterization_checks.RuntimeGateReport(
        configured_targets=("tests/characterization/safety_contract",),
        checked_targets=1,
        passed_targets=1,
        failed_targets=0,
        budget_seconds=180,
        elapsed_seconds=1.0,
        mapped_parity_ids=mapped_parity_ids,
        infos=(),
        diagnostics=runtime_diagnostics,
    )


def setup_readiness_repo(readiness_modules, tmp_path: Path):
    """Create a fully valid temporary repo for readiness tests."""
    (
        characterization_contract,
        _characterization_checks,
        parity_contract,
        readiness_checks,
        _,
    ) = readiness_modules
    repo_root, _cli_baseline_path, _parity_path = _write_valid_artifacts(
        tmp_path,
        characterization_contract,
        parity_contract,
    )
    sync_route_fence_json(repo_root, parity_contract)
    return repo_root, parity_contract, readiness_checks
