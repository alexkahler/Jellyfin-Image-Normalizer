"""Parity and route-fence validators used by governance checks."""

from __future__ import annotations

import json
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
    ROUTE_FENCE_JSON_RELATIVE_PATH,
    ROUTE_FENCE_JSON_VERSION,
    ParityContractError,
    load_marked_route_fence_table,
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
        table = load_marked_route_fence_table(route_fence_path)
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


def _canonical_route_row_from_markdown(row: dict[str, str]) -> dict[str, str]:
    """Normalize one route row from markdown to canonical JSON comparison shape."""
    return {
        "command": row["command"].strip(),
        "mode": row["mode"].strip(),
        "route": row["route(v0|v1)"].strip().lower(),
        "owner_slice": row["owner slice"].strip(),
        "parity_status": row["parity status"].strip(),
    }


def _load_route_fence_json_rows(
    route_fence_json_path: Path, result: CheckResult
) -> list[dict[str, str]] | None:
    """Load and validate route-fence JSON rows in canonical comparison shape."""
    try:
        payload = json.loads(route_fence_json_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        result.add_error(f"route-fence-json: file not found: {route_fence_json_path}")
        return None
    except json.JSONDecodeError as exc:
        result.add_error(f"route-fence-json: JSON decode failed: {exc}")
        return None

    if not isinstance(payload, dict):
        result.add_error("route-fence-json: payload must be an object.")
        return None

    if payload.get("version") != ROUTE_FENCE_JSON_VERSION:
        result.add_error(
            "route-fence-json: version must be "
            f"{ROUTE_FENCE_JSON_VERSION}, found {payload.get('version')!r}."
        )

    rows = payload.get("rows")
    if not isinstance(rows, list):
        result.add_error("route-fence-json: rows must be a list.")
        return None
    if not rows:
        result.add_error("route-fence-json: rows must not be empty.")
        return None

    required_fields = ("command", "mode", "route", "owner_slice", "parity_status")
    normalized_rows: list[dict[str, str]] = []
    seen_keys: set[tuple[str, str]] = set()
    for index, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            result.add_error(
                f"route-fence-json: row {index} must be an object, found {type(row)}."
            )
            continue

        missing_fields = [field for field in required_fields if field not in row]
        if missing_fields:
            result.add_error(
                f"route-fence-json: row {index} missing fields: {missing_fields}."
            )
            continue

        normalized: dict[str, str] = {}
        for field in required_fields:
            value = row[field]
            if not isinstance(value, str) or not value.strip():
                result.add_error(
                    f"route-fence-json: row {index} field '{field}' must be non-empty string."
                )
                break
            normalized[field] = value.strip()
        else:
            normalized["route"] = normalized["route"].lower()
            if normalized["route"] not in {"v0", "v1"}:
                result.add_error(
                    f"route-fence-json: row {index} has invalid route '{row['route']}'."
                )

            key = (normalized["command"], normalized["mode"])
            if key in seen_keys:
                result.add_error(
                    f"route-fence-json: duplicate command/mode row {key} at row {index}."
                )
            else:
                seen_keys.add(key)

            normalized_rows.append(normalized)

    if result.errors:
        return None
    return normalized_rows


def check_route_fence_json_sync(
    route_fence_path: Path, route_fence_json_path: Path
) -> CheckResult:
    """Validate markdown route-fence rows are exactly synchronized to JSON rows."""
    result = CheckResult()

    try:
        markdown_table = load_marked_route_fence_table(route_fence_path)
    except ParityContractError as exc:
        result.add_error(str(exc))
        return result

    markdown_rows = [
        _canonical_route_row_from_markdown(row) for row in markdown_table.rows
    ]
    json_rows = _load_route_fence_json_rows(route_fence_json_path, result)
    if json_rows is None:
        return result

    markdown_keys = {(row["command"], row["mode"]) for row in markdown_rows}
    json_keys = {(row["command"], row["mode"]) for row in json_rows}
    missing_keys = sorted(markdown_keys - json_keys)
    extra_keys = sorted(json_keys - markdown_keys)
    if missing_keys:
        result.add_error(
            "route-fence-json: missing rows for markdown keys: "
            + ", ".join(f"{command}|{mode}" for command, mode in missing_keys)
        )
    if extra_keys:
        result.add_error(
            "route-fence-json: contains rows not present in markdown: "
            + ", ".join(f"{command}|{mode}" for command, mode in extra_keys)
        )

    if result.errors:
        return result

    markdown_by_key = {(row["command"], row["mode"]): row for row in markdown_rows}
    for row in json_rows:
        key = (row["command"], row["mode"])
        markdown_row = markdown_by_key[key]
        for field in ("route", "owner_slice", "parity_status"):
            if row[field] != markdown_row[field]:
                result.add_error(
                    "route-fence-json: mismatch for "
                    f"{key[0]}|{key[1]} field '{field}': "
                    f"markdown={markdown_row[field]!r}, json={row[field]!r}."
                )

    if markdown_rows != json_rows:
        result.add_error(
            "route-fence-json: row ordering differs from markdown canonical order."
        )

    return result


def check_parity_artifacts(repo_root: Path) -> CheckResult:
    """Run parity matrix and route-fence validation from repository root."""
    parity_matrix_path = repo_root / "project" / "parity-matrix.md"
    route_fence_path = repo_root / "project" / "route-fence.md"
    route_fence_json_path = repo_root / ROUTE_FENCE_JSON_RELATIVE_PATH

    result = CheckResult()
    result.merge(check_parity_matrix(parity_matrix_path))
    result.merge(check_route_fence(route_fence_path))
    result.merge(check_route_fence_json_sync(route_fence_path, route_fence_json_path))
    return result
