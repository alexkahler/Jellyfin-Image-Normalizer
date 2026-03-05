"""Slice-10 runtime gate tests for characterization governance checks."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from tests.test_characterization_checks import (
    _build_valid_parity_rows,
    _write_file,
    _write_valid_artifacts,
)

pytest_plugins = ("tests.test_characterization_checks",)


def _setup_runtime_context(characterization_modules, tmp_path: Path):
    characterization_contract, characterization_checks, parity_contract = (
        characterization_modules
    )
    repo_root, _cli_baseline_path, _parity_path = _write_valid_artifacts(
        tmp_path,
        characterization_contract,
        parity_contract,
    )
    rows = _build_valid_parity_rows(
        characterization_contract.REQUIRED_CHARACTERIZATION_BEHAVIOR_IDS
    )
    parity_rows = {row["behavior_id"]: row for row in rows}
    return characterization_checks, repo_root, parity_rows


def _set_runtime_budget(repo_root: Path, budget_seconds: int) -> None:
    contract_path = repo_root / "project/verification-contract.yml"
    text = contract_path.read_text(encoding="utf-8")
    text = text.replace(
        "characterization_runtime_gate_budget_seconds: 180",
        f"characterization_runtime_gate_budget_seconds: {budget_seconds}",
    )
    _write_file(contract_path, text)


def _completed(stdout: str, *, returncode: int = 0, stderr: str = ""):
    return subprocess.CompletedProcess(
        args=["pytest"],
        returncode=returncode,
        stdout=stdout,
        stderr=stderr,
    )


def test_runtime_gate_passes_for_safety_target(
    characterization_modules, tmp_path: Path
):
    """Runtime gate should pass with no runtime warnings for safety target scope."""
    characterization_checks, repo_root, parity_rows = _setup_runtime_context(
        characterization_modules,
        tmp_path,
    )
    result = characterization_checks.CheckResult()

    report = characterization_checks._check_runtime_characterization_gate(
        repo_root,
        parity_rows,
        result,
    )

    runtime_warnings = [
        warning for warning in result.warnings if warning.startswith("runtime_gate.")
    ]
    assert not runtime_warnings
    assert report.checked_targets == 1
    assert report.passed_targets == 1
    assert report.failed_targets == 0
    assert report.mapped_parity_ids


def test_runtime_gate_warns_on_execution_failure(
    characterization_modules,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    """Runtime gate should emit execution_failed warning with mapped parity ids."""
    characterization_checks, repo_root, parity_rows = _setup_runtime_context(
        characterization_modules,
        tmp_path,
    )
    owner_nodeid = parity_rows["API-DRYRUN-001"]["owner_test"].replace("\\", "/")

    def _fake_run(*, repo_root, args, timeout_seconds=None):  # noqa: ANN001
        if "--collect-only" in args:
            return _completed(f"{owner_nodeid}\n")
        return _completed("FAILED\n", returncode=1, stderr="synthetic failure")

    monkeypatch.setattr(characterization_checks, "_run_pytest_command", _fake_run)
    result = characterization_checks.CheckResult()

    report = characterization_checks._check_runtime_characterization_gate(
        repo_root,
        parity_rows,
        result,
    )

    assert any(
        warning.startswith("runtime_gate.execution_failed")
        and "mapped_parity_ids=['API-DRYRUN-001']" in warning
        for warning in result.warnings
    )
    assert report.failed_targets == 1


def test_runtime_gate_warns_on_timeout(
    characterization_modules,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    """Runtime gate should emit timeout warning when runtime execution exceeds timeout."""
    characterization_checks, repo_root, parity_rows = _setup_runtime_context(
        characterization_modules,
        tmp_path,
    )
    owner_nodeid = parity_rows["API-DRYRUN-001"]["owner_test"].replace("\\", "/")

    def _fake_run(*, repo_root, args, timeout_seconds=None):  # noqa: ANN001
        if "--collect-only" in args:
            return _completed(f"{owner_nodeid}\n")
        raise subprocess.TimeoutExpired(cmd=args, timeout=timeout_seconds or 0.1)

    monkeypatch.setattr(characterization_checks, "_run_pytest_command", _fake_run)
    result = characterization_checks.CheckResult()

    characterization_checks._check_runtime_characterization_gate(
        repo_root,
        parity_rows,
        result,
    )

    assert any(
        warning.startswith("runtime_gate.timeout") for warning in result.warnings
    )


def test_runtime_gate_warns_when_budget_exceeded(
    characterization_modules,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    """Completed runs over budget should emit budget_exceeded warning."""
    characterization_checks, repo_root, parity_rows = _setup_runtime_context(
        characterization_modules,
        tmp_path,
    )
    owner_nodeid = parity_rows["API-DRYRUN-001"]["owner_test"].replace("\\", "/")
    _set_runtime_budget(repo_root, 1)
    monotonic_values = iter([0.0, 0.2, 2.4])

    def _fake_monotonic() -> float:
        return next(monotonic_values)

    def _fake_run(*, repo_root, args, timeout_seconds=None):  # noqa: ANN001
        if "--collect-only" in args:
            return _completed(f"{owner_nodeid}\n")
        return _completed("1 passed\n")

    monkeypatch.setattr(characterization_checks.time, "monotonic", _fake_monotonic)
    monkeypatch.setattr(characterization_checks, "_run_pytest_command", _fake_run)
    result = characterization_checks.CheckResult()

    characterization_checks._check_runtime_characterization_gate(
        repo_root,
        parity_rows,
        result,
    )

    assert any(
        warning.startswith("runtime_gate.budget_exceeded")
        for warning in result.warnings
    )
    assert not any(
        warning.startswith("runtime_gate.timeout") for warning in result.warnings
    )


def test_runtime_gate_timeout_takes_precedence_over_budget(
    characterization_modules,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    """Budget warning should not be emitted when timeout warning is present."""
    characterization_checks, repo_root, parity_rows = _setup_runtime_context(
        characterization_modules,
        tmp_path,
    )
    owner_nodeid = parity_rows["API-DRYRUN-001"]["owner_test"].replace("\\", "/")
    _set_runtime_budget(repo_root, 1)
    monotonic_values = iter([0.0, 0.2, 2.4])

    def _fake_monotonic() -> float:
        return next(monotonic_values)

    def _fake_run(*, repo_root, args, timeout_seconds=None):  # noqa: ANN001
        if "--collect-only" in args:
            return _completed(f"{owner_nodeid}\n")
        raise subprocess.TimeoutExpired(cmd=args, timeout=timeout_seconds or 0.1)

    monkeypatch.setattr(characterization_checks.time, "monotonic", _fake_monotonic)
    monkeypatch.setattr(characterization_checks, "_run_pytest_command", _fake_run)
    result = characterization_checks.CheckResult()

    characterization_checks._check_runtime_characterization_gate(
        repo_root,
        parity_rows,
        result,
    )

    assert any(
        warning.startswith("runtime_gate.timeout") for warning in result.warnings
    )
    assert not any(
        warning.startswith("runtime_gate.budget_exceeded")
        for warning in result.warnings
    )


def test_runtime_gate_nodeid_normalization_intersection(
    characterization_modules,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    """Owner nodeids with backslash paths should still intersect collected nodeids."""
    characterization_checks, repo_root, parity_rows = _setup_runtime_context(
        characterization_modules,
        tmp_path,
    )
    behavior_id = "API-DRYRUN-001"
    owner_test = parity_rows[behavior_id]["owner_test"]
    owner_path, owner_function = owner_test.split("::", 1)
    owner_nodeid = f"{owner_path.replace('\\', '/')}::{owner_function}"
    owner_path_windows = owner_path.replace("/", "\\")
    parity_rows[behavior_id]["owner_test"] = f"{owner_path_windows}::{owner_function}"

    def _fake_run(*, repo_root, args, timeout_seconds=None):  # noqa: ANN001
        if "--collect-only" in args:
            return _completed(f"{owner_nodeid}\n")
        return _completed("1 passed\n")

    monkeypatch.setattr(characterization_checks, "_run_pytest_command", _fake_run)
    result = characterization_checks.CheckResult()

    report = characterization_checks._check_runtime_characterization_gate(
        repo_root,
        parity_rows,
        result,
    )

    assert behavior_id in report.mapped_parity_ids


def test_runtime_gate_emits_mapping_empty_as_info(
    characterization_modules,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    """Mapping gaps should be surfaced as info lines, not warnings/errors."""
    characterization_checks, repo_root, parity_rows = _setup_runtime_context(
        characterization_modules,
        tmp_path,
    )

    def _fake_run(*, repo_root, args, timeout_seconds=None):  # noqa: ANN001
        if "--collect-only" in args:
            return _completed(
                "tests/characterization/safety_contract/test_unknown.py::test_unknown\n"
            )
        return _completed("1 passed\n")

    monkeypatch.setattr(characterization_checks, "_run_pytest_command", _fake_run)
    result = characterization_checks.CheckResult()

    report = characterization_checks._check_runtime_characterization_gate(
        repo_root,
        parity_rows,
        result,
    )

    assert any(
        info.startswith("runtime_gate.parity_mapping_empty") for info in report.infos
    )
    assert not any(
        "runtime_gate.parity_mapping_empty" in warning for warning in result.warnings
    )
