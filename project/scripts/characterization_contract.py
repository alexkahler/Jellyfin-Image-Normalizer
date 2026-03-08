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
IMG_BEHAVIOR_IDS = [
    "IMG-SCALE-001",
    "IMG-NOSCALE-001",
    "IMG-LOGO-001",
    "IMG-CROP-001",
    "IMG-ENCODE-001",
]
SAFETY_BEHAVIOR_IDS = [
    "API-DRYRUN-001",
    "API-DRYRUN-002",
    "API-DELETE-001",
    "PIPE-DRYRUN-001",
    "PIPE-BACKDROP-001",
    "PIPE-BACKDROP-002",
    "RST-BULK-001",
    "RST-SINGLE-001",
    "RST-REFUSE-001",
    "RST-PATH-001",
]
REQUIRED_CHARACTERIZATION_BEHAVIOR_IDS = [
    *CLI_BEHAVIOR_IDS,
    *CFG_BEHAVIOR_IDS,
    *IMG_BEHAVIOR_IDS,
    *SAFETY_BEHAVIOR_IDS,
]
IMAGING_BASELINE_PATH = (
    "tests/characterization/baselines/imaging_contract_baseline.json"
)
SAFETY_BASELINE_PATH = "tests/characterization/baselines/safety_contract_baseline.json"
IMAGING_GOLDEN_MANIFEST_PATH = "tests/golden/imaging/manifest.json"
IMAGING_EXPECTED_ROOT = "tests/golden/imaging/expected"
IMAGING_FIXTURE_ROOT = "tests/golden/imaging/fixtures/realish"
IMAGING_EXPECTED_MAX_FILES = 16
IMAGING_EXPECTED_MAX_BYTES = 2_097_152
IMAGING_FIXTURE_MAX_FILES = 4
IMAGING_FIXTURE_MAX_BYTES = 524_288
DEFAULT_TOLERANT_MAE = 2.0
REQUIRED_BASELINE_FILES = {
    "tests/characterization/baselines/cli_contract_baseline.json": CLI_BEHAVIOR_IDS,
    "tests/characterization/baselines/config_contract_baseline.json": CFG_BEHAVIOR_IDS,
    IMAGING_BASELINE_PATH: IMG_BEHAVIOR_IDS,
    SAFETY_BASELINE_PATH: SAFETY_BEHAVIOR_IDS,
}
OPTIONAL_CASE_KEYS = {
    "expected_stats",
    "expected_messages",
    "expected_effective_config",
    "expected_preflight",
    "notes",
}
ALLOWED_PREFLIGHT_VALUES = {"not_reached", "mocked_ok", "mocked_fail"}
ALLOWED_GOLDEN_COMPARE_MODES = {"exact", "tolerant"}
ALLOWED_TRACE_PHASES = {
    "fetch",
    "normalize",
    "delete",
    "verify",
    "upload",
    "finalize",
}
TRACE_REQUIRED_DETAIL_KEYS = {
    "fetch": {"source_index"},
    "normalize": {"source_index", "target_index"},
    "delete": {"target_index"},
    "verify": {"target_index", "status_code"},
    "upload": {"source_index", "target_index"},
    "finalize": {"retained", "failure_kind"},
}


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


def _validate_cli_or_config_case_schema(
    *,
    baseline_path: Path,
    behavior_id: str,
    case_payload: Any,
) -> None:
    """Validate one CLI/config baseline case payload."""
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


def _validate_imaging_case_schema(
    *,
    baseline_path: Path,
    behavior_id: str,
    case_payload: Any,
) -> None:
    """Validate one imaging baseline case payload against WI-003 schema rules."""
    if not isinstance(case_payload, dict):
        raise CharacterizationError(
            f"{baseline_path}#{behavior_id} must be an object, found {type(case_payload)}."
        )

    allowed_keys = {"expected_properties", "golden_key", "notes"}
    unknown_keys = sorted(set(case_payload) - allowed_keys)
    if unknown_keys:
        raise CharacterizationError(
            f"{baseline_path}#{behavior_id} has unknown keys: {unknown_keys}."
        )

    if "expected_properties" not in case_payload:
        raise CharacterizationError(
            f"{baseline_path}#{behavior_id} missing required key: expected_properties."
        )
    expected_properties = case_payload["expected_properties"]
    if not isinstance(expected_properties, dict):
        raise CharacterizationError(
            f"{baseline_path}#{behavior_id} expected_properties must be an object."
        )

    required_property_keys = {"decision", "size", "mode", "format", "content_type"}
    missing_property_keys = sorted(required_property_keys - set(expected_properties))
    if missing_property_keys:
        raise CharacterizationError(
            f"{baseline_path}#{behavior_id} expected_properties missing keys: "
            f"{missing_property_keys}."
        )

    if (
        not isinstance(expected_properties["decision"], str)
        or not expected_properties["decision"].strip()
    ):
        raise CharacterizationError(
            f"{baseline_path}#{behavior_id} expected_properties.decision must be a "
            "non-empty string."
        )
    if (
        not isinstance(expected_properties["size"], list)
        or len(expected_properties["size"]) != 2
    ):
        raise CharacterizationError(
            f"{baseline_path}#{behavior_id} expected_properties.size must be [width, "
            "height]."
        )
    for index, value in enumerate(expected_properties["size"]):
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise CharacterizationError(
                f"{baseline_path}#{behavior_id} expected_properties.size[{index}] must "
                "be a positive integer."
            )
    for key in ("mode", "format", "content_type"):
        if (
            not isinstance(expected_properties[key], str)
            or not expected_properties[key].strip()
        ):
            raise CharacterizationError(
                f"{baseline_path}#{behavior_id} expected_properties.{key} must be a "
                "non-empty string."
            )

    golden_key = case_payload.get("golden_key")
    if not isinstance(golden_key, str) or not golden_key.strip():
        raise CharacterizationError(
            f"{baseline_path}#{behavior_id} golden_key must be a non-empty string."
        )

    notes = case_payload.get("notes")
    if notes is not None and not isinstance(notes, str):
        raise CharacterizationError(
            f"{baseline_path}#{behavior_id} notes must be a string when provided."
        )


def _is_scalar_like(value: Any) -> bool:
    """Return True when value is JSON-scalar-like for baseline observations."""
    return value is None or isinstance(value, (str, int, float, bool))


def _validate_scalar_mapping(
    *,
    baseline_path: Path,
    behavior_id: str,
    field_name: str,
    payload: Any,
) -> None:
    """Validate that a payload is an object with scalar-like leaf values."""
    if not isinstance(payload, dict):
        raise CharacterizationError(
            f"{baseline_path}#{behavior_id} {field_name} must be an object."
        )
    for key, value in payload.items():
        if not isinstance(key, str) or not key.strip():
            raise CharacterizationError(
                f"{baseline_path}#{behavior_id} {field_name} contains invalid key."
            )
        if not _is_scalar_like(value):
            raise CharacterizationError(
                f"{baseline_path}#{behavior_id} {field_name}.{key} must be a scalar "
                "value."
            )


def _is_non_negative_int(value: Any) -> bool:
    """Return True for non-bool integers >= 0."""
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _validate_trace_details(
    *,
    baseline_path: Path,
    behavior_id: str,
    event_index: int,
    phase: str,
    details: Any,
) -> None:
    """Validate phase-specific trace details payload."""
    if not isinstance(details, dict):
        raise CharacterizationError(
            f"{baseline_path}#{behavior_id} expected_observations.trace.events[{event_index}].details "
            "must be an object."
        )
    required_keys = TRACE_REQUIRED_DETAIL_KEYS[phase]
    missing_keys = sorted(required_keys - set(details))
    if missing_keys:
        raise CharacterizationError(
            f"{baseline_path}#{behavior_id} expected_observations.trace.events[{event_index}].details "
            f"missing keys: {missing_keys}."
        )

    for key in ("source_index", "target_index", "status_code"):
        if key in required_keys and not _is_non_negative_int(details.get(key)):
            raise CharacterizationError(
                f"{baseline_path}#{behavior_id} expected_observations.trace.events[{event_index}].details.{key} "
                "must be a non-negative integer."
            )
    if "retained" in required_keys and not isinstance(details.get("retained"), bool):
        raise CharacterizationError(
            f"{baseline_path}#{behavior_id} expected_observations.trace.events[{event_index}].details.retained "
            "must be bool."
        )
    if "failure_kind" in required_keys:
        failure_kind = details.get("failure_kind")
        if not isinstance(failure_kind, str) or not failure_kind.strip():
            raise CharacterizationError(
                f"{baseline_path}#{behavior_id} expected_observations.trace.events[{event_index}].details.failure_kind "
                "must be non-empty string."
            )


def _validate_trace_event_schema(
    *,
    baseline_path: Path,
    behavior_id: str,
    event_index: int,
    event_payload: Any,
) -> None:
    """Validate one structured trace event payload."""
    if not isinstance(event_payload, dict):
        raise CharacterizationError(
            f"{baseline_path}#{behavior_id} expected_observations.trace.events[{event_index}] "
            f"must be an object, found {type(event_payload)}."
        )
    required_keys = {"phase", "index", "action", "result", "details"}
    missing_keys = sorted(required_keys - set(event_payload))
    if missing_keys:
        raise CharacterizationError(
            f"{baseline_path}#{behavior_id} expected_observations.trace.events[{event_index}] "
            f"missing keys: {missing_keys}."
        )

    phase = event_payload.get("phase")
    if not isinstance(phase, str) or phase not in ALLOWED_TRACE_PHASES:
        raise CharacterizationError(
            f"{baseline_path}#{behavior_id} expected_observations.trace.events[{event_index}].phase "
            f"must be one of {sorted(ALLOWED_TRACE_PHASES)}."
        )

    event_index_value = event_payload.get("index")
    if event_index_value is not None and not _is_non_negative_int(event_index_value):
        raise CharacterizationError(
            f"{baseline_path}#{behavior_id} expected_observations.trace.events[{event_index}].index "
            "must be non-negative integer or null."
        )

    for key in ("action", "result"):
        value = event_payload.get(key)
        if not isinstance(value, str) or not value.strip():
            raise CharacterizationError(
                f"{baseline_path}#{behavior_id} expected_observations.trace.events[{event_index}].{key} "
                "must be non-empty string."
            )

    _validate_trace_details(
        baseline_path=baseline_path,
        behavior_id=behavior_id,
        event_index=event_index,
        phase=phase,
        details=event_payload.get("details"),
    )


def _validate_safety_case_schema(
    *,
    baseline_path: Path,
    behavior_id: str,
    case_payload: Any,
) -> None:
    """Validate one safety baseline case payload against WI-005 schema rules."""
    if not isinstance(case_payload, dict):
        raise CharacterizationError(
            f"{baseline_path}#{behavior_id} must be an object, found {type(case_payload)}."
        )

    allowed_keys = {"expected_observations", "expected_messages", "notes"}
    unknown_keys = sorted(set(case_payload) - allowed_keys)
    if unknown_keys:
        raise CharacterizationError(
            f"{baseline_path}#{behavior_id} has unknown keys: {unknown_keys}."
        )

    expected_observations = case_payload.get("expected_observations")
    if not isinstance(expected_observations, dict):
        raise CharacterizationError(
            f"{baseline_path}#{behavior_id} missing required object: expected_observations."
        )

    result_payload = expected_observations.get("result")
    if not isinstance(result_payload, dict):
        raise CharacterizationError(
            f"{baseline_path}#{behavior_id} expected_observations.result must be an object."
        )
    required_result_keys = {"return_value", "raises"}
    missing_result_keys = sorted(required_result_keys - set(result_payload))
    if missing_result_keys:
        raise CharacterizationError(
            f"{baseline_path}#{behavior_id} expected_observations.result missing keys: "
            f"{missing_result_keys}."
        )
    for key in required_result_keys:
        if not _is_scalar_like(result_payload[key]):
            raise CharacterizationError(
                f"{baseline_path}#{behavior_id} expected_observations.result.{key} "
                "must be a scalar value."
            )

    for optional_object in ("calls", "stats", "filesystem"):
        payload = expected_observations.get(optional_object)
        if payload is None:
            continue
        _validate_scalar_mapping(
            baseline_path=baseline_path,
            behavior_id=behavior_id,
            field_name=f"expected_observations.{optional_object}",
            payload=payload,
        )

    ordering = expected_observations.get("ordering")
    if ordering is not None:
        if not isinstance(ordering, list) or not all(
            isinstance(token, str) and token.strip() for token in ordering
        ):
            raise CharacterizationError(
                f"{baseline_path}#{behavior_id} expected_observations.ordering must "
                "be list[str]."
            )

    trace_payload = expected_observations.get("trace")
    if trace_payload is not None:
        if not isinstance(trace_payload, dict):
            raise CharacterizationError(
                f"{baseline_path}#{behavior_id} expected_observations.trace must be an object."
            )
        events = trace_payload.get("events")
        if not isinstance(events, list) or not events:
            raise CharacterizationError(
                f"{baseline_path}#{behavior_id} expected_observations.trace.events must be a non-empty list."
            )
        for event_index, event_payload in enumerate(events):
            _validate_trace_event_schema(
                baseline_path=baseline_path,
                behavior_id=behavior_id,
                event_index=event_index,
                event_payload=event_payload,
            )

    expected_messages = case_payload.get("expected_messages")
    if expected_messages is not None:
        if not isinstance(expected_messages, list) or not all(
            isinstance(item, str) for item in expected_messages
        ):
            raise CharacterizationError(
                f"{baseline_path}#{behavior_id} expected_messages must be list[str]."
            )

    notes = case_payload.get("notes")
    if not isinstance(notes, str) or not notes.strip():
        raise CharacterizationError(
            f"{baseline_path}#{behavior_id} notes must be a non-empty string."
        )


def validate_baseline_case_schema(
    *,
    baseline_relpath: str,
    baseline_path: Path,
    behavior_id: str,
    case_payload: Any,
) -> None:
    """Validate one baseline case payload using schema by baseline path."""
    if baseline_relpath == IMAGING_BASELINE_PATH:
        _validate_imaging_case_schema(
            baseline_path=baseline_path,
            behavior_id=behavior_id,
            case_payload=case_payload,
        )
        return
    if baseline_relpath == SAFETY_BASELINE_PATH:
        _validate_safety_case_schema(
            baseline_path=baseline_path,
            behavior_id=behavior_id,
            case_payload=case_payload,
        )
        return

    _validate_cli_or_config_case_schema(
        baseline_path=baseline_path,
        behavior_id=behavior_id,
        case_payload=case_payload,
    )


def load_imaging_golden_manifest(path: Path) -> dict[str, Any]:
    """Load one imaging golden manifest payload and validate schema keys."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise CharacterizationError(f"golden manifest file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise CharacterizationError(
            f"golden manifest file is not valid JSON: {path}"
        ) from exc

    if not isinstance(payload, dict):
        raise CharacterizationError(
            f"golden manifest payload must be an object: {path}"
        )
    if payload.get("version") != 1:
        raise CharacterizationError(
            f"golden manifest version must be 1 in {path}, found "
            f"{payload.get('version')!r}."
        )

    metadata = payload.get("metadata")
    if not isinstance(metadata, dict):
        raise CharacterizationError(
            f"golden manifest metadata must be an object: {path}"
        )
    for key in ("python_version", "pillow_version", "generated_at"):
        value = metadata.get(key)
        if not isinstance(value, str) or not value.strip():
            raise CharacterizationError(
                f"golden manifest metadata.{key} must be a non-empty string: {path}."
            )

    cases = payload.get("cases")
    if not isinstance(cases, dict):
        raise CharacterizationError(f"golden manifest cases must be an object: {path}.")

    for golden_key, case in cases.items():
        if not isinstance(golden_key, str) or not golden_key.strip():
            raise CharacterizationError(
                f"golden manifest contains invalid case key in {path}."
            )
        if not isinstance(case, dict):
            raise CharacterizationError(
                f"golden manifest case '{golden_key}' must be an object."
            )

        expected_path = case.get("expected_path")
        if not isinstance(expected_path, str) or not expected_path.strip():
            raise CharacterizationError(
                f"golden manifest case '{golden_key}' expected_path must be a non-empty "
                "string."
            )

        compare_mode = case.get("compare_mode")
        if compare_mode not in ALLOWED_GOLDEN_COMPARE_MODES:
            raise CharacterizationError(
                f"golden manifest case '{golden_key}' compare_mode must be one of "
                f"{sorted(ALLOWED_GOLDEN_COMPARE_MODES)}, found {compare_mode!r}."
            )

        tolerance_note = case.get("tolerance_note")
        if tolerance_note is not None and not isinstance(tolerance_note, str):
            raise CharacterizationError(
                f"golden manifest case '{golden_key}' tolerance_note must be a string."
            )

        if compare_mode == "tolerant":
            max_mae = case.get("max_mean_abs_error")
            if isinstance(max_mae, bool) or not isinstance(max_mae, (int, float)):
                raise CharacterizationError(
                    f"golden manifest case '{golden_key}' max_mean_abs_error must be "
                    "a number in tolerant mode."
                )
            if float(max_mae) <= 0:
                raise CharacterizationError(
                    f"golden manifest case '{golden_key}' max_mean_abs_error must be > 0."
                )

            max_diff_pixels = case.get("max_diff_pixels")
            if max_diff_pixels is not None:
                if (
                    isinstance(max_diff_pixels, bool)
                    or not isinstance(max_diff_pixels, int)
                    or max_diff_pixels < 0
                ):
                    raise CharacterizationError(
                        f"golden manifest case '{golden_key}' max_diff_pixels must be "
                        "a non-negative integer when provided."
                    )

            requires_tolerance_note = (
                float(max_mae) != DEFAULT_TOLERANT_MAE or max_diff_pixels is not None
            )
            if requires_tolerance_note and (
                tolerance_note is None or not tolerance_note.strip()
            ):
                raise CharacterizationError(
                    f"golden manifest case '{golden_key}' uses tolerance overrides "
                    "and requires tolerance_note."
                )

    return payload


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
