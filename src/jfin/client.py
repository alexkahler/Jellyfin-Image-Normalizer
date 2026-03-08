from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import requests

from . import client_http, client_image_ops, state


@dataclass
class JellyfinClient:
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
        self.base_url = self.base_url.rstrip("/")

    def _headers(self) -> dict[str, str]:
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
        _ = action
        return not self.dry_run

    def _guess_content_type(self, image_path: Path) -> str | None:
        suffix = image_path.suffix.lower()
        if suffix == ".png":
            return "image/png"
        if suffix in (".jpg", ".jpeg"):
            return "image/jpeg"
        return "application/octet-stream"

    def test_connection(self) -> bool:
        return client_http.test_connection(
            self, request_fn=requests.get, sleep_fn=time.sleep
        )

    def list_users(self, is_disabled: bool | None = None) -> list[dict[str, Any]]:
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

    def query_items(
        self,
        *,
        parent_id: str | None,
        include_item_types: list[str],
        enable_image_types: str | list[str],
        recursive: bool,
        start_index: int | None = None,
        limit: int | None = None,
    ) -> dict[str, Any] | None:
        return client_image_ops.query_items(
            self,
            parent_id=parent_id,
            include_item_types=include_item_types,
            enable_image_types=enable_image_types,
            recursive=recursive,
            start_index=start_index,
            limit=limit,
        )

    def get_item(self, item_id: str) -> dict[str, Any] | None:
        return client_image_ops.get_item(self, item_id=item_id)

    def get_item_image(
        self, item_id: str, image_type: str, index: int | None = None
    ) -> tuple[bytes, str] | None:
        return client_image_ops.get_item_image(
            self,
            item_id=item_id,
            image_type=image_type,
            index=index,
        )

    def get_item_image_head(
        self,
        item_id: str,
        image_type: str,
        index: int | None = None,
        retry: bool = True,
    ) -> tuple[bytes, str] | None:
        return client_image_ops.get_item_image_head(
            self,
            item_id=item_id,
            image_type=image_type,
            index=index,
            retry=retry,
        )

    def get_user_image(self, user_id: str) -> tuple[bytes, str] | None:
        return client_image_ops.get_user_image(self, user_id=user_id)

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

    def set_item_image_bytes(
        self,
        item_id: str,
        image_type: str,
        data: bytes,
        content_type: str,
        backdrop_index: int | None,
        failures: list[dict[str, Any]] | None = None,
    ) -> bool:
        return client_image_ops.set_item_image_bytes(
            self,
            item_id=item_id,
            image_type=image_type,
            data=data,
            content_type=content_type,
            backdrop_index=backdrop_index,
            failures=failures,
        )

    def set_item_image(
        self,
        item_id: str,
        image_type: str,
        image_path: Path,
        backdrop_index: int | None,
        failures: list[dict[str, Any]] | None = None,
    ) -> bool:
        return client_image_ops.set_item_image(
            self,
            item_id=item_id,
            image_type=image_type,
            image_path=image_path,
            backdrop_index=backdrop_index,
            failures=failures,
        )

    def set_user_image_bytes(
        self,
        user_id: str,
        image_type: str,
        data: bytes,
        content_type: str,
        failures: list[dict[str, Any]] | None = None,
    ) -> bool:
        return client_image_ops.set_user_image_bytes(
            self,
            user_id=user_id,
            image_type=image_type,
            data=data,
            content_type=content_type,
            failures=failures,
        )

    def delete_image(self, uuid: str, image_type: str, image_index: int | None) -> bool:
        return client_http.delete_image(
            self,
            request_fn=requests.delete,
            sleep_fn=time.sleep,
            uuid=uuid,
            image_type=image_type,
            image_index=image_index,
        )

    def set_user_profile_image(
        self,
        user_id: str,
        data: bytes,
        content_type: str,
        failures: list[dict[str, Any]] | None = None,
    ) -> bool:
        return client_image_ops.set_user_profile_image(
            self,
            user_id=user_id,
            data=data,
            content_type=content_type,
            failures=failures,
        )
