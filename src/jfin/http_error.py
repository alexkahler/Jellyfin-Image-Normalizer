"""Provide shared HTTP error text formatting."""

from __future__ import annotations

import requests


def http_error(resp: requests.Response) -> str:
    """Build a compact HTTP error summary string from a response."""
    return f"HTTP {resp.status_code} {(resp.text or '')[:200].replace('\n', ' ')}"
