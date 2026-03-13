"""Verification contract parsing and schema validation."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

EXPECTED_VERIFICATION_COMMANDS = [
    "PYTHONPATH=src ./.venv/bin/python -m pytest",
    "./.venv/bin/python -m ruff check .",
    "./.venv/bin/python project/scripts/format_policy.py --target src --mode block",
    "./.venv/bin/python project/scripts/format_policy.py --target tests --mode warn",
    "./.venv/bin/python -m mypy src",
    "./.venv/bin/python -m bandit -r src",
    "./.venv/bin/python -m pip_audit",
]
EXPECTED_REQUIRED_CI_JOBS = ["test", "security", "quality", "governance"]
EXPECTED_RUNTIME_GATE_TARGETS = [
    "tests/characterization/safety_contract",
    "tests/characterization/cli_contract/test_cli_contract_characterization.py::test_cli_test_jf_blocks_operational_flags",
    "tests/characterization/config_contract/test_config_contract_characterization.py::test_config_requires_core_fields",
    "tests/characterization/cli_contract/test_cli_contract_characterization.py::test_cli_generate_config_blocks_operational_flags",
    "tests/characterization/cli_contract/test_cli_contract_characterization.py::test_cli_warns_for_unrecommended_aspect_ratio",
]
EXPECTED_RUNTIME_GATE_BUDGET_SECONDS = 180
EXPECTED_LOC_POLICY_ANTI_EVASION_RATIONALE = "honest_loc_required_for_maintainability"
EXPECTED_LOC_POLICY_ANTI_EVASION_NONCOMPLIANCE_RULE = (
    "suppression_or_packing_invalidates_loc_claim"
)
DOCSTRING_POLICY_REQUIRED_SRC_MAX_VIOLATIONS = 0
DOCSTRING_POLICY_MAX_BASELINE_TESTS = 189
EXPECTED_DOCSTRING_POLICY_CONVENTION = "google"
EXPECTED_DOCSTRING_POLICY_COMMENTS = (
    "targeted_inline_comments_for_non_obvious_logic"
)
EXPECTED_FORMAT_POLICY_SRC_TARGET = "src"
EXPECTED_FORMAT_POLICY_TESTS_TARGET = "tests"
EXPECTED_FORMAT_POLICY_ON_CHECK_FAILURE = "run_format"


class GovernanceError(Exception):
    """Raised when governance artifacts cannot be parsed or validated."""


@dataclass(frozen=True)
class LocPolicy:
    """Line-count policy parsed from the verification contract."""

    src_max_lines: int
    src_mode: str
    tests_max_lines: int
    tests_mode: str
    anti_evasion_disallow_fmt: bool
    anti_evasion_disallow_multi_statement: bool
    anti_evasion_disallow_dense_control_flow: bool
    anti_evasion_fail_closed: bool
    anti_evasion_rationale: str
    anti_evasion_noncompliance_rule: str
    anti_evasion_multi_statement_max_semicolons: int
    anti_evasion_control_flow_inline_suite_max: int


@dataclass(frozen=True)
class RuntimeGatePolicy:
    """Runtime characterization gate policy from verification contract."""

    targets: list[str]
    budget_seconds: int


@dataclass(frozen=True)
class DocstringPolicy:
    """Docstring governance policy parsed from the verification contract."""

    convention: str
    src_mode: str
    tests_mode: str
    src_max_violations: int
    tests_max_violations: int
    comments_policy: str


@dataclass(frozen=True)
class FormatPolicy:
    """Formatting governance policy parsed from the verification contract."""

    src_mode: str
    tests_mode: str
    src_target: str
    tests_target: str
    on_check_failure: str


@dataclass(frozen=True)
class VerificationContract:
    """Parsed verification-contract values used by governance checks."""

    version: int
    python_version: str
    verification_commands: list[str]
    required_ci_jobs: list[str]
    loc_policy: LocPolicy
    runtime_gate: RuntimeGatePolicy
    docstring_policy: DocstringPolicy
    format_policy: FormatPolicy


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


def _parse_non_negative_int(value: str, key: str) -> int:
    """Parse and validate a non-negative integer scalar."""
    if not re.fullmatch(r"\d+", value):
        raise GovernanceError(f"{key} must be a non-negative integer, got '{value}'.")
    return int(value)


def _parse_bool(value: str, key: str) -> bool:
    """Parse and validate one YAML-like boolean scalar."""
    normalized = value.strip().lower()
    if normalized == "true":
        return True
    if normalized == "false":
        return False
    raise GovernanceError(f"{key} must be 'true' or 'false', got '{value}'.")


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
    runtime_gate_targets = _parse_list_block(
        _extract_indented_block(text, "characterization_runtime_gate_targets"),
        "characterization_runtime_gate_targets",
    )
    runtime_gate_budget_seconds = _parse_positive_int(
        _extract_scalar(text, "characterization_runtime_gate_budget_seconds"),
        "characterization_runtime_gate_budget_seconds",
    )

    loc_policy_map = _parse_map_block(
        _extract_indented_block(text, "loc_policy"),
        "loc_policy",
    )
    required_loc_policy_keys = (
        "src_max_lines",
        "src_mode",
        "tests_max_lines",
        "tests_mode",
        "anti_evasion_disallow_fmt",
        "anti_evasion_disallow_multi_statement",
        "anti_evasion_disallow_dense_control_flow",
        "anti_evasion_fail_closed",
        "anti_evasion_rationale",
        "anti_evasion_noncompliance_rule",
        "anti_evasion_multi_statement_max_semicolons",
        "anti_evasion_control_flow_inline_suite_max",
    )
    for required_key in required_loc_policy_keys:
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
        anti_evasion_disallow_fmt=_parse_bool(
            loc_policy_map["anti_evasion_disallow_fmt"],
            "loc_policy.anti_evasion_disallow_fmt",
        ),
        anti_evasion_disallow_multi_statement=_parse_bool(
            loc_policy_map["anti_evasion_disallow_multi_statement"],
            "loc_policy.anti_evasion_disallow_multi_statement",
        ),
        anti_evasion_disallow_dense_control_flow=_parse_bool(
            loc_policy_map["anti_evasion_disallow_dense_control_flow"],
            "loc_policy.anti_evasion_disallow_dense_control_flow",
        ),
        anti_evasion_fail_closed=_parse_bool(
            loc_policy_map["anti_evasion_fail_closed"],
            "loc_policy.anti_evasion_fail_closed",
        ),
        anti_evasion_rationale=loc_policy_map["anti_evasion_rationale"],
        anti_evasion_noncompliance_rule=loc_policy_map[
            "anti_evasion_noncompliance_rule"
        ],
        anti_evasion_multi_statement_max_semicolons=_parse_non_negative_int(
            loc_policy_map["anti_evasion_multi_statement_max_semicolons"],
            "loc_policy.anti_evasion_multi_statement_max_semicolons",
        ),
        anti_evasion_control_flow_inline_suite_max=_parse_non_negative_int(
            loc_policy_map["anti_evasion_control_flow_inline_suite_max"],
            "loc_policy.anti_evasion_control_flow_inline_suite_max",
        ),
    )
    runtime_gate = RuntimeGatePolicy(
        targets=runtime_gate_targets,
        budget_seconds=runtime_gate_budget_seconds,
    )
    docstring_policy_map = _parse_map_block(
        _extract_indented_block(text, "docstring_policy"),
        "docstring_policy",
    )
    required_docstring_policy_keys = (
        "convention",
        "src_mode",
        "tests_mode",
        "src_max_violations",
        "tests_max_violations",
        "comments_policy",
    )
    for required_key in required_docstring_policy_keys:
        if required_key not in docstring_policy_map:
            raise GovernanceError(
                f"docstring_policy missing required key: {required_key}"
            )
    docstring_policy = DocstringPolicy(
        convention=docstring_policy_map["convention"],
        src_mode=docstring_policy_map["src_mode"],
        tests_mode=docstring_policy_map["tests_mode"],
        src_max_violations=_parse_non_negative_int(
            docstring_policy_map["src_max_violations"],
            "docstring_policy.src_max_violations",
        ),
        tests_max_violations=_parse_non_negative_int(
            docstring_policy_map["tests_max_violations"],
            "docstring_policy.tests_max_violations",
        ),
        comments_policy=docstring_policy_map["comments_policy"],
    )
    format_policy_map = _parse_map_block(
        _extract_indented_block(text, "format_policy"),
        "format_policy",
    )
    required_format_policy_keys = (
        "src_mode",
        "tests_mode",
        "src_target",
        "tests_target",
        "on_check_failure",
    )
    for required_key in required_format_policy_keys:
        if required_key not in format_policy_map:
            raise GovernanceError(f"format_policy missing required key: {required_key}")
    format_policy = FormatPolicy(
        src_mode=format_policy_map["src_mode"],
        tests_mode=format_policy_map["tests_mode"],
        src_target=format_policy_map["src_target"],
        tests_target=format_policy_map["tests_target"],
        on_check_failure=format_policy_map["on_check_failure"],
    )

    return VerificationContract(
        version=version,
        python_version=python_version,
        verification_commands=verification_commands,
        required_ci_jobs=required_ci_jobs,
        loc_policy=loc_policy,
        runtime_gate=runtime_gate,
        docstring_policy=docstring_policy,
        format_policy=format_policy,
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
    if not contract.loc_policy.anti_evasion_disallow_fmt:
        result.add_error("loc_policy.anti_evasion_disallow_fmt must be true.")
    if not contract.loc_policy.anti_evasion_disallow_multi_statement:
        result.add_error(
            "loc_policy.anti_evasion_disallow_multi_statement must be true."
        )
    if not contract.loc_policy.anti_evasion_disallow_dense_control_flow:
        result.add_error(
            "loc_policy.anti_evasion_disallow_dense_control_flow must be true."
        )
    if not contract.loc_policy.anti_evasion_fail_closed:
        result.add_error("loc_policy.anti_evasion_fail_closed must be true.")
    if (
        contract.loc_policy.anti_evasion_rationale
        != EXPECTED_LOC_POLICY_ANTI_EVASION_RATIONALE
    ):
        result.add_error(
            "loc_policy.anti_evasion_rationale must be "
            f"'{EXPECTED_LOC_POLICY_ANTI_EVASION_RATIONALE}'."
        )
    if (
        contract.loc_policy.anti_evasion_noncompliance_rule
        != EXPECTED_LOC_POLICY_ANTI_EVASION_NONCOMPLIANCE_RULE
    ):
        result.add_error(
            "loc_policy.anti_evasion_noncompliance_rule must be "
            f"'{EXPECTED_LOC_POLICY_ANTI_EVASION_NONCOMPLIANCE_RULE}'."
        )
    if contract.loc_policy.anti_evasion_multi_statement_max_semicolons != 0:
        result.add_error(
            "loc_policy.anti_evasion_multi_statement_max_semicolons must be 0."
        )
    if contract.loc_policy.anti_evasion_control_flow_inline_suite_max != 0:
        result.add_error(
            "loc_policy.anti_evasion_control_flow_inline_suite_max must be 0."
        )
    if contract.runtime_gate.targets != EXPECTED_RUNTIME_GATE_TARGETS:
        result.add_error(
            "characterization_runtime_gate_targets must be exactly "
            f"{EXPECTED_RUNTIME_GATE_TARGETS}, found {contract.runtime_gate.targets}."
        )
    if contract.runtime_gate.budget_seconds != EXPECTED_RUNTIME_GATE_BUDGET_SECONDS:
        result.add_error(
            "characterization_runtime_gate_budget_seconds must be "
            f"{EXPECTED_RUNTIME_GATE_BUDGET_SECONDS}."
        )
    if contract.docstring_policy.convention != EXPECTED_DOCSTRING_POLICY_CONVENTION:
        result.add_error(
            "docstring_policy.convention must be "
            f"'{EXPECTED_DOCSTRING_POLICY_CONVENTION}'."
        )
    if contract.docstring_policy.src_mode != "block":
        result.add_error("docstring_policy.src_mode must be 'block'.")
    if contract.docstring_policy.tests_mode != "warn":
        result.add_error("docstring_policy.tests_mode must be 'warn'.")
    if (
        contract.docstring_policy.src_max_violations
        != DOCSTRING_POLICY_REQUIRED_SRC_MAX_VIOLATIONS
    ):
        result.add_error(
            "docstring_policy.src_max_violations must be "
            f"{DOCSTRING_POLICY_REQUIRED_SRC_MAX_VIOLATIONS}."
        )
    if (
        contract.docstring_policy.tests_max_violations
        > DOCSTRING_POLICY_MAX_BASELINE_TESTS
    ):
        result.add_error(
            "docstring_policy.tests_max_violations must be <= "
            f"{DOCSTRING_POLICY_MAX_BASELINE_TESTS}."
        )
    if contract.docstring_policy.comments_policy != EXPECTED_DOCSTRING_POLICY_COMMENTS:
        result.add_error(
            "docstring_policy.comments_policy must be "
            f"'{EXPECTED_DOCSTRING_POLICY_COMMENTS}'."
        )
    if contract.format_policy.src_mode != "block":
        result.add_error("format_policy.src_mode must be 'block'.")
    if contract.format_policy.tests_mode != "warn":
        result.add_error("format_policy.tests_mode must be 'warn'.")
    if contract.format_policy.src_target != EXPECTED_FORMAT_POLICY_SRC_TARGET:
        result.add_error(
            "format_policy.src_target must be "
            f"'{EXPECTED_FORMAT_POLICY_SRC_TARGET}'."
        )
    if contract.format_policy.tests_target != EXPECTED_FORMAT_POLICY_TESTS_TARGET:
        result.add_error(
            "format_policy.tests_target must be "
            f"'{EXPECTED_FORMAT_POLICY_TESTS_TARGET}'."
        )
    if (
        contract.format_policy.on_check_failure
        != EXPECTED_FORMAT_POLICY_ON_CHECK_FAILURE
    ):
        result.add_error(
            "format_policy.on_check_failure must be "
            f"'{EXPECTED_FORMAT_POLICY_ON_CHECK_FAILURE}'."
        )

    return result
