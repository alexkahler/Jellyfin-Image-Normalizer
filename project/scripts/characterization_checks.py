"""Characterization artifact checks for WI-004, WI-003, and WI-005 governance enforcement."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from characterization_contract import (
    IMG_BEHAVIOR_IDS,
    IMAGING_BASELINE_PATH,
    IMAGING_EXPECTED_MAX_BYTES,
    IMAGING_EXPECTED_MAX_FILES,
    IMAGING_EXPECTED_ROOT,
    IMAGING_FIXTURE_MAX_BYTES,
    IMAGING_FIXTURE_MAX_FILES,
    IMAGING_FIXTURE_ROOT,
    IMAGING_GOLDEN_MANIFEST_PATH,
    REQUIRED_BASELINE_FILES,
    REQUIRED_CHARACTERIZATION_BEHAVIOR_IDS,
    CharacterizationError,
    load_baseline_payload,
    load_imaging_golden_manifest,
    owner_test_exists,
    parse_baseline_source,
    parse_owner_test_reference,
    validate_baseline_case_schema,
)
from governance_contract import (
    CheckResult,
    GovernanceError,
    parse_verification_contract,
)
from parity_contract import (
    REQUIRED_PARITY_COLUMNS,
    load_markdown_table,
    load_marked_route_fence_table,
)
from surface_coverage_checks import check_surface_coverage_artifacts

REQUIRED_COLLECTABILITY_PYTEST_COMMAND = "PYTHONPATH=src ./.venv/bin/python -m pytest"
COLLECT_ONLY_NODEID_PATTERN = re.compile(r"^tests[\\/].+::.+$")
RUNTIME_GATE_TIMEOUT_BUFFER_SECONDS = 15
WORKFLOW_COVERAGE_INDEX_PATH = "project/workflow-coverage-index.json"
ALLOWED_WORKFLOW_SEVERITY_VALUES = {"block", "warn"}
WORKFLOW_DEFAULT_CONTRACT_SEVERITY = "block"
WORKFLOW_DEFAULT_SEQUENCE_SEVERITY = "warn"


@dataclass(frozen=True)
class CollectabilityReport:
    """Collectability counters surfaced by governance output."""

    total_owner_nodeids: int
    resolved_owner_nodeids: int
    unresolved_owner_nodeids: int


@dataclass(frozen=True)
class RuntimeGateReport:
    """Runtime characterization gate counters surfaced by governance output."""

    configured_targets: tuple[str, ...]
    checked_targets: int
    passed_targets: int
    failed_targets: int
    budget_seconds: int
    elapsed_seconds: float
    mapped_parity_ids: tuple[str, ...]
    infos: tuple[str, ...]


@dataclass(frozen=True)
class WorkflowCoverageReport:
    """Workflow-coverage gate counters surfaced by governance output."""

    configured_cells: int
    validated_cells: int
    contract_errors: int
    sequence_warnings: int
    count_only_warnings: int
    open_debts: int


def _add_collectability_error(
    result: CheckResult,
    category: str,
    behavior_id: str,
    detail: str,
) -> None:
    """Record one deterministic collectability error with stable taxonomy."""
    result.add_error(f"collectability.{category}: {behavior_id}: {detail}")


def _has_collectability_contract_context(repo_root: Path, result: CheckResult) -> bool:
    """Ensure collectability checks run under the verification-contract pytest context."""
    contract_path = repo_root / "project" / "verification-contract.yml"
    try:
        contract = parse_verification_contract(contract_path)
    except GovernanceError as exc:
        result.add_error(f"collectability.contract_context_missing: {exc}")
        return False
    if REQUIRED_COLLECTABILITY_PYTEST_COMMAND not in contract.verification_commands:
        result.add_error(
            "collectability.contract_context_missing: verification_commands missing "
            f"required command '{REQUIRED_COLLECTABILITY_PYTEST_COMMAND}'."
        )
        return False
    return True


def _looks_like_collect_only_nodeid(line: str) -> bool:
    """Return True when one collect-only output line is a pytest nodeid."""
    stripped = line.strip()
    if not stripped:
        return False
    if stripped.startswith("=") or stripped.startswith("-"):
        return False
    if "collected" in stripped:
        return False
    if " " in stripped:
        return False
    return bool(COLLECT_ONLY_NODEID_PATTERN.match(stripped))


def _normalize_nodeid(nodeid: str) -> str:
    """Normalize nodeids to repo-relative POSIX-style strings."""
    return nodeid.strip().replace("\\", "/")


def _run_pytest_command(
    *,
    repo_root: Path,
    args: list[str],
    timeout_seconds: float | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run pytest with deterministic repo-root context and captured output."""
    env = {**os.environ, "PYTHONPATH": "src"}
    return subprocess.run(
        [sys.executable, "-m", "pytest", *args],
        cwd=repo_root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout_seconds,
    )


def _first_non_empty_output(*streams: str) -> str:
    """Return first non-empty output line from ordered streams."""
    for stream in streams:
        for line in stream.splitlines():
            if line.strip():
                return line.strip()
    return "<no output>"


def _target_path_part(target: str) -> str:
    """Return the filesystem path portion of a target or nodeid."""
    return target.split("::", 1)[0]


def _nodeid_matches_target(nodeid: str, target: str) -> bool:
    """Return True when a normalized nodeid belongs to a normalized target."""
    normalized_nodeid = _normalize_nodeid(nodeid)
    normalized_target = _normalize_nodeid(target)
    node_path = _target_path_part(normalized_nodeid).rstrip("/")
    target_path = _target_path_part(normalized_target).rstrip("/")
    if "::" in normalized_target:
        return normalized_nodeid.startswith(normalized_target)
    if target_path.endswith(".py"):
        return node_path == target_path
    return node_path.startswith(target_path + "/")


def _collect_characterization_nodeids(repo_root: Path, result: CheckResult) -> set[str]:
    """Collect characterization nodeids via pinned repo-root pytest context."""
    completed = _run_pytest_command(
        repo_root=repo_root,
        args=["--collect-only", "-q", "tests/characterization"],
    )
    if completed.returncode != 0:
        detail = _first_non_empty_output(completed.stderr, completed.stdout)
        result.add_error(
            "collectability.collect_only_failed: "
            "pytest --collect-only failed for tests/characterization "
            f"(exit_code={completed.returncode}, detail={detail!r})."
        )
        return set()
    nodeids: set[str] = set()
    for line in completed.stdout.splitlines():
        if _looks_like_collect_only_nodeid(line):
            nodeids.add(_normalize_nodeid(line))
    return nodeids


def _check_owner_collectability(
    repo_root: Path,
    parity_rows: dict[str, dict[str, str]],
    result: CheckResult,
) -> CollectabilityReport:
    """Validate parity-owned owner_test nodeids are collectable under pytest."""
    total_owner_nodeids = len(REQUIRED_CHARACTERIZATION_BEHAVIOR_IDS)
    resolved_owner_nodeids = 0

    owner_nodeids: dict[str, str] = {}
    for behavior_id in REQUIRED_CHARACTERIZATION_BEHAVIOR_IDS:
        row = parity_rows.get(behavior_id)
        if row is None:
            continue
        owner_test = row.get("owner_test", "").strip()
        if not owner_test:
            _add_collectability_error(
                result,
                "owner_ref_invalid",
                behavior_id,
                "owner_test must be non-empty.",
            )
            continue
        try:
            owner_path_part, owner_function = parse_owner_test_reference(owner_test)
        except CharacterizationError as exc:
            _add_collectability_error(
                result,
                "owner_ref_invalid",
                behavior_id,
                str(exc),
            )
            continue

        normalized_owner_path = owner_path_part.replace("\\", "/")
        if not normalized_owner_path.startswith("tests/characterization/"):
            _add_collectability_error(
                result,
                "contract_gap",
                behavior_id,
                "owner_test must be under tests/characterization/ for verification-contract inclusion.",
            )
            continue

        owner_test_path = repo_root / normalized_owner_path
        if not owner_test_path.exists():
            _add_collectability_error(
                result,
                "owner_file_missing",
                behavior_id,
                f"owner_test file not found: {normalized_owner_path}",
            )
            continue
        if not owner_test_exists(owner_test_path, owner_function):
            _add_collectability_error(
                result,
                "owner_symbol_missing",
                behavior_id,
                f"owner_test function '{owner_function}' not found in {normalized_owner_path}.",
            )
            continue
        owner_nodeids[behavior_id] = f"{normalized_owner_path}::{owner_function}"

    if not _has_collectability_contract_context(repo_root, result):
        unresolved_owner_nodeids = total_owner_nodeids - resolved_owner_nodeids
        return CollectabilityReport(
            total_owner_nodeids=total_owner_nodeids,
            resolved_owner_nodeids=resolved_owner_nodeids,
            unresolved_owner_nodeids=unresolved_owner_nodeids,
        )

    collected_nodeids = _collect_characterization_nodeids(repo_root, result)
    if not collected_nodeids:
        unresolved_owner_nodeids = total_owner_nodeids - resolved_owner_nodeids
        return CollectabilityReport(
            total_owner_nodeids=total_owner_nodeids,
            resolved_owner_nodeids=resolved_owner_nodeids,
            unresolved_owner_nodeids=unresolved_owner_nodeids,
        )

    for behavior_id in sorted(owner_nodeids):
        owner_nodeid = owner_nodeids[behavior_id]
        if owner_nodeid not in collected_nodeids:
            _add_collectability_error(
                result,
                "collect_only_unresolved",
                behavior_id,
                (
                    "owner_test nodeid is not collectable via "
                    "'PYTHONPATH=src ./.venv/bin/python -m pytest --collect-only -q <nodeid>'. "
                    f"(nodeid={owner_nodeid})"
                ),
            )
            continue
        resolved_owner_nodeids += 1

    unresolved_owner_nodeids = total_owner_nodeids - resolved_owner_nodeids
    return CollectabilityReport(
        total_owner_nodeids=total_owner_nodeids,
        resolved_owner_nodeids=resolved_owner_nodeids,
        unresolved_owner_nodeids=unresolved_owner_nodeids,
    )


def _add_runtime_gate_warning(
    result: CheckResult,
    category: str,
    detail: str,
) -> None:
    """Record one deterministic runtime-gate warning with stable taxonomy."""
    result.add_warning(f"runtime_gate.{category}: {detail}")


def _add_workflow_contract_finding(
    result: CheckResult,
    *,
    severity: str,
    category: str,
    detail: str,
) -> None:
    """Record one workflow-coverage contract finding."""
    message = f"workflow_coverage.contract_{category}: {detail}"
    if severity == "warn":
        result.add_warning(message)
        return
    result.add_error(message)


def _add_workflow_sequence_finding(
    result: CheckResult,
    *,
    severity: str,
    category: str,
    detail: str,
) -> None:
    """Record one workflow-coverage sequence finding."""
    message = f"workflow_coverage.sequence_gap.{category}: {detail}"
    if severity == "block":
        result.add_error(message)
        return
    result.add_warning(message)


def _normalize_runtime_targets(targets: list[str]) -> list[str]:
    """Normalize runtime target strings to repo-relative POSIX paths/nodeids."""
    return [_normalize_nodeid(target) for target in targets]


def _owner_nodeids_for_targets(
    parity_rows: dict[str, dict[str, str]],
    targets: list[str],
) -> dict[str, str]:
    """Return parity owner nodeids that belong to configured runtime targets."""
    owner_nodeids: dict[str, str] = {}
    for behavior_id, row in parity_rows.items():
        owner_test = row.get("owner_test", "").strip()
        if not owner_test:
            continue
        try:
            owner_path, owner_function = parse_owner_test_reference(owner_test)
        except CharacterizationError:
            continue
        owner_nodeid = _normalize_nodeid(f"{owner_path}::{owner_function}")
        if any(_nodeid_matches_target(owner_nodeid, target) for target in targets):
            owner_nodeids[behavior_id] = owner_nodeid
    return owner_nodeids


def _collect_runtime_target_nodeids(
    repo_root: Path,
    targets: list[str],
    timeout_seconds: float,
    result: CheckResult,
    parity_ids: list[str],
) -> set[str]:
    """Collect nodeids for configured runtime targets."""
    try:
        completed = _run_pytest_command(
            repo_root=repo_root,
            args=["--collect-only", "-q", *targets],
            timeout_seconds=timeout_seconds,
        )
    except subprocess.TimeoutExpired:
        _add_runtime_gate_warning(
            result,
            "timeout",
            (
                "collect-only timed out for runtime targets "
                f"{targets} with mapped_parity_ids={parity_ids}."
            ),
        )
        return set()

    if completed.returncode != 0:
        detail = _first_non_empty_output(completed.stderr, completed.stdout)
        _add_runtime_gate_warning(
            result,
            "execution_failed",
            (
                "collect-only failed for runtime targets "
                f"{targets} (exit_code={completed.returncode}, detail={detail!r}, "
                f"mapped_parity_ids={parity_ids})."
            ),
        )
        return set()

    nodeids: set[str] = set()
    for line in completed.stdout.splitlines():
        if _looks_like_collect_only_nodeid(line):
            nodeids.add(_normalize_nodeid(line))
    return nodeids


def _check_runtime_characterization_gate(
    repo_root: Path,
    parity_rows: dict[str, dict[str, str]],
    result: CheckResult,
) -> RuntimeGateReport:
    """Run Slice-10 runtime characterization gate for configured targets."""
    contract_path = repo_root / "project" / "verification-contract.yml"
    try:
        contract = parse_verification_contract(contract_path)
    except GovernanceError as exc:
        _add_runtime_gate_warning(
            result,
            "target_invalid",
            f"unable to parse runtime gate contract context: {exc}",
        )
        return RuntimeGateReport(
            configured_targets=(),
            checked_targets=0,
            passed_targets=0,
            failed_targets=0,
            budget_seconds=0,
            elapsed_seconds=0.0,
            mapped_parity_ids=(),
            infos=(),
        )

    configured_targets = _normalize_runtime_targets(contract.runtime_gate.targets)
    budget_seconds = contract.runtime_gate.budget_seconds
    warning_start = len(result.warnings)
    valid_targets: list[str] = []
    for target in configured_targets:
        target_path_part = _target_path_part(target)
        if not target_path_part.startswith("tests/characterization/"):
            _add_runtime_gate_warning(
                result,
                "target_invalid",
                f"target must be under tests/characterization/: {target!r}",
            )
            continue
        if not (repo_root / target_path_part).exists():
            _add_runtime_gate_warning(
                result,
                "target_invalid",
                f"target path not found: {target_path_part!r}",
            )
            continue
        valid_targets.append(target)

    start_time = time.monotonic()
    infos: list[str] = []

    owner_nodeids = _owner_nodeids_for_targets(parity_rows, valid_targets)
    candidate_parity_ids = sorted(owner_nodeids)
    mapped_parity_ids: list[str] = []
    timeout_seconds = float(budget_seconds + RUNTIME_GATE_TIMEOUT_BUFFER_SECONDS)

    if valid_targets:
        collected_nodeids = _collect_runtime_target_nodeids(
            repo_root=repo_root,
            targets=valid_targets,
            timeout_seconds=timeout_seconds,
            result=result,
            parity_ids=candidate_parity_ids,
        )
        if collected_nodeids:
            mapped_parity_ids = sorted(
                behavior_id
                for behavior_id, owner_nodeid in owner_nodeids.items()
                if owner_nodeid in collected_nodeids
            )
            if not mapped_parity_ids:
                infos.append(
                    "runtime_gate.parity_mapping_empty: no parity owner nodeids intersect "
                    f"collect-only nodeids for targets {valid_targets}."
                )

    elapsed_before_runtime = time.monotonic() - start_time
    timeout_remaining = timeout_seconds - elapsed_before_runtime
    if timeout_remaining <= 0:
        _add_runtime_gate_warning(
            result,
            "timeout",
            (
                "runtime execution skipped because collect+run exceeded timeout budget "
                f"for targets {valid_targets} with mapped_parity_ids={mapped_parity_ids}."
            ),
        )
    elif valid_targets and not any(
        warning.startswith("runtime_gate.timeout")
        or warning.startswith("runtime_gate.execution_failed")
        for warning in result.warnings[warning_start:]
    ):
        try:
            completed = _run_pytest_command(
                repo_root=repo_root,
                args=["-q", "--maxfail=1", *valid_targets],
                timeout_seconds=timeout_remaining,
            )
        except subprocess.TimeoutExpired:
            _add_runtime_gate_warning(
                result,
                "timeout",
                (
                    "runtime execution timed out for targets "
                    f"{valid_targets} with mapped_parity_ids={mapped_parity_ids}."
                ),
            )
        else:
            if completed.returncode != 0:
                detail = _first_non_empty_output(completed.stderr, completed.stdout)
                _add_runtime_gate_warning(
                    result,
                    "execution_failed",
                    (
                        "runtime execution failed for targets "
                        f"{valid_targets} (exit_code={completed.returncode}, "
                        f"detail={detail!r}, mapped_parity_ids={mapped_parity_ids})."
                    ),
                )

    elapsed_seconds = time.monotonic() - start_time
    runtime_warnings = result.warnings[warning_start:]
    timed_out = any(
        warning.startswith("runtime_gate.timeout") for warning in runtime_warnings
    )
    if not timed_out and elapsed_seconds > float(budget_seconds):
        _add_runtime_gate_warning(
            result,
            "budget_exceeded",
            (
                "collect+run elapsed time exceeded runtime gate budget "
                f"(elapsed_seconds={elapsed_seconds:.3f}, "
                f"budget_seconds={budget_seconds}, targets={valid_targets}, "
                f"mapped_parity_ids={mapped_parity_ids})."
            ),
        )

    warning_count = len(result.warnings) - warning_start
    checked_targets = len(valid_targets)
    passed_targets = checked_targets if warning_count == 0 else 0
    if checked_targets == 0:
        failed_targets = len(configured_targets) if warning_count else 0
    else:
        failed_targets = checked_targets if warning_count else 0

    return RuntimeGateReport(
        configured_targets=tuple(configured_targets),
        checked_targets=checked_targets,
        passed_targets=passed_targets,
        failed_targets=failed_targets,
        budget_seconds=budget_seconds,
        elapsed_seconds=elapsed_seconds,
        mapped_parity_ids=tuple(mapped_parity_ids),
        infos=tuple(infos),
    )


def _load_all_parity_rows(
    repo_root: Path,
    result: CheckResult,
) -> dict[str, dict[str, str]]:
    """Load all parity-matrix rows by behavior ID."""
    parity_matrix_path = repo_root / "project" / "parity-matrix.md"
    try:
        table = load_markdown_table(
            parity_matrix_path,
            REQUIRED_PARITY_COLUMNS,
            "parity-matrix",
        )
    except Exception as exc:  # pragma: no cover - parity check tests cover this path
        result.add_error(str(exc))
        return {}
    return {row["behavior_id"]: row for row in table.rows}


def _resolve_dotted_path(
    payload: dict[str, Any],
    dotted_path: str,
) -> tuple[bool, Any]:
    """Resolve one dotted key-path from a dict payload."""
    current: Any = payload
    for token in dotted_path.split("."):
        if not isinstance(current, dict) or token not in current:
            return False, None
        current = current[token]
    return True, current


def _normalize_string_list(
    *,
    value: Any,
    field_name: str,
    cell_key: str,
    result: CheckResult,
) -> list[str] | None:
    """Normalize and validate one required list[str] workflow cell field."""
    if not isinstance(value, list) or not value:
        _add_workflow_contract_finding(
            result,
            severity="block",
            category="schema",
            detail=(
                f"cell={cell_key} field '{field_name}' must be a non-empty list[str]."
            ),
        )
        return None
    normalized: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            _add_workflow_contract_finding(
                result,
                severity="block",
                category="schema",
                detail=(
                    f"cell={cell_key} field '{field_name}' must contain non-empty strings."
                ),
            )
            return None
        normalized.append(item.strip())
    return normalized


def _normalize_workflow_cell(
    *,
    cell_key: str,
    cell_payload: Any,
    result: CheckResult,
) -> dict[str, Any] | None:
    """Validate and normalize one workflow-coverage index cell payload."""
    if not isinstance(cell_payload, dict):
        _add_workflow_contract_finding(
            result,
            severity="block",
            category="schema",
            detail=f"cell={cell_key} must be an object.",
        )
        return None

    required_keys = {
        "command",
        "mode",
        "required_parity_ids",
        "required_owner_tests",
        "evidence_layout",
        "required_evidence_fields",
        "required_ordering_tokens",
        "future_split_debt",
    }
    missing_keys = sorted(required_keys - set(cell_payload))
    if missing_keys:
        _add_workflow_contract_finding(
            result,
            severity="block",
            category="schema",
            detail=f"cell={cell_key} missing required keys: {missing_keys}.",
        )
        return None

    command = cell_payload.get("command")
    mode = cell_payload.get("mode")
    if not isinstance(command, str) or not command.strip():
        _add_workflow_contract_finding(
            result,
            severity="block",
            category="schema",
            detail=f"cell={cell_key} field 'command' must be non-empty string.",
        )
        return None
    if not isinstance(mode, str) or not mode.strip():
        _add_workflow_contract_finding(
            result,
            severity="block",
            category="schema",
            detail=f"cell={cell_key} field 'mode' must be non-empty string.",
        )
        return None
    command = command.strip()
    mode = mode.strip()
    expected_key = f"{command}|{mode}"
    if cell_key != expected_key:
        _add_workflow_contract_finding(
            result,
            severity="block",
            category="schema",
            detail=f"cell key '{cell_key}' must match command|mode '{expected_key}'.",
        )
        return None

    required_parity_ids = _normalize_string_list(
        value=cell_payload.get("required_parity_ids"),
        field_name="required_parity_ids",
        cell_key=cell_key,
        result=result,
    )
    if required_parity_ids is None:
        return None
    required_owner_tests = _normalize_string_list(
        value=cell_payload.get("required_owner_tests"),
        field_name="required_owner_tests",
        cell_key=cell_key,
        result=result,
    )
    if required_owner_tests is None:
        return None
    required_evidence_fields = _normalize_string_list(
        value=cell_payload.get("required_evidence_fields"),
        field_name="required_evidence_fields",
        cell_key=cell_key,
        result=result,
    )
    if required_evidence_fields is None:
        return None
    required_ordering_tokens = _normalize_string_list(
        value=cell_payload.get("required_ordering_tokens"),
        field_name="required_ordering_tokens",
        cell_key=cell_key,
        result=result,
    )
    if required_ordering_tokens is None:
        return None

    evidence_layout = cell_payload.get("evidence_layout")
    if not isinstance(evidence_layout, dict):
        _add_workflow_contract_finding(
            result,
            severity="block",
            category="schema",
            detail=f"cell={cell_key} field 'evidence_layout' must be an object.",
        )
        return None
    field_container = evidence_layout.get("field_container")
    ordering_container = evidence_layout.get("ordering_container")
    if not isinstance(field_container, str) or not field_container.strip():
        _add_workflow_contract_finding(
            result,
            severity="block",
            category="schema",
            detail=(
                f"cell={cell_key} evidence_layout.field_container must be non-empty string."
            ),
        )
        return None
    if not isinstance(ordering_container, str) or not ordering_container.strip():
        _add_workflow_contract_finding(
            result,
            severity="block",
            category="schema",
            detail=(
                f"cell={cell_key} evidence_layout.ordering_container must be non-empty string."
            ),
        )
        return None

    raw_severity = cell_payload.get("severity")
    if raw_severity is None:
        contract_severity = WORKFLOW_DEFAULT_CONTRACT_SEVERITY
        sequence_severity = WORKFLOW_DEFAULT_SEQUENCE_SEVERITY
    elif isinstance(raw_severity, dict):
        contract_severity = str(
            raw_severity.get("contract", WORKFLOW_DEFAULT_CONTRACT_SEVERITY)
        ).strip()
        sequence_severity = str(
            raw_severity.get("sequence", WORKFLOW_DEFAULT_SEQUENCE_SEVERITY)
        ).strip()
    else:
        _add_workflow_contract_finding(
            result,
            severity="block",
            category="schema",
            detail=f"cell={cell_key} field 'severity' must be an object when provided.",
        )
        return None

    if contract_severity not in ALLOWED_WORKFLOW_SEVERITY_VALUES:
        _add_workflow_contract_finding(
            result,
            severity="block",
            category="schema",
            detail=(
                f"cell={cell_key} severity.contract must be one of "
                f"{sorted(ALLOWED_WORKFLOW_SEVERITY_VALUES)}."
            ),
        )
        return None
    if sequence_severity not in ALLOWED_WORKFLOW_SEVERITY_VALUES:
        _add_workflow_contract_finding(
            result,
            severity="block",
            category="schema",
            detail=(
                f"cell={cell_key} severity.sequence must be one of "
                f"{sorted(ALLOWED_WORKFLOW_SEVERITY_VALUES)}."
            ),
        )
        return None

    debt = cell_payload.get("future_split_debt")
    if not isinstance(debt, dict):
        _add_workflow_contract_finding(
            result,
            severity="block",
            category="schema",
            detail=f"cell={cell_key} future_split_debt must be an object.",
        )
        return None
    for debt_key in (
        "id",
        "status",
        "readiness_blocking",
        "enforcement_phase",
        "closure",
    ):
        if debt_key not in debt:
            _add_workflow_contract_finding(
                result,
                severity="block",
                category="schema",
                detail=f"cell={cell_key} future_split_debt missing key '{debt_key}'.",
            )
            return None
    if not isinstance(debt["id"], str) or not debt["id"].strip():
        _add_workflow_contract_finding(
            result,
            severity="block",
            category="schema",
            detail=f"cell={cell_key} future_split_debt.id must be non-empty string.",
        )
        return None
    if not isinstance(debt["status"], str) or not debt["status"].strip():
        _add_workflow_contract_finding(
            result,
            severity="block",
            category="schema",
            detail=f"cell={cell_key} future_split_debt.status must be non-empty string.",
        )
        return None
    if not isinstance(debt["readiness_blocking"], bool):
        _add_workflow_contract_finding(
            result,
            severity="block",
            category="schema",
            detail=f"cell={cell_key} future_split_debt.readiness_blocking must be bool.",
        )
        return None
    if (
        not isinstance(debt["enforcement_phase"], str)
        or not debt["enforcement_phase"].strip()
    ):
        _add_workflow_contract_finding(
            result,
            severity="block",
            category="schema",
            detail=(
                f"cell={cell_key} future_split_debt.enforcement_phase must be non-empty string."
            ),
        )
        return None
    closure = debt["closure"]
    if not isinstance(closure, dict):
        _add_workflow_contract_finding(
            result,
            severity="block",
            category="schema",
            detail=f"cell={cell_key} future_split_debt.closure must be an object.",
        )
        return None
    if closure.get("type") != "parity_id_count_min":
        _add_workflow_contract_finding(
            result,
            severity="block",
            category="schema",
            detail=(
                f"cell={cell_key} future_split_debt.closure.type must be "
                "'parity_id_count_min'."
            ),
        )
        return None
    if closure.get("cell") != cell_key:
        _add_workflow_contract_finding(
            result,
            severity="block",
            category="schema",
            detail=(
                f"cell={cell_key} future_split_debt.closure.cell must equal '{cell_key}'."
            ),
        )
        return None
    min_required = closure.get("min_required")
    if isinstance(min_required, bool) or not isinstance(min_required, int):
        _add_workflow_contract_finding(
            result,
            severity="block",
            category="schema",
            detail=(
                f"cell={cell_key} future_split_debt.closure.min_required must be integer."
            ),
        )
        return None
    if min_required < 1:
        _add_workflow_contract_finding(
            result,
            severity="block",
            category="schema",
            detail=(
                f"cell={cell_key} future_split_debt.closure.min_required must be >= 1."
            ),
        )
        return None

    return {
        "cell_key": cell_key,
        "command": command,
        "mode": mode,
        "required_parity_ids": required_parity_ids,
        "required_owner_tests": required_owner_tests,
        "field_container": field_container.strip(),
        "ordering_container": ordering_container.strip(),
        "required_evidence_fields": required_evidence_fields,
        "required_ordering_tokens": required_ordering_tokens,
        "contract_severity": contract_severity,
        "sequence_severity": sequence_severity,
        "future_split_debt_status": str(debt["status"]).strip().lower(),
    }


def _load_workflow_cells(
    repo_root: Path,
    result: CheckResult,
) -> dict[str, dict[str, Any]]:
    """Load and validate workflow-coverage index cells."""
    workflow_path = repo_root / WORKFLOW_COVERAGE_INDEX_PATH
    try:
        payload = json.loads(workflow_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        _add_workflow_contract_finding(
            result,
            severity="block",
            category="missing_index",
            detail=f"workflow coverage index not found: {WORKFLOW_COVERAGE_INDEX_PATH}",
        )
        return {}
    except json.JSONDecodeError as exc:
        _add_workflow_contract_finding(
            result,
            severity="block",
            category="invalid_json",
            detail=f"{WORKFLOW_COVERAGE_INDEX_PATH} JSON decode failed: {exc}",
        )
        return {}

    if not isinstance(payload, dict):
        _add_workflow_contract_finding(
            result,
            severity="block",
            category="schema",
            detail=f"{WORKFLOW_COVERAGE_INDEX_PATH} payload must be an object.",
        )
        return {}
    if payload.get("version") != 1:
        _add_workflow_contract_finding(
            result,
            severity="block",
            category="schema",
            detail=(
                f"{WORKFLOW_COVERAGE_INDEX_PATH} version must be 1, found "
                f"{payload.get('version')!r}."
            ),
        )
        return {}

    raw_cells = payload.get("cells")
    if not isinstance(raw_cells, dict) or not raw_cells:
        _add_workflow_contract_finding(
            result,
            severity="block",
            category="schema",
            detail=f"{WORKFLOW_COVERAGE_INDEX_PATH} cells must be a non-empty object.",
        )
        return {}

    normalized_cells: dict[str, dict[str, Any]] = {}
    for cell_key, cell_payload in raw_cells.items():
        if not isinstance(cell_key, str) or not cell_key.strip():
            _add_workflow_contract_finding(
                result,
                severity="block",
                category="schema",
                detail=(
                    f"{WORKFLOW_COVERAGE_INDEX_PATH} cells must use non-empty string keys."
                ),
            )
            continue
        normalized = _normalize_workflow_cell(
            cell_key=cell_key.strip(),
            cell_payload=cell_payload,
            result=result,
        )
        if normalized is None:
            continue
        normalized_cells[normalized["cell_key"]] = normalized
    return normalized_cells


def _collect_workflow_owner_nodeids(
    repo_root: Path,
    result: CheckResult,
) -> set[str]:
    """Collect pytest nodeids for workflow owner-test validation."""
    completed = _run_pytest_command(
        repo_root=repo_root,
        args=["--collect-only", "-q", "tests/characterization"],
    )
    if completed.returncode != 0:
        detail = _first_non_empty_output(completed.stderr, completed.stdout)
        _add_workflow_contract_finding(
            result,
            severity="block",
            category="owner_collect_only_failed",
            detail=(
                "pytest --collect-only failed for tests/characterization "
                f"(exit_code={completed.returncode}, detail={detail!r})."
            ),
        )
        return set()

    nodeids: set[str] = set()
    for line in completed.stdout.splitlines():
        if _looks_like_collect_only_nodeid(line):
            nodeids.add(_normalize_nodeid(line))
    return nodeids


def _check_workflow_coverage(
    repo_root: Path,
    all_parity_rows: dict[str, dict[str, str]],
    baseline_cases_by_path: dict[str, dict[str, Any]],
    result: CheckResult,
) -> WorkflowCoverageReport:
    """Run workflow sequence coverage contract + evidence checks."""
    error_start = len(result.errors)
    warning_start = len(result.warnings)

    workflow_cells = _load_workflow_cells(repo_root, result)
    configured_cells = len(workflow_cells)
    validated_cells = 0
    open_debts = 0

    try:
        route_table = load_marked_route_fence_table(
            repo_root / "project" / "route-fence.md"
        )
        known_route_cells = {
            (row["command"].strip(), row["mode"].strip()) for row in route_table.rows
        }
    except Exception as exc:  # pragma: no cover - route-fence checks cover this path
        _add_workflow_contract_finding(
            result,
            severity="block",
            category="route_fence_load_failed",
            detail=str(exc),
        )
        known_route_cells = set()

    collected_owner_nodeids: set[str] | None = None
    collect_failed = False

    for cell_key in sorted(workflow_cells):
        cell = workflow_cells[cell_key]
        contract_severity = cell["contract_severity"]
        sequence_severity = cell["sequence_severity"]
        cell_had_contract_issue = False

        if (cell["command"], cell["mode"]) not in known_route_cells:
            _add_workflow_contract_finding(
                result,
                severity=contract_severity,
                category="route_cell_missing",
                detail=(
                    f"cell={cell_key} does not exist in project/route-fence.md command/mode rows."
                ),
            )
            cell_had_contract_issue = True

        if collected_owner_nodeids is None:
            collected_owner_nodeids = _collect_workflow_owner_nodeids(repo_root, result)
            collect_failed = not bool(collected_owner_nodeids)

        for owner_ref in cell["required_owner_tests"]:
            try:
                owner_path_part, owner_function = parse_owner_test_reference(owner_ref)
            except CharacterizationError as exc:
                _add_workflow_contract_finding(
                    result,
                    severity=contract_severity,
                    category="owner_ref_invalid",
                    detail=f"cell={cell_key} owner_test={owner_ref!r}: {exc}",
                )
                cell_had_contract_issue = True
                continue

            normalized_owner_path = owner_path_part.replace("\\", "/")
            if not normalized_owner_path.startswith("tests/characterization/"):
                _add_workflow_contract_finding(
                    result,
                    severity=contract_severity,
                    category="owner_ref_invalid",
                    detail=(
                        f"cell={cell_key} owner_test path must be under tests/characterization/, "
                        f"found '{owner_path_part}'."
                    ),
                )
                cell_had_contract_issue = True
                continue

            owner_test_path = repo_root / normalized_owner_path
            if not owner_test_path.exists():
                _add_workflow_contract_finding(
                    result,
                    severity=contract_severity,
                    category="owner_file_missing",
                    detail=(
                        f"cell={cell_key} owner_test file not found: {normalized_owner_path}"
                    ),
                )
                cell_had_contract_issue = True
                continue
            if not owner_test_exists(owner_test_path, owner_function):
                _add_workflow_contract_finding(
                    result,
                    severity=contract_severity,
                    category="owner_symbol_missing",
                    detail=(
                        f"cell={cell_key} owner_test function '{owner_function}' not found in "
                        f"{normalized_owner_path}."
                    ),
                )
                cell_had_contract_issue = True
                continue

            if not collect_failed:
                owner_nodeid = _normalize_nodeid(
                    f"{normalized_owner_path}::{owner_function}"
                )
                if owner_nodeid not in (collected_owner_nodeids or set()):
                    _add_workflow_contract_finding(
                        result,
                        severity=contract_severity,
                        category="owner_nodeid_uncollectable",
                        detail=(
                            f"cell={cell_key} owner_test nodeid is not collectable: "
                            f"{owner_nodeid}."
                        ),
                    )
                    cell_had_contract_issue = True

        for parity_id in cell["required_parity_ids"]:
            parity_row = all_parity_rows.get(parity_id)
            if parity_row is None:
                _add_workflow_contract_finding(
                    result,
                    severity=contract_severity,
                    category="parity_id_missing",
                    detail=f"cell={cell_key} required parity_id '{parity_id}' not found.",
                )
                cell_had_contract_issue = True
                continue

            baseline_source = parity_row.get("baseline_source", "").strip()
            if not baseline_source:
                _add_workflow_contract_finding(
                    result,
                    severity=contract_severity,
                    category="baseline_link_invalid",
                    detail=f"cell={cell_key} parity_id={parity_id} baseline_source is empty.",
                )
                cell_had_contract_issue = True
                continue

            try:
                baseline_path_part, baseline_anchor = parse_baseline_source(
                    baseline_source
                )
            except CharacterizationError as exc:
                _add_workflow_contract_finding(
                    result,
                    severity=contract_severity,
                    category="baseline_link_invalid",
                    detail=f"cell={cell_key} parity_id={parity_id}: {exc}",
                )
                cell_had_contract_issue = True
                continue

            normalized_baseline_path = baseline_path_part.replace("\\", "/")
            baseline_cases = baseline_cases_by_path.get(normalized_baseline_path)
            if baseline_cases is None:
                _add_workflow_contract_finding(
                    result,
                    severity=contract_severity,
                    category="baseline_link_invalid",
                    detail=(
                        f"cell={cell_key} parity_id={parity_id} baseline path "
                        f"'{normalized_baseline_path}' is unknown."
                    ),
                )
                cell_had_contract_issue = True
                continue
            case_payload = baseline_cases.get(baseline_anchor)
            if not isinstance(case_payload, dict):
                _add_workflow_contract_finding(
                    result,
                    severity=contract_severity,
                    category="baseline_link_invalid",
                    detail=(
                        f"cell={cell_key} parity_id={parity_id} baseline anchor "
                        f"'{baseline_anchor}' not found."
                    ),
                )
                cell_had_contract_issue = True
                continue

            fields_found, fields_payload = _resolve_dotted_path(
                case_payload,
                cell["field_container"],
            )
            evidence_fields = (
                fields_payload
                if fields_found and isinstance(fields_payload, dict)
                else {}
            )

            required_fields = cell["required_evidence_fields"]
            missing_fields: list[str] = []
            satisfied_count = 0
            for field_name in required_fields:
                if field_name in evidence_fields and bool(evidence_fields[field_name]):
                    satisfied_count += 1
                else:
                    missing_fields.append(field_name)

            if missing_fields:
                _add_workflow_sequence_finding(
                    result,
                    severity=sequence_severity,
                    category="missing_evidence_fields",
                    detail=(
                        f"cell={cell_key} parity_id={parity_id} missing_fields={missing_fields}."
                    ),
                )

            if required_fields and satisfied_count == 0:
                _add_workflow_sequence_finding(
                    result,
                    severity=sequence_severity,
                    category="count_only_detected",
                    detail=(
                        f"cell={cell_key} parity_id={parity_id} "
                        f"satisfied=0/{len(required_fields)}."
                    ),
                )

            ordering_found, ordering_payload = _resolve_dotted_path(
                case_payload,
                cell["ordering_container"],
            )
            ordering_tokens = (
                ordering_payload
                if ordering_found and isinstance(ordering_payload, list)
                else []
            )
            normalized_ordering_tokens = [
                token.strip()
                for token in ordering_tokens
                if isinstance(token, str) and token.strip()
            ]
            missing_tokens = [
                token
                for token in cell["required_ordering_tokens"]
                if token not in normalized_ordering_tokens
            ]
            if missing_tokens:
                _add_workflow_sequence_finding(
                    result,
                    severity=sequence_severity,
                    category="missing_ordering_tokens",
                    detail=(
                        f"cell={cell_key} parity_id={parity_id} missing_tokens={missing_tokens}."
                    ),
                )

        if cell["future_split_debt_status"] != "closed":
            open_debts += 1
        if not cell_had_contract_issue:
            validated_cells += 1

    new_errors = result.errors[error_start:]
    new_warnings = result.warnings[warning_start:]
    contract_errors = sum(
        1 for error in new_errors if error.startswith("workflow_coverage.contract_")
    )
    sequence_warnings = sum(
        1
        for warning in new_warnings
        if warning.startswith("workflow_coverage.sequence_gap.")
    )
    count_only_warnings = sum(
        1
        for warning in new_warnings
        if warning.startswith("workflow_coverage.sequence_gap.count_only_detected")
    )

    return WorkflowCoverageReport(
        configured_cells=configured_cells,
        validated_cells=validated_cells,
        contract_errors=contract_errors,
        sequence_warnings=sequence_warnings,
        count_only_warnings=count_only_warnings,
        open_debts=open_debts,
    )


def _load_and_validate_baselines(
    repo_root: Path,
    result: CheckResult,
) -> dict[str, dict[str, Any]]:
    """Load required baseline files and validate required case schema entries."""
    baseline_cases_by_path: dict[str, dict[str, Any]] = {}
    for relative_path, required_ids in REQUIRED_BASELINE_FILES.items():
        baseline_path = repo_root / relative_path
        try:
            payload = load_baseline_payload(baseline_path)
        except CharacterizationError as exc:
            result.add_error(str(exc))
            continue

        cases = payload["cases"]
        for behavior_id in required_ids:
            if behavior_id not in cases:
                result.add_error(
                    f"{relative_path} missing required behavior_id '{behavior_id}'."
                )
                continue
            try:
                validate_baseline_case_schema(
                    baseline_relpath=relative_path,
                    baseline_path=baseline_path,
                    behavior_id=behavior_id,
                    case_payload=cases[behavior_id],
                )
            except CharacterizationError as exc:
                result.add_error(str(exc))

        baseline_cases_by_path[relative_path] = cases
    return baseline_cases_by_path


def _load_and_validate_imaging_manifest(
    repo_root: Path,
    result: CheckResult,
) -> dict[str, Any]:
    """Load and validate the WI-003 imaging golden manifest payload."""
    manifest_path = repo_root / IMAGING_GOLDEN_MANIFEST_PATH
    try:
        return load_imaging_golden_manifest(manifest_path)
    except CharacterizationError as exc:
        result.add_error(str(exc))
        return {}


def _load_required_parity_rows(
    repo_root: Path, result: CheckResult
) -> dict[str, dict[str, str]]:
    """Load parity matrix rows and return only required WI-004 behavior rows."""
    row_by_behavior = _load_all_parity_rows(repo_root, result)
    if not row_by_behavior:
        return {}
    required_rows: dict[str, dict[str, str]] = {}
    for behavior_id in REQUIRED_CHARACTERIZATION_BEHAVIOR_IDS:
        row = row_by_behavior.get(behavior_id)
        if row is None:
            result.add_error(
                f"parity-matrix missing required characterization row '{behavior_id}'."
            )
            continue
        required_rows[behavior_id] = row
    return required_rows


def _check_parity_row_linkage(
    *,
    repo_root: Path,
    behavior_id: str,
    row: dict[str, str],
    baseline_cases_by_path: dict[str, dict[str, Any]],
    result: CheckResult,
) -> None:
    """Validate one parity row's linkage to baseline artifacts and owner tests."""
    baseline_source = row["baseline_source"].strip()
    owner_test = row["owner_test"].strip()

    if not baseline_source:
        result.add_error(f"{behavior_id}: baseline_source must be non-empty.")
        return
    if not owner_test:
        result.add_error(f"{behavior_id}: owner_test must be non-empty.")
        return

    if row.get("status") != "preserved":
        result.add_error(
            f"{behavior_id}: status must remain 'preserved' in characterization slices."
        )
    if row.get("current_result") != "matches-baseline":
        result.add_error(
            f"{behavior_id}: current_result must remain 'matches-baseline' in "
            "characterization slices."
        )

    try:
        baseline_path_part, baseline_anchor = parse_baseline_source(baseline_source)
    except CharacterizationError as exc:
        result.add_error(f"{behavior_id}: {exc}")
        return
    if baseline_anchor != behavior_id:
        result.add_error(
            f"{behavior_id}: baseline_source anchor must match behavior_id "
            f"(found '{baseline_anchor}')."
        )

    normalized_baseline_path = baseline_path_part.replace("\\", "/")
    if normalized_baseline_path not in REQUIRED_BASELINE_FILES:
        result.add_error(
            f"{behavior_id}: baseline_source path must reference one of "
            f"{sorted(REQUIRED_BASELINE_FILES)}, found '{baseline_path_part}'."
        )
    else:
        known_cases = baseline_cases_by_path.get(normalized_baseline_path, {})
        if baseline_anchor not in known_cases:
            result.add_error(
                f"{behavior_id}: baseline anchor '{baseline_anchor}' not found in "
                f"{normalized_baseline_path}."
            )

    try:
        owner_test_path_part, owner_test_function = parse_owner_test_reference(
            owner_test
        )
    except CharacterizationError as exc:
        result.add_error(f"{behavior_id}: {exc}")
        return

    normalized_owner_path = owner_test_path_part.replace("\\", "/")
    if not normalized_owner_path.startswith("tests/characterization/"):
        result.add_error(
            f"{behavior_id}: owner_test path must be under tests/characterization/, "
            f"found '{owner_test_path_part}'."
        )
        return

    owner_test_path = repo_root / normalized_owner_path
    if not owner_test_path.exists():
        result.add_error(
            f"{behavior_id}: owner_test file not found: {normalized_owner_path}"
        )
        return
    if not owner_test_exists(owner_test_path, owner_test_function):
        result.add_error(
            f"{behavior_id}: owner_test function '{owner_test_function}' not found in "
            f"{normalized_owner_path}."
        )


def _check_imaging_parity_row_linkage(
    *,
    repo_root: Path,
    behavior_id: str,
    row: dict[str, str],
    baseline_cases_by_path: dict[str, dict[str, Any]],
    imaging_manifest: dict[str, Any],
    result: CheckResult,
) -> None:
    """Validate IMG-* parity linkage to imaging baseline cases and golden artifacts."""
    baseline_source = row["baseline_source"].strip()
    try:
        baseline_path_part, _baseline_anchor = parse_baseline_source(baseline_source)
    except CharacterizationError as exc:
        result.add_error(f"{behavior_id}: {exc}")
        return
    normalized_baseline_path = baseline_path_part.replace("\\", "/")
    if normalized_baseline_path != IMAGING_BASELINE_PATH:
        result.add_error(
            f"{behavior_id}: baseline_source must reference {IMAGING_BASELINE_PATH}, "
            f"found '{baseline_path_part}'."
        )
        return

    imaging_cases = baseline_cases_by_path.get(IMAGING_BASELINE_PATH, {})
    case_payload = imaging_cases.get(behavior_id)
    if not isinstance(case_payload, dict):
        result.add_error(
            f"{behavior_id}: imaging baseline case not found in {IMAGING_BASELINE_PATH}."
        )
        return

    golden_key = case_payload.get("golden_key")
    if not isinstance(golden_key, str) or not golden_key.strip():
        result.add_error(
            f"{behavior_id}: imaging baseline golden_key must be non-empty."
        )
        return

    manifest_cases = imaging_manifest.get("cases")
    if not isinstance(manifest_cases, dict):
        result.add_error(
            f"{behavior_id}: golden manifest is missing a valid cases mapping."
        )
        return

    manifest_case = manifest_cases.get(golden_key)
    if not isinstance(manifest_case, dict):
        result.add_error(
            f"{behavior_id}: golden_key '{golden_key}' not found in "
            f"{IMAGING_GOLDEN_MANIFEST_PATH}."
        )
        return

    expected_path = manifest_case.get("expected_path")
    if not isinstance(expected_path, str) or not expected_path.strip():
        result.add_error(
            f"{behavior_id}: golden manifest case '{golden_key}' missing expected_path."
        )
        return
    normalized_expected = expected_path.replace("\\", "/")
    if not normalized_expected.startswith(IMAGING_EXPECTED_ROOT + "/"):
        result.add_error(
            f"{behavior_id}: expected_path must be under {IMAGING_EXPECTED_ROOT}/, "
            f"found '{expected_path}'."
        )
        return

    expected_file_path = repo_root / normalized_expected
    if not expected_file_path.exists():
        result.add_error(
            f"{behavior_id}: expected artifact not found at '{normalized_expected}'."
        )


def _check_artifact_budget(
    *,
    repo_root: Path,
    relative_root: str,
    max_files: int,
    max_bytes: int,
    label: str,
    result: CheckResult,
) -> None:
    """Check file-count and total-size budgets for golden artifact directories."""
    artifact_root = repo_root / relative_root
    if not artifact_root.exists():
        result.add_error(f"{label} directory not found: {relative_root}")
        return

    files = [path for path in artifact_root.rglob("*") if path.is_file()]
    if len(files) > max_files:
        result.add_error(
            f"{label} file count exceeds budget: {len(files)} > {max_files} "
            f"({relative_root})."
        )

    total_bytes = sum(path.stat().st_size for path in files)
    if total_bytes > max_bytes:
        result.add_error(
            f"{label} total bytes exceeds budget: {total_bytes} > {max_bytes} "
            f"({relative_root})."
        )


def check_characterization_artifacts(repo_root: Path) -> CheckResult:
    """Run WI-004/WI-003/WI-005 characterization linkage checks from repository root."""
    result = CheckResult()
    baseline_cases_by_path = _load_and_validate_baselines(repo_root, result)
    imaging_manifest = _load_and_validate_imaging_manifest(repo_root, result)
    all_parity_rows = _load_all_parity_rows(repo_root, result)
    parity_rows = _load_required_parity_rows(repo_root, result)

    for behavior_id, row in parity_rows.items():
        _check_parity_row_linkage(
            repo_root=repo_root,
            behavior_id=behavior_id,
            row=row,
            baseline_cases_by_path=baseline_cases_by_path,
            result=result,
        )
        if behavior_id in IMG_BEHAVIOR_IDS:
            _check_imaging_parity_row_linkage(
                repo_root=repo_root,
                behavior_id=behavior_id,
                row=row,
                baseline_cases_by_path=baseline_cases_by_path,
                imaging_manifest=imaging_manifest,
                result=result,
            )

    workflow_coverage_report = _check_workflow_coverage(
        repo_root=repo_root,
        all_parity_rows=all_parity_rows,
        baseline_cases_by_path=baseline_cases_by_path,
        result=result,
    )
    setattr(result, "workflow_coverage_report", workflow_coverage_report)

    collectability_report = _check_owner_collectability(repo_root, parity_rows, result)
    setattr(result, "collectability_report", collectability_report)
    runtime_gate_report = _check_runtime_characterization_gate(
        repo_root,
        parity_rows,
        result,
    )
    setattr(result, "runtime_gate_report", runtime_gate_report)

    _check_artifact_budget(
        repo_root=repo_root,
        relative_root=IMAGING_EXPECTED_ROOT,
        max_files=IMAGING_EXPECTED_MAX_FILES,
        max_bytes=IMAGING_EXPECTED_MAX_BYTES,
        label="imaging expected artifact",
        result=result,
    )
    _check_artifact_budget(
        repo_root=repo_root,
        relative_root=IMAGING_FIXTURE_ROOT,
        max_files=IMAGING_FIXTURE_MAX_FILES,
        max_bytes=IMAGING_FIXTURE_MAX_BYTES,
        label="imaging fixture artifact",
        result=result,
    )

    surface_report = check_surface_coverage_artifacts(repo_root)
    result.merge(surface_report.result)
    setattr(result, "surface_report", surface_report)

    return result
