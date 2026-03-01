import io
import sys
from pathlib import Path

import pytest
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
# Ensure the src layout package is importable even when tests live behind reparse points.
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from jfin import state  # noqa: E402


@pytest.fixture(autouse=True)
def reset_state():
    """Reset global run state between tests to avoid cross-test leakage."""
    state.reset_state()
    yield
    state.reset_state()


@pytest.fixture
def rgb_image_bytes():
    """Factory fixture that builds simple RGB images and returns raw bytes."""

    def _factory(size=(120, 60), color=(255, 0, 0), fmt="PNG") -> bytes:
        img = Image.new("RGB", size, color)
        buf = io.BytesIO()
        img.save(buf, format=fmt)
        return buf.getvalue()

    return _factory
