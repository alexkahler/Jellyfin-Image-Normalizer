"""Executable governance checks for CI, LOC policy, and version consistency."""

from __future__ import annotations

import argparse
import re
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

SUPPORTED_CHECKS = (
    "schema",
    "ci-sync",
    "loc",
    "python-version",
    "architecture",
    "parity",
    "characterization",
)
EXPECTED_VENV_BOOTSTRAP = "python -m venv .venv"


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
        lines = _line_count(src_file)
        if lines > contract.loc_policy.src_max_lines:
            relative_path = src_file.relative_to(repo_root).as_posix()
            _mode_to_violation(
                result,
                contract.loc_policy.src_mode,
                (
                    f"{relative_path} has {lines} lines "
                    f"(max {contract.loc_policy.src_max_lines})."
                ),
            )

    for test_file in _iter_python_files(tests_dir):
        lines = _line_count(test_file)
        if lines > contract.loc_policy.tests_max_lines:
            relative_path = test_file.relative_to(repo_root).as_posix()
            _mode_to_violation(
                result,
                contract.loc_policy.tests_mode,
                (
                    f"{relative_path} has {lines} lines "
                    f"(max {contract.loc_policy.tests_max_lines})."
                ),
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
        "characterization": lambda: check_characterization_artifacts(repo_root),
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
