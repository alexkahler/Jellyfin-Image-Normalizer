import io

import pytest
from PIL import Image

from jfin_core import state


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
