"""Executable governance checks for CI, LOC policy, and version consistency."""

from __future__ import annotations

import argparse
import ast
import io
import re
import tokenize
from pathlib import Path
from typing import Iterable

from architecture_checks import (
    check_architecture_artifacts,
    render_architecture_baseline,
)
from characterization_checks import check_characterization_artifacts
from governance_contract import (
    CheckResult,
    GovernanceError,
    VerificationContract,
    check_contract_schema,
    parse_verification_contract,
)
from parity_checks import check_parity_artifacts
from readiness_checks import check_readiness_artifacts

SUPPORTED_CHECKS = (
    "schema",
    "ci-sync",
    "loc",
    "python-version",
    "architecture",
    "parity",
    "characterization",
    "readiness",
)
EXPECTED_VENV_BOOTSTRAP = "python -m venv .venv"
EXPECTED_GOVERNANCE_INSTALL_PREFIX = "./.venv/bin/python -m pip install"
DOCS_TOPOLOGY_ERROR_PREFIX = "docs_topology.contract"
CANONICAL_CHARACTERIZATION_SUITES = (
    "tests/characterization/cli_contract/",
    "tests/characterization/config_contract/",
    "tests/characterization/imaging_contract/",
    "tests/characterization/safety_contract/",
)
CANONICAL_CHARACTERIZATION_BASELINES = "tests/characterization/baselines/"
V1_PLAN_CHARACTERIZATION_SUITES_HEADING = "### Characterization suites"
TECHNICAL_NOTES_SUITES_ANCHOR = "Characterization suites live in"
CHARACTERIZATION_PATH_TOKEN_PATTERN = re.compile(
    r"tests[\\/]+characterization[\\/]+[A-Za-z0-9_-]+[\\/]?",
    re.IGNORECASE,
)
FMT_SUPPRESSION_PATTERN = re.compile(r"#\s*fmt:\s*(off|on)\b", re.IGNORECASE)
INLINE_CONTROL_FLOW_NODES: tuple[type[ast.AST], ...] = (
    ast.If,
    ast.For,
    ast.AsyncFor,
    ast.While,
    ast.With,
    ast.AsyncWith,
    ast.Try,
    ast.Match,
)
if hasattr(ast, "TryStar"):
    INLINE_CONTROL_FLOW_NODES = (*INLINE_CONTROL_FLOW_NODES, ast.TryStar)


def _extract_ci_job_block(ci_text: str, job_name: str) -> str | None:
    """Extract one top-level CI job block by name."""
    pattern = re.compile(
        rf"(?ms)^  {re.escape(job_name)}:\s*\n(.*?)(?=^  [A-Za-z0-9_-]+:\s*$|\Z)"
    )
    match = pattern.search(ci_text)
    if not match:
        return None
    return match.group(1)


def check_ci_contract_sync(
    contract: VerificationContract, ci_path: Path
) -> CheckResult:
    """Validate CI workflow content against the verification contract."""
    result = CheckResult()
    try:
        ci_text = ci_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        result.add_error(f"CI workflow not found: {ci_path}")
        return result

    if "pull_request:" not in ci_text:
        result.add_error("CI workflow must include a pull_request trigger.")

    required_job_blocks: dict[str, str] = {}
    for job_name in contract.required_ci_jobs:
        job_pattern = re.compile(rf"(?m)^  {re.escape(job_name)}:\s*$")
        if not job_pattern.search(ci_text):
            result.add_error(f"CI workflow is missing required job: {job_name}")
            continue
        block = _extract_ci_job_block(ci_text, job_name)
        if block is not None:
            required_job_blocks[job_name] = block

    for command in contract.verification_commands:
        if command not in ci_text:
            result.add_error(
                f"CI workflow is missing contract verification command: '{command}'"
            )

    for job_name, block in required_job_blocks.items():
        if EXPECTED_VENV_BOOTSTRAP not in block:
            result.add_error(
                "CI workflow job "
                f"'{job_name}' must bootstrap repo virtualenv with "
                f"'{EXPECTED_VENV_BOOTSTRAP}'."
            )

    governance_command = (
        "./.venv/bin/python project/scripts/verify_governance.py --check all"
    )
    if governance_command not in ci_text:
        result.add_error(
            "CI governance job must execute "
            "'./.venv/bin/python project/scripts/verify_governance.py --check all'."
        )
    governance_block = required_job_blocks.get("governance")
    if governance_block is not None:
        if EXPECTED_GOVERNANCE_INSTALL_PREFIX not in governance_block:
            result.add_error(
                "CI workflow job 'governance' must install dependencies in .venv "
                "before running governance checks."
            )
        if "pytest" not in governance_block:
            result.add_error(
                "CI workflow job 'governance' install step must include pytest "
                "availability."
            )

    return result


def _iter_python_files(root_dir: Path) -> Iterable[Path]:
    """Yield Python files from a directory in deterministic sorted order."""
    if not root_dir.exists():
        return ()
    return sorted(root_dir.rglob("*.py"))


def _line_count(path: Path) -> int:
    """Count text lines in a source file."""
    return len(path.read_text(encoding="utf-8").splitlines())


def _mode_to_violation(result: CheckResult, mode: str, message: str) -> None:
    """Route policy violations to either errors or warnings based on mode."""
    if mode == "block":
        result.add_error(message)
        return
    if mode == "warn":
        result.add_warning(message)
        return
    result.add_error(f"Unsupported LOC policy mode '{mode}' for message: {message}")


def _add_anti_evasion_violation(
    result: CheckResult,
    relative_path: str,
    category: str,
    detail: str,
) -> None:
    """Record one anti-evasion policy violation as a blocking LOC error."""
    result.add_error(f"{relative_path} [anti_evasion.{category}] {detail}")


def _add_fail_closed_violation(
    result: CheckResult,
    relative_path: str,
    detail: str,
    fail_closed: bool,
) -> None:
    """Record analysis failures as errors when fail-closed mode is enabled."""
    message = f"{relative_path} [anti_evasion.fail_closed] {detail}"
    if fail_closed:
        result.add_error(message)
        return
    result.add_warning(message)


def _count_semicolons(file_text: str) -> int:
    """Count semicolon tokens while ignoring comments and string literals."""
    count = 0
    reader = io.StringIO(file_text).readline
    for token in tokenize.generate_tokens(reader):
        if token.type == tokenize.OP and token.string == ";":
            count += 1
    return count


def _count_fmt_suppression_markers(file_text: str) -> int:
    """Count formatter suppression markers in comment tokens only."""
    count = 0
    reader = io.StringIO(file_text).readline
    for token in tokenize.generate_tokens(reader):
        if (
            token.type == tokenize.COMMENT
            and FMT_SUPPRESSION_PATTERN.search(token.string) is not None
        ):
            count += 1
    return count


def _iter_inline_suite_statements(node: ast.AST) -> Iterable[ast.stmt]:
    """Yield statements that belong to one control-flow suite."""
    for attribute in ("body", "orelse", "finalbody"):
        suite = getattr(node, attribute, None)
        if isinstance(suite, list):
            for statement in suite:
                if isinstance(statement, ast.stmt):
                    yield statement
    handlers = getattr(node, "handlers", None)
    if isinstance(handlers, list):
        for handler in handlers:
            body = getattr(handler, "body", None)
            if isinstance(body, list):
                for statement in body:
                    if isinstance(statement, ast.stmt):
                        yield statement
    cases = getattr(node, "cases", None)
    if isinstance(cases, list):
        for case in cases:
            body = getattr(case, "body", None)
            if isinstance(body, list):
                for statement in body:
                    if isinstance(statement, ast.stmt):
                        yield statement


def _count_inline_control_flow_suites(file_text: str) -> int:
    """Count statements packed into inline control-flow suites."""
    parsed = ast.parse(file_text)
    inline_suite_count = 0
    for node in ast.walk(parsed):
        if not isinstance(node, INLINE_CONTROL_FLOW_NODES):
            continue
        node_line = getattr(node, "lineno", None)
        if node_line is None:
            continue
        for statement in _iter_inline_suite_statements(node):
            if getattr(statement, "lineno", None) == node_line:
                inline_suite_count += 1
    return inline_suite_count


def _check_anti_evasion_policy(
    contract: VerificationContract,
    *,
    relative_path: str,
    file_text: str,
    result: CheckResult,
) -> None:
    """Apply anti-evasion LOC checks to one Python file."""
    loc_policy = contract.loc_policy

    if loc_policy.anti_evasion_disallow_fmt:
        try:
            fmt_markers = _count_fmt_suppression_markers(file_text)
        except tokenize.TokenError as exc:
            _add_fail_closed_violation(
                result,
                relative_path,
                (
                    "tokenization failed while evaluating formatter suppression "
                    f"markers: {exc}."
                ),
                loc_policy.anti_evasion_fail_closed,
            )
        else:
            if fmt_markers > 0:
                _add_anti_evasion_violation(
                    result,
                    relative_path,
                    "fmt_suppression",
                    (
                        f"found {fmt_markers} formatter suppression marker(s); "
                        "honest LOC cannot rely on # fmt: off/on."
                    ),
                )

    if loc_policy.anti_evasion_disallow_multi_statement:
        try:
            semicolon_count = _count_semicolons(file_text)
        except tokenize.TokenError as exc:
            _add_fail_closed_violation(
                result,
                relative_path,
                (
                    "tokenization failed while evaluating multi-statement packing: "
                    f"{exc}."
                ),
                loc_policy.anti_evasion_fail_closed,
            )
        else:
            if semicolon_count > loc_policy.anti_evasion_multi_statement_max_semicolons:
                _add_anti_evasion_violation(
                    result,
                    relative_path,
                    "multi_statement",
                    (
                        f"semicolon token count {semicolon_count} exceeds max "
                        f"{loc_policy.anti_evasion_multi_statement_max_semicolons}."
                    ),
                )

    if loc_policy.anti_evasion_disallow_dense_control_flow:
        try:
            inline_suite_count = _count_inline_control_flow_suites(file_text)
        except SyntaxError as exc:
            location = (
                f"line {exc.lineno}" if exc.lineno is not None else "unknown line"
            )
            _add_fail_closed_violation(
                result,
                relative_path,
                (
                    "AST parsing failed while evaluating dense inline control-flow "
                    f"suites ({location}: {exc.msg})."
                ),
                loc_policy.anti_evasion_fail_closed,
            )
        else:
            if (
                inline_suite_count
                > loc_policy.anti_evasion_control_flow_inline_suite_max
            ):
                _add_anti_evasion_violation(
                    result,
                    relative_path,
                    "dense_control_flow",
                    (
                        f"inline suite count {inline_suite_count} exceeds max "
                        f"{loc_policy.anti_evasion_control_flow_inline_suite_max}."
                    ),
                )


def check_loc_policy(
    contract: VerificationContract,
    repo_root: Path,
    src_dir: Path,
    tests_dir: Path,
) -> CheckResult:
    """Validate Python file line counts under `src/` and `tests/`."""
    result = CheckResult()

    if not src_dir.exists():
        result.add_error(f"Missing src directory: {src_dir}")
        return result
    if not tests_dir.exists():
        result.add_warning(f"Missing tests directory: {tests_dir}")

    for src_file in _iter_python_files(src_dir):
        relative_path = src_file.relative_to(repo_root).as_posix()
        try:
            file_text = src_file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            _add_fail_closed_violation(
                result,
                relative_path,
                f"unable to read UTF-8 text for LOC analysis: {exc}.",
                contract.loc_policy.anti_evasion_fail_closed,
            )
            continue
        lines = len(file_text.splitlines())
        if lines > contract.loc_policy.src_max_lines:
            _mode_to_violation(
                result,
                contract.loc_policy.src_mode,
                (
                    f"{relative_path} has {lines} lines "
                    f"(max {contract.loc_policy.src_max_lines})."
                ),
            )
        _check_anti_evasion_policy(
            contract,
            relative_path=relative_path,
            file_text=file_text,
            result=result,
        )

    for test_file in _iter_python_files(tests_dir):
        relative_path = test_file.relative_to(repo_root).as_posix()
        try:
            file_text = test_file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            _add_fail_closed_violation(
                result,
                relative_path,
                f"unable to read UTF-8 text for LOC analysis: {exc}.",
                contract.loc_policy.anti_evasion_fail_closed,
            )
            continue
        lines = len(file_text.splitlines())
        if lines > contract.loc_policy.tests_max_lines:
            _mode_to_violation(
                result,
                contract.loc_policy.tests_mode,
                (
                    f"{relative_path} has {lines} lines "
                    f"(max {contract.loc_policy.tests_max_lines})."
                ),
            )
        _check_anti_evasion_policy(
            contract,
            relative_path=relative_path,
            file_text=file_text,
            result=result,
        )

    return result


def _extract_python_versions_from_ci(ci_text: str) -> list[str]:
    """Extract all configured Python versions from a CI workflow."""
    return re.findall(r'python-version:\s*["\']?([0-9]+\.[0-9]+)["\']?', ci_text)


def _extract_python_versions_from_readme(readme_text: str) -> list[str]:
    """Extract Python version mentions from README prose."""
    return re.findall(r"Python\s+([0-9]+\.[0-9]+)\+?", readme_text)


def check_python_version_consistency(
    contract: VerificationContract,
    ci_path: Path,
    readme_path: Path,
) -> CheckResult:
    """Ensure Python versions are consistent across contract, CI, and docs."""
    result = CheckResult()

    try:
        ci_text = ci_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        result.add_error(f"CI workflow not found: {ci_path}")
        return result

    try:
        readme_text = readme_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        result.add_error(f"README not found: {readme_path}")
        return result

    ci_versions = _extract_python_versions_from_ci(ci_text)
    if not ci_versions:
        result.add_error("No python-version entries found in CI workflow.")
    else:
        for ci_version in sorted(set(ci_versions)):
            if ci_version != contract.python_version:
                result.add_error(
                    "CI python-version mismatch: "
                    f"expected {contract.python_version}, found {ci_version}."
                )

    readme_versions = _extract_python_versions_from_readme(readme_text)
    if not readme_versions:
        result.add_error("No Python version mention found in README.md.")
    else:
        for readme_version in sorted(set(readme_versions)):
            if readme_version != contract.python_version:
                result.add_error(
                    "README Python version mismatch: "
                    f"expected {contract.python_version}, found {readme_version}."
                )

    return result


def _add_docs_topology_error(result: CheckResult, detail: str) -> None:
    """Record one docs-topology error under the stable contract prefix."""
    result.add_error(f"{DOCS_TOPOLOGY_ERROR_PREFIX}: {detail}")


def _normalize_characterization_path(path_token: str) -> str:
    """Normalize one docs path token for robust, order-insensitive comparison."""
    normalized = path_token.strip()
    normalized = normalized.strip("`'\"()[]{}<>,.;:")
    normalized = normalized.replace("\\", "/")
    normalized = re.sub(r"/+", "/", normalized)
    normalized = normalized.rstrip("/") + "/"
    return normalized.lower()


def _extract_characterization_paths(block: str) -> set[str]:
    """Extract characterization suite path tokens from a bounded doc text block."""
    extracted_paths = {
        _normalize_characterization_path(match)
        for match in CHARACTERIZATION_PATH_TOKEN_PATTERN.findall(block)
    }
    return {
        path for path in extracted_paths if path != CANONICAL_CHARACTERIZATION_BASELINES
    }


def _extract_markdown_section(text: str, heading: str) -> str | None:
    """Extract one markdown section body until the next same-level heading."""
    lines = text.splitlines()
    start = None
    heading_pattern = re.compile(rf"^\s*{re.escape(heading)}\s*$")
    for index, line in enumerate(lines):
        if heading_pattern.match(line):
            start = index + 1
            break
    if start is None:
        return None

    section_lines: list[str] = []
    for line in lines[start:]:
        if re.match(r"^\s*###\s+", line):
            break
        section_lines.append(line)
    return "\n".join(section_lines)


def _extract_bounded_statement(text: str, anchor: str) -> str | None:
    """Extract one markdown bullet statement plus wrapped continuation lines."""
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if anchor not in line:
            continue
        statement_lines = [line]
        for follow_line in lines[index + 1 :]:
            if re.match(r"^\s*-\s+", follow_line) or re.match(
                r"^\s*##+\s+", follow_line
            ):
                break
            statement_lines.append(follow_line)
        return "\n".join(statement_lines)
    return None


def _validate_doc_suite_set(
    *,
    source_label: str,
    observed_paths: set[str],
    expected_paths: set[str],
    result: CheckResult,
) -> None:
    """Validate one observed doc suite set against the canonical expected set."""
    missing = sorted(expected_paths - observed_paths)
    unexpected = sorted(observed_paths - expected_paths)
    if not missing and not unexpected:
        return

    details: list[str] = []
    if missing:
        details.append(f"missing={missing}")
    if unexpected:
        details.append(f"unexpected={unexpected}")
    _add_docs_topology_error(
        result,
        f"{source_label} characterization suite topology mismatch ({'; '.join(details)}).",
    )


def check_docs_topology_contract(repo_root: Path) -> CheckResult:
    """Ensure blueprint/docs suite topology stays aligned with canonical paths."""
    result = CheckResult()
    expected_suites = {
        _normalize_characterization_path(path)
        for path in CANONICAL_CHARACTERIZATION_SUITES
    }

    v1_plan_path = repo_root / "project" / "v1-plan.md"
    technical_notes_path = repo_root / "docs" / "TECHNICAL_NOTES.md"
    try:
        v1_plan_text = v1_plan_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        _add_docs_topology_error(result, "project/v1-plan.md not found.")
        v1_plan_text = ""
    try:
        technical_notes_text = technical_notes_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        _add_docs_topology_error(result, "docs/TECHNICAL_NOTES.md not found.")
        technical_notes_text = ""

    if v1_plan_text:
        v1_plan_section = _extract_markdown_section(
            v1_plan_text, V1_PLAN_CHARACTERIZATION_SUITES_HEADING
        )
        if v1_plan_section is None:
            _add_docs_topology_error(
                result,
                "project/v1-plan.md missing '### Characterization suites' section.",
            )
        else:
            _validate_doc_suite_set(
                source_label="project/v1-plan.md",
                observed_paths=_extract_characterization_paths(v1_plan_section),
                expected_paths=expected_suites,
                result=result,
            )

    if technical_notes_text:
        technical_statement = _extract_bounded_statement(
            technical_notes_text, TECHNICAL_NOTES_SUITES_ANCHOR
        )
        if technical_statement is None:
            _add_docs_topology_error(
                result,
                "docs/TECHNICAL_NOTES.md missing characterization suites statement.",
            )
        else:
            _validate_doc_suite_set(
                source_label="docs/TECHNICAL_NOTES.md",
                observed_paths=_extract_characterization_paths(technical_statement),
                expected_paths=expected_suites,
                result=result,
            )

    required_dirs = [
        *CANONICAL_CHARACTERIZATION_SUITES,
        CANONICAL_CHARACTERIZATION_BASELINES,
    ]
    for relative_dir in required_dirs:
        dir_path = repo_root / relative_dir
        if dir_path.is_dir():
            continue
        _add_docs_topology_error(
            result,
            f"required directory missing: {relative_dir}",
        )

    return result


def _check_characterization_with_docs_topology(repo_root: Path) -> CheckResult:
    """Run characterization checks plus the docs-topology contract overlay."""
    result = check_characterization_artifacts(repo_root)
    result.merge(check_docs_topology_contract(repo_root))
    return result


def _print_check_result(check_name: str, result: CheckResult) -> None:
    """Print check output in a stable, CI-friendly format."""
    status = "PASS" if not result.errors else "FAIL"
    print(f"[{status}] {check_name}")
    surface_report = getattr(result, "surface_report", None)
    if surface_report is not None:
        print(
            f"  INFO: Remaining unmapped CLI items: {surface_report.unmapped_cli_items}"
        )
        print(
            "  INFO: Remaining unmapped config keys: "
            f"{surface_report.unmapped_config_keys}"
        )
        print(
            "  INFO: Remaining unmapped observability items: "
            f"{surface_report.unmapped_observability_items}"
        )
        print(
            "  INFO: Remaining parity/test linkage gaps: "
            f"{surface_report.parity_test_linkage_gaps}"
        )
    workflow_coverage_report = getattr(result, "workflow_coverage_report", None)
    if workflow_coverage_report is not None:
        print(
            "  INFO: Workflow sequence cells configured: "
            f"{workflow_coverage_report.configured_cells}"
        )
        print(
            "  INFO: Workflow sequence cells validated: "
            f"{workflow_coverage_report.validated_cells}"
        )
        print(
            "  INFO: Workflow sequence open debts: "
            f"{workflow_coverage_report.open_debts}"
        )
        if workflow_coverage_report.contract_errors == 0:
            print("  INFO: Workflow sequence contract OK")
        else:
            print("  INFO: Workflow sequence contract NOT OK")
        print(
            "  INFO: Workflow trace required rows: "
            f"{workflow_coverage_report.trace_required_rows}"
        )
        print(
            "  INFO: Workflow trace validated rows: "
            f"{workflow_coverage_report.trace_validated_rows}"
        )
        print(
            "  INFO: Workflow trace assertion failures: "
            f"{workflow_coverage_report.trace_assertion_failures}"
        )
        if workflow_coverage_report.trace_contract_errors == 0:
            print("  INFO: Workflow trace contract OK")
        else:
            print("  INFO: Workflow trace contract NOT OK")
        print(
            "  INFO: Workflow sequence evidence warnings: "
            f"{workflow_coverage_report.sequence_warnings}"
        )
        print(
            "  INFO: Workflow sequence count-only detections: "
            f"{workflow_coverage_report.count_only_warnings}"
        )
    collectability_report = getattr(result, "collectability_report", None)
    if collectability_report is not None:
        print(
            "  INFO: Characterization collectability owner nodeids checked: "
            f"{collectability_report.total_owner_nodeids}"
        )
        print(
            "  INFO: Characterization collectability owner nodeids resolved: "
            f"{collectability_report.resolved_owner_nodeids}"
        )
        print(
            "  INFO: Characterization collectability owner nodeids unresolved: "
            f"{collectability_report.unresolved_owner_nodeids}"
        )
        if collectability_report.unresolved_owner_nodeids == 0:
            print("  INFO: Characterization collectability/linkage OK")
        else:
            print("  INFO: Characterization collectability/linkage NOT OK")
    runtime_gate_report = getattr(result, "runtime_gate_report", None)
    if runtime_gate_report is not None:
        print(
            "  INFO: Characterization runtime gate targets configured: "
            f"{len(runtime_gate_report.configured_targets)}"
        )
        print(
            "  INFO: Characterization runtime gate targets checked: "
            f"{runtime_gate_report.checked_targets}"
        )
        print(
            "  INFO: Characterization runtime gate targets passed: "
            f"{runtime_gate_report.passed_targets}"
        )
        print(
            "  INFO: Characterization runtime gate targets failed: "
            f"{runtime_gate_report.failed_targets}"
        )
        print(
            "  INFO: Characterization runtime gate elapsed seconds: "
            f"{runtime_gate_report.elapsed_seconds:.3f}"
        )
        print(
            "  INFO: Characterization runtime gate budget seconds: "
            f"{runtime_gate_report.budget_seconds}"
        )
        print(
            "  INFO: Characterization runtime gate mapped parity ids: "
            f"{len(runtime_gate_report.mapped_parity_ids)}"
        )
        for info_line in runtime_gate_report.infos:
            print(f"  INFO: {info_line}")
        if runtime_gate_report.failed_targets == 0 and not any(
            warning.startswith("runtime_gate.") for warning in result.warnings
        ):
            print("  INFO: Characterization runtime gate OK (warn)")
        else:
            print("  INFO: Characterization runtime gate NOT OK (warn)")
    readiness_report = getattr(result, "readiness_report", None)
    if readiness_report is not None:
        print(f"  INFO: Route readiness claims: {readiness_report.claimed_rows}")
        print(
            "  INFO: Route readiness claims validated: "
            f"{readiness_report.validated_rows}"
        )
        if result.errors:
            print("  INFO: Route readiness proof NOT OK")
        else:
            print("  INFO: Route readiness proof OK")
    for warning in result.warnings:
        print(f"  WARN: {warning}")
    for error in result.errors:
        print(f"  ERROR: {error}")


def run_selected_checks(
    check_name: str,
    repo_root: Path,
    *,
    print_baseline: bool = False,
) -> int:
    """Run one or all governance checks and return a process exit code."""
    if print_baseline:
        if check_name != "architecture":
            print("[FAIL] architecture-baseline")
            print("  ERROR: --print-baseline requires '--check architecture'.")
            return 1
        print(render_architecture_baseline(repo_root), end="")
        return 0

    contract_path = repo_root / "project" / "verification-contract.yml"
    ci_path = repo_root / ".github" / "workflows" / "ci.yml"
    readme_path = repo_root / "README.md"
    src_dir = repo_root / "src"
    tests_dir = repo_root / "tests"

    try:
        contract = parse_verification_contract(contract_path)
    except GovernanceError as exc:
        print("[FAIL] schema")
        print(f"  ERROR: {exc}")
        return 1

    check_functions = {
        "schema": lambda: check_contract_schema(contract),
        "ci-sync": lambda: check_ci_contract_sync(contract, ci_path),
        "loc": lambda: check_loc_policy(contract, repo_root, src_dir, tests_dir),
        "python-version": lambda: check_python_version_consistency(
            contract,
            ci_path,
            readme_path,
        ),
        "architecture": lambda: check_architecture_artifacts(repo_root),
        "parity": lambda: check_parity_artifacts(repo_root),
        "characterization": lambda: _check_characterization_with_docs_topology(
            repo_root
        ),
        "readiness": lambda: check_readiness_artifacts(repo_root),
    }

    selected_checks = SUPPORTED_CHECKS if check_name == "all" else (check_name,)
    overall_result = CheckResult()

    for selected in selected_checks:
        result = check_functions[selected]()
        _print_check_result(selected, result)
        overall_result.merge(result)

    if overall_result.errors:
        print(
            f"Governance checks failed with {len(overall_result.errors)} error(s) "
            f"and {len(overall_result.warnings)} warning(s)."
        )
        return 1

    print(f"Governance checks passed with {len(overall_result.warnings)} warning(s).")
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser for governance checks."""
    parser = argparse.ArgumentParser(description="Run governance contract checks.")
    parser.add_argument(
        "--check",
        choices=["all", *SUPPORTED_CHECKS],
        default="all",
        help="Select one check or run all checks.",
    )
    parser.add_argument(
        "--print-baseline",
        action="store_true",
        help=(
            "Print generated architecture baseline JSON and exit. "
            "Requires --check architecture."
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for governance checking."""
    parser = build_parser()
    args = parser.parse_args(argv)
    repo_root = Path(__file__).resolve().parents[2]
    return run_selected_checks(
        args.check,
        repo_root,
        print_baseline=args.print_baseline,
    )
