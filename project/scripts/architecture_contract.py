"""Schema and serialization helpers for architecture governance artifacts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

V1_ROOT = "src/jfin"
BASELINE_RELATIVE_PATH = "project/architecture-baseline.json"
BASELINE_VERSION = 1
DEFAULT_ENTRY_EXIT_MODULES = (f"{V1_ROOT}/cli.py",)
EXIT_COUNTER_KEYS = (
    "sys_exit_calls",
    "system_exit_raises",
    "sys_import_exit_calls",
    "builtins_exit_calls",
)


class ArchitectureContractError(Exception):
    """Raised when architecture governance artifacts are malformed."""


@dataclass(frozen=True)
class ExitCounters:
    """Exit-pattern counter set tracked by architecture governance."""

    sys_exit_calls: int
    system_exit_raises: int
    sys_import_exit_calls: int
    builtins_exit_calls: int

    @property
    def total(self) -> int:
        """Return the sum of all tracked exit pattern counters."""
        return (
            self.sys_exit_calls
            + self.system_exit_raises
            + self.sys_import_exit_calls
            + self.builtins_exit_calls
        )


@dataclass(frozen=True)
class ArchitectureBaseline:
    """Parsed architecture baseline payload used by ratchet checks."""

    version: int
    v1_root: str
    entry_exit_modules: tuple[str, ...]
    non_entry_exit_allowlist: dict[str, ExitCounters]


def _normalize_posix_path(value: str) -> str:
    """Normalize path separators to forward slashes for stable comparisons."""
    return value.replace("\\", "/").strip()


def _require_object(payload: Any, *, context: str) -> dict[str, Any]:
    """Return payload as dict or raise a schema error."""
    if not isinstance(payload, dict):
        raise ArchitectureContractError(f"{context} must be an object.")
    return payload


def _require_string(value: Any, *, field: str) -> str:
    """Return a non-empty string value or raise a schema error."""
    if not isinstance(value, str) or not value.strip():
        raise ArchitectureContractError(f"{field} must be a non-empty string.")
    return value


def _require_non_negative_int(value: Any, *, field: str) -> int:
    """Return an integer >= 0 or raise a schema error."""
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ArchitectureContractError(f"{field} must be a non-negative integer.")
    return value


def _parse_exit_counters(payload: Any, *, path_key: str) -> ExitCounters:
    """Validate and parse one file counter payload."""
    counters_obj = _require_object(payload, context=f"{path_key} counters")
    unknown_keys = sorted(set(counters_obj) - set(EXIT_COUNTER_KEYS))
    if unknown_keys:
        raise ArchitectureContractError(
            f"{path_key} counters contain unknown keys: {unknown_keys}."
        )

    counter_values: dict[str, int] = {}
    for key in EXIT_COUNTER_KEYS:
        if key not in counters_obj:
            raise ArchitectureContractError(f"{path_key} counters missing key: {key}.")
        counter_values[key] = _require_non_negative_int(
            counters_obj[key],
            field=f"{path_key}.{key}",
        )

    return ExitCounters(**counter_values)


def load_architecture_baseline(path: Path) -> ArchitectureBaseline:
    """Load and validate `project/architecture-baseline.json`."""
    try:
        raw_payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ArchitectureContractError(
            f"architecture baseline file not found: {path}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise ArchitectureContractError(
            f"architecture baseline is not valid JSON: {path}"
        ) from exc

    payload = _require_object(raw_payload, context="architecture baseline payload")

    version = _require_non_negative_int(payload.get("version"), field="version")
    if version != BASELINE_VERSION:
        raise ArchitectureContractError(
            f"version must be {BASELINE_VERSION}, found {version}."
        )

    v1_root = _normalize_posix_path(
        _require_string(payload.get("v1_root"), field="v1_root")
    )
    if v1_root != V1_ROOT:
        raise ArchitectureContractError(
            f"v1_root must be '{V1_ROOT}', found '{v1_root}'."
        )

    entry_exit_modules_raw = payload.get("entry_exit_modules")
    if not isinstance(entry_exit_modules_raw, list) or not entry_exit_modules_raw:
        raise ArchitectureContractError("entry_exit_modules must be a non-empty list.")
    entry_exit_modules: list[str] = []
    for index, value in enumerate(entry_exit_modules_raw):
        module_path = _normalize_posix_path(
            _require_string(value, field=f"entry_exit_modules[{index}]")
        )
        if not module_path.startswith(f"{v1_root}/"):
            raise ArchitectureContractError(
                f"entry_exit_modules[{index}] must be under {v1_root}/."
            )
        entry_exit_modules.append(module_path)

    expected_entry_modules = list(DEFAULT_ENTRY_EXIT_MODULES)
    if entry_exit_modules != expected_entry_modules:
        raise ArchitectureContractError(
            "entry_exit_modules must be exactly "
            f"{expected_entry_modules}, found {entry_exit_modules}."
        )

    allowlist_raw = payload.get("non_entry_exit_allowlist")
    allowlist_obj = _require_object(
        allowlist_raw,
        context="non_entry_exit_allowlist",
    )

    non_entry_exit_allowlist: dict[str, ExitCounters] = {}
    for raw_path, counter_payload in allowlist_obj.items():
        normalized_path = _normalize_posix_path(
            _require_string(raw_path, field="non_entry_exit_allowlist key")
        )
        if not normalized_path.startswith(
            f"{v1_root}/"
        ) or not normalized_path.endswith(".py"):
            raise ArchitectureContractError(
                "non_entry_exit_allowlist keys must be Python files under "
                f"{v1_root}/, found '{raw_path}'."
            )
        non_entry_exit_allowlist[normalized_path] = _parse_exit_counters(
            counter_payload,
            path_key=normalized_path,
        )

    return ArchitectureBaseline(
        version=version,
        v1_root=v1_root,
        entry_exit_modules=tuple(entry_exit_modules),
        non_entry_exit_allowlist=dict(sorted(non_entry_exit_allowlist.items())),
    )


def _baseline_to_payload(baseline: ArchitectureBaseline) -> dict[str, Any]:
    """Convert baseline dataclass objects to a JSON-serializable payload."""
    return {
        "version": baseline.version,
        "v1_root": baseline.v1_root,
        "entry_exit_modules": list(baseline.entry_exit_modules),
        "non_entry_exit_allowlist": {
            path: {
                "sys_exit_calls": counters.sys_exit_calls,
                "system_exit_raises": counters.system_exit_raises,
                "sys_import_exit_calls": counters.sys_import_exit_calls,
                "builtins_exit_calls": counters.builtins_exit_calls,
            }
            for path, counters in baseline.non_entry_exit_allowlist.items()
        },
    }


def serialize_architecture_baseline(baseline: ArchitectureBaseline) -> str:
    """Serialize an architecture baseline payload using stable formatting."""
    return json.dumps(_baseline_to_payload(baseline), indent=2, sort_keys=True) + "\n"
