#!/usr/bin/env python3
"""Generate and verify project/route-fence.json from canonical markdown."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from parity_contract import (
    ROUTE_FENCE_JSON_RELATIVE_PATH,
    ROUTE_FENCE_JSON_VERSION,
    ROUTE_FENCE_MARKDOWN_RELATIVE_PATH,
    ParityContractError,
    load_marked_route_fence_table,
)


def _canonical_rows(route_table_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    """Convert markdown rows to deterministic JSON rows."""
    return [
        {
            "command": row["command"].strip(),
            "mode": row["mode"].strip(),
            "route": row["route(v0|v1)"].strip().lower(),
            "owner_slice": row["owner slice"].strip(),
            "parity_status": row["parity status"].strip(),
        }
        for row in route_table_rows
    ]


def build_route_fence_payload(route_fence_markdown_path: Path) -> dict[str, object]:
    """Build the JSON payload from the canonical marked markdown table."""
    route_table = load_marked_route_fence_table(route_fence_markdown_path)
    return {
        "version": ROUTE_FENCE_JSON_VERSION,
        "rows": _canonical_rows(route_table.rows),
    }


def render_route_fence_json(payload: dict[str, object]) -> str:
    """Render deterministic JSON output text for route-fence artifact."""
    return json.dumps(payload, indent=2) + "\n"


def _check_route_fence_json_sync(
    route_fence_markdown_path: Path,
    route_fence_json_path: Path,
) -> tuple[bool, str]:
    """Return whether JSON artifact matches markdown-derived payload exactly."""
    expected_text = render_route_fence_json(
        build_route_fence_payload(route_fence_markdown_path)
    )

    if not route_fence_json_path.exists():
        return False, f"Missing route-fence JSON artifact: {route_fence_json_path}"

    current_text = route_fence_json_path.read_text(encoding="utf-8")
    if current_text != expected_text:
        return False, (
            "route-fence JSON drift detected. "
            "Run `python project/scripts/generate_route_fence_json.py --write`."
        )

    return True, "route-fence JSON is synchronized."


def build_parser() -> argparse.ArgumentParser:
    """Build CLI parser for route-fence JSON generation/sync checks."""
    parser = argparse.ArgumentParser(
        description="Generate and verify project/route-fence.json"
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write project/route-fence.json from project/route-fence.md.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify project/route-fence.json is synchronized with markdown.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint."""
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.write and args.check:
        parser.error("--write and --check are mutually exclusive.")

    repo_root = Path(__file__).resolve().parents[2]
    route_fence_markdown_path = repo_root / ROUTE_FENCE_MARKDOWN_RELATIVE_PATH
    route_fence_json_path = repo_root / ROUTE_FENCE_JSON_RELATIVE_PATH

    try:
        if args.write:
            payload = build_route_fence_payload(route_fence_markdown_path)
            route_fence_json_path.write_text(
                render_route_fence_json(payload), encoding="utf-8"
            )
            print(f"Wrote route-fence JSON artifact: {route_fence_json_path}")
            return 0

        ok, message = _check_route_fence_json_sync(
            route_fence_markdown_path,
            route_fence_json_path,
        )
        print(message)
        return 0 if ok else 1
    except ParityContractError as exc:
        print(f"route-fence generation failed: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
