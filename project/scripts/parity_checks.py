"""Parity and route-fence validators used by governance checks."""

from __future__ import annotations

from pathlib import Path

from governance_contract import CheckResult
from parity_contract import (
    ALLOWED_PARITY_STATUS,
    APPROVAL_REQUIRED_STATUSES,
    PLACEHOLDER_APPROVAL_REFS,
    REQUIRED_BEHAVIOR_IDS,
    REQUIRED_PARITY_COLUMNS,
    REQUIRED_ROUTE_FENCE_COLUMNS,
    REQUIRED_ROUTE_ROWS,
    ParityContractError,
    load_markdown_table,
)


def _require_non_empty(
    result: CheckResult,
    *,
    table_name: str,
    row_number: int,
    field_name: str,
    value: str,
) -> None:
    """Validate that required table fields are not blank."""
    if not value.strip():
        result.add_error(
            f"{table_name}: row {row_number} field '{field_name}' must be non-empty."
        )


def check_parity_matrix(parity_matrix_path: Path) -> CheckResult:
    """Validate schema and starter inventory constraints for parity matrix rows."""
    result = CheckResult()
    try:
        table = load_markdown_table(
            parity_matrix_path,
            REQUIRED_PARITY_COLUMNS,
            "parity-matrix",
        )
    except ParityContractError as exc:
        result.add_error(str(exc))
        return result

    seen_behavior_ids: set[str] = set()
    for row_index, row in enumerate(table.rows, start=1):
        for field in (
            "behavior_id",
            "baseline_source",
            "current_result",
            "status",
            "owner_test",
            "approval_ref",
        ):
            _require_non_empty(
                result,
                table_name="parity-matrix",
                row_number=row_index,
                field_name=field,
                value=row[field],
            )

        behavior_id = row["behavior_id"]
        status = row["status"].strip().lower()
        approval_ref = row["approval_ref"].strip().lower()

        if status not in ALLOWED_PARITY_STATUS:
            result.add_error(
                f"parity-matrix: row {row_index} has invalid status '{row['status']}'."
            )
        if behavior_id in seen_behavior_ids:
            result.add_error(
                f"parity-matrix: duplicate behavior_id '{behavior_id}' at row {row_index}."
            )
        else:
            seen_behavior_ids.add(behavior_id)

        if (
            status in APPROVAL_REQUIRED_STATUSES
            and approval_ref in PLACEHOLDER_APPROVAL_REFS
        ):
            result.add_error(
                "parity-matrix: row "
                f"{row_index} status '{status}' requires non-placeholder approval_ref."
            )

    missing_behavior_ids = sorted(set(REQUIRED_BEHAVIOR_IDS) - seen_behavior_ids)
    if missing_behavior_ids:
        result.add_error(
            "parity-matrix: missing required starter behavior IDs: "
            + ", ".join(missing_behavior_ids)
        )

    return result


def check_route_fence(route_fence_path: Path) -> CheckResult:
    """Validate route-fence schema and required strangler routing rows."""
    result = CheckResult()
    try:
        table = load_markdown_table(
            route_fence_path,
            REQUIRED_ROUTE_FENCE_COLUMNS,
            "route-fence",
        )
    except ParityContractError as exc:
        result.add_error(str(exc))
        return result

    seen_route_keys: set[tuple[str, str]] = set()
    for row_index, row in enumerate(table.rows, start=1):
        for field in REQUIRED_ROUTE_FENCE_COLUMNS:
            _require_non_empty(
                result,
                table_name="route-fence",
                row_number=row_index,
                field_name=field,
                value=row[field],
            )

        route_value = row["route(v0|v1)"].strip().lower()
        if route_value not in {"v0", "v1"}:
            result.add_error(
                "route-fence: row "
                f"{row_index} has invalid route(v0|v1) '{row['route(v0|v1)']}'."
            )

        route_key = (row["command"], row["mode"])
        if route_key in seen_route_keys:
            result.add_error(
                f"route-fence: duplicate command/mode row {route_key} at row {row_index}."
            )
        else:
            seen_route_keys.add(route_key)

    missing_rows = sorted(set(REQUIRED_ROUTE_ROWS) - seen_route_keys)
    if missing_rows:
        missing_values = [f"{command}|{mode}" for command, mode in missing_rows]
        result.add_error(
            "route-fence: missing required command/mode rows: "
            + ", ".join(missing_values)
        )

    return result


def check_parity_artifacts(repo_root: Path) -> CheckResult:
    """Run parity matrix and route-fence validation from repository root."""
    parity_matrix_path = repo_root / "project" / "parity-matrix.md"
    route_fence_path = repo_root / "project" / "route-fence.md"

    result = CheckResult()
    result.merge(check_parity_matrix(parity_matrix_path))
    result.merge(check_route_fence(route_fence_path))
    return result
