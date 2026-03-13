"""Provide client helpers."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import requests

from . import client_http, state
from .client_ops_mixin import JellyfinClientOpsMixin


@dataclass
class JellyfinClient(JellyfinClientOpsMixin):
    """Represent JellyfinClient behavior and state."""

    base_url: str
    api_key: str
    client_name: str = "Jellyfin Image Normalizer"
    client_version: str = "unknown"
    timeout: float = 15.0
    verify_tls: bool = True
    delay: float = 0.1
    retry_count: int = 3
    backoff_base: float = 0.5
    fail_fast: bool = False
    dry_run: bool = True
    logger: Any = field(default_factory=lambda: state.log)

    def __post_init__(self) -> None:
        """Finalize dataclass initialization."""
        self.base_url = self.base_url.rstrip("/")

    def _headers(self) -> dict[str, str]:
        """Run  headers."""
        auth_value = f'MediaBrowser Token="{self.api_key}", Client="{self.client_name}", Version="{self.client_version}"'
        return {"Authorization": auth_value}

    def _get(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        stream: bool = False,
        label: str = "request",
    ) -> requests.Response | None:
        """Run  get."""
        return client_http.get_response(
            self,
            request_fn=requests.get,
            url=url,
            params=params,
            stream=stream,
            label=label,
            sleep_fn=time.sleep,
        )

    def _get_json(
        self, url: str, *, params: dict[str, Any] | None = None, label: str
    ) -> Any | None:
        """Run  get json."""
        resp = self._get(url, params=params, stream=False, label=label)
        if resp is None:
            return None
        try:
            return resp.json()
        except Exception as exc:
            self.logger.error(
                "[API-ERROR] Failed to decode JSON from %s: %s (%s)",
                url,
                exc,
                (resp.text or "")[:200].replace("\n", " "),
            )
            return None

    def _head(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        stream: bool = False,
        label: str = "request",
        allow_retry: bool = True,
    ) -> requests.Response | None:
        """Run  head."""
        return client_http.head_response(
            self,
            request_fn=requests.head,
            url=url,
            params=params,
            stream=stream,
            label=label,
            sleep_fn=time.sleep,
            allow_retry=allow_retry,
        )

    def _writes_allowed(self, action: str) -> bool:
        """Run  writes allowed."""
        _ = action
        return not self.dry_run

    def _guess_content_type(self, image_path: Path) -> str | None:
        """Run  guess content type."""
        suffix = image_path.suffix.lower()
        if suffix == ".png":
            return "image/png"
        if suffix in (".jpg", ".jpeg"):
            return "image/jpeg"
        return "application/octet-stream"

    def test_connection(self) -> bool:
        """Run test connection."""
        return client_http.test_connection(
            self, request_fn=requests.get, sleep_fn=time.sleep
        )

    def list_users(self, is_disabled: bool | None = None) -> list[dict[str, Any]]:
        """Run list users."""
        params: dict[str, str] | None = None
        if is_disabled is not None:
            params = {"isDisabled": str(is_disabled).lower()}
        data = self._get_json(
            f"{self.base_url}/Users", params=params, label="list users"
        )
        if data is None:
            return []
        if not isinstance(data, list):
            self.logger.error("[API-ERROR] /Users response is not a list")
            return []
        return data

    def list_media_folders(self) -> dict[str, Any] | None:
        """Run list media folders."""
        data = self._get_json(
            f"{self.base_url}/Library/MediaFolders", label="list media folders"
        )
        if data is None:
            return None
        if not isinstance(data, dict):
            self.logger.error(
                "[API-ERROR] /Library/MediaFolders response is not an object"
            )
            return None
        return data

    def _post_image(
        self,
        *,
        url: str,
        headers: dict[str, str],
        data: bytes,
        encode_base64: bool,
        success_message: str,
        error_label: str,
        action_label: str,
        failures: list[dict[str, Any]] | None,
        failure_entry: dict[str, Any],
        fail_fast_prefix: str,
    ) -> bool:
        """Run  post image."""
        return client_http.post_image(
            self,
            request_fn=requests.post,
            sleep_fn=time.sleep,
            url=url,
            headers=headers,
            data=data,
            encode_base64=encode_base64,
            success_message=success_message,
            error_label=error_label,
            action_label=action_label,
            failures=failures,
            failure_entry=failure_entry,
            fail_fast_prefix=fail_fast_prefix,
        )

    def delete_image(self, uuid: str, image_type: str, image_index: int | None) -> bool:
        """Run delete image."""
        return client_http.delete_image(
            self,
            request_fn=requests.delete,
            sleep_fn=time.sleep,
            uuid=uuid,
            image_type=image_type,
            image_index=image_index,
        )
