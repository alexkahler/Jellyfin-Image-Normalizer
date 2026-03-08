"""Unit tests for core COV-03 readiness semantic checks."""

from __future__ import annotations

from pathlib import Path

from tests._readiness_test_helpers import (
    runtime_report,
    set_parity_row,
    set_route_row,
    set_workflow_cell,
    setup_readiness_repo,
)

pytest_plugins = ("tests._readiness_test_helpers",)


def test_readiness_fails_on_invalid_status_token(readiness_modules, tmp_path: Path):
    """Route rows with non pending|ready status should fail readiness checks."""
    repo_root, parity_contract, readiness_checks = setup_readiness_repo(
        readiness_modules, tmp_path
    )
    set_route_row(
        repo_root,
        parity_contract,
        command="run",
        mode="backdrop",
        parity_status="review",
    )

    result = readiness_checks.check_readiness_artifacts(repo_root)
    assert any(error.startswith("readiness.invalid_status") for error in result.errors)


def test_readiness_fails_when_route_v1_without_ready_status(
    readiness_modules,
    tmp_path: Path,
):
    """route=v1 rows must also declare parity status=ready."""
    repo_root, parity_contract, readiness_checks = setup_readiness_repo(
        readiness_modules, tmp_path
    )
    set_workflow_cell(repo_root, debt_status="closed")
    set_route_row(
        repo_root,
        parity_contract,
        command="run",
        mode="backdrop",
        route="v1",
        parity_status="pending",
    )

    result = readiness_checks.check_readiness_artifacts(repo_root)
    assert any(
        error.startswith("readiness.route_requires_ready_status")
        for error in result.errors
    )


def test_readiness_fails_for_unmapped_ready_cell(readiness_modules, tmp_path: Path):
    """Rows outside workflow mapping cannot claim readiness."""
    repo_root, parity_contract, readiness_checks = setup_readiness_repo(
        readiness_modules, tmp_path
    )
    set_route_row(
        repo_root,
        parity_contract,
        command="run",
        mode="logo",
        parity_status="ready",
    )

    result = readiness_checks.check_readiness_artifacts(repo_root)
    assert any(
        error.startswith("readiness.unmapped_ready_cell") for error in result.errors
    )


def test_readiness_fails_for_missing_required_parity_id(
    readiness_modules, tmp_path: Path
):
    """Ready claims must reference existing parity rows."""
    repo_root, parity_contract, readiness_checks = setup_readiness_repo(
        readiness_modules, tmp_path
    )
    set_workflow_cell(
        repo_root, parity_ids=["PIPE-NOT-FOUND-001"], debt_status="closed"
    )
    set_route_row(
        repo_root,
        parity_contract,
        command="run",
        mode="backdrop",
        parity_status="ready",
    )

    result = readiness_checks.check_readiness_artifacts(repo_root)
    assert any(
        error.startswith("readiness.parity_id_missing") for error in result.errors
    )


def test_readiness_fails_when_parity_not_preserved(readiness_modules, tmp_path: Path):
    """Ready claims require preserved parity rows with matches-baseline result."""
    repo_root, parity_contract, readiness_checks = setup_readiness_repo(
        readiness_modules, tmp_path
    )
    set_workflow_cell(repo_root, debt_status="closed")
    set_parity_row(repo_root, parity_contract, "PIPE-BACKDROP-001", status="changed")
    set_route_row(
        repo_root,
        parity_contract,
        command="run",
        mode="backdrop",
        parity_status="ready",
    )

    result = readiness_checks.check_readiness_artifacts(repo_root)
    assert any(
        error.startswith("readiness.parity_not_preserved") for error in result.errors
    )


def test_readiness_fails_when_baseline_link_invalid(readiness_modules, tmp_path: Path):
    """Ready claims require baseline_source that resolves to an existing baseline case."""
    repo_root, parity_contract, readiness_checks = setup_readiness_repo(
        readiness_modules, tmp_path
    )
    set_workflow_cell(repo_root, debt_status="closed")
    set_parity_row(
        repo_root,
        parity_contract,
        "PIPE-BACKDROP-001",
        baseline_source="tests/characterization/baselines/safety_contract_baseline.json#MISSING-ID",
    )
    set_route_row(
        repo_root,
        parity_contract,
        command="run",
        mode="backdrop",
        parity_status="ready",
    )

    result = readiness_checks.check_readiness_artifacts(repo_root)
    assert any(
        error.startswith("readiness.baseline_link_invalid") for error in result.errors
    )


def test_readiness_fails_on_owner_linkage_subset_violation(
    readiness_modules,
    tmp_path: Path,
):
    """Workflow owner tests must be represented by required parity-owner evidence."""
    repo_root, parity_contract, readiness_checks = setup_readiness_repo(
        readiness_modules, tmp_path
    )
    set_workflow_cell(
        repo_root,
        owner_tests=[
            "tests/characterization/safety_contract/test_safety_contract_restore.py::test_rst_path_001"
        ],
        debt_status="closed",
    )
    set_route_row(
        repo_root,
        parity_contract,
        command="run",
        mode="backdrop",
        parity_status="ready",
    )

    result = readiness_checks.check_readiness_artifacts(repo_root)
    assert any(
        error.startswith("readiness.owner_linkage_mismatch") for error in result.errors
    )


def test_readiness_fails_when_blocked_by_open_debt(readiness_modules, tmp_path: Path):
    """Open readiness-blocking workflow debt should block readiness claims."""
    repo_root, parity_contract, readiness_checks = setup_readiness_repo(
        readiness_modules, tmp_path
    )
    set_workflow_cell(repo_root, debt_status="open")
    set_route_row(
        repo_root,
        parity_contract,
        command="run",
        mode="backdrop",
        parity_status="ready",
    )

    result = readiness_checks.check_readiness_artifacts(repo_root)
    assert any(error.startswith("readiness.blocked_by_debt") for error in result.errors)


def test_readiness_evaluates_run_backdrop_real_claim_candidate_after_debt_closure(
    readiness_modules,
    tmp_path: Path,
    monkeypatch,
):
    """Readiness should validate a real run|backdrop claim candidate without route activation."""
    (
        _characterization_contract,
        characterization_checks,
        _parity_contract,
        readiness_checks,
        _parity_checks,
    ) = readiness_modules
    repo_root, parity_contract, _ = setup_readiness_repo(readiness_modules, tmp_path)
    set_workflow_cell(
        repo_root,
        parity_ids=["PIPE-BACKDROP-001", "PIPE-BACKDROP-002"],
        owner_tests=[
            "tests/characterization/safety_contract/test_safety_contract_pipeline.py::test_pipe_backdrop_001",
            "tests/characterization/safety_contract/test_safety_contract_pipeline_backdrop_split.py::test_pipe_backdrop_002",
        ],
        debt_status="closed",
    )
    set_route_row(
        repo_root,
        parity_contract,
        command="run",
        mode="backdrop",
        parity_status="ready",
    )

    route_table = parity_contract.load_marked_route_fence_table(
        repo_root / "project/route-fence.md"
    )
    run_backdrop_row = next(
        row
        for row in route_table.rows
        if row["command"] == "run" and row["mode"] == "backdrop"
    )
    assert run_backdrop_row["route(v0|v1)"] == "v0"

    monkeypatch.setattr(
        readiness_checks,
        "_check_runtime_characterization_gate",
        lambda *_args, **_kwargs: runtime_report(
            characterization_checks,
            mapped_parity_ids=("PIPE-BACKDROP-001", "PIPE-BACKDROP-002"),
            diagnostics=(),
        ),
    )

    result = readiness_checks.check_readiness_artifacts(repo_root)
    readiness_report = getattr(result, "readiness_report")
    assert not result.errors
    assert readiness_report.claimed_rows == 1
    assert readiness_report.validated_rows == 1


def test_readiness_passes_for_fully_proven_ready_claim(
    readiness_modules, tmp_path: Path
):
    """A ready claim should pass when workflow, parity, debt, and runtime proof all align."""
    repo_root, parity_contract, readiness_checks = setup_readiness_repo(
        readiness_modules, tmp_path
    )
    set_workflow_cell(repo_root, debt_status="closed")
    set_route_row(
        repo_root,
        parity_contract,
        command="run",
        mode="backdrop",
        parity_status="ready",
    )

    result = readiness_checks.check_readiness_artifacts(repo_root)
    readiness_report = getattr(result, "readiness_report")
    assert not result.errors
    assert readiness_report.claimed_rows == 1
    assert readiness_report.validated_rows == 1
