"""Architecture-selector unit tests for project/scripts/governance_checks.py."""

from __future__ import annotations

import importlib.util
import sys
import textwrap
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = ROOT / "project" / "scripts" / "governance_checks.py"


@pytest.fixture(scope="module")
def governance_module():
    """Load governance_checks directly from file path for isolated testing."""
    script_dir = SCRIPT_PATH.parent
    if str(script_dir) not in sys.path:
        sys.path.insert(0, str(script_dir))
    spec = importlib.util.spec_from_file_location("verify_governance_arch", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).lstrip(), encoding="utf-8")


def _contract_text() -> str:
    return (
        "version: 1\n"
        'python_version: "3.13"\n'
        "verification_commands:\n"
        "  - PYTHONPATH=src ./.venv/bin/python -m pytest\n"
        "  - ./.venv/bin/python -m ruff check .\n"
        "  - ./.venv/bin/python -m ruff format --check .\n"
        "  - ./.venv/bin/python -m mypy src\n"
        "  - ./.venv/bin/python -m bandit -r src\n"
        "  - ./.venv/bin/python -m pip_audit\n"
        "required_ci_jobs:\n"
        "  - test\n"
        "  - security\n"
        "  - quality\n"
        "  - governance\n"
        "characterization_runtime_gate_targets:\n"
        "  - tests/characterization/safety_contract\n"
        "characterization_runtime_gate_budget_seconds: 180\n"
        "loc_policy:\n"
        "  src_max_lines: 300\n"
        "  src_mode: block\n"
        "  tests_max_lines: 300\n"
        "  tests_mode: warn\n"
    )


def test_supported_checks_include_architecture(governance_module):
    """Governance parser should expose the architecture selector."""
    parser = governance_module.build_parser()
    check_action = next(
        action
        for action in parser._actions
        if action.dest == "check"  # noqa: SLF001
    )
    assert "architecture" in check_action.choices


def test_print_baseline_requires_architecture_check(governance_module, capsys):
    """--print-baseline should fail when check target is not architecture."""
    exit_code = governance_module.main(["--check", "schema", "--print-baseline"])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "--check architecture" in output


def test_print_baseline_outputs_json(governance_module, tmp_path: Path, capsys):
    """--print-baseline should emit generated architecture baseline JSON."""
    _write_file(tmp_path / "project" / "verification-contract.yml", _contract_text())
    _write_file(tmp_path / "src" / "jfin" / "cli.py", "import sys\nsys.exit(0)\n")
    _write_file(tmp_path / "src" / "jfin" / "config.py", "import sys\nsys.exit(1)\n")

    exit_code = governance_module.run_selected_checks(
        "architecture",
        tmp_path,
        print_baseline=True,
    )
    output = capsys.readouterr().out

    assert exit_code == 0
    assert '"non_entry_exit_allowlist"' in output
    assert '"src/jfin/config.py"' in output
