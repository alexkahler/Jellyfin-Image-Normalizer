"""Path-scoped ruff format policy with optional warn-only handling."""

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class FormatPolicyOutcome:
    """Capture one path-scoped formatter check/apply execution."""

    target: str
    mode: str
    had_drift: bool
    check_returncode: int
    format_returncode: int | None
    check_stdout: str
    check_stderr: str
    format_stdout: str
    format_stderr: str
    command_error: str | None = None


def run_format_policy(
    repo_root: Path,
    *,
    target: str,
    mode: str,
) -> FormatPolicyOutcome:
    """Run `ruff format --check` then `ruff format` when drift is detected."""
    check_command = [sys.executable, "-m", "ruff", "format", "--check", target]
    check_proc = subprocess.run(
        check_command,
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    if check_proc.returncode == 0:
        return FormatPolicyOutcome(
            target=target,
            mode=mode,
            had_drift=False,
            check_returncode=0,
            format_returncode=None,
            check_stdout=check_proc.stdout,
            check_stderr=check_proc.stderr,
            format_stdout="",
            format_stderr="",
        )
    if check_proc.returncode != 1:
        return FormatPolicyOutcome(
            target=target,
            mode=mode,
            had_drift=False,
            check_returncode=check_proc.returncode,
            format_returncode=None,
            check_stdout=check_proc.stdout,
            check_stderr=check_proc.stderr,
            format_stdout="",
            format_stderr="",
            command_error=(
                f"ruff format --check failed unexpectedly for '{target}' with "
                f"exit code {check_proc.returncode}."
            ),
        )

    format_command = [sys.executable, "-m", "ruff", "format", target]
    format_proc = subprocess.run(
        format_command,
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    if format_proc.returncode != 0:
        return FormatPolicyOutcome(
            target=target,
            mode=mode,
            had_drift=True,
            check_returncode=1,
            format_returncode=format_proc.returncode,
            check_stdout=check_proc.stdout,
            check_stderr=check_proc.stderr,
            format_stdout=format_proc.stdout,
            format_stderr=format_proc.stderr,
            command_error=(
                f"ruff format failed for '{target}' with exit code "
                f"{format_proc.returncode}."
            ),
        )

    return FormatPolicyOutcome(
        target=target,
        mode=mode,
        had_drift=True,
        check_returncode=1,
        format_returncode=0,
        check_stdout=check_proc.stdout,
        check_stderr=check_proc.stderr,
        format_stdout=format_proc.stdout,
        format_stderr=format_proc.stderr,
    )


def build_parser() -> argparse.ArgumentParser:
    """Build CLI argument parser for path-scoped formatter policy."""
    parser = argparse.ArgumentParser(
        description="Run ruff format policy for one target path."
    )
    parser.add_argument("--target", required=True, help="Path to check/format.")
    parser.add_argument(
        "--mode",
        required=True,
        choices=["block", "warn"],
        help="Severity when formatting drift is detected.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for path-scoped formatter policy."""
    args = build_parser().parse_args(argv)
    repo_root = Path(__file__).resolve().parents[2]
    outcome = run_format_policy(repo_root, target=args.target, mode=args.mode)

    if outcome.command_error is not None:
        print(f"[FAIL] format:{args.target}")
        print(f"  ERROR: {outcome.command_error}")
        if outcome.check_stderr.strip():
            print(f"  STDERR: {outcome.check_stderr.strip()}")
        if outcome.format_stderr.strip():
            print(f"  STDERR: {outcome.format_stderr.strip()}")
        return 1

    if not outcome.had_drift:
        print(f"[PASS] format:{args.target}")
        return 0

    print(f"[FIXED] format:{args.target}")
    if args.mode == "warn":
        print(
            "  WARN: Formatting drift detected and auto-formatted for "
            f"'{args.target}' (warn mode)."
        )
        return 0
    print(
        "  ERROR: Formatting drift detected and auto-formatted for "
        f"'{args.target}' (block mode)."
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
