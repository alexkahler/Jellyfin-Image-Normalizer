"""Parsing utilities and constants for parity governance artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

REQUIRED_PARITY_COLUMNS = [
    "behavior_id",
    "baseline_source",
    "current_result",
    "status",
    "owner_test",
    "approval_ref",
    "notes",
    "migration_note",
]
REQUIRED_ROUTE_FENCE_COLUMNS = [
    "command",
    "mode",
    "route(v0|v1)",
    "owner slice",
    "parity status",
]
ALLOWED_PARITY_STATUS = {"preserved", "changed", "removed", "suspicious"}
APPROVAL_REQUIRED_STATUSES = {"changed", "removed", "suspicious"}
PLACEHOLDER_APPROVAL_REFS = {"", "-", "n/a", "na", "none", "pending", "tbd"}

REQUIRED_BEHAVIOR_IDS = [
    "CLI-RESTORE-001",
    "CLI-GENCFG-001",
    "CLI-TESTJF-001",
    "CLI-SINGLE-001",
    "CLI-OVERRIDE-001",
    "CLI-ASPECT-001",
    "CFG-TOML-001",
    "CFG-TOML-002",
    "CFG-TYPE-001",
    "CFG-CORE-001",
    "CFG-OPS-001",
    "CFG-DISC-001",
    "CFG-OVERRIDE-001",
    "API-QUERY-001",
    "API-WRITE-001",
    "API-DRYRUN-001",
    "API-DRYRUN-002",
    "API-DELETE-001",
    "API-GETIMG-001",
    "API-RETRY-001",
    "DISC-LIB-001",
    "DISC-LIB-002",
    "DISC-ITEM-001",
    "DISC-ITEM-002",
    "IMG-SCALE-001",
    "IMG-NOSCALE-001",
    "IMG-LOGO-001",
    "IMG-CROP-001",
    "IMG-ENCODE-001",
    "PIPE-DRYRUN-001",
    "PIPE-BACKUP-001",
    "PIPE-BACKDROP-001",
    "PIPE-SINGLE-001",
    "PIPE-COUNT-001",
    "BKP-MODE-001",
    "BKP-PATH-001",
    "RST-BULK-001",
    "RST-SINGLE-001",
    "RST-REFUSE-001",
    "RST-PATH-001",
    "OBS-SUMLOG-001",
    "CFG-SCALEFLAGS-001",
    "OBS-EXITCODE-001",
]
REQUIRED_ROUTE_ROWS = [
    ("run", "logo"),
    ("run", "thumb"),
    ("run", "backdrop"),
    ("run", "profile"),
    ("restore", "logo|thumb|backdrop|profile"),
    ("test_connection", "n/a"),
    ("config_init", "n/a"),
    ("config_validate", "n/a"),
]


class ParityContractError(Exception):
    """Raised when parity or route-fence artifacts are malformed."""


@dataclass(frozen=True)
class MarkdownTable:
    """Represents one parsed markdown table."""

    columns: list[str]
    rows: list[dict[str, str]]


def _normalize_cell(cell: str) -> str:
    """Normalize escaped pipe characters in markdown table cells."""
    return cell.strip().replace("\\|", "|")


def _split_markdown_row(raw_line: str) -> list[str]:
    """Split a markdown table row while preserving escaped pipe characters."""
    stripped = raw_line.strip()
    if "|" not in stripped:
        raise ParityContractError(f"Invalid markdown row (missing '|'): {raw_line!r}")

    sentinel = "__PARITY_ESCAPED_PIPE__"
    protected = stripped.replace("\\|", sentinel)
    if protected.startswith("|"):
        protected = protected[1:]
    if protected.endswith("|"):
        protected = protected[:-1]
    return [part.strip().replace(sentinel, "|") for part in protected.split("|")]


def _is_separator_row(cells: list[str]) -> bool:
    """Return True when cells form a markdown table separator row."""
    if not cells:
        return False
    for cell in cells:
        normalized = cell.strip().replace(":", "").replace("-", "")
        if normalized:
            return False
    return True


def parse_markdown_table(
    table_text: str,
    expected_columns: list[str],
    table_name: str,
) -> MarkdownTable:
    """Parse a markdown table and validate header columns exactly."""
    lines = table_text.splitlines()

    for index, line in enumerate(lines):
        if "|" not in line:
            continue

        header_cells = [_normalize_cell(cell) for cell in _split_markdown_row(line)]
        if header_cells != expected_columns:
            continue

        if index + 1 >= len(lines):
            raise ParityContractError(
                f"{table_name}: header found but separator row is missing."
            )
        separator_cells = _split_markdown_row(lines[index + 1])
        if not _is_separator_row(separator_cells):
            raise ParityContractError(
                f"{table_name}: expected markdown separator after header row."
            )

        rows: list[dict[str, str]] = []
        for row_line in lines[index + 2 :]:
            if not row_line.strip():
                if rows:
                    break
                continue
            if "|" not in row_line:
                if rows:
                    break
                continue

            row_cells = [
                _normalize_cell(cell) for cell in _split_markdown_row(row_line)
            ]
            if len(row_cells) != len(expected_columns):
                raise ParityContractError(
                    f"{table_name}: row has {len(row_cells)} cells, expected "
                    f"{len(expected_columns)}. Row={row_line!r}"
                )
            rows.append(dict(zip(expected_columns, row_cells)))

        if not rows:
            raise ParityContractError(f"{table_name}: table contains no data rows.")
        return MarkdownTable(columns=expected_columns, rows=rows)

    raise ParityContractError(
        f"{table_name}: required header not found. Expected columns={expected_columns}."
    )


def load_markdown_table(
    path: Path,
    expected_columns: list[str],
    table_name: str,
) -> MarkdownTable:
    """Load and parse a markdown table file with fixed expected columns."""
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise ParityContractError(f"{table_name}: file not found: {path}") from exc
    return parse_markdown_table(text, expected_columns, table_name)
