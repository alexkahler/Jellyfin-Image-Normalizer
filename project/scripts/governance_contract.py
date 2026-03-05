"""Verification contract parsing and schema validation."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

EXPECTED_VERIFICATION_COMMANDS = [
    "PYTHONPATH=src ./.venv/bin/python -m pytest",
    "./.venv/bin/python -m ruff check .",
    "./.venv/bin/python -m ruff format --check .",
    "./.venv/bin/python -m mypy src",
    "./.venv/bin/python -m bandit -r src",
    "./.venv/bin/python -m pip_audit",
]
EXPECTED_REQUIRED_CI_JOBS = ["test", "security", "quality", "governance"]


class GovernanceError(Exception):
    """Raised when governance artifacts cannot be parsed or validated."""


@dataclass(frozen=True)
class LocPolicy:
    """Line-count policy parsed from the verification contract."""

    src_max_lines: int
    src_mode: str
    tests_max_lines: int
    tests_mode: str


@dataclass(frozen=True)
class VerificationContract:
    """Parsed verification-contract values used by governance checks."""

    version: int
    python_version: str
    verification_commands: list[str]
    required_ci_jobs: list[str]
    loc_policy: LocPolicy


@dataclass
class CheckResult:
    """Collect blocking errors and non-blocking warnings from one check."""

    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def add_error(self, message: str) -> None:
        """Record one blocking check failure."""
        self.errors.append(message)

    def add_warning(self, message: str) -> None:
        """Record one non-blocking check warning."""
        self.warnings.append(message)

    def merge(self, other: "CheckResult") -> None:
        """Merge another check result into this one."""
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)


def _strip_quotes(value: str) -> str:
    """Remove optional matching single or double quotes around a scalar value."""
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def _extract_scalar(text: str, key: str) -> str:
    """Extract a top-level `key: value` scalar from a YAML-like document."""
    pattern = re.compile(rf"(?m)^{re.escape(key)}:\s*(.+?)\s*$")
    match = pattern.search(text)
    if not match:
        raise GovernanceError(f"Missing required key: {key}")
    return _strip_quotes(match.group(1))


def _extract_indented_block(text: str, key: str) -> str:
    """Extract an indented block directly under a top-level key."""
    pattern = re.compile(rf"(?ms)^{re.escape(key)}:\s*\n((?:^[ ]{{2}}[^\n]*(?:\n|$))*)")
    match = pattern.search(text)
    if not match:
        raise GovernanceError(f"Missing required block: {key}")
    return match.group(1)


def _parse_list_block(block_text: str, key: str) -> list[str]:
    """Parse a YAML-like list block where each line is formatted as `  - value`."""
    parsed_items: list[str] = []
    for raw_line in block_text.splitlines():
        line = raw_line.rstrip()
        if not line:
            continue
        if not line.startswith("  - "):
            raise GovernanceError(
                f"Malformed list item in {key}: expected '  - value', got '{line}'."
            )
        parsed_items.append(_strip_quotes(line[4:].strip()))
    if not parsed_items:
        raise GovernanceError(f"{key} must contain at least one list item.")
    return parsed_items


def _parse_map_block(block_text: str, key: str) -> dict[str, str]:
    """Parse a YAML-like map block where each line is formatted as `  key: value`."""
    parsed_map: dict[str, str] = {}
    for raw_line in block_text.splitlines():
        line = raw_line.rstrip()
        if not line:
            continue
        match = re.match(r"^[ ]{2}([a-z_]+):\s*(.+?)\s*$", line)
        if not match:
            raise GovernanceError(
                f"Malformed map item in {key}: expected '  key: value', got '{line}'."
            )
        parsed_map[match.group(1)] = _strip_quotes(match.group(2))
    if not parsed_map:
        raise GovernanceError(f"{key} must contain at least one mapping entry.")
    return parsed_map


def _parse_positive_int(value: str, key: str) -> int:
    """Parse and validate a positive integer scalar."""
    if not re.fullmatch(r"\d+", value):
        raise GovernanceError(f"{key} must be a positive integer, got '{value}'.")
    parsed = int(value)
    if parsed <= 0:
        raise GovernanceError(f"{key} must be greater than zero.")
    return parsed


def parse_verification_contract(contract_path: Path) -> VerificationContract:
    """Load and parse `project/verification-contract.yml`."""
    try:
        text = contract_path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise GovernanceError(f"Contract file not found: {contract_path}") from exc

    version = _parse_positive_int(_extract_scalar(text, "version"), "version")
    python_version = _extract_scalar(text, "python_version")
    verification_commands = _parse_list_block(
        _extract_indented_block(text, "verification_commands"),
        "verification_commands",
    )
    required_ci_jobs = _parse_list_block(
        _extract_indented_block(text, "required_ci_jobs"),
        "required_ci_jobs",
    )

    loc_policy_map = _parse_map_block(
        _extract_indented_block(text, "loc_policy"),
        "loc_policy",
    )
    for required_key in ("src_max_lines", "src_mode", "tests_max_lines", "tests_mode"):
        if required_key not in loc_policy_map:
            raise GovernanceError(f"loc_policy missing required key: {required_key}")

    loc_policy = LocPolicy(
        src_max_lines=_parse_positive_int(
            loc_policy_map["src_max_lines"],
            "loc_policy.src_max_lines",
        ),
        src_mode=loc_policy_map["src_mode"],
        tests_max_lines=_parse_positive_int(
            loc_policy_map["tests_max_lines"],
            "loc_policy.tests_max_lines",
        ),
        tests_mode=loc_policy_map["tests_mode"],
    )

    return VerificationContract(
        version=version,
        python_version=python_version,
        verification_commands=verification_commands,
        required_ci_jobs=required_ci_jobs,
        loc_policy=loc_policy,
    )


def check_contract_schema(contract: VerificationContract) -> CheckResult:
    """Validate contract values against the WI-001 fixed governance schema."""
    result = CheckResult()

    if contract.version != 1:
        result.add_error(f"version must be 1, found {contract.version}.")
    if contract.python_version != "3.13":
        result.add_error(
            f"python_version must be exactly '3.13', found '{contract.python_version}'."
        )
    if contract.verification_commands != EXPECTED_VERIFICATION_COMMANDS:
        result.add_error(
            "verification_commands must match the required ordered command set."
        )
    if contract.required_ci_jobs != EXPECTED_REQUIRED_CI_JOBS:
        result.add_error(
            "required_ci_jobs must be exactly "
            f"{EXPECTED_REQUIRED_CI_JOBS}, found {contract.required_ci_jobs}."
        )
    if contract.loc_policy.src_max_lines != 300:
        result.add_error("loc_policy.src_max_lines must be 300.")
    if contract.loc_policy.src_mode != "block":
        result.add_error("loc_policy.src_mode must be 'block'.")
    if contract.loc_policy.tests_max_lines != 300:
        result.add_error("loc_policy.tests_max_lines must be 300.")
    if contract.loc_policy.tests_mode != "warn":
        result.add_error("loc_policy.tests_mode must be 'warn'.")

    return result
