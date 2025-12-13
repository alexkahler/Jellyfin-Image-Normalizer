import logging
from pathlib import Path
import sys
from typing import Any

from . import state
from .constants import APP_VERSION
from .state import RunStats


class _ColorFormatter(logging.Formatter):
    """Formatter that adds ANSI colors for CLI output."""

    COLORS = {
        logging.DEBUG: "\033[0m",  # grey
        logging.INFO: "\033[37m",  # white
        logging.WARNING: "\033[33m",  # yellow
        logging.ERROR: "\033[31m",  # red
        logging.CRITICAL: "\033[1;31m",  # bold red
    }
    RESET = "\033[0m"

    def __init__(self, use_color: bool, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.use_color = use_color

    def format(self, record: logging.LogRecord) -> str:
        message = super().format(record)
        if not self.use_color:
            return message
        color = self.COLORS.get(record.levelno)
        if not color:
            return message
        return f"{color}{message}{self.RESET}"


def _parse_log_level(name: str | None, default: str = "INFO") -> int:
    """Map a level name to a logging constant, defaulting when input is missing or unknown."""
    mapping = {
        "CRITICAL": logging.CRITICAL,
        "ERROR": logging.ERROR,
        "WARNING": logging.WARNING,
        "WARN": logging.WARNING,
        "INFO": logging.INFO,
        "DEBUG": logging.DEBUG,
    }
    if not name:
        return mapping.get(default.upper(), logging.INFO)
    return mapping.get(str(name).upper(), logging.INFO)


def setup_logging(cfg: dict[str, Any], args: Any) -> tuple[logging.LoggerAdapter, dict[str, Any]]:
    """Configure logging handlers/adapters based on config/CLI args and return the adapter plus effective settings."""
    logging_cfg = cfg.get("logging", {}) or {}

    silent = bool(getattr(args, "silent", False) or logging_cfg.get("silent", False))
    cli_level_name = "DEBUG" if getattr(args, "verbose", False) else logging_cfg.get("cli_level", "INFO")
    cli_level = _parse_log_level(cli_level_name)

    file_enabled = bool(logging_cfg.get("file_enabled", True))
    file_level_name = logging_cfg.get("file_level", "INFO")
    file_level = _parse_log_level(file_level_name)
    file_path_cfg = logging_cfg.get("file_path")
    file_path = Path(file_path_cfg).expanduser() if file_path_cfg else Path(__file__).with_name("jfin.log")

    logger = logging.getLogger("jfin")
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    logger.handlers.clear()

    formatter = logging.Formatter(
        fmt="%(asctime)s.%(msecs)03d [%(levelname)s] [run_id=%(run_id)s] %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    color_formatter = _ColorFormatter(
        use_color=True,
        fmt="%(asctime)s.%(msecs)03d [%(levelname)s] [run_id=%(run_id)s] %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )

    if not silent:
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(cli_level)
        ch.setFormatter(color_formatter)
        logger.addHandler(ch)
    else:
        err_handler = logging.StreamHandler(sys.stderr)
        err_handler.setLevel(logging.CRITICAL)
        err_handler.setFormatter(formatter)
        logger.addHandler(err_handler)

    adapter = logging.LoggerAdapter(logger, {"run_id": state.run_id})
    state.log = adapter

    if file_enabled:
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            fh = logging.FileHandler(file_path, mode="a", encoding="utf-8")
        except Exception as e:
            adapter.critical("Failed to open log file %s: %s", file_path, e)
        else:
            fh.setLevel(file_level)
            fh.setFormatter(formatter)
            logger.addHandler(fh)

    settings = {
        "silent": silent,
        "cli_level": cli_level_name,
        "file_level": file_level_name,
        "file_path": file_path,
    }
    return adapter, settings


def log_run_start(
    *,
    config_path: Path,
    cfg: dict[str, Any],
    operations: list[str],
    dry_run: bool,
    writes_enabled: bool,
    backup: bool,
    silent: bool,
    cli_level: str,
    file_level: str,
    log_file: Path,
) -> None:
    """Record run metadata (config, operations, flags) and flip shared dry_run flag before processing."""
    state.dry_run = dry_run
    version = cfg.get("version") or APP_VERSION
    state.log.info(
        "Run started. version=%s, config=%s, operations=%s, dry_run=%s, writes_enabled=%s, backup=%s, "
        "cli_level=%s, file_level=%s, silent=%s, log_file=%s",
        version,
        config_path,
        "|".join(operations),
        dry_run,
        writes_enabled,
        backup,
        cli_level,
        file_level,
        silent,
        log_file,
    )


def log_run_summary(stats: RunStats) -> None:
    """Log completion summary with counts of processed/skipped/warned items (and highlight dry-run mode)."""
    state.log.info("Run completed.")
    state.log.info(
        "Summary: items processed=%s, images found=%s, success=%s, skipped=%s, warnings=%s, errors=%s",
        stats.processed,
        stats.images_found,
        stats.successes,
        stats.skipped,
        stats.warnings,
        stats.errors,
    )
    if stats.failed_items:
        state.log.error("Failed items:")
        for path, reason in stats.failed_items:
            state.log.error(" - %s: %s", path, reason)
    if state.dry_run:
        state.log.info(
            "DRY RUN ENABLED: No changes were made and no images were uploaded, deleted, or saved to backups. All actions were simulated."
        )
