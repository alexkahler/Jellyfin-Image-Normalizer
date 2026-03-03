"""Shared constants and parsing helpers for characterization governance checks."""

from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any

CLI_BEHAVIOR_IDS = [
    "CLI-RESTORE-001",
    "CLI-GENCFG-001",
    "CLI-TESTJF-001",
    "CLI-SINGLE-001",
    "CLI-OVERRIDE-001",
    "CLI-ASPECT-001",
]
CFG_BEHAVIOR_IDS = [
    "CFG-TOML-001",
    "CFG-TOML-002",
    "CFG-TYPE-001",
    "CFG-CORE-001",
    "CFG-OPS-001",
    "CFG-DISC-001",
    "CFG-OVERRIDE-001",
]
REQUIRED_CHARACTERIZATION_BEHAVIOR_IDS = [*CLI_BEHAVIOR_IDS, *CFG_BEHAVIOR_IDS]
REQUIRED_BASELINE_FILES = {
    "tests/characterization/baselines/cli_contract_baseline.json": CLI_BEHAVIOR_IDS,
    "tests/characterization/baselines/config_contract_baseline.json": CFG_BEHAVIOR_IDS,
}
OPTIONAL_CASE_KEYS = {
    "expected_stats",
    "expected_messages",
    "expected_effective_config",
    "expected_preflight",
    "notes",
}
ALLOWED_PREFLIGHT_VALUES = {"not_reached", "mocked_ok", "mocked_fail"}


class CharacterizationError(Exception):
    """Raised when characterization artifacts are malformed."""


def load_baseline_payload(path: Path) -> dict[str, Any]:
    """Load one baseline JSON payload and enforce top-level schema keys."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise CharacterizationError(f"baseline file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise CharacterizationError(f"baseline file is not valid JSON: {path}") from exc

    if not isinstance(payload, dict):
        raise CharacterizationError(f"baseline payload must be an object: {path}")
    if payload.get("version") != 1:
        raise CharacterizationError(
            f"baseline version must be 1 in {path}, found {payload.get('version')!r}."
        )
    cases = payload.get("cases")
    if not isinstance(cases, dict):
        raise CharacterizationError(f"'cases' must be an object in {path}.")
    return payload


def validate_baseline_case_schema(
    *,
    baseline_path: Path,
    behavior_id: str,
    case_payload: Any,
) -> None:
    """Validate one baseline case payload against WI-004 case schema rules."""
    if not isinstance(case_payload, dict):
        raise CharacterizationError(
            f"{baseline_path}#{behavior_id} must be an object, found {type(case_payload)}."
        )

    allowed_keys = {"expected_exit_code", *OPTIONAL_CASE_KEYS}
    unknown_keys = sorted(set(case_payload) - allowed_keys)
    if unknown_keys:
        raise CharacterizationError(
            f"{baseline_path}#{behavior_id} has unknown keys: {unknown_keys}."
        )

    if "expected_exit_code" not in case_payload:
        raise CharacterizationError(
            f"{baseline_path}#{behavior_id} missing required key: expected_exit_code."
        )
    exit_code = case_payload["expected_exit_code"]
    if isinstance(exit_code, bool) or not isinstance(exit_code, int):
        raise CharacterizationError(
            f"{baseline_path}#{behavior_id} expected_exit_code must be int."
        )

    expected_stats = case_payload.get("expected_stats")
    if expected_stats is not None:
        if not isinstance(expected_stats, dict):
            raise CharacterizationError(
                f"{baseline_path}#{behavior_id} expected_stats must be an object."
            )
        for key, value in expected_stats.items():
            if key not in {"errors", "warnings", "successes"}:
                raise CharacterizationError(
                    f"{baseline_path}#{behavior_id} expected_stats has invalid key '{key}'."
                )
            if isinstance(value, bool) or not isinstance(value, int):
                raise CharacterizationError(
                    f"{baseline_path}#{behavior_id} expected_stats.{key} must be int."
                )

    expected_messages = case_payload.get("expected_messages")
    if expected_messages is not None:
        if not isinstance(expected_messages, list) or not all(
            isinstance(item, str) for item in expected_messages
        ):
            raise CharacterizationError(
                f"{baseline_path}#{behavior_id} expected_messages must be list[str]."
            )

    expected_effective_config = case_payload.get("expected_effective_config")
    if expected_effective_config is not None and not isinstance(
        expected_effective_config,
        dict,
    ):
        raise CharacterizationError(
            f"{baseline_path}#{behavior_id} expected_effective_config must be an object."
        )

    expected_preflight = case_payload.get("expected_preflight")
    if (
        expected_preflight is not None
        and expected_preflight not in ALLOWED_PREFLIGHT_VALUES
    ):
        raise CharacterizationError(
            f"{baseline_path}#{behavior_id} has invalid expected_preflight "
            f"'{expected_preflight}'."
        )

    notes = case_payload.get("notes")
    if notes is not None and not isinstance(notes, str):
        raise CharacterizationError(
            f"{baseline_path}#{behavior_id} notes must be a string when provided."
        )


def parse_baseline_source(reference: str) -> tuple[str, str]:
    """Parse `path#behavior_id` references used by parity baseline_source fields."""
    path_part, sep, anchor = reference.partition("#")
    if not sep or not path_part or not anchor:
        raise CharacterizationError(
            f"baseline_source must be formatted as <path>#<behavior_id>, found '{reference}'."
        )
    return path_part, anchor


def parse_owner_test_reference(owner_test: str) -> tuple[str, str]:
    """Parse `path::function_name` references used by parity owner_test fields."""
    path_part, sep, function_name = owner_test.partition("::")
    if not sep or not path_part or not function_name:
        raise CharacterizationError(
            f"owner_test must be formatted as <path>::<function>, found '{owner_test}'."
        )
    return path_part, function_name


def owner_test_exists(test_file_path: Path, function_name: str) -> bool:
    """Return True when a function name exists in a Python test file's AST."""
    try:
        source = test_file_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return False
    tree = ast.parse(source, filename=str(test_file_path))
    return any(
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == function_name
        for node in ast.walk(tree)
    )
