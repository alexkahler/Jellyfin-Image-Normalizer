"""Runtime route-fence loading and dispatch resolution."""

from __future__ import annotations

import json
from pathlib import Path

ROUTE_FENCE_JSON_RELATIVE_PATH = Path("project/route-fence.json")
ROUTE_FENCE_MARKDOWN_RELATIVE_PATH = Path("project/route-fence.md")
ROUTE_FENCE_JSON_VERSION = 1
MAX_REPO_ROOT_SEARCH_DEPTH = 12

# Slice 8 gates only user-invoked entrypoints.
RUNTIME_GATED_ROUTE_KEYS = frozenset(
    {
        ("config_init", "n/a"),
        ("test_connection", "n/a"),
        ("restore", "logo|thumb|backdrop|profile"),
        ("run", "logo"),
        ("run", "thumb"),
        ("run", "backdrop"),
        ("run", "profile"),
    }
)


class RouteFenceError(Exception):
    """Raised when route-fence artifacts cannot be resolved or validated."""


def _discover_repo_root(
    *, start_path: Path | None = None, max_depth: int = MAX_REPO_ROOT_SEARCH_DEPTH
) -> Path:
    """Walk upward from this module until project route-fence artifacts are found."""
    start = start_path or Path(__file__).resolve()
    current = start if start.is_dir() else start.parent

    for depth, candidate in enumerate([current, *current.parents]):
        if depth > max_depth:
            break
        has_json = (candidate / ROUTE_FENCE_JSON_RELATIVE_PATH).exists()
        has_markdown = (candidate / ROUTE_FENCE_MARKDOWN_RELATIVE_PATH).exists()
        if has_json or has_markdown:
            return candidate

    raise RouteFenceError(
        "route-fence: unable to locate repo root from "
        f"{start} within depth {max_depth}."
    )


def route_fence_json_path() -> Path:
    """Return the canonical route-fence JSON artifact path."""
    return _discover_repo_root() / ROUTE_FENCE_JSON_RELATIVE_PATH


def load_route_table() -> dict[tuple[str, str], str]:
    """Load and validate route-fence rows as a command/mode -> route mapping."""
    json_path = route_fence_json_path()
    try:
        payload = json.loads(json_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RouteFenceError(f"route-fence JSON not found: {json_path}") from exc
    except json.JSONDecodeError as exc:
        raise RouteFenceError(
            f"route-fence JSON decode failed at {json_path}: {exc}"
        ) from exc

    if not isinstance(payload, dict):
        raise RouteFenceError(
            f"route-fence JSON payload must be an object: {json_path}"
        )
    if payload.get("version") != ROUTE_FENCE_JSON_VERSION:
        raise RouteFenceError(
            "route-fence JSON version mismatch at "
            f"{json_path}: expected {ROUTE_FENCE_JSON_VERSION}, found {payload.get('version')!r}."
        )

    rows = payload.get("rows")
    if not isinstance(rows, list) or not rows:
        raise RouteFenceError(
            f"route-fence JSON rows must be a non-empty list: {json_path}"
        )

    mapping: dict[tuple[str, str], str] = {}
    required_fields = ("command", "mode", "route", "owner_slice", "parity_status")
    for index, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            raise RouteFenceError(
                f"route-fence JSON row {index} must be object at {json_path}."
            )
        missing_fields = [field for field in required_fields if field not in row]
        if missing_fields:
            raise RouteFenceError(
                f"route-fence JSON row {index} missing fields {missing_fields} at {json_path}."
            )

        command = row["command"]
        mode = row["mode"]
        route = row["route"]
        owner_slice = row["owner_slice"]
        parity_status = row["parity_status"]
        values = {
            "command": command,
            "mode": mode,
            "route": route,
            "owner_slice": owner_slice,
            "parity_status": parity_status,
        }
        for field, value in values.items():
            if not isinstance(value, str) or not value.strip():
                raise RouteFenceError(
                    f"route-fence JSON row {index} field '{field}' must be non-empty string at {json_path}."
                )

        normalized_command = command.strip()
        normalized_mode = mode.strip()
        normalized_route = route.strip().lower()
        if normalized_route not in {"v0", "v1"}:
            raise RouteFenceError(
                f"route-fence JSON row {index} has invalid route '{route}' at {json_path}."
            )

        route_key = (normalized_command, normalized_mode)
        if route_key in mapping:
            raise RouteFenceError(
                f"route-fence JSON duplicate command/mode row {route_key} at {json_path}."
            )
        mapping[route_key] = normalized_route

    return mapping


def resolve_route(command: str, mode: str) -> str:
    """Resolve route value for a command/mode key from route-fence JSON."""
    key = (command.strip(), mode.strip())
    mapping = load_route_table()
    if key not in mapping:
        raise RouteFenceError(
            "route-fence JSON missing command/mode row "
            f"{key} in {route_fence_json_path()}."
        )
    return mapping[key]
