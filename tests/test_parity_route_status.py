"""Route-fence parity-status schema tests for parity governance checks."""

from __future__ import annotations

import json
from pathlib import Path

from tests.test_parity_checks import _write_file, _write_valid_artifacts

pytest_plugins = ("tests.test_parity_checks",)


def test_parity_check_fails_on_invalid_route_fence_parity_status_markdown(
    parity_modules,
    tmp_path: Path,
):
    """Parity checks should reject route-fence rows outside pending|ready."""
    parity_contract, parity_checks = parity_modules
    _parity_path, route_path = _write_valid_artifacts(tmp_path, parity_contract)

    route_rows = [
        {
            "command": command,
            "mode": mode,
            "route(v0|v1)": "v0",
            "owner slice": "WI-00X",
            "parity status": "pending",
        }
        for command, mode in parity_contract.REQUIRED_ROUTE_ROWS
    ]
    route_rows[0]["parity status"] = "review"
    route_table_body = (
        "| command | mode | route(v0\\|v1) | owner slice | parity status |\n"
        "| --- | --- | --- | --- | --- |\n"
        + "\n".join(
            f"| {row['command']} | {row['mode'].replace('|', '\\|')} | "
            f"{row['route(v0|v1)']} | {row['owner slice']} | {row['parity status']} |"
            for row in route_rows
        )
        + "\n"
    )
    route_table = (
        f"{parity_contract.ROUTE_FENCE_MARKER_START}\n"
        f"{route_table_body}"
        f"{parity_contract.ROUTE_FENCE_MARKER_END}\n"
    )
    _write_file(route_path, route_table)

    result = parity_checks.check_parity_artifacts(tmp_path)
    assert any("invalid parity status" in error for error in result.errors)


def test_parity_check_fails_on_invalid_route_fence_parity_status_json(
    parity_modules,
    tmp_path: Path,
):
    """Parity checks should reject route-fence JSON parity_status outside pending|ready."""
    parity_contract, parity_checks = parity_modules
    _write_valid_artifacts(tmp_path, parity_contract)
    route_json_path = tmp_path / "project" / "route-fence.json"
    payload = json.loads(route_json_path.read_text(encoding="utf-8"))
    payload["rows"][0]["parity_status"] = "review"
    _write_file(route_json_path, json.dumps(payload, indent=2) + "\n")

    result = parity_checks.check_parity_artifacts(tmp_path)
    assert any("invalid parity_status" in error for error in result.errors)
