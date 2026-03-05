"""Unit tests for route-fence markdown -> JSON generator/check flow."""

from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = ROOT / "project" / "scripts"


@pytest.fixture(scope="module")
def route_fence_modules():
    """Load route-fence generator and contract modules from project/scripts."""
    if str(SCRIPTS_DIR) not in sys.path:
        sys.path.insert(0, str(SCRIPTS_DIR))

    for module_name in ("parity_contract", "generate_route_fence_json"):
        if module_name in sys.modules:
            del sys.modules[module_name]

    parity_contract = importlib.import_module("parity_contract")
    generator = importlib.import_module("generate_route_fence_json")
    return parity_contract, generator


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _route_fence_markdown(parity_contract, route_rows: list[str]) -> str:
    header = "| command | mode | route(v0\\|v1) | owner slice | parity status |"
    separator = "| --- | --- | --- | --- | --- |"
    body = "\n".join(route_rows)
    return (
        "# Route Fence\n\n"
        f"{parity_contract.ROUTE_FENCE_MARKER_START}\n"
        f"{header}\n"
        f"{separator}\n"
        f"{body}\n"
        f"{parity_contract.ROUTE_FENCE_MARKER_END}\n"
    )


def _default_route_rows() -> list[str]:
    return [
        "| run | logo | v0 | WI-00X | pending |",
        "| run | thumb | v0 | WI-00X | pending |",
        "| run | backdrop | v0 | WI-00X | pending |",
        "| run | profile | v0 | WI-00X | pending |",
        "| restore | logo\\|thumb\\|backdrop\\|profile | v0 | WI-00X | pending |",
        "| test_connection | n/a | v0 | WI-00X | pending |",
        "| config_init | n/a | v0 | WI-00X | pending |",
        "| config_validate | n/a | v0 | WI-00X | pending |",
    ]


def test_generator_payload_is_deterministic(route_fence_modules, tmp_path: Path):
    """Repeated payload generation from same markdown should be deterministic."""
    parity_contract, generator = route_fence_modules
    route_fence_path = tmp_path / "project" / "route-fence.md"
    _write(
        route_fence_path, _route_fence_markdown(parity_contract, _default_route_rows())
    )

    first_payload = generator.build_route_fence_payload(route_fence_path)
    second_payload = generator.build_route_fence_payload(route_fence_path)
    assert first_payload == second_payload

    rendered = generator.render_route_fence_json(first_payload)
    assert rendered.endswith("\n")
    assert json.loads(rendered)["version"] == parity_contract.ROUTE_FENCE_JSON_VERSION


def test_generator_check_fails_on_missing_json(route_fence_modules, tmp_path: Path):
    """--check flow should fail when route-fence.json does not exist."""
    parity_contract, generator = route_fence_modules
    route_fence_path = tmp_path / "project" / "route-fence.md"
    route_fence_json_path = tmp_path / "project" / "route-fence.json"
    _write(
        route_fence_path, _route_fence_markdown(parity_contract, _default_route_rows())
    )

    ok, message = generator._check_route_fence_json_sync(  # noqa: SLF001
        route_fence_path, route_fence_json_path
    )
    assert not ok
    assert "Missing route-fence JSON artifact" in message


def test_generator_check_fails_on_row_mismatch(route_fence_modules, tmp_path: Path):
    """--check flow should fail when JSON rows drift from markdown rows."""
    parity_contract, generator = route_fence_modules
    route_fence_path = tmp_path / "project" / "route-fence.md"
    route_fence_json_path = tmp_path / "project" / "route-fence.json"
    _write(
        route_fence_path, _route_fence_markdown(parity_contract, _default_route_rows())
    )
    payload = generator.build_route_fence_payload(route_fence_path)
    payload["rows"][0]["route"] = "v1"
    _write(route_fence_json_path, json.dumps(payload, indent=2) + "\n")

    ok, message = generator._check_route_fence_json_sync(  # noqa: SLF001
        route_fence_path, route_fence_json_path
    )
    assert not ok
    assert "route-fence JSON drift detected" in message


def test_generator_fails_when_markers_missing(route_fence_modules, tmp_path: Path):
    """Generator should fail when canonical marker block is removed."""
    parity_contract, generator = route_fence_modules
    route_fence_path = tmp_path / "project" / "route-fence.md"
    _write(
        route_fence_path,
        (
            "# Route Fence\n\n"
            "| command | mode | route(v0\\|v1) | owner slice | parity status |\n"
            "| --- | --- | --- | --- | --- |\n"
            "| run | logo | v0 | WI-00X | pending |\n"
        ),
    )

    with pytest.raises(parity_contract.ParityContractError, match="start marker"):
        generator.build_route_fence_payload(route_fence_path)


def test_generator_fails_when_header_drifts(route_fence_modules, tmp_path: Path):
    """Generator should fail if canonical route-fence headers drift."""
    parity_contract, generator = route_fence_modules
    route_fence_path = tmp_path / "project" / "route-fence.md"
    _write(
        route_fence_path,
        (
            "# Route Fence\n\n"
            f"{parity_contract.ROUTE_FENCE_MARKER_START}\n"
            "| command | mode | route | owner slice | parity status |\n"
            "| --- | --- | --- | --- | --- |\n"
            "| run | logo | v0 | WI-00X | pending |\n"
            f"{parity_contract.ROUTE_FENCE_MARKER_END}\n"
        ),
    )

    with pytest.raises(
        parity_contract.ParityContractError, match="required header not found"
    ):
        generator.build_route_fence_payload(route_fence_path)
