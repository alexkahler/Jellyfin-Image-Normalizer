"""Characterization artifact checks for WI-004, WI-003, and WI-005 governance enforcement."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from characterization_contract import (
    IMG_BEHAVIOR_IDS,
    IMAGING_BASELINE_PATH,
    IMAGING_EXPECTED_MAX_BYTES,
    IMAGING_EXPECTED_MAX_FILES,
    IMAGING_EXPECTED_ROOT,
    IMAGING_FIXTURE_MAX_BYTES,
    IMAGING_FIXTURE_MAX_FILES,
    IMAGING_FIXTURE_ROOT,
    IMAGING_GOLDEN_MANIFEST_PATH,
    REQUIRED_BASELINE_FILES,
    REQUIRED_CHARACTERIZATION_BEHAVIOR_IDS,
    CharacterizationError,
    load_baseline_payload,
    load_imaging_golden_manifest,
    owner_test_exists,
    parse_baseline_source,
    parse_owner_test_reference,
    validate_baseline_case_schema,
)
from governance_contract import CheckResult
from parity_contract import REQUIRED_PARITY_COLUMNS, load_markdown_table


def _load_and_validate_baselines(
    repo_root: Path,
    result: CheckResult,
) -> dict[str, dict[str, Any]]:
    """Load required baseline files and validate required case schema entries."""
    baseline_cases_by_path: dict[str, dict[str, Any]] = {}
    for relative_path, required_ids in REQUIRED_BASELINE_FILES.items():
        baseline_path = repo_root / relative_path
        try:
            payload = load_baseline_payload(baseline_path)
        except CharacterizationError as exc:
            result.add_error(str(exc))
            continue

        cases = payload["cases"]
        for behavior_id in required_ids:
            if behavior_id not in cases:
                result.add_error(
                    f"{relative_path} missing required behavior_id '{behavior_id}'."
                )
                continue
            try:
                validate_baseline_case_schema(
                    baseline_relpath=relative_path,
                    baseline_path=baseline_path,
                    behavior_id=behavior_id,
                    case_payload=cases[behavior_id],
                )
            except CharacterizationError as exc:
                result.add_error(str(exc))

        baseline_cases_by_path[relative_path] = cases
    return baseline_cases_by_path


def _load_and_validate_imaging_manifest(
    repo_root: Path,
    result: CheckResult,
) -> dict[str, Any]:
    """Load and validate the WI-003 imaging golden manifest payload."""
    manifest_path = repo_root / IMAGING_GOLDEN_MANIFEST_PATH
    try:
        return load_imaging_golden_manifest(manifest_path)
    except CharacterizationError as exc:
        result.add_error(str(exc))
        return {}


def _load_required_parity_rows(
    repo_root: Path, result: CheckResult
) -> dict[str, dict[str, str]]:
    """Load parity matrix rows and return only required WI-004 behavior rows."""
    parity_matrix_path = repo_root / "project" / "parity-matrix.md"
    try:
        table = load_markdown_table(
            parity_matrix_path,
            REQUIRED_PARITY_COLUMNS,
            "parity-matrix",
        )
    except Exception as exc:  # pragma: no cover - handled by parity check tests
        result.add_error(str(exc))
        return {}

    row_by_behavior = {row["behavior_id"]: row for row in table.rows}
    required_rows: dict[str, dict[str, str]] = {}
    for behavior_id in REQUIRED_CHARACTERIZATION_BEHAVIOR_IDS:
        row = row_by_behavior.get(behavior_id)
        if row is None:
            result.add_error(
                f"parity-matrix missing required characterization row '{behavior_id}'."
            )
            continue
        required_rows[behavior_id] = row
    return required_rows


def _check_parity_row_linkage(
    *,
    repo_root: Path,
    behavior_id: str,
    row: dict[str, str],
    baseline_cases_by_path: dict[str, dict[str, Any]],
    result: CheckResult,
) -> None:
    """Validate one parity row's linkage to baseline artifacts and owner tests."""
    baseline_source = row["baseline_source"].strip()
    owner_test = row["owner_test"].strip()

    if not baseline_source:
        result.add_error(f"{behavior_id}: baseline_source must be non-empty.")
        return
    if not owner_test:
        result.add_error(f"{behavior_id}: owner_test must be non-empty.")
        return

    if row.get("status") != "preserved":
        result.add_error(
            f"{behavior_id}: status must remain 'preserved' in characterization slices."
        )
    if row.get("current_result") != "matches-baseline":
        result.add_error(
            f"{behavior_id}: current_result must remain 'matches-baseline' in "
            "characterization slices."
        )

    try:
        baseline_path_part, baseline_anchor = parse_baseline_source(baseline_source)
    except CharacterizationError as exc:
        result.add_error(f"{behavior_id}: {exc}")
        return
    if baseline_anchor != behavior_id:
        result.add_error(
            f"{behavior_id}: baseline_source anchor must match behavior_id "
            f"(found '{baseline_anchor}')."
        )

    normalized_baseline_path = baseline_path_part.replace("\\", "/")
    if normalized_baseline_path not in REQUIRED_BASELINE_FILES:
        result.add_error(
            f"{behavior_id}: baseline_source path must reference one of "
            f"{sorted(REQUIRED_BASELINE_FILES)}, found '{baseline_path_part}'."
        )
    else:
        known_cases = baseline_cases_by_path.get(normalized_baseline_path, {})
        if baseline_anchor not in known_cases:
            result.add_error(
                f"{behavior_id}: baseline anchor '{baseline_anchor}' not found in "
                f"{normalized_baseline_path}."
            )

    try:
        owner_test_path_part, owner_test_function = parse_owner_test_reference(
            owner_test
        )
    except CharacterizationError as exc:
        result.add_error(f"{behavior_id}: {exc}")
        return

    normalized_owner_path = owner_test_path_part.replace("\\", "/")
    if not normalized_owner_path.startswith("tests/characterization/"):
        result.add_error(
            f"{behavior_id}: owner_test path must be under tests/characterization/, "
            f"found '{owner_test_path_part}'."
        )
        return

    owner_test_path = repo_root / normalized_owner_path
    if not owner_test_path.exists():
        result.add_error(
            f"{behavior_id}: owner_test file not found: {normalized_owner_path}"
        )
        return
    if not owner_test_exists(owner_test_path, owner_test_function):
        result.add_error(
            f"{behavior_id}: owner_test function '{owner_test_function}' not found in "
            f"{normalized_owner_path}."
        )


def _check_imaging_parity_row_linkage(
    *,
    repo_root: Path,
    behavior_id: str,
    row: dict[str, str],
    baseline_cases_by_path: dict[str, dict[str, Any]],
    imaging_manifest: dict[str, Any],
    result: CheckResult,
) -> None:
    """Validate IMG-* parity linkage to imaging baseline cases and golden artifacts."""
    baseline_source = row["baseline_source"].strip()
    try:
        baseline_path_part, _baseline_anchor = parse_baseline_source(baseline_source)
    except CharacterizationError as exc:
        result.add_error(f"{behavior_id}: {exc}")
        return
    normalized_baseline_path = baseline_path_part.replace("\\", "/")
    if normalized_baseline_path != IMAGING_BASELINE_PATH:
        result.add_error(
            f"{behavior_id}: baseline_source must reference {IMAGING_BASELINE_PATH}, "
            f"found '{baseline_path_part}'."
        )
        return

    imaging_cases = baseline_cases_by_path.get(IMAGING_BASELINE_PATH, {})
    case_payload = imaging_cases.get(behavior_id)
    if not isinstance(case_payload, dict):
        result.add_error(
            f"{behavior_id}: imaging baseline case not found in {IMAGING_BASELINE_PATH}."
        )
        return

    golden_key = case_payload.get("golden_key")
    if not isinstance(golden_key, str) or not golden_key.strip():
        result.add_error(
            f"{behavior_id}: imaging baseline golden_key must be non-empty."
        )
        return

    manifest_cases = imaging_manifest.get("cases")
    if not isinstance(manifest_cases, dict):
        result.add_error(
            f"{behavior_id}: golden manifest is missing a valid cases mapping."
        )
        return

    manifest_case = manifest_cases.get(golden_key)
    if not isinstance(manifest_case, dict):
        result.add_error(
            f"{behavior_id}: golden_key '{golden_key}' not found in "
            f"{IMAGING_GOLDEN_MANIFEST_PATH}."
        )
        return

    expected_path = manifest_case.get("expected_path")
    if not isinstance(expected_path, str) or not expected_path.strip():
        result.add_error(
            f"{behavior_id}: golden manifest case '{golden_key}' missing expected_path."
        )
        return
    normalized_expected = expected_path.replace("\\", "/")
    if not normalized_expected.startswith(IMAGING_EXPECTED_ROOT + "/"):
        result.add_error(
            f"{behavior_id}: expected_path must be under {IMAGING_EXPECTED_ROOT}/, "
            f"found '{expected_path}'."
        )
        return

    expected_file_path = repo_root / normalized_expected
    if not expected_file_path.exists():
        result.add_error(
            f"{behavior_id}: expected artifact not found at '{normalized_expected}'."
        )


def _check_artifact_budget(
    *,
    repo_root: Path,
    relative_root: str,
    max_files: int,
    max_bytes: int,
    label: str,
    result: CheckResult,
) -> None:
    """Check file-count and total-size budgets for golden artifact directories."""
    artifact_root = repo_root / relative_root
    if not artifact_root.exists():
        result.add_error(f"{label} directory not found: {relative_root}")
        return

    files = [path for path in artifact_root.rglob("*") if path.is_file()]
    if len(files) > max_files:
        result.add_error(
            f"{label} file count exceeds budget: {len(files)} > {max_files} "
            f"({relative_root})."
        )

    total_bytes = sum(path.stat().st_size for path in files)
    if total_bytes > max_bytes:
        result.add_error(
            f"{label} total bytes exceeds budget: {total_bytes} > {max_bytes} "
            f"({relative_root})."
        )


def check_characterization_artifacts(repo_root: Path) -> CheckResult:
    """Run WI-004/WI-003/WI-005 characterization linkage checks from repository root."""
    result = CheckResult()
    baseline_cases_by_path = _load_and_validate_baselines(repo_root, result)
    imaging_manifest = _load_and_validate_imaging_manifest(repo_root, result)
    parity_rows = _load_required_parity_rows(repo_root, result)

    for behavior_id, row in parity_rows.items():
        _check_parity_row_linkage(
            repo_root=repo_root,
            behavior_id=behavior_id,
            row=row,
            baseline_cases_by_path=baseline_cases_by_path,
            result=result,
        )
        if behavior_id in IMG_BEHAVIOR_IDS:
            _check_imaging_parity_row_linkage(
                repo_root=repo_root,
                behavior_id=behavior_id,
                row=row,
                baseline_cases_by_path=baseline_cases_by_path,
                imaging_manifest=imaging_manifest,
                result=result,
            )

    _check_artifact_budget(
        repo_root=repo_root,
        relative_root=IMAGING_EXPECTED_ROOT,
        max_files=IMAGING_EXPECTED_MAX_FILES,
        max_bytes=IMAGING_EXPECTED_MAX_BYTES,
        label="imaging expected artifact",
        result=result,
    )
    _check_artifact_budget(
        repo_root=repo_root,
        relative_root=IMAGING_FIXTURE_ROOT,
        max_files=IMAGING_FIXTURE_MAX_FILES,
        max_bytes=IMAGING_FIXTURE_MAX_BYTES,
        label="imaging fixture artifact",
        result=result,
    )

    return result
