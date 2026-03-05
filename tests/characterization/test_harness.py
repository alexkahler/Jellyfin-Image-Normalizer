"""Unit tests for shared characterization harness helpers."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.characterization._harness import (
    assert_effective_config_subset,
    assert_expected_messages,
    assert_expected_preflight,
    assert_expected_stats_subset,
    build_minimal_runtime_config_text,
    load_baseline_cases,
    merge_observed_messages,
)


def test_harness_load_baseline_cases_reads_cases(tmp_path: Path) -> None:
    """Harness should load `cases` from versioned baseline JSON payloads."""
    baseline_path = tmp_path / "baseline.json"
    baseline_path.write_text(
        json.dumps(
            {
                "version": 1,
                "cases": {"CASE-001": {"expected_exit_code": 0}},
            }
        ),
        encoding="utf-8",
    )

    cases = load_baseline_cases(baseline_path)
    assert "CASE-001" in cases


def test_harness_expected_stats_asserts_subset() -> None:
    """Harness stat assertion should only enforce keys provided in baseline."""
    assert_expected_stats_subset(
        {"warnings": 1},
        {"errors": 0, "warnings": 1, "successes": 0},
    )


def test_harness_expected_preflight_checks_call_counts() -> None:
    """Harness preflight assertion should enforce not_reached and mocked variants."""
    assert_expected_preflight("not_reached", observed_calls=0)
    assert_expected_preflight("mocked_ok", observed_calls=1)
    assert_expected_preflight("mocked_fail", observed_calls=1)


def test_harness_expected_messages_match_substrings() -> None:
    """Harness message assertion should verify stable token substrings."""
    assert_expected_messages(
        ["token-a", "token-b"],
        ["prefix token-a suffix", "other token-b entry"],
    )


def test_harness_expected_effective_config_asserts_subset_keys() -> None:
    """Harness effective-config assertion should support subset matching."""
    assert_effective_config_subset(
        {"logo_width": 800},
        {"logo_width": 800, "logo_height": 310},
    )


def test_harness_build_minimal_runtime_config_text_contains_core_keys() -> None:
    """Harness should emit TOML text with required connection and mode keys."""
    rendered = build_minimal_runtime_config_text()
    assert 'jf_url = "https://demo.example.com"' in rendered
    assert "[logo]" in rendered
    assert "[thumb]" in rendered
    assert "[backdrop]" in rendered
    assert "[profile]" in rendered


def test_harness_expected_messages_fails_for_missing_token() -> None:
    """Harness should raise on missing message tokens for baseline checks."""
    with pytest.raises(AssertionError):
        assert_expected_messages(["required-token"], ["irrelevant output"])


def test_harness_merge_observed_messages_strips_ansi_and_deduplicates() -> None:
    """Message merge should normalize ANSI wrappers without rewriting semantics."""
    merged = merge_observed_messages(
        ["\x1b[1;31mcritical message\x1b[0m", "critical message"],
        ["secondary message"],
    )
    assert merged == ["critical message", "secondary message"]


def test_harness_expected_messages_negative_control_precision() -> None:
    """Near-match text should fail to avoid permissive token regressions."""
    with pytest.raises(AssertionError):
        assert_expected_messages(
            ["DRY RUN - Would upload normalized image"],
            ["DRY RUN - Would upload image"],
        )
