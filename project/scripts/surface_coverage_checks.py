"""Surface coverage checks for Track 1 externally observable behavior mappings."""

from __future__ import annotations

import ast
import contextlib
import importlib
import io
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from governance_contract import CheckResult
from parity_contract import REQUIRED_PARITY_COLUMNS, load_markdown_table

SURFACE_INDEX_PATH = "project/surface-coverage-index.json"
CONFIG_EXAMPLE_PATH = "config.example.toml"
TECHNICAL_NOTES_PATH = "docs/TECHNICAL_NOTES.md"
CLI_MODULE_PATH = "src/jfin/cli.py"
PYTHON_HELP_CANDIDATES = (
    (sys.executable,),
    ("py", "-3.13"),
    ("python3.13",),
    ("python3.12",),
    ("python3.11",),
)

OBSERVABILITY_CONTRACT_ITEMS = {
    "obs.summary.counters": (
        "images_found/processed/success/skipped/warning/error and failed items",
    ),
    "obs.summary.failure_list": ("failed items",),
    "obs.summary.warning_error_presence": ("warning/error",),
    "obs.summary.scale_decision_reporting": (
        "always log scale decisions, api failures, and run summary before exit",
        "upscaled_images",
        "downscaled_images",
    ),
    "obs.exit_codes.major_classes": ("exit behavior:",),
}


@dataclass(frozen=True)
class DetectedCliItem:
    """Represents one CLI surface item detected from help output."""

    item_id: str
    command_path: str
    source_token: str
    default_text: str


@dataclass(frozen=True)
class SurfaceCoverageReport:
    """Result bundle for surface coverage checks and report counters."""

    result: CheckResult
    unmapped_cli_items: int
    unmapped_config_keys: int
    unmapped_observability_items: int
    parity_test_linkage_gaps: int


def _normalize_text(value: str) -> str:
    """Normalize free-form text for deterministic comparisons."""
    return " ".join(value.strip().split()).lower()


def _normalize_path(path: str) -> str:
    """Normalize path separators for cross-platform checks."""
    return path.replace("\\", "/")


def _command_label(command_path: str) -> str:
    """Convert command path into a stable CLI ID segment."""
    if command_path == "root":
        return "root"
    return command_path.replace(" ", ".")


def _extract_help_option_rows(help_text: str) -> list[tuple[str, str]]:
    """Extract option token rows as (token, description) tuples from help text."""
    rows: list[tuple[str, str]] = []
    current_tokens = ""
    current_desc_parts: list[str] = []

    def flush() -> None:
        if not current_tokens:
            return
        description = " ".join(current_desc_parts).strip()
        for raw_token in current_tokens.split(","):
            cleaned = raw_token.strip()
            if not cleaned.startswith("-"):
                continue
            token = cleaned.split()[0]
            rows.append((token, description))

    for line in help_text.splitlines():
        if re.match(r"^\s{2,}-", line):
            flush()
            parts = re.split(r"\s{2,}", line.strip(), maxsplit=1)
            current_tokens = parts[0]
            current_desc_parts = [parts[1].strip()] if len(parts) > 1 else []
            continue

        if current_tokens and re.match(r"^\s{20,}\S", line):
            current_desc_parts.append(line.strip())
            continue

        if current_tokens:
            flush()
            current_tokens = ""
            current_desc_parts = []

    flush()
    return rows


def _extract_default_text(description: str) -> str:
    """Extract default-value text from one option description."""
    match = re.search(r"default:\s*([^)]+)\)", description, flags=re.IGNORECASE)
    if match:
        return " ".join(match.group(1).split())
    return ""


def _extract_modes_from_mode_option(help_rows: list[tuple[str, str]]) -> list[str]:
    """Extract known mode names mentioned in the --mode option description."""
    for token, description in help_rows:
        if token != "--mode":
            continue
        normalized = description.lower()
        modes = [
            candidate
            for candidate in ("logo", "thumb", "backdrop", "profile")
            if re.search(rf"\b{candidate}\b", normalized)
        ]
        return sorted(set(modes))
    return []


def _extract_subcommands(help_text: str) -> list[str]:
    """Extract subcommand names from argparse-style positional argument blocks."""
    commands: list[str] = []
    in_positional = False
    for line in help_text.splitlines():
        stripped = line.strip()
        lower = stripped.lower()
        if lower.startswith("positional arguments"):
            in_positional = True
            continue
        if not in_positional:
            continue
        if lower.startswith("options:") or lower.startswith("optional arguments:"):
            break
        if not stripped:
            continue
        if re.match(r"^\s{2,}[A-Za-z0-9_-]+\s{2,}", line):
            token = stripped.split()[0]
            if token.startswith("-"):
                continue
            commands.append(token)
    return sorted(set(commands))


def _collect_help_in_process(
    repo_root: Path, command_path: tuple[str, ...]
) -> str | None:
    """Try collecting CLI help output in-process first for deterministic behavior."""
    src_root = repo_root / "src"
    if not src_root.exists():
        return None

    inserted_sys_path = False
    if str(src_root) not in sys.path:
        sys.path.insert(0, str(src_root))
        inserted_sys_path = True

    old_argv = sys.argv[:]
    old_columns = os.environ.get("COLUMNS")
    old_lc_all = os.environ.get("LC_ALL")
    old_lang = os.environ.get("LANG")
    output_buffer = io.StringIO()
    error_buffer = io.StringIO()
    previous_modules: dict[str, Any] = {}
    try:
        os.environ["COLUMNS"] = "120"
        os.environ["LC_ALL"] = "C"
        os.environ["LANG"] = "C"
        for module_name in ("jfin.cli", "jfin"):
            if module_name in sys.modules:
                previous_modules[module_name] = sys.modules[module_name]
                del sys.modules[module_name]
        try:
            cli_module = importlib.import_module("jfin.cli")
        except Exception:
            return None

        sys.argv = ["jfin", *command_path, "--help"]
        with (
            contextlib.redirect_stdout(output_buffer),
            contextlib.redirect_stderr(error_buffer),
        ):
            try:
                cli_module.parse_args()
            except SystemExit as exc:
                if exc.code != 0:
                    return None
        rendered = output_buffer.getvalue() + error_buffer.getvalue()
        if "usage:" not in rendered.lower():
            return None
        return rendered
    finally:
        sys.argv = old_argv
        if old_columns is None:
            os.environ.pop("COLUMNS", None)
        else:
            os.environ["COLUMNS"] = old_columns
        if old_lc_all is None:
            os.environ.pop("LC_ALL", None)
        else:
            os.environ["LC_ALL"] = old_lc_all
        if old_lang is None:
            os.environ.pop("LANG", None)
        else:
            os.environ["LANG"] = old_lang
        for module_name in ("jfin.cli", "jfin"):
            sys.modules.pop(module_name, None)
        for module_name, module in previous_modules.items():
            sys.modules[module_name] = module
        if inserted_sys_path:
            sys.path.remove(str(src_root))


def _collect_help_subprocess(
    repo_root: Path, command_path: tuple[str, ...]
) -> str | None:
    """Fallback: collect CLI help output via subprocess with deterministic env."""
    env = os.environ.copy()
    src_root = repo_root / "src"
    current_pythonpath = env.get("PYTHONPATH")
    if current_pythonpath:
        env["PYTHONPATH"] = f"{src_root}{os.pathsep}{current_pythonpath}"
    else:
        env["PYTHONPATH"] = str(src_root)
    env["COLUMNS"] = "120"
    env["LC_ALL"] = "C"
    env["LANG"] = "C"
    env["PYTHONUTF8"] = "1"

    seen_candidates: set[tuple[str, ...]] = set()
    for prefix in PYTHON_HELP_CANDIDATES:
        if prefix in seen_candidates:
            continue
        seen_candidates.add(prefix)
        try:
            completed = subprocess.run(
                [*prefix, "-m", "jfin", *command_path, "--help"],
                cwd=repo_root,
                env=env,
                check=False,
                capture_output=True,
                text=True,
            )
        except OSError:
            continue
        if completed.returncode != 0:
            continue
        rendered = (completed.stdout or "") + (completed.stderr or "")
        if "usage:" not in rendered.lower():
            continue
        return rendered
    return None


def _collect_help_output(repo_root: Path, command_path: tuple[str, ...]) -> str | None:
    """Collect help text using in-process first, then subprocess fallback."""
    in_process = _collect_help_in_process(repo_root, command_path)
    if in_process is not None:
        return in_process
    return _collect_help_subprocess(repo_root, command_path)


def _detect_cli_surface(repo_root: Path, result: CheckResult) -> list[DetectedCliItem]:
    """Detect CLI root/subcommand options and mode values from help output."""
    cli_path = repo_root / CLI_MODULE_PATH
    if not cli_path.exists():
        result.add_error(f"surface-coverage: missing CLI module: {CLI_MODULE_PATH}")
        return []

    root_help = _collect_help_output(repo_root, ())
    if root_help is None:
        result.add_error(
            "surface-coverage: unable to collect root CLI help output from 'python -m jfin --help'."
        )
        return []

    detected: dict[str, DetectedCliItem] = {}

    def add_item(item: DetectedCliItem) -> None:
        if item.item_id not in detected:
            detected[item.item_id] = item

    add_item(
        DetectedCliItem(
            item_id="cli.root.command",
            command_path="root",
            source_token="command:root",
            default_text="",
        )
    )

    root_rows = _extract_help_option_rows(root_help)
    for token, description in root_rows:
        add_item(
            DetectedCliItem(
                item_id=f"cli.root.option.{token}",
                command_path="root",
                source_token=token,
                default_text=_extract_default_text(description),
            )
        )

    for mode in _extract_modes_from_mode_option(root_rows):
        add_item(
            DetectedCliItem(
                item_id=f"cli.root.mode.{mode}",
                command_path="root",
                source_token=mode,
                default_text="",
            )
        )

    for command in _extract_subcommands(root_help):
        command_help = _collect_help_output(repo_root, (command,))
        if command_help is None:
            continue
        command_label = _command_label(command)
        add_item(
            DetectedCliItem(
                item_id=f"cli.{command_label}.command",
                command_path=command,
                source_token=f"command:{command}",
                default_text="",
            )
        )
        for token, description in _extract_help_option_rows(command_help):
            add_item(
                DetectedCliItem(
                    item_id=f"cli.{command_label}.option.{token}",
                    command_path=command,
                    source_token=token,
                    default_text=_extract_default_text(description),
                )
            )

    return sorted(detected.values(), key=lambda item: item.item_id)


def _detect_config_surface(repo_root: Path, result: CheckResult) -> list[str]:
    """Detect config keys from config.example.toml as flattened section.key paths."""
    config_path = repo_root / CONFIG_EXAMPLE_PATH
    if not config_path.exists():
        result.add_error(
            f"surface-coverage: missing config example file: {CONFIG_EXAMPLE_PATH}"
        )
        return []

    current_section = ""
    keys: list[str] = []
    for raw_line in config_path.read_text(encoding="utf-8").splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        section_match = re.fullmatch(r"\[(.+)\]", stripped)
        if section_match:
            current_section = section_match.group(1).strip()
            continue

        key_match = re.match(r"([A-Za-z0-9_]+)\s*=", stripped)
        if not key_match:
            continue
        key = key_match.group(1)
        if current_section:
            keys.append(f"config.{current_section}.{key}")
        else:
            keys.append(f"config.{key}")
    return sorted(set(keys))


def _detect_observability_contract_items(
    repo_root: Path, result: CheckResult
) -> list[str]:
    """Detect required observability contract items from TECHNICAL_NOTES anchors."""
    notes_path = repo_root / TECHNICAL_NOTES_PATH
    if not notes_path.exists():
        result.add_error(
            f"surface-coverage: missing technical notes file: {TECHNICAL_NOTES_PATH}"
        )
        return []

    notes_text = _normalize_text(notes_path.read_text(encoding="utf-8"))
    for item_id, required_tokens in OBSERVABILITY_CONTRACT_ITEMS.items():
        for token in required_tokens:
            if token in notes_text:
                break
        else:
            result.add_error(
                f"surface-coverage: missing TECHNICAL_NOTES anchor for '{item_id}'."
            )
    return sorted(OBSERVABILITY_CONTRACT_ITEMS.keys())


def _load_surface_index(repo_root: Path, result: CheckResult) -> dict[str, Any]:
    """Load surface coverage index JSON and validate top-level shape."""
    index_path = repo_root / SURFACE_INDEX_PATH
    try:
        payload = json.loads(index_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        result.add_error(
            f"surface-coverage: missing canonical index file: {SURFACE_INDEX_PATH}"
        )
        return {}
    except json.JSONDecodeError as exc:
        result.add_error(f"surface-coverage: index JSON decode failed: {exc}")
        return {}

    if not isinstance(payload, dict):
        result.add_error("surface-coverage: index payload must be a JSON object.")
        return {}

    expected_keys = {"version", "cli_items", "config_items", "observability_items"}
    missing_keys = sorted(expected_keys - set(payload))
    if missing_keys:
        result.add_error(
            f"surface-coverage: index missing required top-level keys: {missing_keys}"
        )
    if payload.get("version") != 1:
        result.add_error(
            "surface-coverage: index version must be 1, "
            f"found {payload.get('version')!r}."
        )
    return payload


def _owner_symbol_exists(path: Path, symbol_name: str) -> bool:
    """Return True when a function or class symbol exists in one Python file."""
    try:
        source = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return False
    tree = ast.parse(source, filename=str(path))
    return any(
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        and node.name == symbol_name
        for node in ast.walk(tree)
    )


def _validate_owner_reference(repo_root: Path, owner_ref: str) -> tuple[bool, str]:
    """Validate one owner_test reference (path or path::symbol)."""
    owner_ref = owner_ref.strip()
    if not owner_ref:
        return False, "empty owner_test reference"

    path_part = owner_ref
    symbol_name = ""
    if "::" in owner_ref:
        path_part, symbol_name = owner_ref.split("::", 1)
        if not path_part or not symbol_name:
            return False, f"invalid owner_test reference '{owner_ref}'"

    normalized_path = _normalize_path(path_part)
    owner_path = repo_root / normalized_path
    if not owner_path.exists():
        return False, f"owner_test file not found: {normalized_path}"
    if symbol_name and not _owner_symbol_exists(owner_path, symbol_name):
        return (
            False,
            f"owner_test symbol '{symbol_name}' not found in {normalized_path}",
        )
    return True, ""


def _validate_item_schema(
    *,
    section_name: str,
    item: Any,
    result: CheckResult,
) -> dict[str, Any] | None:
    """Validate index item schema and strict out-of-scope rules."""
    if not isinstance(item, dict):
        result.add_error(
            f"surface-coverage: {section_name} entry must be an object, found {type(item)}."
        )
        return None

    required_fields = {
        "id",
        "parity_ids",
        "owner_tests",
        "out_of_scope",
        "out_of_scope_reason",
        "code_refs",
        "notes",
    }
    missing_fields = sorted(required_fields - set(item))
    if missing_fields:
        result.add_error(
            f"surface-coverage: {section_name} '{item.get('id', '<missing>')}' missing required fields: {missing_fields}."
        )
        return None

    item_id = item["id"]
    if not isinstance(item_id, str) or not item_id.strip():
        result.add_error(f"surface-coverage: {section_name} entry has invalid 'id'.")
        return None

    out_of_scope = item["out_of_scope"]
    if not isinstance(out_of_scope, bool):
        result.add_error(
            f"surface-coverage: {section_name} '{item_id}' field 'out_of_scope' must be bool."
        )
        return None

    parity_ids = item["parity_ids"]
    owner_tests = item["owner_tests"]
    out_of_scope_reason = item["out_of_scope_reason"]
    code_refs = item["code_refs"]
    notes = item["notes"]

    if not isinstance(parity_ids, list) or not all(
        isinstance(value, str) and value.strip() for value in parity_ids
    ):
        result.add_error(
            f"surface-coverage: {section_name} '{item_id}' field 'parity_ids' must be list[str]."
        )
        return None
    if not isinstance(owner_tests, list) or not all(
        isinstance(value, str) and value.strip() for value in owner_tests
    ):
        result.add_error(
            f"surface-coverage: {section_name} '{item_id}' field 'owner_tests' must be list[str]."
        )
        return None
    if not isinstance(out_of_scope_reason, str):
        result.add_error(
            f"surface-coverage: {section_name} '{item_id}' field 'out_of_scope_reason' must be string."
        )
        return None
    if not isinstance(code_refs, list) or not all(
        isinstance(value, str) and value.strip() for value in code_refs
    ):
        result.add_error(
            f"surface-coverage: {section_name} '{item_id}' field 'code_refs' must be list[str]."
        )
        return None
    if not isinstance(notes, str):
        result.add_error(
            f"surface-coverage: {section_name} '{item_id}' field 'notes' must be string."
        )
        return None

    if out_of_scope:
        if not out_of_scope_reason.strip():
            result.add_error(
                f"surface-coverage: {section_name} '{item_id}' out_of_scope=true requires non-empty out_of_scope_reason."
            )
        if parity_ids:
            result.add_error(
                f"surface-coverage: {section_name} '{item_id}' out_of_scope=true requires empty parity_ids."
            )
        if owner_tests:
            result.add_error(
                f"surface-coverage: {section_name} '{item_id}' out_of_scope=true requires empty owner_tests."
            )
    else:
        if not parity_ids:
            result.add_error(
                f"surface-coverage: {section_name} '{item_id}' out_of_scope=false requires non-empty parity_ids."
            )
        if not owner_tests:
            result.add_error(
                f"surface-coverage: {section_name} '{item_id}' out_of_scope=false requires non-empty owner_tests."
            )
        if out_of_scope_reason.strip():
            result.add_error(
                f"surface-coverage: {section_name} '{item_id}' out_of_scope=false requires empty out_of_scope_reason."
            )

    return item


def _validate_index_section(
    *,
    section_name: str,
    payload: dict[str, Any],
    require_cli_fields: bool,
    result: CheckResult,
) -> dict[str, dict[str, Any]]:
    """Validate one index section and return items by id."""
    section = payload.get(section_name)
    if not isinstance(section, list):
        result.add_error(f"surface-coverage: '{section_name}' must be a list.")
        return {}

    by_id: dict[str, dict[str, Any]] = {}
    for item in section:
        validated = _validate_item_schema(
            section_name=section_name,
            item=item,
            result=result,
        )
        if validated is None:
            continue
        item_id = validated["id"]
        if item_id in by_id:
            result.add_error(
                f"surface-coverage: duplicate {section_name} id '{item_id}'."
            )
            continue
        if require_cli_fields:
            command_path = validated.get("command_path")
            source_token = validated.get("source_token")
            default_text = validated.get("default_text", "")
            if not isinstance(command_path, str) or not command_path.strip():
                result.add_error(
                    f"surface-coverage: {section_name} '{item_id}' requires non-empty 'command_path'."
                )
                continue
            if not isinstance(source_token, str) or not source_token.strip():
                result.add_error(
                    f"surface-coverage: {section_name} '{item_id}' requires non-empty 'source_token'."
                )
                continue
            if not isinstance(default_text, str):
                result.add_error(
                    f"surface-coverage: {section_name} '{item_id}' field 'default_text' must be string when provided."
                )
                continue
        by_id[item_id] = validated
    return by_id


def check_surface_coverage_artifacts(repo_root: Path) -> SurfaceCoverageReport:
    """Validate surface coverage index completeness and linkage."""
    result = CheckResult()
    index_payload = _load_surface_index(repo_root, result)
    cli_items_by_id = _validate_index_section(
        section_name="cli_items",
        payload=index_payload,
        require_cli_fields=True,
        result=result,
    )
    config_items_by_id = _validate_index_section(
        section_name="config_items",
        payload=index_payload,
        require_cli_fields=False,
        result=result,
    )
    obs_items_by_id = _validate_index_section(
        section_name="observability_items",
        payload=index_payload,
        require_cli_fields=False,
        result=result,
    )

    detected_cli = _detect_cli_surface(repo_root, result)
    detected_config = _detect_config_surface(repo_root, result)
    detected_observability = _detect_observability_contract_items(repo_root, result)

    detected_cli_ids = {item.item_id for item in detected_cli}
    detected_config_ids = set(detected_config)
    detected_observability_ids = set(detected_observability)

    unmapped_cli_ids = sorted(detected_cli_ids - set(cli_items_by_id))
    unmapped_config_ids = sorted(detected_config_ids - set(config_items_by_id))
    unmapped_observability_ids = sorted(
        detected_observability_ids - set(obs_items_by_id)
    )

    if unmapped_cli_ids:
        result.add_error(
            "surface-coverage: missing CLI mappings: " + ", ".join(unmapped_cli_ids)
        )
    if unmapped_config_ids:
        result.add_error(
            "surface-coverage: missing config mappings: "
            + ", ".join(unmapped_config_ids)
        )
    if unmapped_observability_ids:
        result.add_error(
            "surface-coverage: missing observability mappings: "
            + ", ".join(unmapped_observability_ids)
        )

    detected_cli_map = {item.item_id: item for item in detected_cli}
    for item_id, index_entry in cli_items_by_id.items():
        detected_item = detected_cli_map.get(item_id)
        if detected_item is None:
            continue
        expected_default = _normalize_text(detected_item.default_text)
        indexed_default = _normalize_text(index_entry.get("default_text", ""))
        if expected_default != indexed_default:
            result.add_error(
                f"surface-coverage: CLI default mismatch for '{item_id}': "
                f"detected='{detected_item.default_text}', indexed='{index_entry.get('default_text', '')}'."
            )

    known_parity_ids: set[str] = set()
    try:
        parity_table = load_markdown_table(
            repo_root / "project" / "parity-matrix.md",
            REQUIRED_PARITY_COLUMNS,
            "parity-matrix",
        )
    except Exception as exc:  # pragma: no cover - parity contract covers this path
        result.add_error(f"surface-coverage: unable to load parity matrix: {exc}")
    else:
        known_parity_ids = {row["behavior_id"] for row in parity_table.rows}

    linkage_gap_count = 0
    for section_name, entries in (
        ("cli_items", cli_items_by_id.values()),
        ("config_items", config_items_by_id.values()),
        ("observability_items", obs_items_by_id.values()),
    ):
        for entry in entries:
            if entry["out_of_scope"]:
                continue
            item_id = entry["id"]
            for parity_id in entry["parity_ids"]:
                if parity_id not in known_parity_ids:
                    linkage_gap_count += 1
                    result.add_error(
                        f"surface-coverage: {section_name} '{item_id}' references unknown parity_id '{parity_id}'."
                    )
            for owner_ref in entry["owner_tests"]:
                is_valid, error_message = _validate_owner_reference(
                    repo_root, owner_ref
                )
                if not is_valid:
                    linkage_gap_count += 1
                    result.add_error(
                        f"surface-coverage: {section_name} '{item_id}' {error_message}."
                    )

    return SurfaceCoverageReport(
        result=result,
        unmapped_cli_items=len(unmapped_cli_ids),
        unmapped_config_keys=len(unmapped_config_ids),
        unmapped_observability_items=len(unmapped_observability_ids),
        parity_test_linkage_gaps=linkage_gap_count,
    )
