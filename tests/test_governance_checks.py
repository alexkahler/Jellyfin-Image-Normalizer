"""Unit tests for project/scripts/verify_governance.py."""

from __future__ import annotations

import importlib.util
import sys
import textwrap
from types import SimpleNamespace
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = ROOT / "project" / "scripts" / "governance_checks.py"


@pytest.fixture(scope="module")
def governance_module():
    """Load the governance script module directly from its file path."""
    script_dir = SCRIPT_PATH.parent
    if str(script_dir) not in sys.path:
        sys.path.insert(0, str(script_dir))
    spec = importlib.util.spec_from_file_location("verify_governance", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    # Register the module before execution so dataclass annotation resolution works.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _write_file(path: Path, content: str) -> None:
    """Write UTF-8 test content to a file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).lstrip(), encoding="utf-8")


def _contract_text(
    verification_commands: list[str] | None = None,
    required_ci_jobs: list[str] | None = None,
    python_version: str = "3.13",
    src_max_lines: int = 300,
    src_mode: str = "block",
    tests_max_lines: int = 300,
    tests_mode: str = "warn",
) -> str:
    """Create a contract YAML string using default WI-001 values."""
    commands = verification_commands or [
        "PYTHONPATH=src ./.venv/bin/python -m pytest",
        "./.venv/bin/python -m ruff check .",
        "./.venv/bin/python -m ruff format --check .",
        "./.venv/bin/python -m mypy src",
        "./.venv/bin/python -m bandit -r src",
        "./.venv/bin/python -m pip_audit",
    ]
    jobs = required_ci_jobs or ["test", "security", "quality", "governance"]
    lines = [
        "version: 1",
        f'python_version: "{python_version}"',
        "verification_commands:",
    ]
    lines.extend(f"  - {command}" for command in commands)
    lines.append("required_ci_jobs:")
    lines.extend(f"  - {job}" for job in jobs)
    lines.extend(
        [
            "loc_policy:",
            f"  src_max_lines: {src_max_lines}",
            f"  src_mode: {src_mode}",
            f"  tests_max_lines: {tests_max_lines}",
            f"  tests_mode: {tests_mode}",
        ]
    )
    return "\n".join(lines) + "\n"


def _ci_text(
    python_version: str = "3.13",
    include_governance_job: bool = True,
    include_pull_request: bool = True,
    include_ruff_format_command: bool = True,
    include_venv_bootstrap: bool = True,
) -> str:
    """Create a minimal CI workflow YAML string for governance tests."""
    lines = ["name: CI", "on:"]
    if include_pull_request:
        lines.extend(["  pull_request:", "    branches: [ main ]"])
    lines.extend(["  push:", "    branches: [ main ]", "", "jobs:"])
    lines.extend(
        [
            "  test:",
            "    runs-on: ubuntu-latest",
            "    steps:",
            "      - name: Set up Python",
            "        uses: actions/setup-python@v5",
            "        with:",
            f'          python-version: "{python_version}"',
            "      - name: Bootstrap virtual environment",
            "        run: |",
            "          python -m venv .venv",
            "      - name: Run tests",
            "        run: |",
            "          PYTHONPATH=src ./.venv/bin/python -m pytest",
            "  security:",
            "    runs-on: ubuntu-latest",
            "    steps:",
            "      - name: Set up Python",
            "        uses: actions/setup-python@v5",
            "        with:",
            f'          python-version: "{python_version}"',
            "      - name: Bootstrap virtual environment",
            "        run: |",
            "          python -m venv .venv",
            "      - name: Security",
            "        run: |",
            "          ./.venv/bin/python -m bandit -r src",
            "          ./.venv/bin/python -m pip_audit",
            "  quality:",
            "    runs-on: ubuntu-latest",
            "    steps:",
            "      - name: Set up Python",
            "        uses: actions/setup-python@v5",
            "        with:",
            f'          python-version: "{python_version}"',
            "      - name: Bootstrap virtual environment",
            "        run: |",
            "          python -m venv .venv",
            "      - name: Quality",
            "        run: |",
            "          ./.venv/bin/python -m ruff check .",
        ]
    )
    if include_ruff_format_command:
        lines.append("          ./.venv/bin/python -m ruff format --check .")
    lines.append("          ./.venv/bin/python -m mypy src")
    if include_governance_job:
        lines.extend(
            [
                "  governance:",
                "    runs-on: ubuntu-latest",
                "    steps:",
                "      - name: Set up Python",
                "        uses: actions/setup-python@v5",
                "        with:",
                f'          python-version: "{python_version}"',
                "      - name: Bootstrap virtual environment",
                "        run: |",
                "          python -m venv .venv",
                "      - name: Run governance checks",
                "        run: |",
                "          ./.venv/bin/python project/scripts/verify_governance.py --check all",
            ]
        )
    if not include_venv_bootstrap:
        lines = [line for line in lines if line != "          python -m venv .venv"]
    return "\n".join(lines) + "\n"


def _readme_text(python_version: str = "3.13") -> str:
    """Create a minimal README string containing a Python version declaration."""
    return f"Requires **Python {python_version}+**.\n"


def test_contract_schema_success(governance_module, tmp_path: Path):
    """Contract parsing and schema validation should pass for valid input."""
    contract_path = tmp_path / "verification-contract.yml"
    _write_file(contract_path, _contract_text())

    contract = governance_module.parse_verification_contract(contract_path)
    result = governance_module.check_contract_schema(contract)

    assert not result.errors
    assert not result.warnings


@pytest.mark.parametrize(
    ("contract_content", "expected_message"),
    [
        (
            """
            version: 1
            python_version: "3.13"
            verification_commands:
              - PYTHONPATH=src ./.venv/bin/python -m pytest
            loc_policy:
              src_max_lines: 300
              src_mode: block
              tests_max_lines: 300
              tests_mode: warn
            """,
            "required block: required_ci_jobs",
        ),
        (
            """
            version: 1
            python_version: "3.13"
            verification_commands:
              - PYTHONPATH=src ./.venv/bin/python -m pytest
            required_ci_jobs:
              - test
              - security
              - quality
              - governance
            loc_policy:
              src_max_lines: 300
              src_mode: block
              tests_max_lines: 300
            """,
            "loc_policy missing required key: tests_mode",
        ),
    ],
)
def test_contract_schema_parse_failures(
    governance_module,
    tmp_path: Path,
    contract_content: str,
    expected_message: str,
):
    """Contract parsing should fail when required keys or fields are missing."""
    contract_path = tmp_path / "verification-contract.yml"
    _write_file(contract_path, contract_content)

    with pytest.raises(governance_module.GovernanceError, match=expected_message):
        governance_module.parse_verification_contract(contract_path)


def test_ci_sync_fails_when_contract_command_missing(
    governance_module,
    tmp_path: Path,
):
    """CI sync should fail when a required command is missing from workflow."""
    contract_path = tmp_path / "verification-contract.yml"
    ci_path = tmp_path / "ci.yml"
    _write_file(contract_path, _contract_text())
    _write_file(ci_path, _ci_text(include_ruff_format_command=False))

    contract = governance_module.parse_verification_contract(contract_path)
    result = governance_module.check_ci_contract_sync(contract, ci_path)

    assert any(
        "./.venv/bin/python -m ruff format --check ." in error
        for error in result.errors
    )


def test_ci_sync_fails_when_governance_job_missing(
    governance_module,
    tmp_path: Path,
):
    """CI sync should fail when the governance job is not defined."""
    contract_path = tmp_path / "verification-contract.yml"
    ci_path = tmp_path / "ci.yml"
    _write_file(contract_path, _contract_text())
    _write_file(ci_path, _ci_text(include_governance_job=False))

    contract = governance_module.parse_verification_contract(contract_path)
    result = governance_module.check_ci_contract_sync(contract, ci_path)

    assert any("required job: governance" in error for error in result.errors)


def test_ci_sync_fails_when_venv_bootstrap_missing(
    governance_module,
    tmp_path: Path,
):
    """CI sync should fail when required jobs do not create .venv."""
    contract_path = tmp_path / "verification-contract.yml"
    ci_path = tmp_path / "ci.yml"
    _write_file(contract_path, _contract_text())
    _write_file(ci_path, _ci_text(include_venv_bootstrap=False))

    contract = governance_module.parse_verification_contract(contract_path)
    result = governance_module.check_ci_contract_sync(contract, ci_path)

    assert any(
        "must bootstrap repo virtualenv with 'python -m venv .venv'" in error
        for error in result.errors
    )


def test_loc_policy_blocks_src_overflow(governance_module, tmp_path: Path):
    """LOC check should fail when a src file exceeds the block threshold."""
    contract_path = tmp_path / "verification-contract.yml"
    src_file = tmp_path / "src" / "module.py"
    test_file = tmp_path / "tests" / "test_module.py"
    _write_file(contract_path, _contract_text())
    _write_file(src_file, "\n".join("x = 1" for _ in range(301)))
    _write_file(test_file, "def test_ok():\n    assert True\n")

    contract = governance_module.parse_verification_contract(contract_path)
    result = governance_module.check_loc_policy(
        contract,
        tmp_path,
        tmp_path / "src",
        tmp_path / "tests",
    )

    assert result.errors
    assert any("src/module.py has 301 lines" in error for error in result.errors)


def test_loc_policy_warns_for_tests_overflow(governance_module, tmp_path: Path):
    """LOC check should warn (not fail) when test files exceed warning threshold."""
    contract_path = tmp_path / "verification-contract.yml"
    src_file = tmp_path / "src" / "module.py"
    test_file = tmp_path / "tests" / "test_large.py"
    _write_file(contract_path, _contract_text())
    _write_file(src_file, "x = 1\n")
    _write_file(test_file, "\n".join("x = 1" for _ in range(301)))

    contract = governance_module.parse_verification_contract(contract_path)
    result = governance_module.check_loc_policy(
        contract,
        tmp_path,
        tmp_path / "src",
        tmp_path / "tests",
    )

    assert not result.errors
    assert any(
        "tests/test_large.py has 301 lines" in warning for warning in result.warnings
    )


def test_python_version_consistency_failure(governance_module, tmp_path: Path):
    """Version consistency check should fail when CI/docs drift from contract."""
    contract_path = tmp_path / "verification-contract.yml"
    ci_path = tmp_path / "ci.yml"
    readme_path = tmp_path / "README.md"
    _write_file(contract_path, _contract_text(python_version="3.13"))
    _write_file(ci_path, _ci_text(python_version="3.12"))
    _write_file(readme_path, _readme_text(python_version="3.12"))

    contract = governance_module.parse_verification_contract(contract_path)
    result = governance_module.check_python_version_consistency(
        contract,
        ci_path,
        readme_path,
    )

    assert any("expected 3.13, found 3.12" in error for error in result.errors)


def test_supported_checks_include_architecture_and_characterization(governance_module):
    """Governance CLI should expose architecture and characterization selectors."""
    parser = governance_module.build_parser()
    check_action = next(
        action
        for action in parser._actions
        if action.dest == "check"  # noqa: SLF001
    )
    assert "architecture" in check_action.choices
    assert "characterization" in check_action.choices


def test_print_check_result_includes_collectability_ok_signal(
    governance_module,
    capsys: pytest.CaptureFixture[str],
):
    """Characterization output should emit explicit collectability/linkage status."""
    result = governance_module.CheckResult()
    setattr(
        result,
        "collectability_report",
        SimpleNamespace(
            total_owner_nodeids=3,
            resolved_owner_nodeids=3,
            unresolved_owner_nodeids=0,
        ),
    )

    governance_module._print_check_result("characterization", result)
    output = capsys.readouterr().out
    assert "Characterization collectability/linkage OK" in output
