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
    runtime_gate_targets: list[str] | None = None,
    runtime_gate_budget_seconds: int = 180,
    anti_evasion_disallow_fmt: bool = True,
    anti_evasion_disallow_multi_statement: bool = True,
    anti_evasion_disallow_dense_control_flow: bool = True,
    anti_evasion_fail_closed: bool = True,
    anti_evasion_rationale: str = "honest_loc_required_for_maintainability",
    anti_evasion_noncompliance_rule: str = (
        "suppression_or_packing_invalidates_loc_claim"
    ),
    anti_evasion_multi_statement_max_semicolons: int = 0,
    anti_evasion_control_flow_inline_suite_max: int = 0,
    docstring_convention: str = "google",
    docstring_src_mode: str = "block",
    docstring_tests_mode: str = "warn",
    docstring_src_max_violations: int = 0,
    docstring_tests_max_violations: int = 189,
    comments_policy: str = "targeted_inline_comments_for_non_obvious_logic",
    format_src_mode: str = "block",
    format_tests_mode: str = "warn",
    format_src_target: str = "src",
    format_tests_target: str = "tests",
    format_on_check_failure: str = "run_format",
) -> str:
    """Create a contract YAML string using default WI-001 values."""
    commands = verification_commands or [
        "PYTHONPATH=src ./.venv/bin/python -m pytest",
        "./.venv/bin/python -m ruff check .",
        "./.venv/bin/python project/scripts/format_policy.py --target src --mode block",
        "./.venv/bin/python project/scripts/format_policy.py --target tests --mode warn",
        "./.venv/bin/python -m mypy src",
        "./.venv/bin/python -m bandit -r src",
        "./.venv/bin/python -m pip_audit",
    ]
    jobs = required_ci_jobs or ["test", "security", "quality", "governance"]
    runtime_targets = runtime_gate_targets or [
        "tests/characterization/safety_contract",
        "tests/characterization/cli_contract/test_cli_contract_characterization.py::test_cli_test_jf_blocks_operational_flags",
        "tests/characterization/config_contract/test_config_contract_characterization.py::test_config_requires_core_fields",
        "tests/characterization/cli_contract/test_cli_contract_characterization.py::test_cli_generate_config_blocks_operational_flags",
        "tests/characterization/cli_contract/test_cli_contract_characterization.py::test_cli_warns_for_unrecommended_aspect_ratio",
    ]
    lines = [
        "version: 1",
        f'python_version: "{python_version}"',
        "verification_commands:",
    ]
    lines.extend(f"  - {command}" for command in commands)
    lines.append("required_ci_jobs:")
    lines.extend(f"  - {job}" for job in jobs)
    lines.append("characterization_runtime_gate_targets:")
    lines.extend(f"  - {target}" for target in runtime_targets)
    lines.append(
        f"characterization_runtime_gate_budget_seconds: {runtime_gate_budget_seconds}"
    )
    lines.extend(
        [
            "loc_policy:",
            f"  src_max_lines: {src_max_lines}",
            f"  src_mode: {src_mode}",
            f"  tests_max_lines: {tests_max_lines}",
            f"  tests_mode: {tests_mode}",
            f"  anti_evasion_disallow_fmt: {str(anti_evasion_disallow_fmt).lower()}",
            "  anti_evasion_disallow_multi_statement: "
            f"{str(anti_evasion_disallow_multi_statement).lower()}",
            "  anti_evasion_disallow_dense_control_flow: "
            f"{str(anti_evasion_disallow_dense_control_flow).lower()}",
            f"  anti_evasion_fail_closed: {str(anti_evasion_fail_closed).lower()}",
            f"  anti_evasion_rationale: {anti_evasion_rationale}",
            f"  anti_evasion_noncompliance_rule: {anti_evasion_noncompliance_rule}",
            "  anti_evasion_multi_statement_max_semicolons: "
            f"{anti_evasion_multi_statement_max_semicolons}",
            "  anti_evasion_control_flow_inline_suite_max: "
            f"{anti_evasion_control_flow_inline_suite_max}",
            "docstring_policy:",
            f"  convention: {docstring_convention}",
            f"  src_mode: {docstring_src_mode}",
            f"  tests_mode: {docstring_tests_mode}",
            f"  src_max_violations: {docstring_src_max_violations}",
            f"  tests_max_violations: {docstring_tests_max_violations}",
            f"  comments_policy: {comments_policy}",
            "format_policy:",
            f"  src_mode: {format_src_mode}",
            f"  tests_mode: {format_tests_mode}",
            f"  src_target: {format_src_target}",
            f"  tests_target: {format_tests_target}",
            f"  on_check_failure: {format_on_check_failure}",
        ]
    )
    return "\n".join(lines) + "\n"


def _ci_text(
    python_version: str = "3.13",
    include_governance_job: bool = True,
    include_pull_request: bool = True,
    include_format_policy_commands: bool = True,
    include_venv_bootstrap: bool = True,
    include_governance_install: bool = True,
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
    if include_format_policy_commands:
        lines.append(
            "          ./.venv/bin/python project/scripts/format_policy.py --target src --mode block"
        )
        lines.append(
            "          ./.venv/bin/python project/scripts/format_policy.py --target tests --mode warn"
        )
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
            ]
        )
        if include_governance_install:
            lines.extend(
                [
                    "      - name: Install dependencies",
                    "        run: |",
                    "          ./.venv/bin/python -m pip install --upgrade pip",
                    "          ./.venv/bin/python -m pip install -r requirements.txt pytest",
                ]
            )
        lines.extend(
            [
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


def test_contract_parse_requires_anti_evasion_keys(governance_module, tmp_path: Path):
    """Contract parsing should fail when anti-evasion keys are missing."""
    contract_path = tmp_path / "verification-contract.yml"
    _write_file(
        contract_path,
        _contract_text().replace("  anti_evasion_fail_closed: true\n", ""),
    )

    with pytest.raises(
        governance_module.GovernanceError,
        match="loc_policy missing required key: anti_evasion_fail_closed",
    ):
        governance_module.parse_verification_contract(contract_path)


@pytest.mark.parametrize(
    ("contract_kwargs", "expected_message"),
    [
        (
            {"anti_evasion_disallow_fmt": False},
            "loc_policy.anti_evasion_disallow_fmt must be true.",
        ),
        (
            {"anti_evasion_fail_closed": False},
            "loc_policy.anti_evasion_fail_closed must be true.",
        ),
        (
            {"anti_evasion_multi_statement_max_semicolons": 1},
            "loc_policy.anti_evasion_multi_statement_max_semicolons must be 0.",
        ),
        (
            {
                "anti_evasion_noncompliance_rule": "allow_packing",
            },
            "loc_policy.anti_evasion_noncompliance_rule must be "
            "'suppression_or_packing_invalidates_loc_claim'.",
        ),
    ],
)
def test_contract_schema_fails_for_anti_evasion_drift(
    governance_module,
    tmp_path: Path,
    contract_kwargs: dict[str, object],
    expected_message: str,
):
    """Schema should fail when anti-evasion contract values drift."""
    contract_path = tmp_path / "verification-contract.yml"
    _write_file(contract_path, _contract_text(**contract_kwargs))

    contract = governance_module.parse_verification_contract(contract_path)
    result = governance_module.check_contract_schema(contract)

    assert expected_message in result.errors


@pytest.mark.parametrize(
    ("contract_kwargs", "expected_message"),
    [
        (
            {"docstring_convention": "numpy"},
            "docstring_policy.convention must be 'google'.",
        ),
        (
            {"docstring_src_max_violations": 1},
            "docstring_policy.src_max_violations must be 0.",
        ),
        (
            {"format_on_check_failure": "ignore"},
            "format_policy.on_check_failure must be 'run_format'.",
        ),
    ],
)
def test_contract_schema_fails_for_docstring_and_format_policy_drift(
    governance_module,
    tmp_path: Path,
    contract_kwargs: dict[str, object],
    expected_message: str,
):
    """Schema should fail when docstring/format policy values drift."""
    contract_path = tmp_path / "verification-contract.yml"
    _write_file(contract_path, _contract_text(**contract_kwargs))

    contract = governance_module.parse_verification_contract(contract_path)
    result = governance_module.check_contract_schema(contract)

    assert expected_message in result.errors


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
            docstring_policy:
              convention: google
              src_mode: block
              tests_mode: warn
              src_max_violations: 0
              tests_max_violations: 189
              comments_policy: targeted_inline_comments_for_non_obvious_logic
            format_policy:
              src_mode: block
              tests_mode: warn
              src_target: src
              tests_target: tests
              on_check_failure: run_format
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
            characterization_runtime_gate_targets:
              - tests/characterization/safety_contract
            characterization_runtime_gate_budget_seconds: 180
            loc_policy:
              src_max_lines: 300
              src_mode: block
              tests_max_lines: 300
            docstring_policy:
              convention: google
              src_mode: block
              tests_mode: warn
              src_max_violations: 0
              tests_max_violations: 189
              comments_policy: targeted_inline_comments_for_non_obvious_logic
            format_policy:
              src_mode: block
              tests_mode: warn
              src_target: src
              tests_target: tests
              on_check_failure: run_format
            """,
            "loc_policy missing required key: tests_mode",
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
            characterization_runtime_gate_targets:
              - tests/characterization/safety_contract
            loc_policy:
              src_max_lines: 300
              src_mode: block
              tests_max_lines: 300
              tests_mode: warn
            docstring_policy:
              convention: google
              src_mode: block
              tests_mode: warn
              src_max_violations: 0
              tests_max_violations: 189
              comments_policy: targeted_inline_comments_for_non_obvious_logic
            format_policy:
              src_mode: block
              tests_mode: warn
              src_target: src
              tests_target: tests
              on_check_failure: run_format
            """,
            "required key: characterization_runtime_gate_budget_seconds",
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
    _write_file(ci_path, _ci_text(include_format_policy_commands=False))

    contract = governance_module.parse_verification_contract(contract_path)
    result = governance_module.check_ci_contract_sync(contract, ci_path)

    assert any(
        "./.venv/bin/python project/scripts/format_policy.py --target src --mode block"
        in error
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


def test_loc_policy_blocks_fmt_suppression(governance_module, tmp_path: Path):
    """LOC check should fail when formatter suppression markers are present."""
    contract_path = tmp_path / "verification-contract.yml"
    src_file = tmp_path / "src" / "fmt_blocked.py"
    _write_file(contract_path, _contract_text())
    _write_file(src_file, "# fmt: off\nx = 1\n")
    _write_file(tmp_path / "tests" / "test_ok.py", "def test_ok():\n    assert True\n")

    contract = governance_module.parse_verification_contract(contract_path)
    result = governance_module.check_loc_policy(
        contract,
        tmp_path,
        tmp_path / "src",
        tmp_path / "tests",
    )

    assert any(
        "src/fmt_blocked.py [anti_evasion.fmt_suppression]" in error
        for error in result.errors
    )


def test_loc_policy_blocks_semicolon_packing(governance_module, tmp_path: Path):
    """LOC check should fail when semicolon packing exceeds policy max."""
    contract_path = tmp_path / "verification-contract.yml"
    src_file = tmp_path / "src" / "packed.py"
    _write_file(contract_path, _contract_text())
    _write_file(src_file, "x = 1; y = 2\n")
    _write_file(tmp_path / "tests" / "test_ok.py", "def test_ok():\n    assert True\n")

    contract = governance_module.parse_verification_contract(contract_path)
    result = governance_module.check_loc_policy(
        contract,
        tmp_path,
        tmp_path / "src",
        tmp_path / "tests",
    )

    assert any(
        "src/packed.py [anti_evasion.multi_statement]" in error
        for error in result.errors
    )


def test_loc_policy_blocks_dense_inline_control_flow(
    governance_module,
    tmp_path: Path,
):
    """LOC check should fail when inline control-flow suites exceed policy max."""
    contract_path = tmp_path / "verification-contract.yml"
    src_file = tmp_path / "src" / "dense.py"
    _write_file(contract_path, _contract_text())
    _write_file(src_file, "if True: x = 1\n")
    _write_file(tmp_path / "tests" / "test_ok.py", "def test_ok():\n    assert True\n")

    contract = governance_module.parse_verification_contract(contract_path)
    result = governance_module.check_loc_policy(
        contract,
        tmp_path,
        tmp_path / "src",
        tmp_path / "tests",
    )

    assert any(
        "src/dense.py [anti_evasion.dense_control_flow]" in error
        for error in result.errors
    )


def test_loc_policy_fail_closed_when_ast_analysis_unavailable(
    governance_module,
    tmp_path: Path,
):
    """LOC check should fail closed if dense-control-flow analysis cannot run."""
    contract_path = tmp_path / "verification-contract.yml"
    src_file = tmp_path / "src" / "broken.py"
    _write_file(contract_path, _contract_text())
    _write_file(src_file, "if True print('oops')\n")
    _write_file(tmp_path / "tests" / "test_ok.py", "def test_ok():\n    assert True\n")

    contract = governance_module.parse_verification_contract(contract_path)
    result = governance_module.check_loc_policy(
        contract,
        tmp_path,
        tmp_path / "src",
        tmp_path / "tests",
    )

    assert any(
        "src/broken.py [anti_evasion.fail_closed]" in error for error in result.errors
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
    assert "docstrings" in check_action.choices
    assert "format" in check_action.choices


def test_docstring_policy_blocks_src_regression(governance_module, tmp_path: Path):
    """Docstring checks should block when src violations exceed configured max."""
    contract_path = tmp_path / "verification-contract.yml"
    _write_file(contract_path, _contract_text(docstring_src_max_violations=0))
    _write_file(tmp_path / "src" / "module.py", "def f():\n    return 1\n")
    _write_file(tmp_path / "tests" / "test_ok.py", "def test_ok():\n    assert True\n")

    contract = governance_module.parse_verification_contract(contract_path)
    result = governance_module.check_docstring_policy(contract, tmp_path)

    assert any(
        "docstring policy violation count for 'src'" in error for error in result.errors
    )


def test_docstring_policy_warns_for_tests_regression(governance_module, tmp_path: Path):
    """Docstring checks should warn when tests violations exceed configured max."""
    contract_path = tmp_path / "verification-contract.yml"
    _write_file(contract_path, _contract_text(docstring_tests_max_violations=0))
    _write_file(
        tmp_path / "src" / "module.py",
        '"""Do module work."""\n\n\ndef f():\n    """Do work."""\n    return 1\n',
    )
    _write_file(
        tmp_path / "tests" / "test_bad.py", "def test_bad():\n    assert True\n"
    )

    contract = governance_module.parse_verification_contract(contract_path)
    result = governance_module.check_docstring_policy(contract, tmp_path)

    assert not result.errors
    assert any(
        "docstring policy violation count for 'tests'" in warning
        for warning in result.warnings
    )


def test_format_policy_blocks_src_drift(governance_module, tmp_path: Path):
    """Format policy should block on src drift even after auto-formatting."""
    contract_path = tmp_path / "verification-contract.yml"
    _write_file(contract_path, _contract_text())
    _write_file(tmp_path / "src" / "bad.py", "x=1\n")
    _write_file(tmp_path / "tests" / "test_ok.py", "def test_ok():\n    assert True\n")

    contract = governance_module.parse_verification_contract(contract_path)
    result = governance_module.check_format_policy(contract, tmp_path)

    assert any(
        "format policy detected drift and auto-formatted 'src'" in error
        for error in result.errors
    )


def test_format_policy_warns_for_tests_drift(governance_module, tmp_path: Path):
    """Format policy should warn on tests drift and keep src clean."""
    contract_path = tmp_path / "verification-contract.yml"
    _write_file(contract_path, _contract_text())
    _write_file(
        tmp_path / "src" / "good.py",
        '"""Do module work."""\n\n\ndef f() -> int:\n    """Return one."""\n    return 1\n',
    )
    _write_file(tmp_path / "tests" / "test_bad.py", "x=1\n")

    contract = governance_module.parse_verification_contract(contract_path)
    result = governance_module.check_format_policy(contract, tmp_path)

    assert not result.errors
    assert any(
        "format policy detected drift and auto-formatted 'tests'" in warning
        for warning in result.warnings
    )


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


def test_print_check_result_includes_workflow_sequence_lines(
    governance_module,
    capsys: pytest.CaptureFixture[str],
):
    """Characterization output should include workflow sequence + trace counters."""
    result = governance_module.CheckResult()
    setattr(
        result,
        "workflow_coverage_report",
        SimpleNamespace(
            configured_cells=1,
            validated_cells=1,
            contract_errors=0,
            trace_contract_errors=0,
            trace_assertion_failures=0,
            trace_required_rows=1,
            trace_validated_rows=1,
            sequence_warnings=2,
            count_only_warnings=1,
            open_debts=1,
        ),
    )

    governance_module._print_check_result("characterization", result)
    output = capsys.readouterr().out
    assert "Workflow sequence contract OK" in output
    assert "Workflow trace contract OK" in output
    assert "Workflow trace required rows: 1" in output
    assert "Workflow sequence evidence warnings: 2" in output
