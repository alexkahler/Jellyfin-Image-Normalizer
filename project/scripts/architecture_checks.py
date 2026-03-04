"""Architecture guard checks for non-entry exits and boundary imports."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Iterable

from architecture_contract import (
    BASELINE_RELATIVE_PATH,
    BASELINE_VERSION,
    DEFAULT_ENTRY_EXIT_MODULES,
    EXIT_COUNTER_KEYS,
    V1_ROOT,
    ArchitectureBaseline,
    ArchitectureContractError,
    ExitCounters,
    load_architecture_baseline,
    serialize_architecture_baseline,
)
from governance_contract import CheckResult

DOMAIN_FORBIDDEN_PACKAGE_PREFIXES = ("jfin.adapters", "jfin.app", "jfin.bootstrap")
DOMAIN_FORBIDDEN_MODULE_PREFIXES = (
    "requests",
    "PIL",
    "shutil",
    "tempfile",
    "glob",
    "subprocess",
    "socket",
    "urllib",
    "http.client",
)
APP_SERVICES_FORBIDDEN_PACKAGE_PREFIX = "jfin.adapters"


def _iter_python_files(root_dir: Path) -> Iterable[Path]:
    """Yield Python files in deterministic order from a root directory."""
    if not root_dir.exists():
        return ()
    return sorted(root_dir.rglob("*.py"))


def _path_as_repo_rel(path: Path, repo_root: Path) -> str:
    """Return a path relative to the repo root using forward slashes."""
    return path.relative_to(repo_root).as_posix()


def _matches_module_prefix(module_name: str, prefix: str) -> bool:
    """Return True when `module_name` matches `prefix` exactly or by dotted prefix."""
    return module_name == prefix or module_name.startswith(f"{prefix}.")


def _current_package_parts(repo_rel_path: str) -> list[str]:
    """Resolve current module package parts for relative import resolution."""
    parts = repo_rel_path.split("/")
    if not parts or parts[0] != "src":
        return []

    module_parts = parts[1:]
    if not module_parts or not module_parts[-1].endswith(".py"):
        return []

    module_parts[-1] = module_parts[-1][:-3]
    if module_parts[-1] == "__init__":
        return module_parts
    return module_parts[:-1]


def _resolve_importfrom_module(
    repo_rel_path: str, import_node: ast.ImportFrom
) -> str | None:
    """Resolve an import-from node to an absolute module path when possible."""
    if import_node.level == 0:
        return import_node.module

    package_parts = _current_package_parts(repo_rel_path)
    up_levels = import_node.level - 1
    if up_levels > len(package_parts):
        return None

    base_parts = package_parts[: len(package_parts) - up_levels]
    module_parts = import_node.module.split(".") if import_node.module else []
    resolved = base_parts + module_parts
    return ".".join(resolved) if resolved else None


def _iter_import_targets(repo_rel_path: str, tree: ast.AST) -> Iterable[str]:
    """Yield import targets normalized for boundary rule matching."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name:
                    yield alias.name
            continue

        if not isinstance(node, ast.ImportFrom):
            continue

        module_name = _resolve_importfrom_module(repo_rel_path, node)
        if not module_name:
            continue

        for alias in node.names:
            if alias.name == "*":
                yield module_name
            else:
                yield f"{module_name}.{alias.name}"


def _count_exit_patterns_from_tree(tree: ast.AST) -> ExitCounters:
    """Count tracked exit invocation patterns from one parsed AST tree."""
    sys_exit_aliases: set[str] = set()
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.ImportFrom)
            and node.level == 0
            and node.module == "sys"
        ):
            for alias in node.names:
                if alias.name == "exit":
                    sys_exit_aliases.add(alias.asname or alias.name)

    sys_exit_calls = 0
    system_exit_raises = 0
    sys_import_exit_calls = 0
    builtins_exit_calls = 0

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
                if func.value.id == "sys" and func.attr == "exit":
                    sys_exit_calls += 1
                elif func.value.id == "builtins" and func.attr in {"exit", "quit"}:
                    builtins_exit_calls += 1
            elif isinstance(func, ast.Name) and func.id in sys_exit_aliases:
                sys_import_exit_calls += 1

        if isinstance(node, ast.Raise) and node.exc is not None:
            if isinstance(node.exc, ast.Name) and node.exc.id == "SystemExit":
                system_exit_raises += 1
            elif (
                isinstance(node.exc, ast.Call)
                and isinstance(node.exc.func, ast.Name)
                and node.exc.func.id == "SystemExit"
            ):
                system_exit_raises += 1

    return ExitCounters(
        sys_exit_calls=sys_exit_calls,
        system_exit_raises=system_exit_raises,
        sys_import_exit_calls=sys_import_exit_calls,
        builtins_exit_calls=builtins_exit_calls,
    )


def count_exit_patterns_in_file(path: Path) -> ExitCounters:
    """Parse one Python file and count tracked exit patterns."""
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    return _count_exit_patterns_from_tree(tree)


def _format_counters(counters: ExitCounters) -> str:
    """Format one counter set for human-readable diagnostics."""
    return (
        f"sys_exit_calls={counters.sys_exit_calls}, "
        f"system_exit_raises={counters.system_exit_raises}, "
        f"sys_import_exit_calls={counters.sys_import_exit_calls}, "
        f"builtins_exit_calls={counters.builtins_exit_calls}"
    )


def generate_architecture_baseline(repo_root: Path) -> ArchitectureBaseline:
    """Generate a baseline payload from current source-tree exit counters."""
    src_root = repo_root / V1_ROOT
    allowlist: dict[str, ExitCounters] = {}

    for py_file in _iter_python_files(src_root):
        repo_rel = _path_as_repo_rel(py_file, repo_root)
        if repo_rel in DEFAULT_ENTRY_EXIT_MODULES:
            continue

        counters = count_exit_patterns_in_file(py_file)
        if counters.total > 0:
            allowlist[repo_rel] = counters

    return ArchitectureBaseline(
        version=BASELINE_VERSION,
        v1_root=V1_ROOT,
        entry_exit_modules=tuple(DEFAULT_ENTRY_EXIT_MODULES),
        non_entry_exit_allowlist=dict(sorted(allowlist.items())),
    )


def render_architecture_baseline(repo_root: Path) -> str:
    """Render a generated architecture baseline JSON string."""
    baseline = generate_architecture_baseline(repo_root)
    return serialize_architecture_baseline(baseline)


def check_non_entry_exit_ratchet(repo_root: Path) -> CheckResult:
    """Enforce ratcheted non-entry exit usage against baseline allowlist."""
    result = CheckResult()
    baseline_path = repo_root / BASELINE_RELATIVE_PATH
    try:
        baseline = load_architecture_baseline(baseline_path)
    except ArchitectureContractError as exc:
        result.add_error(str(exc))
        return result

    src_root = repo_root / baseline.v1_root
    if not src_root.exists():
        result.add_error(f"v1_root directory not found: {src_root}")
        return result

    observed_by_file: dict[str, ExitCounters] = {}
    for py_file in _iter_python_files(src_root):
        repo_rel = _path_as_repo_rel(py_file, repo_root)
        if repo_rel in baseline.entry_exit_modules:
            continue

        try:
            counters = count_exit_patterns_in_file(py_file)
        except SyntaxError as exc:
            result.add_error(f"failed to parse {repo_rel}: {exc.msg}")
            continue

        if counters.total > 0:
            observed_by_file[repo_rel] = counters

    allowlist = baseline.non_entry_exit_allowlist
    for path, observed in observed_by_file.items():
        allowed = allowlist.get(path)
        if allowed is None:
            result.add_error(
                "architecture: new non-entry exit violation in "
                f"{path}: {_format_counters(observed)}."
            )
            continue

        for key in EXIT_COUNTER_KEYS:
            observed_count = getattr(observed, key)
            allowed_count = getattr(allowed, key)
            if observed_count > allowed_count:
                result.add_error(
                    "architecture: exit counter exceeds baseline for "
                    f"{path}.{key}: observed {observed_count}, baseline {allowed_count}."
                )
            elif observed_count < allowed_count:
                result.add_warning(
                    "architecture: exit counter dropped below baseline for "
                    f"{path}.{key}: observed {observed_count}, baseline {allowed_count}. "
                    "Update project/architecture-baseline.json to ratchet downward."
                )

    for path, allowed in allowlist.items():
        if path in observed_by_file:
            continue
        if allowed.total > 0:
            result.add_warning(
                "architecture: exit counters dropped to zero for "
                f"{path}; update project/architecture-baseline.json to ratchet downward."
            )

    return result


def _check_domain_import_boundaries(repo_root: Path) -> CheckResult:
    """Validate domain module imports against forbidden package/module prefixes."""
    result = CheckResult()
    domain_root = repo_root / V1_ROOT / "domain"
    if not domain_root.exists():
        return result

    for py_file in _iter_python_files(domain_root):
        repo_rel = _path_as_repo_rel(py_file, repo_root)
        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=repo_rel)
        except SyntaxError as exc:
            result.add_error(f"domain boundary parse failure in {repo_rel}: {exc.msg}")
            continue

        for import_target in _iter_import_targets(repo_rel, tree):
            blocked = any(
                _matches_module_prefix(import_target, prefix)
                for prefix in DOMAIN_FORBIDDEN_PACKAGE_PREFIXES
            ) or any(
                _matches_module_prefix(import_target, prefix)
                for prefix in DOMAIN_FORBIDDEN_MODULE_PREFIXES
            )
            if blocked:
                result.add_error(
                    f"architecture: domain import boundary violation in {repo_rel}: "
                    f"'{import_target}' is forbidden."
                )

    return result


def _check_app_services_boundaries(repo_root: Path) -> CheckResult:
    """Validate app/services imports against adapter import prohibitions."""
    result = CheckResult()
    app_services_root = repo_root / V1_ROOT / "app" / "services"
    if not app_services_root.exists():
        return result

    for py_file in _iter_python_files(app_services_root):
        repo_rel = _path_as_repo_rel(py_file, repo_root)
        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=repo_rel)
        except SyntaxError as exc:
            result.add_error(
                f"app/services boundary parse failure in {repo_rel}: {exc.msg}"
            )
            continue

        for import_target in _iter_import_targets(repo_rel, tree):
            if _matches_module_prefix(
                import_target,
                APP_SERVICES_FORBIDDEN_PACKAGE_PREFIX,
            ):
                result.add_error(
                    "architecture: app/services import boundary violation in "
                    f"{repo_rel}: '{import_target}' imports adapters."
                )

    return result


def check_import_boundaries(repo_root: Path) -> CheckResult:
    """Run conditional domain and app/services import-boundary checks."""
    result = CheckResult()
    result.merge(_check_domain_import_boundaries(repo_root))
    result.merge(_check_app_services_boundaries(repo_root))
    return result


def check_architecture_artifacts(repo_root: Path) -> CheckResult:
    """Run all WI-001 architecture checks from repository root."""
    result = CheckResult()
    result.merge(check_non_entry_exit_ratchet(repo_root))
    result.merge(check_import_boundaries(repo_root))
    return result
