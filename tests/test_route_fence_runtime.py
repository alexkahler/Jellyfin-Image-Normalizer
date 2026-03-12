"""Unit tests for runtime route-fence loading and CLI fail-closed gating."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from jfin import cli as cli_module
from jfin import route_fence


def test_discover_repo_root_from_nested_path(tmp_path: Path):
    """Repo-root discovery should walk upward until route-fence artifacts are found."""
    repo_root = tmp_path / "repo"
    nested_dir = repo_root / "a" / "b" / "c"
    nested_dir.mkdir(parents=True)
    (repo_root / "project").mkdir(parents=True)
    (repo_root / "project" / "route-fence.md").write_text(
        "# Route Fence\n", encoding="utf-8"
    )

    discovered = route_fence._discover_repo_root(  # noqa: SLF001
        start_path=nested_dir / "route_fence.py",
        max_depth=10,
    )
    assert discovered == repo_root


def test_discover_repo_root_fails_when_artifacts_absent(tmp_path: Path):
    """Repo-root discovery should fail clearly if artifacts are not present."""
    start_path = tmp_path / "x" / "y" / "z" / "route_fence.py"
    start_path.parent.mkdir(parents=True)

    with pytest.raises(route_fence.RouteFenceError, match="unable to locate repo root"):
        route_fence._discover_repo_root(  # noqa: SLF001
            start_path=start_path,
            max_depth=3,
        )


def test_load_route_table_fails_when_json_missing(tmp_path: Path, monkeypatch):
    """load_route_table should fail closed when JSON artifact is missing."""
    repo_root = tmp_path / "repo"
    (repo_root / "project").mkdir(parents=True)
    (repo_root / "project" / "route-fence.md").write_text(
        "# Route Fence\n", encoding="utf-8"
    )
    monkeypatch.setattr(route_fence, "_discover_repo_root", lambda **_: repo_root)

    with pytest.raises(route_fence.RouteFenceError, match="JSON not found"):
        route_fence.load_route_table()


def test_load_route_table_fails_on_invalid_json(tmp_path: Path, monkeypatch):
    """load_route_table should fail closed on malformed JSON content."""
    repo_root = tmp_path / "repo"
    project_dir = repo_root / "project"
    project_dir.mkdir(parents=True)
    (project_dir / "route-fence.json").write_text("{invalid", encoding="utf-8")
    monkeypatch.setattr(route_fence, "_discover_repo_root", lambda **_: repo_root)

    with pytest.raises(route_fence.RouteFenceError, match="JSON decode failed"):
        route_fence.load_route_table()


def test_load_route_table_fails_on_unknown_route_value(tmp_path: Path, monkeypatch):
    """load_route_table should fail when row route value is not v0|v1."""
    repo_root = tmp_path / "repo"
    project_dir = repo_root / "project"
    project_dir.mkdir(parents=True)
    payload = {
        "version": route_fence.ROUTE_FENCE_JSON_VERSION,
        "rows": [
            {
                "command": "run",
                "mode": "logo",
                "route": "legacy",
                "owner_slice": "WI-00X",
                "parity_status": "pending",
            }
        ],
    }
    (project_dir / "route-fence.json").write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(route_fence, "_discover_repo_root", lambda **_: repo_root)

    with pytest.raises(route_fence.RouteFenceError, match="invalid route"):
        route_fence.load_route_table()


def test_runtime_gated_keys_are_covered_by_route_table():
    """Every runtime-gated entrypoint key must exist in route-fence JSON."""
    mapping = route_fence.load_route_table()
    missing_keys = sorted(route_fence.RUNTIME_GATED_ROUTE_KEYS - set(mapping))
    assert missing_keys == []


def test_generate_config_succeeds_when_route_fence_is_v0(tmp_path: Path, monkeypatch):
    """CLI should allow --generate-config when route resolves to v0."""
    config_path = tmp_path / "generated.toml"
    monkeypatch.setattr(cli_module, "resolve_route", lambda _command, _mode: "v0")
    monkeypatch.setattr(
        sys,
        "argv",
        ["jfin", "--generate-config", "--config", str(config_path)],
    )

    with pytest.raises(SystemExit) as exc:
        cli_module.main()

    assert exc.value.code == 0
    assert config_path.exists()


def test_generate_config_fails_closed_when_route_resolution_errors(
    tmp_path: Path, monkeypatch
):
    """CLI should fail closed with validation-class exit code when route lookup fails."""
    config_path = tmp_path / "generated.toml"

    def _raise_route_error(_command: str, _mode: str) -> str:
        raise route_fence.RouteFenceError(
            "route-fence JSON not found: project/route-fence.json"
        )

    monkeypatch.setattr(cli_module, "resolve_route", _raise_route_error)
    monkeypatch.setattr(
        sys,
        "argv",
        ["jfin", "--generate-config", "--config", str(config_path)],
    )

    with pytest.raises(SystemExit) as exc:
        cli_module.main()

    assert exc.value.code == 1
    assert not config_path.exists()


def test_generate_config_succeeds_when_route_declares_v1_for_config_init(
    tmp_path: Path, monkeypatch
):
    """CLI should allow --generate-config when config_init route resolves to v1."""
    config_path = tmp_path / "generated.toml"
    monkeypatch.setattr(cli_module, "resolve_route", lambda _command, _mode: "v1")
    monkeypatch.setattr(
        sys,
        "argv",
        ["jfin", "--generate-config", "--config", str(config_path)],
    )

    with pytest.raises(SystemExit) as exc:
        cli_module.main()

    assert exc.value.code == 0
    assert config_path.exists()


def test_enforce_route_fails_closed_for_unimplemented_v1_key(monkeypatch):
    """_enforce_route should still fail closed for v1 keys without runtime support."""
    monkeypatch.setattr(cli_module, "resolve_route", lambda _command, _mode: "v1")
    monkeypatch.setattr(
        cli_module,
        "route_fence_json_path",
        lambda: Path("project/route-fence.json"),
    )

    with pytest.raises(SystemExit) as exc:
        cli_module._enforce_route("run", "logo")

    assert exc.value.code == 1
