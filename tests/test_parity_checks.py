"""Unit tests for parity and route-fence governance validation."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = ROOT / "project" / "scripts"


@pytest.fixture(scope="module")
def parity_modules():
    """Load parity modules from project/scripts for isolated unit testing."""
    if str(SCRIPTS_DIR) not in sys.path:
        sys.path.insert(0, str(SCRIPTS_DIR))

    for module_name in ("parity_contract", "parity_checks"):
        if module_name in sys.modules:
            del sys.modules[module_name]

    parity_contract = importlib.import_module("parity_contract")
    parity_checks = importlib.import_module("parity_checks")
    return parity_contract, parity_checks


def _escape_cell(value: str) -> str:
    """Escape table cell delimiters for markdown serialization."""
    return value.replace("|", "\\|")


def _render_table(columns: list[str], rows: list[dict[str, str]]) -> str:
    """Render a markdown table with deterministic column order."""
    escaped_columns = [_escape_cell(column) for column in columns]
    lines = [
        "| " + " | ".join(escaped_columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]
    for row in rows:
        line_cells = [_escape_cell(row.get(column, "")) for column in columns]
        lines.append("| " + " | ".join(line_cells) + " |")
    return "\n".join(lines) + "\n"


def _write_file(path: Path, content: str) -> None:
    """Write UTF-8 content to a temporary file path for tests."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _build_valid_parity_rows(parity_contract) -> list[dict[str, str]]:
    """Build a valid starter parity row set from required behavior IDs."""
    return [
        {
            "behavior_id": behavior_id,
            "baseline_source": "tests-baseline",
            "current_result": "matches-baseline",
            "status": "preserved",
            "owner_test": f"tests/owner::{behavior_id.lower()}",
            "approval_ref": "n/a",
            "notes": "seed",
            "migration_note": "-",
        }
        for behavior_id in parity_contract.REQUIRED_BEHAVIOR_IDS
    ]


def _build_valid_route_rows(parity_contract) -> list[dict[str, str]]:
    """Build valid route-fence rows from required command/mode pairs."""
    return [
        {
            "command": command,
            "mode": mode,
            "route(v0|v1)": "v0",
            "owner slice": "WI-00X",
            "parity status": "pending",
        }
        for command, mode in parity_contract.REQUIRED_ROUTE_ROWS
    ]


def _write_valid_artifacts(tmp_path: Path, parity_contract) -> tuple[Path, Path]:
    """Write valid parity and route-fence markdown files under a temp repo root."""
    parity_rows = _build_valid_parity_rows(parity_contract)
    route_rows = _build_valid_route_rows(parity_contract)

    parity_table = _render_table(parity_contract.REQUIRED_PARITY_COLUMNS, parity_rows)
    route_table = _render_table(
        parity_contract.REQUIRED_ROUTE_FENCE_COLUMNS,
        route_rows,
    )

    parity_path = tmp_path / "project" / "parity-matrix.md"
    route_path = tmp_path / "project" / "route-fence.md"
    _write_file(parity_path, parity_table)
    _write_file(route_path, route_table)
    return parity_path, route_path


def test_parity_and_route_fence_valid_pass(parity_modules, tmp_path: Path):
    """Valid parity matrix and route-fence artifacts should pass checks."""
    parity_contract, parity_checks = parity_modules
    _write_valid_artifacts(tmp_path, parity_contract)

    result = parity_checks.check_parity_artifacts(tmp_path)
    assert not result.errors
    assert not result.warnings


def test_parity_fails_when_required_column_missing(parity_modules, tmp_path: Path):
    """Parity validation should fail when a required column is absent."""
    parity_contract, parity_checks = parity_modules
    _write_valid_artifacts(tmp_path, parity_contract)

    columns = [
        column
        for column in parity_contract.REQUIRED_PARITY_COLUMNS
        if column != "approval_ref"
    ]
    parity_rows = _build_valid_parity_rows(parity_contract)
    parity_table = _render_table(columns, parity_rows)
    _write_file(tmp_path / "project" / "parity-matrix.md", parity_table)

    result = parity_checks.check_parity_artifacts(tmp_path)
    assert any("required header not found" in error for error in result.errors)


def test_parity_fails_on_invalid_status(parity_modules, tmp_path: Path):
    """Parity validation should fail for unknown status values."""
    parity_contract, parity_checks = parity_modules
    parity_path, _ = _write_valid_artifacts(tmp_path, parity_contract)

    parity_rows = _build_valid_parity_rows(parity_contract)
    parity_rows[0]["status"] = "unknown"
    parity_table = _render_table(parity_contract.REQUIRED_PARITY_COLUMNS, parity_rows)
    _write_file(parity_path, parity_table)

    result = parity_checks.check_parity_artifacts(tmp_path)
    assert any("invalid status" in error for error in result.errors)


def test_parity_fails_when_changed_row_has_placeholder_approval_ref(
    parity_modules,
    tmp_path: Path,
):
    """Changed rows must provide non-placeholder approval references."""
    parity_contract, parity_checks = parity_modules
    parity_path, _ = _write_valid_artifacts(tmp_path, parity_contract)

    parity_rows = _build_valid_parity_rows(parity_contract)
    parity_rows[0]["status"] = "changed"
    parity_rows[0]["approval_ref"] = "n/a"
    parity_table = _render_table(parity_contract.REQUIRED_PARITY_COLUMNS, parity_rows)
    _write_file(parity_path, parity_table)

    result = parity_checks.check_parity_artifacts(tmp_path)
    assert any(
        "requires non-placeholder approval_ref" in error for error in result.errors
    )


def test_parity_fails_on_duplicate_behavior_id(parity_modules, tmp_path: Path):
    """Behavior IDs must be unique across parity matrix rows."""
    parity_contract, parity_checks = parity_modules
    parity_path, _ = _write_valid_artifacts(tmp_path, parity_contract)

    parity_rows = _build_valid_parity_rows(parity_contract)
    parity_rows[1]["behavior_id"] = parity_rows[0]["behavior_id"]
    parity_table = _render_table(parity_contract.REQUIRED_PARITY_COLUMNS, parity_rows)
    _write_file(parity_path, parity_table)

    result = parity_checks.check_parity_artifacts(tmp_path)
    assert any("duplicate behavior_id" in error for error in result.errors)


def test_parity_fails_when_required_behavior_id_missing(parity_modules, tmp_path: Path):
    """All required starter behavior IDs must be present in the matrix."""
    parity_contract, parity_checks = parity_modules
    parity_path, _ = _write_valid_artifacts(tmp_path, parity_contract)

    parity_rows = _build_valid_parity_rows(parity_contract)
    parity_rows = parity_rows[1:]
    parity_table = _render_table(parity_contract.REQUIRED_PARITY_COLUMNS, parity_rows)
    _write_file(parity_path, parity_table)

    result = parity_checks.check_parity_artifacts(tmp_path)
    assert any(
        "missing required starter behavior IDs" in error for error in result.errors
    )


def test_route_fence_fails_when_required_row_missing(parity_modules, tmp_path: Path):
    """Route-fence validation should fail if required command/mode rows are missing."""
    parity_contract, parity_checks = parity_modules
    _, route_path = _write_valid_artifacts(tmp_path, parity_contract)

    route_rows = _build_valid_route_rows(parity_contract)
    route_rows = route_rows[:-1]
    route_table = _render_table(
        parity_contract.REQUIRED_ROUTE_FENCE_COLUMNS,
        route_rows,
    )
    _write_file(route_path, route_table)

    result = parity_checks.check_parity_artifacts(tmp_path)
    assert any("missing required command/mode rows" in error for error in result.errors)


def test_route_fence_fails_on_invalid_route_value(parity_modules, tmp_path: Path):
    """Route-fence rows must use route values restricted to v0 or v1."""
    parity_contract, parity_checks = parity_modules
    _, route_path = _write_valid_artifacts(tmp_path, parity_contract)

    route_rows = _build_valid_route_rows(parity_contract)
    route_rows[0]["route(v0|v1)"] = "legacy"
    route_table = _render_table(
        parity_contract.REQUIRED_ROUTE_FENCE_COLUMNS,
        route_rows,
    )
    _write_file(route_path, route_table)

    result = parity_checks.check_parity_artifacts(tmp_path)
    assert any("invalid route(v0|v1)" in error for error in result.errors)
