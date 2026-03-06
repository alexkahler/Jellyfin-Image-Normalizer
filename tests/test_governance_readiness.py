"""Readiness-check wiring tests for project/scripts/governance_checks.py."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from tests.test_governance_checks import _contract_text, _write_file

pytest_plugins = ("tests.test_governance_checks",)


def test_supported_checks_include_readiness(governance_module):
    """Governance CLI should expose the readiness selector."""
    parser = governance_module.build_parser()
    check_action = next(
        action
        for action in parser._actions
        if action.dest == "check"  # noqa: SLF001
    )
    assert "readiness" in check_action.choices


def test_print_check_result_includes_readiness_lines(
    governance_module,
    capsys: pytest.CaptureFixture[str],
):
    """Readiness output should emit deterministic counters and status line."""
    result = governance_module.CheckResult()
    setattr(
        result,
        "readiness_report",
        SimpleNamespace(claimed_rows=2, validated_rows=1),
    )
    result.add_error("readiness.runtime_not_green: synthetic")

    governance_module._print_check_result("readiness", result)
    output = capsys.readouterr().out
    assert "Route readiness claims: 2" in output
    assert "Route readiness claims validated: 1" in output
    assert "Route readiness proof NOT OK" in output


def test_run_selected_checks_readiness_returns_zero_when_green(
    governance_module,
    tmp_path: Path,
):
    """Readiness check should return zero when no readiness errors are reported."""
    _write_file(tmp_path / "project/verification-contract.yml", _contract_text())
    readiness_result = governance_module.CheckResult()
    setattr(
        readiness_result,
        "readiness_report",
        SimpleNamespace(claimed_rows=1, validated_rows=1),
    )

    with patch.object(
        governance_module,
        "check_readiness_artifacts",
        return_value=readiness_result,
    ):
        exit_code = governance_module.run_selected_checks("readiness", tmp_path)

    assert exit_code == 0
