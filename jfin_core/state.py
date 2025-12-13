from dataclasses import dataclass, field
import logging
from secrets import token_hex
from typing import Any


@dataclass
class RunStats:
    """
    In-memory counters for a single JFIN run.

    Semantics:
    - processed: count of unique items/entities processed (e.g., a movie/series id).
    - images_found: count of images discovered/considered.
    - successes/skipped/warnings/errors: per-image outcomes.
    """

    processed: int = 0
    images_found: int = 0
    successes: int = 0
    skipped: int = 0
    warnings: int = 0
    errors: int = 0
    failed_items: list[tuple[str, str]] = field(default_factory=list)
    _processed_item_ids: set[str] = field(default_factory=set, repr=False)

    def record_item_processed(self, item_id: str) -> None:
        """Count a processed item exactly once per run."""
        if not item_id:
            return
        if item_id in self._processed_item_ids:
            return
        self._processed_item_ids.add(item_id)
        self.processed += 1

    def record_success(self) -> None:
        """Count a successful processed image."""
        self.successes += 1

    def record_warning(self, count_processed: bool = False) -> None:
        """Count a warning (per-image). `count_processed` is kept for compatibility."""
        self.warnings += 1

    def record_skip(self, count_processed: bool = False) -> None:
        """Count a skip separately from warnings (per-image). `count_processed` is kept for compatibility."""
        self.skipped += 1

    def record_images_found(self, count: int) -> None:
        """Track how many images were discovered for this run."""
        if count < 0:
            return
        self.images_found += count

    def record_error(self, path: str, reason: str) -> None:
        """Count an error (per-image) and capture the failing identifier and reason."""
        self.errors += 1
        self.failed_items.append((path, reason))


run_id = token_hex(4)
stats = RunStats()
api_failures: list[dict[str, Any]] = []
upscaled_images: list[tuple[str, int, int, int, int]] = []
downscaled_images: list[tuple[str, int, int, int, int]] = []
dry_run = False

# Default logger; configured at runtime by logging_utils.setup_logging
log: logging.LoggerAdapter = logging.LoggerAdapter(logging.getLogger("jfin"), {"run_id": run_id})


def latest_api_error(prev_len: int) -> str | None:
    """Return the most recent API error string if a new failure was recorded."""
    if len(api_failures) > prev_len:
        return api_failures[-1].get("error") or None
    return None


def reset_state() -> None:
    """
    Reset counters and in-memory tracking. Useful in tests to isolate runs.
    """
    global stats
    stats = RunStats()
    api_failures.clear()
    upscaled_images.clear()
    downscaled_images.clear()
    globals()["dry_run"] = False
