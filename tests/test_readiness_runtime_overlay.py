"""Unit tests for claim-scoped runtime overlay in COV-03 readiness checks."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests._readiness_test_helpers import (
    runtime_report,
    set_route_row,
    set_workflow_cell,
    setup_readiness_repo,
)

pytest_plugins = ("tests._readiness_test_helpers",)


def test_readiness_runtime_overlay_ignores_unrelated_target_warning(
    readiness_modules,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    """Runtime warnings from unrelated targets must not fail a readiness claim."""
    (
        _characterization_contract,
        characterization_checks,
        _parity_contract,
        readiness_checks,
        _parity_checks,
    ) = readiness_modules
    repo_root, parity_contract, _ = setup_readiness_repo(readiness_modules, tmp_path)
    set_workflow_cell(repo_root, debt_status="closed")
    set_route_row(
        repo_root,
        parity_contract,
        command="run",
        mode="backdrop",
        owner_slice="Slice-Test",
        parity_status="ready",
    )

    unrelated = characterization_checks.RuntimeGateDiagnostic(
        category="execution_failed",
        targets=("tests/characterization/cli_contract",),
        mapped_parity_ids=("PIPE-BACKDROP-001",),
    )
    monkeypatch.setattr(
        readiness_checks,
        "_check_runtime_characterization_gate",
        lambda *_args, **_kwargs: runtime_report(
            characterization_checks,
            diagnostics=(unrelated,),
        ),
    )

    result = readiness_checks.check_readiness_artifacts(repo_root)
    assert not any(
        error.startswith("readiness.runtime_not_green") for error in result.errors
    )
    assert not result.errors


def test_readiness_runtime_overlay_fails_on_claim_target_warning(
    readiness_modules,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    """Runtime warnings intersecting claim targets must fail readiness."""
    (
        _characterization_contract,
        characterization_checks,
        _parity_contract,
        readiness_checks,
        _parity_checks,
    ) = readiness_modules
    repo_root, parity_contract, _ = setup_readiness_repo(readiness_modules, tmp_path)
    set_workflow_cell(repo_root, debt_status="closed")
    set_route_row(
        repo_root,
        parity_contract,
        command="run",
        mode="backdrop",
        owner_slice="Slice-Test",
        parity_status="ready",
    )

    targeted = characterization_checks.RuntimeGateDiagnostic(
        category="execution_failed",
        targets=("tests/characterization/safety_contract",),
        mapped_parity_ids=("PIPE-BACKDROP-001",),
    )
    monkeypatch.setattr(
        readiness_checks,
        "_check_runtime_characterization_gate",
        lambda *_args, **_kwargs: runtime_report(
            characterization_checks,
            diagnostics=(targeted,),
        ),
    )

    result = readiness_checks.check_readiness_artifacts(repo_root)
    assert any(
        error.startswith("readiness.runtime_not_green") for error in result.errors
    )


def test_readiness_runtime_overlay_fails_when_parity_unmapped(
    readiness_modules,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    """Ready claims require claim parity IDs in runtime mapped parity output."""
    (
        _characterization_contract,
        characterization_checks,
        _parity_contract,
        readiness_checks,
        _parity_checks,
    ) = readiness_modules
    repo_root, parity_contract, _ = setup_readiness_repo(readiness_modules, tmp_path)
    set_workflow_cell(repo_root, debt_status="closed")
    set_route_row(
        repo_root,
        parity_contract,
        command="run",
        mode="backdrop",
        owner_slice="Slice-Test",
        parity_status="ready",
    )

    monkeypatch.setattr(
        readiness_checks,
        "_check_runtime_characterization_gate",
        lambda *_args, **_kwargs: runtime_report(
            characterization_checks,
            mapped_parity_ids=(),
            diagnostics=(),
        ),
    )

    result = readiness_checks.check_readiness_artifacts(repo_root)
    assert any(
        error.startswith("readiness.runtime_unmapped_parity") for error in result.errors
    )
