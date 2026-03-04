import logging
from types import SimpleNamespace

from jfin import state
from jfin.logging_utils import log_run_summary, setup_logging
from jfin.state import RunStats


class _CaptureLogger:
    def __init__(self) -> None:
        self.info_messages: list[str] = []
        self.error_messages: list[str] = []

    def info(self, message: str, *args) -> None:
        rendered = message % args if args else message
        self.info_messages.append(rendered)

    def error(self, message: str, *args) -> None:
        rendered = message % args if args else message
        self.error_messages.append(rendered)


def test_log_run_summary_reports_counters_and_failures(monkeypatch):
    capture = _CaptureLogger()
    monkeypatch.setattr(state, "log", capture, raising=False)
    state.dry_run = True

    stats = RunStats(
        processed=3,
        images_found=5,
        successes=2,
        skipped=1,
        warnings=1,
        errors=1,
        failed_items=[("item-7", "upload failed")],
    )
    log_run_summary(stats)

    assert any("Run completed." in line for line in capture.info_messages)
    assert any(
        "Summary: items processed=3, images found=5, success=2, skipped=1, warnings=1, errors=1"
        in line
        for line in capture.info_messages
    )
    assert any("Failed items:" in line for line in capture.error_messages)
    assert any("item-7: upload failed" in line for line in capture.error_messages)
    assert any("DRY RUN ENABLED" in line for line in capture.info_messages)


def test_setup_logging_respects_silent_and_verbose_flags():
    cfg = {
        "logging": {
            "file_enabled": False,
            "cli_level": "INFO",
            "file_level": "INFO",
            "silent": False,
        }
    }

    verbose_args = SimpleNamespace(silent=False, verbose=True)
    adapter_verbose, settings_verbose = setup_logging(cfg, verbose_args)
    assert settings_verbose["cli_level"] == "DEBUG"
    assert settings_verbose["silent"] is False
    assert adapter_verbose.logger.handlers

    silent_args = SimpleNamespace(silent=True, verbose=False)
    adapter_silent, settings_silent = setup_logging(cfg, silent_args)
    assert settings_silent["silent"] is True
    assert settings_silent["cli_level"] == "INFO"
    assert adapter_silent.logger.handlers
    assert adapter_silent.logger.handlers[0].level == logging.CRITICAL
