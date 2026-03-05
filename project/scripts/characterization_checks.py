"""Characterization artifact checks for WI-004, WI-003, and WI-005 governance enforcement."""

from __future__ import annotations

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
from parity_contract import REQUIRED_PARITY_COLUMNS, load_markdown_table
from surface_coverage_checks import check_surface_coverage_artifacts

REQUIRED_COLLECTABILITY_PYTEST_COMMAND = "PYTHONPATH=src ./.venv/bin/python -m pytest"
COLLECT_ONLY_NODEID_PATTERN = re.compile(r"^tests[\\/].+::.+$")
RUNTIME_GATE_TIMEOUT_BUFFER_SECONDS = 15


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
    parity_matrix_path = repo_root / "project" / "parity-matrix.md"
    try:
        table = load_markdown_table(
            parity_matrix_path,
            REQUIRED_PARITY_COLUMNS,
            "parity-matrix",
        )
    except Exception as exc:  # pragma: no cover - handled by parity check tests
        result.add_error(str(exc))
        return {}

    row_by_behavior = {row["behavior_id"]: row for row in table.rows}
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
