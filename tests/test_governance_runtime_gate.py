"""Runtime-gate-focused unit tests for project/scripts/governance_checks.py."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from tests.test_governance_checks import _ci_text, _contract_text, _write_file

pytest_plugins = ("tests.test_governance_checks",)


def _write_docs_topology_artifacts(repo_root: Path) -> None:
    """Write minimal canonical docs + directories for docs-topology checks."""
    _write_file(
        repo_root / "project/v1-plan.md",
        """
        ## 16) Behavior Preservation Plan

        ### Characterization suites

        * `tests/characterization/cli_contract/`
        * `tests/characterization/config_contract/`
        * `tests/characterization/imaging_contract/`
        * `tests/characterization/safety_contract/`

        ### Imaging golden suite

        * seed
        """,
    )
    _write_file(
        repo_root / "docs/TECHNICAL_NOTES.md",
        """
        ## Development and Testing Notes
        - Characterization suites live in `tests/characterization/cli_contract/`, `tests/characterization/config_contract/`, `tests/characterization/imaging_contract/`, and `tests/characterization/safety_contract/`, with baseline contracts in `tests/characterization/baselines/`.
        - Characterization message normalization policy for baseline assertions is intentionally narrow.
        """,
    )
    for relative in (
        "tests/characterization/cli_contract",
        "tests/characterization/config_contract",
        "tests/characterization/imaging_contract",
        "tests/characterization/safety_contract",
        "tests/characterization/baselines",
    ):
        (repo_root / relative).mkdir(parents=True, exist_ok=True)


def test_ci_sync_fails_when_governance_install_missing(
    governance_module,
    tmp_path: Path,
):
    """CI sync should fail when governance job skips dependency installation."""
    contract_path = tmp_path / "verification-contract.yml"
    ci_path = tmp_path / "ci.yml"
    _write_file(contract_path, _contract_text())
    _write_file(ci_path, _ci_text(include_governance_install=False))

    contract = governance_module.parse_verification_contract(contract_path)
    result = governance_module.check_ci_contract_sync(contract, ci_path)

    assert any(
        "job 'governance' must install dependencies" in error for error in result.errors
    )


def test_contract_schema_fails_for_unexpected_runtime_gate_targets(
    governance_module,
    tmp_path: Path,
):
    """Schema should fail when runtime gate targets diverge from contract defaults."""
    contract_path = tmp_path / "verification-contract.yml"
    _write_file(
        contract_path,
        _contract_text(runtime_gate_targets=["tests/characterization/cli_contract"]),
    )
    contract = governance_module.parse_verification_contract(contract_path)

    result = governance_module.check_contract_schema(contract)
    assert any(
        "characterization_runtime_gate_targets must be exactly" in error
        for error in result.errors
    )


def test_contract_schema_fails_for_unexpected_runtime_gate_budget(
    governance_module,
    tmp_path: Path,
):
    """Schema should fail when runtime gate budget diverges from contract defaults."""
    contract_path = tmp_path / "verification-contract.yml"
    _write_file(
        contract_path,
        _contract_text(runtime_gate_budget_seconds=120),
    )
    contract = governance_module.parse_verification_contract(contract_path)

    result = governance_module.check_contract_schema(contract)
    assert any(
        "characterization_runtime_gate_budget_seconds must be 180." in error
        for error in result.errors
    )


def test_print_check_result_includes_runtime_gate_signal(
    governance_module,
    capsys: pytest.CaptureFixture[str],
):
    """Characterization output should emit explicit runtime gate status lines."""
    result = governance_module.CheckResult()
    setattr(
        result,
        "runtime_gate_report",
        SimpleNamespace(
            configured_targets=("tests/characterization/safety_contract",),
            checked_targets=1,
            passed_targets=1,
            failed_targets=0,
            budget_seconds=180,
            elapsed_seconds=1.25,
            mapped_parity_ids=("API-DRYRUN-001",),
            infos=(),
        ),
    )

    governance_module._print_check_result("characterization", result)
    output = capsys.readouterr().out
    assert "Characterization runtime gate targets checked: 1" in output
    assert "Characterization runtime gate OK (warn)" in output


def test_run_selected_checks_characterization_returns_zero_for_runtime_warnings(
    governance_module,
    tmp_path: Path,
):
    """Warn-only runtime-gate outcomes should not force a nonzero exit code."""
    _write_file(tmp_path / "project/verification-contract.yml", _contract_text())
    _write_docs_topology_artifacts(tmp_path)
    warning_result = governance_module.CheckResult()
    warning_result.add_warning("runtime_gate.execution_failed: synthetic warning")
    setattr(
        warning_result,
        "runtime_gate_report",
        SimpleNamespace(
            configured_targets=("tests/characterization/safety_contract",),
            checked_targets=1,
            passed_targets=0,
            failed_targets=1,
            budget_seconds=180,
            elapsed_seconds=2.0,
            mapped_parity_ids=("API-DRYRUN-001",),
            infos=(),
        ),
    )

    with patch.object(
        governance_module,
        "check_characterization_artifacts",
        return_value=warning_result,
    ):
        exit_code = governance_module.run_selected_checks("characterization", tmp_path)

    assert exit_code == 0
