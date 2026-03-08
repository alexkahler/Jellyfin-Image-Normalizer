"""Unit tests for Slice-14 docs-topology governance checks."""

from __future__ import annotations

import importlib.util
import sys
import textwrap
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = ROOT / "project" / "scripts" / "governance_checks.py"

CANONICAL_SUITES = (
    "tests/characterization/cli_contract/",
    "tests/characterization/config_contract/",
    "tests/characterization/imaging_contract/",
    "tests/characterization/safety_contract/",
)
BASELINES_DIR = "tests/characterization/baselines/"


@pytest.fixture(scope="module")
def governance_module():
    """Load governance_checks directly from file for isolated unit tests."""
    script_dir = SCRIPT_PATH.parent
    if str(script_dir) not in sys.path:
        sys.path.insert(0, str(script_dir))
    spec = importlib.util.spec_from_file_location("verify_governance", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _write_file(path: Path, content: str) -> None:
    """Write UTF-8 file content with deterministic indentation handling."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).lstrip(), encoding="utf-8")


def _write_required_characterization_dirs(repo_root: Path) -> None:
    """Create the canonical characterization suite + baseline directories."""
    for relative in (*CANONICAL_SUITES, BASELINES_DIR):
        (repo_root / relative).mkdir(parents=True, exist_ok=True)


def _write_v1_plan(repo_root: Path, suite_lines: list[str]) -> None:
    """Write a bounded v1-plan fixture containing the suite section."""
    suite_block = "\n".join(f"* {line}" for line in suite_lines)
    _write_file(
        repo_root / "project/v1-plan.md",
        f"""
        # Seed Blueprint

        ## 16) Behavior Preservation Plan

        ### Characterization suites

        {suite_block}

        ### Imaging golden suite

        * seed
        """,
    )


def _write_technical_notes(repo_root: Path, suites_statement: str) -> None:
    """Write a bounded TECHNICAL_NOTES fixture containing the anchor bullet."""
    _write_file(
        repo_root / "docs/TECHNICAL_NOTES.md",
        f"""
        # Seed Technical Notes

        ## Development and Testing Notes
        - {suites_statement}
        - Characterization message normalization policy for baseline assertions is intentionally narrow.
        """,
    )


def _canonical_suite_lines() -> list[str]:
    """Return canonical suite paths in markdown-inline-code form."""
    return [f"`{path}`" for path in CANONICAL_SUITES]


def _write_minimum_contract(repo_root: Path) -> None:
    """Write the minimal verification contract used by run_selected_checks."""
    _write_file(
        repo_root / "project/verification-contract.yml",
        """
        version: 1
        python_version: "3.13"
        verification_commands:
          - PYTHONPATH=src ./.venv/bin/python -m pytest
          - ./.venv/bin/python -m ruff check .
          - ./.venv/bin/python -m ruff format --check .
          - ./.venv/bin/python -m mypy src
          - ./.venv/bin/python -m bandit -r src
          - ./.venv/bin/python -m pip_audit
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
          tests_mode: warn
          anti_evasion_disallow_fmt: true
          anti_evasion_disallow_multi_statement: true
          anti_evasion_disallow_dense_control_flow: true
          anti_evasion_fail_closed: true
          anti_evasion_rationale: honest_loc_required_for_maintainability
          anti_evasion_noncompliance_rule: suppression_or_packing_invalidates_loc_claim
          anti_evasion_multi_statement_max_semicolons: 0
          anti_evasion_control_flow_inline_suite_max: 0
        """,
    )


def test_docs_topology_contract_passes_for_canonical_docs(
    governance_module,
    tmp_path: Path,
):
    """Canonical suite topology in both docs should pass the contract check."""
    _write_required_characterization_dirs(tmp_path)
    _write_v1_plan(tmp_path, _canonical_suite_lines())
    _write_technical_notes(
        tmp_path,
        (
            "Characterization suites live in "
            "`tests/characterization/cli_contract/`, "
            "`tests/characterization/config_contract/`, "
            "`tests/characterization/imaging_contract/`, and "
            "`tests/characterization/safety_contract/`, "
            "with baseline contracts in `tests/characterization/baselines/`."
        ),
    )

    result = governance_module.check_docs_topology_contract(tmp_path)
    assert not result.errors


def test_docs_topology_contract_fails_for_v1_plan_legacy_paths(
    governance_module,
    tmp_path: Path,
):
    """Legacy path names in v1-plan should fail with docs_topology.contract."""
    _write_required_characterization_dirs(tmp_path)
    _write_v1_plan(
        tmp_path,
        [
            "`tests/characterization/cli_contract/`",
            "`tests/characterization/config_contract/`",
            "`tests/characterization/workflows/`",
            "`tests/characterization/restore_contract/`",
        ],
    )
    _write_technical_notes(
        tmp_path,
        (
            "Characterization suites live in "
            "`tests/characterization/cli_contract/`, "
            "`tests/characterization/config_contract/`, "
            "`tests/characterization/imaging_contract/`, and "
            "`tests/characterization/safety_contract/`, "
            "with baseline contracts in `tests/characterization/baselines/`."
        ),
    )

    result = governance_module.check_docs_topology_contract(tmp_path)
    assert any(error.startswith("docs_topology.contract:") for error in result.errors)
    assert any("project/v1-plan.md" in error for error in result.errors)


def test_docs_topology_contract_fails_for_technical_notes_drift(
    governance_module,
    tmp_path: Path,
):
    """TECHNICAL_NOTES suite drift should fail with the same contract prefix."""
    _write_required_characterization_dirs(tmp_path)
    _write_v1_plan(tmp_path, _canonical_suite_lines())
    _write_technical_notes(
        tmp_path,
        (
            "Characterization suites live in "
            "`tests/characterization/cli_contract/`, "
            "`tests/characterization/config_contract/`, "
            "`tests/characterization/imaging_contract/`, and "
            "`tests/characterization/restore_contract/`, "
            "with baseline contracts in `tests/characterization/baselines/`."
        ),
    )

    result = governance_module.check_docs_topology_contract(tmp_path)
    assert any(error.startswith("docs_topology.contract:") for error in result.errors)
    assert any("docs/TECHNICAL_NOTES.md" in error for error in result.errors)


def test_docs_topology_contract_fails_when_required_dirs_missing(
    governance_module,
    tmp_path: Path,
):
    """Missing canonical suite/baseline directories must fail the contract check."""
    (tmp_path / "tests/characterization/cli_contract").mkdir(
        parents=True, exist_ok=True
    )
    (tmp_path / "tests/characterization/config_contract").mkdir(
        parents=True, exist_ok=True
    )
    _write_v1_plan(tmp_path, _canonical_suite_lines())
    _write_technical_notes(
        tmp_path,
        (
            "Characterization suites live in "
            "`tests/characterization/cli_contract/`, "
            "`tests/characterization/config_contract/`, "
            "`tests/characterization/imaging_contract/`, and "
            "`tests/characterization/safety_contract/`, "
            "with baseline contracts in `tests/characterization/baselines/`."
        ),
    )

    result = governance_module.check_docs_topology_contract(tmp_path)
    assert any(error.startswith("docs_topology.contract:") for error in result.errors)
    assert any("required directory missing" in error for error in result.errors)


def test_docs_topology_contract_tolerates_spacing_order_and_punctuation(
    governance_module,
    tmp_path: Path,
):
    """Path extraction should tolerate formatting changes without false failures."""
    _write_required_characterization_dirs(tmp_path)
    _write_v1_plan(
        tmp_path,
        [
            "(tests\\characterization\\imaging_contract/)",
            "`tests/characterization/cli_contract`;",
            "tests/characterization/safety_contract/,",
            "'tests/characterization/config_contract/'",
        ],
    )
    _write_technical_notes(
        tmp_path,
        (
            "Characterization suites live in "
            "tests/characterization/safety_contract/, "
            "tests\\characterization\\config_contract/, "
            "(tests/characterization/imaging_contract/), and "
            "'tests/characterization/cli_contract/', "
            "with baseline contracts in `tests/characterization/baselines/`."
        ),
    )

    result = governance_module.check_docs_topology_contract(tmp_path)
    assert not result.errors


def test_run_selected_checks_characterization_fails_on_docs_topology_drift(
    governance_module,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    """Characterization selector should fail when docs topology drifts."""
    _write_minimum_contract(tmp_path)
    _write_required_characterization_dirs(tmp_path)
    _write_v1_plan(
        tmp_path,
        [
            "`tests/characterization/cli_contract/`",
            "`tests/characterization/config_contract/`",
            "`tests/characterization/workflows/`",
            "`tests/characterization/restore_contract/`",
        ],
    )
    _write_technical_notes(
        tmp_path,
        (
            "Characterization suites live in "
            "`tests/characterization/cli_contract/`, "
            "`tests/characterization/config_contract/`, "
            "`tests/characterization/imaging_contract/`, and "
            "`tests/characterization/safety_contract/`, "
            "with baseline contracts in `tests/characterization/baselines/`."
        ),
    )
    monkeypatch.setattr(
        governance_module,
        "check_characterization_artifacts",
        lambda _repo_root: governance_module.CheckResult(),
    )

    exit_code = governance_module.run_selected_checks("characterization", tmp_path)
    output = capsys.readouterr().out
    assert exit_code == 1
    assert "docs_topology.contract:" in output
