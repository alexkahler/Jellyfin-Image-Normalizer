"""Route-readiness semantic validation for COV-03 governance hardening."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from characterization_checks import (
    _check_runtime_characterization_gate,
    _normalize_runtime_targets,
)
from characterization_contract import (
    CharacterizationError,
    load_baseline_payload,
    owner_test_exists,
    parse_baseline_source,
    parse_owner_test_reference,
)
from governance_contract import (
    CheckResult,
    GovernanceError,
    parse_verification_contract,
)
from parity_checks import check_route_fence_json_sync
from parity_contract import (
    REQUIRED_PARITY_COLUMNS,
    ALLOWED_ROUTE_PARITY_STATUS,
    load_markdown_table,
    load_marked_route_fence_table,
    ParityContractError,
)

WORKFLOW_COVERAGE_INDEX_PATH = "project/workflow-coverage-index.json"


@dataclass(frozen=True)
class ReadinessReport:
    """Readiness claim counters surfaced by governance output."""

    claimed_rows: int
    validated_rows: int


def _add_readiness_error(result: CheckResult, category: str, detail: str) -> None:
    """Record one deterministic readiness finding."""
    result.add_error(f"readiness.{category}: {detail}")


def _target_path_part(target: str) -> str:
    """Return the filesystem path portion of a target or nodeid."""
    return target.split("::", 1)[0]


def _nodeid_matches_target(nodeid: str, target: str) -> bool:
    """Return True when a normalized nodeid belongs to one runtime target."""
    normalized_nodeid = nodeid.strip().replace("\\", "/")
    normalized_target = target.strip().replace("\\", "/")
    node_path = _target_path_part(normalized_nodeid).rstrip("/")
    target_path = _target_path_part(normalized_target).rstrip("/")
    if "::" in normalized_target:
        return normalized_nodeid.startswith(normalized_target)
    if target_path.endswith(".py"):
        return node_path == target_path
    return node_path.startswith(target_path + "/")


def _load_workflow_cells(
    repo_root: Path,
    result: CheckResult,
) -> dict[str, dict[str, Any]] | None:
    """Load workflow-coverage cells keyed by command|mode."""
    workflow_path = repo_root / WORKFLOW_COVERAGE_INDEX_PATH
    try:
        payload = json.loads(workflow_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        _add_readiness_error(
            result,
            "workflow_schema",
            f"workflow coverage index not found: {WORKFLOW_COVERAGE_INDEX_PATH}",
        )
        return None
    except json.JSONDecodeError as exc:
        _add_readiness_error(
            result,
            "workflow_schema",
            f"{WORKFLOW_COVERAGE_INDEX_PATH} JSON decode failed: {exc}",
        )
        return None

    if not isinstance(payload, dict):
        _add_readiness_error(
            result,
            "workflow_schema",
            f"{WORKFLOW_COVERAGE_INDEX_PATH} payload must be an object.",
        )
        return None
    if payload.get("version") != 1:
        _add_readiness_error(
            result,
            "workflow_schema",
            f"{WORKFLOW_COVERAGE_INDEX_PATH} version must be 1.",
        )
        return None

    cells = payload.get("cells")
    if not isinstance(cells, dict):
        _add_readiness_error(
            result,
            "workflow_schema",
            f"{WORKFLOW_COVERAGE_INDEX_PATH} field 'cells' must be an object.",
        )
        return None

    normalized_cells: dict[str, dict[str, Any]] = {}
    for raw_key, raw_value in cells.items():
        if not isinstance(raw_key, str) or not raw_key.strip():
            _add_readiness_error(
                result,
                "workflow_schema",
                "workflow cell keys must be non-empty strings.",
            )
            continue
        if not isinstance(raw_value, dict):
            _add_readiness_error(
                result,
                "workflow_schema",
                f"workflow cell '{raw_key}' must be an object.",
            )
            continue
        normalized_cells[raw_key.strip()] = raw_value
    return normalized_cells


def _normalize_required_list(
    *,
    value: Any,
    field_name: str,
    cell_key: str,
    result: CheckResult,
) -> list[str]:
    """Normalize one workflow list field to non-empty list[str]."""
    if not isinstance(value, list) or not value:
        _add_readiness_error(
            result,
            "workflow_schema",
            f"cell={cell_key} field '{field_name}' must be non-empty list[str].",
        )
        return []
    normalized: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            _add_readiness_error(
                result,
                "workflow_schema",
                f"cell={cell_key} field '{field_name}' must contain non-empty strings.",
            )
            return []
        normalized.append(item.strip().replace("\\", "/"))
    return normalized


def _resolve_owner_nodeid(
    *,
    repo_root: Path,
    owner_ref: str,
    context: str,
    result: CheckResult,
) -> str | None:
    """Resolve one owner reference into a normalized collectable nodeid."""
    try:
        owner_path, owner_function = parse_owner_test_reference(owner_ref)
    except CharacterizationError as exc:
        _add_readiness_error(result, "owner_ref_invalid", f"{context}: {exc}")
        return None

    normalized_owner_path = owner_path.replace("\\", "/")
    if not normalized_owner_path.startswith("tests/characterization/"):
        _add_readiness_error(
            result,
            "owner_ref_invalid",
            (
                f"{context}: owner_test path must be under tests/characterization/, "
                f"found '{owner_path}'."
            ),
        )
        return None

    owner_test_path = repo_root / normalized_owner_path
    if not owner_test_path.exists():
        _add_readiness_error(
            result,
            "owner_ref_invalid",
            f"{context}: owner_test file not found: {normalized_owner_path}",
        )
        return None
    if not owner_test_exists(owner_test_path, owner_function):
        _add_readiness_error(
            result,
            "owner_ref_invalid",
            (
                f"{context}: owner_test function '{owner_function}' not found in "
                f"{normalized_owner_path}."
            ),
        )
        return None

    return f"{normalized_owner_path}::{owner_function}"


def _load_parity_rows(
    repo_root: Path,
    result: CheckResult,
) -> dict[str, dict[str, str]] | None:
    """Load parity matrix rows by behavior_id."""
    parity_path = repo_root / "project/parity-matrix.md"
    try:
        table = load_markdown_table(
            parity_path, REQUIRED_PARITY_COLUMNS, "parity-matrix"
        )
    except ParityContractError as exc:
        _add_readiness_error(result, "parity_id_missing", str(exc))
        return None
    return {row["behavior_id"]: row for row in table.rows}


def _baseline_case_exists(
    *,
    repo_root: Path,
    parity_id: str,
    baseline_source: str,
    baseline_cache: dict[str, dict[str, Any] | None],
    result: CheckResult,
) -> bool:
    """Return True when one parity row baseline_source resolves to an existing case."""
    try:
        baseline_path_part, baseline_anchor = parse_baseline_source(baseline_source)
    except CharacterizationError as exc:
        _add_readiness_error(
            result,
            "baseline_link_invalid",
            f"parity_id={parity_id}: {exc}",
        )
        return False

    normalized_path = baseline_path_part.replace("\\", "/")
    if normalized_path not in baseline_cache:
        baseline_path = repo_root / normalized_path
        try:
            payload = load_baseline_payload(baseline_path)
        except CharacterizationError as exc:
            _add_readiness_error(
                result,
                "baseline_link_invalid",
                f"parity_id={parity_id}: {exc}",
            )
            baseline_cache[normalized_path] = None
            return False
        cases = payload.get("cases")
        if not isinstance(cases, dict):
            _add_readiness_error(
                result,
                "baseline_link_invalid",
                (
                    f"parity_id={parity_id}: baseline file '{normalized_path}' "
                    "is missing cases mapping."
                ),
            )
            baseline_cache[normalized_path] = None
            return False
        baseline_cache[normalized_path] = cases

    cases = baseline_cache.get(normalized_path)
    if not isinstance(cases, dict):
        return False
    if baseline_anchor not in cases:
        _add_readiness_error(
            result,
            "baseline_link_invalid",
            (
                f"parity_id={parity_id}: baseline anchor '{baseline_anchor}' not found in "
                f"'{normalized_path}'."
            ),
        )
        return False
    return True


def check_readiness_artifacts(repo_root: Path) -> CheckResult:
    """Validate route readiness claims against parity/workflow/runtime evidence."""
    result = CheckResult()
    route_fence_path = repo_root / "project/route-fence.md"
    route_fence_json_path = repo_root / "project/route-fence.json"

    # Readiness claims are evaluated from canonical markdown rows, but they must
    # stay synchronized with the JSON runtime artifact.
    result.merge(check_route_fence_json_sync(route_fence_path, route_fence_json_path))

    try:
        route_table = load_marked_route_fence_table(route_fence_path)
    except ParityContractError as exc:
        _add_readiness_error(result, "invalid_status", str(exc))
        setattr(
            result,
            "readiness_report",
            ReadinessReport(claimed_rows=0, validated_rows=0),
        )
        return result

    workflow_cells = _load_workflow_cells(repo_root, result)
    parity_rows = _load_parity_rows(repo_root, result)
    try:
        contract = parse_verification_contract(
            repo_root / "project/verification-contract.yml"
        )
    except GovernanceError as exc:
        _add_readiness_error(
            result,
            "runtime_not_green",
            f"unable to parse runtime gate contract context: {exc}",
        )
        setattr(
            result,
            "readiness_report",
            ReadinessReport(claimed_rows=0, validated_rows=0),
        )
        return result

    if workflow_cells is None or parity_rows is None:
        setattr(
            result,
            "readiness_report",
            ReadinessReport(claimed_rows=0, validated_rows=0),
        )
        return result

    runtime_targets = _normalize_runtime_targets(contract.runtime_gate.targets)
    runtime_result = CheckResult()
    runtime_report = _check_runtime_characterization_gate(
        repo_root, parity_rows, runtime_result
    )
    mapped_runtime_parity_ids = set(runtime_report.mapped_parity_ids)
    runtime_diagnostics = list(runtime_report.diagnostics)
    baseline_cache: dict[str, dict[str, Any] | None] = {}

    claimed_rows = 0
    validated_rows = 0
    for row in route_table.rows:
        command = row["command"].strip()
        mode = row["mode"].strip()
        route_value = row["route(v0|v1)"].strip().lower()
        parity_status = row["parity status"].strip().lower()
        cell_key = f"{command}|{mode}"

        row_has_error = False
        if parity_status not in ALLOWED_ROUTE_PARITY_STATUS:
            _add_readiness_error(
                result,
                "invalid_status",
                (
                    f"cell={cell_key} parity status '{row['parity status']}' is invalid. "
                    f"Allowed={sorted(ALLOWED_ROUTE_PARITY_STATUS)}."
                ),
            )
            row_has_error = True

        claimed_ready = parity_status == "ready" or route_value == "v1"
        if route_value == "v1" and parity_status != "ready":
            _add_readiness_error(
                result,
                "route_requires_ready_status",
                f"cell={cell_key} route=v1 requires parity status=ready.",
            )
            row_has_error = True

        if not claimed_ready:
            continue
        claimed_rows += 1

        workflow_cell = workflow_cells.get(cell_key)
        if workflow_cell is None:
            _add_readiness_error(
                result,
                "unmapped_ready_cell",
                f"cell={cell_key} claims readiness but is not mapped in workflow index.",
            )
            continue

        required_parity_ids = _normalize_required_list(
            value=workflow_cell.get("required_parity_ids"),
            field_name="required_parity_ids",
            cell_key=cell_key,
            result=result,
        )
        required_owner_tests = _normalize_required_list(
            value=workflow_cell.get("required_owner_tests"),
            field_name="required_owner_tests",
            cell_key=cell_key,
            result=result,
        )
        if not required_parity_ids or not required_owner_tests:
            continue

        workflow_owner_nodeids: set[str] = set()
        for owner_ref in required_owner_tests:
            owner_nodeid = _resolve_owner_nodeid(
                repo_root=repo_root,
                owner_ref=owner_ref,
                context=f"cell={cell_key}",
                result=result,
            )
            if owner_nodeid is None:
                row_has_error = True
                continue
            workflow_owner_nodeids.add(owner_nodeid)

        parity_owner_nodeids: set[str] = set()
        for parity_id in required_parity_ids:
            parity_row = parity_rows.get(parity_id)
            if parity_row is None:
                _add_readiness_error(
                    result,
                    "parity_id_missing",
                    f"cell={cell_key} required parity_id '{parity_id}' not found.",
                )
                row_has_error = True
                continue

            row_status = parity_row.get("status", "").strip().lower()
            current_result = parity_row.get("current_result", "").strip().lower()
            if row_status != "preserved" or current_result != "matches-baseline":
                _add_readiness_error(
                    result,
                    "parity_not_preserved",
                    (
                        f"cell={cell_key} parity_id={parity_id} must be "
                        "status=preserved and current_result=matches-baseline."
                    ),
                )
                row_has_error = True

            baseline_source = parity_row.get("baseline_source", "").strip()
            if not baseline_source or not _baseline_case_exists(
                repo_root=repo_root,
                parity_id=parity_id,
                baseline_source=baseline_source,
                baseline_cache=baseline_cache,
                result=result,
            ):
                row_has_error = True

            parity_owner_ref = parity_row.get("owner_test", "").strip()
            if not parity_owner_ref:
                _add_readiness_error(
                    result,
                    "owner_ref_invalid",
                    f"cell={cell_key} parity_id={parity_id} owner_test is empty.",
                )
                row_has_error = True
                continue
            parity_owner_nodeid = _resolve_owner_nodeid(
                repo_root=repo_root,
                owner_ref=parity_owner_ref,
                context=f"cell={cell_key} parity_id={parity_id}",
                result=result,
            )
            if parity_owner_nodeid is None:
                row_has_error = True
                continue
            parity_owner_nodeids.add(parity_owner_nodeid)

        if not workflow_owner_nodeids.issubset(parity_owner_nodeids):
            missing = sorted(workflow_owner_nodeids - parity_owner_nodeids)
            _add_readiness_error(
                result,
                "owner_linkage_mismatch",
                f"cell={cell_key} workflow owner tests are not parity-backed: {missing}.",
            )
            row_has_error = True

        debt_payload = workflow_cell.get("future_split_debt")
        if not isinstance(debt_payload, dict):
            _add_readiness_error(
                result,
                "workflow_schema",
                f"cell={cell_key} future_split_debt must be an object.",
            )
            row_has_error = True
        else:
            debt_status = str(debt_payload.get("status", "")).strip().lower()
            readiness_blocking = debt_payload.get("readiness_blocking")
            if not isinstance(readiness_blocking, bool):
                _add_readiness_error(
                    result,
                    "workflow_schema",
                    f"cell={cell_key} future_split_debt.readiness_blocking must be bool.",
                )
                row_has_error = True
            elif readiness_blocking and debt_status != "closed":
                _add_readiness_error(
                    result,
                    "blocked_by_debt",
                    f"cell={cell_key} readiness is blocked by open workflow debt.",
                )
                row_has_error = True

        claim_targets = sorted(
            {
                target
                for target in runtime_targets
                if any(
                    _nodeid_matches_target(owner_nodeid, target)
                    for owner_nodeid in workflow_owner_nodeids
                )
            }
        )
        if not claim_targets:
            _add_readiness_error(
                result,
                "runtime_not_green",
                f"cell={cell_key} owner tests are not covered by runtime gate targets.",
            )
            row_has_error = True
        else:
            claim_target_set = set(claim_targets)
            claim_runtime_diagnostics = [
                diagnostic
                for diagnostic in runtime_diagnostics
                if not diagnostic.targets
                or bool(claim_target_set.intersection(diagnostic.targets))
            ]
            if claim_runtime_diagnostics:
                categories = sorted(
                    {diagnostic.category for diagnostic in claim_runtime_diagnostics}
                )
                _add_readiness_error(
                    result,
                    "runtime_not_green",
                    (
                        f"cell={cell_key} runtime diagnostics intersect claim targets "
                        f"{claim_targets}: categories={categories}."
                    ),
                )
                row_has_error = True

        missing_runtime_parity = sorted(
            set(required_parity_ids) - mapped_runtime_parity_ids
        )
        if missing_runtime_parity:
            _add_readiness_error(
                result,
                "runtime_unmapped_parity",
                (
                    f"cell={cell_key} parity IDs missing from runtime gate mapping: "
                    f"{missing_runtime_parity}."
                ),
            )
            row_has_error = True

        if not row_has_error:
            validated_rows += 1

    setattr(
        result,
        "readiness_report",
        ReadinessReport(claimed_rows=claimed_rows, validated_rows=validated_rows),
    )
    return result
