"""Unit tests for WI-001 architecture governance checks."""

from __future__ import annotations

import importlib
import json
import sys
import textwrap
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = ROOT / "project" / "scripts"


@pytest.fixture(scope="module")
def architecture_modules():
    if str(SCRIPTS_DIR) not in sys.path:
        sys.path.insert(0, str(SCRIPTS_DIR))

    for module_name in (
        "governance_contract",
        "architecture_contract",
        "architecture_checks",
    ):
        if module_name in sys.modules:
            del sys.modules[module_name]

    architecture_contract = importlib.import_module("architecture_contract")
    architecture_checks = importlib.import_module("architecture_checks")
    return architecture_contract, architecture_checks


def _write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).lstrip(), encoding="utf-8")


def _baseline_payload(
    architecture_contract,
    *,
    allowlist: dict[str, dict[str, int]] | None = None,
) -> dict[str, object]:
    return {
        "version": architecture_contract.BASELINE_VERSION,
        "v1_root": architecture_contract.V1_ROOT,
        "entry_exit_modules": list(architecture_contract.DEFAULT_ENTRY_EXIT_MODULES),
        "non_entry_exit_allowlist": allowlist or {},
    }


def _write_baseline(repo_root: Path, payload: dict[str, object]) -> None:
    baseline_path = repo_root / "project" / "architecture-baseline.json"
    _write_file(baseline_path, json.dumps(payload, indent=2) + "\n")


def _build_minimal_repo(repo_root: Path) -> None:
    _write_file(
        repo_root / "src" / "jfin" / "cli.py",
        """
        import sys
        def main() -> int:
            return 0
        if __name__ == "__main__":
            sys.exit(main())
        """,
    )


def test_load_architecture_baseline_accepts_valid_payload(
    architecture_modules,
    tmp_path: Path,
):
    architecture_contract, _architecture_checks = architecture_modules
    _build_minimal_repo(tmp_path)
    _write_baseline(tmp_path, _baseline_payload(architecture_contract))

    baseline = architecture_contract.load_architecture_baseline(
        tmp_path / "project" / "architecture-baseline.json"
    )
    assert baseline.version == architecture_contract.BASELINE_VERSION
    assert baseline.v1_root == architecture_contract.V1_ROOT
    assert (
        baseline.entry_exit_modules == architecture_contract.DEFAULT_ENTRY_EXIT_MODULES
    )
    assert baseline.non_entry_exit_allowlist == {}


def test_load_architecture_baseline_rejects_missing_required_key(
    architecture_modules,
    tmp_path: Path,
):
    architecture_contract, _architecture_checks = architecture_modules
    payload = _baseline_payload(architecture_contract)
    payload.pop("non_entry_exit_allowlist")
    _write_baseline(tmp_path, payload)

    with pytest.raises(
        architecture_contract.ArchitectureContractError,
        match="non_entry_exit_allowlist",
    ):
        architecture_contract.load_architecture_baseline(
            tmp_path / "project" / "architecture-baseline.json"
        )


def test_exit_counter_detects_tracked_patterns(architecture_modules, tmp_path: Path):
    _architecture_contract, architecture_checks = architecture_modules
    file_path = tmp_path / "sample.py"
    _write_file(
        file_path,
        """
        import builtins
        import sys
        from sys import exit as sys_exit_alias
        def run() -> None:
            sys.exit(1)
            sys_exit_alias(2)
            builtins.exit()
            builtins.quit()
            raise SystemExit
            raise SystemExit(3)
        """,
    )

    counters = architecture_checks.count_exit_patterns_in_file(file_path)
    assert counters.sys_exit_calls == 1
    assert counters.sys_import_exit_calls == 1
    assert counters.builtins_exit_calls == 2
    assert counters.system_exit_raises == 2


def test_ratchet_fails_on_new_non_entry_exit_violation(
    architecture_modules,
    tmp_path: Path,
):
    architecture_contract, architecture_checks = architecture_modules
    _build_minimal_repo(tmp_path)
    _write_file(tmp_path / "src" / "jfin" / "config.py", "import sys\nsys.exit(1)\n")
    _write_baseline(tmp_path, _baseline_payload(architecture_contract))

    result = architecture_checks.check_non_entry_exit_ratchet(tmp_path)
    assert any("new non-entry exit violation" in error for error in result.errors)


def test_ratchet_fails_when_counter_exceeds_baseline(
    architecture_modules,
    tmp_path: Path,
):
    architecture_contract, architecture_checks = architecture_modules
    _build_minimal_repo(tmp_path)
    _write_file(
        tmp_path / "src" / "jfin" / "config.py",
        """
        import sys
        sys.exit(1)
        sys.exit(2)
        """,
    )
    _write_baseline(
        tmp_path,
        _baseline_payload(
            architecture_contract,
            allowlist={
                "src/jfin/config.py": {
                    "sys_exit_calls": 1,
                    "system_exit_raises": 0,
                    "sys_import_exit_calls": 0,
                    "builtins_exit_calls": 0,
                }
            },
        ),
    )

    result = architecture_checks.check_non_entry_exit_ratchet(tmp_path)
    assert any("exceeds baseline" in error for error in result.errors)


def test_ratchet_warns_when_counter_drops_below_baseline(
    architecture_modules,
    tmp_path: Path,
):
    architecture_contract, architecture_checks = architecture_modules
    _build_minimal_repo(tmp_path)
    _write_file(tmp_path / "src" / "jfin" / "config.py", "import sys\nsys.exit(1)\n")
    _write_baseline(
        tmp_path,
        _baseline_payload(
            architecture_contract,
            allowlist={
                "src/jfin/config.py": {
                    "sys_exit_calls": 2,
                    "system_exit_raises": 0,
                    "sys_import_exit_calls": 0,
                    "builtins_exit_calls": 0,
                }
            },
        ),
    )

    result = architecture_checks.check_non_entry_exit_ratchet(tmp_path)
    assert not result.errors
    assert any("dropped below baseline" in warning for warning in result.warnings)


def test_import_boundaries_pass_when_target_directories_are_absent(
    architecture_modules,
    tmp_path: Path,
):
    _architecture_contract, architecture_checks = architecture_modules
    _build_minimal_repo(tmp_path)

    result = architecture_checks.check_import_boundaries(tmp_path)
    assert not result.errors
    assert not result.warnings


def test_domain_import_boundary_blocks_forbidden_modules(
    architecture_modules,
    tmp_path: Path,
):
    _architecture_contract, architecture_checks = architecture_modules
    _build_minimal_repo(tmp_path)
    _write_file(tmp_path / "src" / "jfin" / "domain" / "rules.py", "import requests\n")

    result = architecture_checks.check_import_boundaries(tmp_path)
    assert any(
        "domain import boundary violation" in error and "requests" in error
        for error in result.errors
    )


def test_app_services_boundary_blocks_absolute_adapter_import(
    architecture_modules,
    tmp_path: Path,
):
    _architecture_contract, architecture_checks = architecture_modules
    _build_minimal_repo(tmp_path)
    _write_file(
        tmp_path / "src" / "jfin" / "app" / "services" / "service.py",
        "from jfin.adapters.http import Client\n",
    )

    result = architecture_checks.check_import_boundaries(tmp_path)
    assert any(
        "app/services import boundary violation" in error for error in result.errors
    )


def test_app_services_boundary_blocks_relative_adapter_import(
    architecture_modules,
    tmp_path: Path,
):
    _architecture_contract, architecture_checks = architecture_modules
    _build_minimal_repo(tmp_path)
    _write_file(
        tmp_path / "src" / "jfin" / "app" / "services" / "service.py",
        "from ...adapters.http import Client\n",
    )

    result = architecture_checks.check_import_boundaries(tmp_path)
    assert any(
        "app/services import boundary violation" in error for error in result.errors
    )


def test_rendered_baseline_uses_same_counting_logic_as_ratchet(
    architecture_modules,
    tmp_path: Path,
):
    architecture_contract, architecture_checks = architecture_modules
    _build_minimal_repo(tmp_path)
    _write_file(
        tmp_path / "src" / "jfin" / "config.py",
        """
        import builtins
        from sys import exit as sys_exit_alias
        sys_exit_alias(3)
        builtins.quit()
        raise SystemExit(1)
        """,
    )

    rendered = architecture_checks.render_architecture_baseline(tmp_path)
    payload = json.loads(rendered)
    counters = payload["non_entry_exit_allowlist"]["src/jfin/config.py"]
    assert counters["sys_import_exit_calls"] == 1
    assert counters["builtins_exit_calls"] == 1
    assert counters["system_exit_raises"] == 1
    assert counters["sys_exit_calls"] == 0

    _write_baseline(tmp_path, payload)
    parsed = architecture_contract.load_architecture_baseline(
        tmp_path / "project" / "architecture-baseline.json"
    )
    assert parsed.v1_root == architecture_contract.V1_ROOT

    result = architecture_checks.check_non_entry_exit_ratchet(tmp_path)
    assert not result.errors
