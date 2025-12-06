from __future__ import annotations

import base64
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import requests

from . import state


@dataclass
class JellyfinClient:
    """Lightweight Jellyfin API wrapper with retry/backoff and dry-run safety."""

    base_url: str
    api_key: str
    timeout: float = 15.0
    verify_tls: bool = True
    delay: float = 0.0
    retry_count: int = 3
    backoff_base: float = 0.5
    fail_fast: bool = False
    dry_run: bool = True
    logger: Any = field(default_factory=lambda: state.log)

    def __post_init__(self) -> None:
        # Normalize base_url once to avoid repeated rstrip calls.
        self.base_url = self.base_url.rstrip("/")

    def _headers(self) -> dict[str, str]:
        """Standard auth headers for Jellyfin requests."""
        return {"X-Emby-Token": self.api_key}

    def _get(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        stream: bool = False,
        label: str = "request",
    ) -> requests.Response | None:
        """Wrapper around requests.get with logging, retry, and ok-status validation."""
        attempts = max(1, int(self.retry_count))
        backoff = max(0.0, float(self.backoff_base))
        last_error = None

        for attempt in range(1, attempts + 1):
            try:
                resp = requests.get(
                    url,
                    headers=self._headers(),
                    params=params,
                    timeout=self.timeout,
                    verify=self.verify_tls,
                    stream=stream,
                )
            except Exception as e:
                last_error = str(e)
                resp = None
            else:
                if resp.ok:
                    return resp
                snippet = (resp.text or "")[:200].replace("\n", " ")
                last_error = f"HTTP {resp.status_code} {snippet}"
                resp = None

            self.logger.error(
                "[API-ERROR] Attempt %s/%s failed for %s: %s",
                attempt,
                attempts,
                label,
                last_error,
            )
            if attempt < attempts and backoff > 0:
                time.sleep(backoff)
                backoff *= 2

        return None

    def _get_json(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        label: str,
    ) -> Any | None:
        """GET and decode JSON, logging errors on decode/HTTP failures."""
        resp = self._get(url, params=params, stream=False, label=label)
        if resp is None:
            return None
        try:
            return resp.json()
        except Exception as e:
            snippet = (resp.text or "")[:200].replace("\n", " ")
            self.logger.error("[API-ERROR] Failed to decode JSON from %s: %s (%s)", url, e, snippet)
            return None

    def _writes_allowed(self, action: str) -> bool:
        if self.dry_run:
            return False
        return True

    def _guess_content_type(self, image_path: Path) -> str | None:
        """Infer a basic content-type from a file suffix."""
        suffix = image_path.suffix.lower()
        if suffix == ".png":
            return "image/png"
        if suffix in (".jpg", ".jpeg"):
            return "image/jpeg"
        return "application/octet-stream"

    def test_connection(self) -> bool:
        """Call /System/Info to validate connectivity and token."""
        url = f"{self.base_url}/System/Info"

        resp = self._get(url, label="system info")
        if resp is None:
            return False

        self.logger.info("[API-TEST] Jellyfin connection OK.")
        return True

    def list_users(self, is_disabled: bool | None = None) -> list[dict[str, Any]]:
        """Return all users (optionally filtered by disabled flag)."""
        url = f"{self.base_url}/Users"
        params: dict[str, str] | None = None
        if is_disabled is not None:
            params = {"isDisabled": str(is_disabled).lower()}

        data = self._get_json(url, params=params, label="list users")
        if data is None:
            return []

        if not isinstance(data, list):
            self.logger.error("[API-ERROR] /Users response is not a list")
            return []

        return data

    def get_user_items(
        self,
        user_id: str,
        params: dict[str, Any] | None = None,
        label: str | None = None,
    ) -> dict[str, Any] | None:
        """Fetch items for a user; parentId omitted returns libraries."""
        url = f"{self.base_url}/Users/{user_id}/Items"
        request_label = label or f"user items for {user_id}"
        return self._get_json(url, params=params, label=request_label)

    def query_library_items(
        self,
        user_id: str,
        *,
        parent_id: str,
        include_item_types: list[str],
        enable_image_types: str | list[str],
        recursive: bool,
        image_type_limit: int,
        start_index: int | None = None,
        limit: int | None = None,
    ) -> dict[str, Any] | None:
        """Query a library for specific item/image types."""
        enable_types = (
            ",".join(enable_image_types) if isinstance(enable_image_types, list) else enable_image_types
        )
        params = {
            "ParentId": parent_id,
            "IncludeItemTypes": ",".join(include_item_types),
            "Recursive": str(recursive).lower(),
            "ImageTypeLimit": image_type_limit,
            "EnableImageTypes": enable_types,
        }
        if start_index is not None:
            params["StartIndex"] = start_index
        if limit is not None:
            params["Limit"] = limit

        request_label = (
            f"user items for {user_id} (parent={parent_id}, image_types={enable_types}, "
            f"start={start_index}, limit={limit})"
        )
        return self.get_user_items(user_id, params=params, label=request_label)

    def get_item_image(self, item_id: str, image_type: str) -> tuple[bytes, str] | None:
        """Fetch raw image bytes and content type for an item image."""
        url = f"{self.base_url}/Items/{item_id}/Images/{image_type}"
        resp = self._get(url, stream=True, label=f"item image {item_id}:{image_type}")
        if resp is None:
            return None
        content_type = resp.headers.get("Content-Type", "application/octet-stream")
        return resp.content, content_type

    def get_user_image(self, user_id: str) -> tuple[bytes, str] | None:
        """Fetch a user's profile image bytes and content type."""
        url = f"{self.base_url}/UserImage"
        resp = self._get(
            url,
            params={"userId": user_id},
            stream=True,
            label=f"profile image for {user_id}",
        )
        if resp is None:
            return None

        content_type = resp.headers.get("Content-Type", "application/octet-stream")
        return resp.content, content_type

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
        """Centralized POST helper used by item and user uploads."""
        if not self._writes_allowed(action_label):
            self.logger.info("DRY RUN - Would upload normalized image for %s.", action_label)
            return True

        attempts = max(1, int(self.retry_count))
        backoff = max(0.0, float(self.backoff_base))

        last_error_msg = "Unknown error"
        payload = base64.b64encode(data) if encode_base64 else data

        for attempt in range(1, attempts + 1):
            try:
                resp = requests.post(
                    url,
                    headers=headers,
                    data=payload,
                    timeout=self.timeout,
                    verify=self.verify_tls,
                )
            except Exception as e:
                last_error_msg = f"Exception: {e}"
                resp = None
            else:
                if resp.ok:
                    self.logger.info(success_message)
                    if self.delay > 0:
                        time.sleep(self.delay)
                    return True
                snippet = (resp.text or "")[:200].replace("\n", " ")
                last_error_msg = f"HTTP {resp.status_code} {snippet}"

            self.logger.error(
                "[API-ERROR] Attempt %s/%s failed for %s: %s",
                attempt,
                attempts,
                error_label,
                last_error_msg,
            )

            if attempt < attempts:
                time.sleep(backoff)
                backoff *= 2.0

        failure_entry["error"] = last_error_msg
        if failures is not None:
            failures.append(failure_entry)

        if self.fail_fast:
            raise RuntimeError(f"{fail_fast_prefix}: {last_error_msg}")

        return False

    def set_item_image_bytes(
        self,
        item_id: str,
        image_type: str,
        data: bytes,
        content_type: str,
        failures: list[dict[str, Any]] | None = None,
    ) -> bool:
        """Upload an image for an item using in-memory bytes."""
        url = f"{self.base_url}/Items/{item_id}/Images/{image_type}"

        headers = {
            "X-Emby-Token": self.api_key,
            "Content-Type": content_type,
        }

        return self._post_image(
            url=url,
            headers=headers,
            data=data,
            encode_base64=True,
            success_message=f"[API] Updated {image_type} image for item {item_id}",
            error_label=f"item {item_id}, type {image_type}",
            action_label=f"item {item_id} (type {image_type})",
            failures=failures,
            failure_entry={
                "item_id": item_id,
                "image_type": image_type,
                "path": None,
            },
            fail_fast_prefix=f"API upload failed for item {item_id} type {image_type}",
        )

    def set_item_image(
        self,
        item_id: str,
        image_type: str,
        image_path: Path,
        failures: list[dict[str, Any]] | None = None,
    ) -> bool:
        """Upload an image for an item from a filesystem path."""
        try:
            with image_path.open("rb") as f:
                data = f.read()
        except Exception as e:
            msg = f"Exception reading image file {image_path}: {e}"
            self.logger.error("[API-ERROR] %s", msg)
            if failures is not None:
                failures.append(
                    {
                        "item_id": item_id,
                        "image_type": image_type,
                        "path": str(image_path),
                        "error": msg,
                    }
                )
            if self.fail_fast:
                raise
            return False

        content_type = self._guess_content_type(image_path) or "application/octet-stream"
        return self.set_item_image_bytes(
            item_id=item_id,
            image_type=image_type,
            data=data,
            content_type=content_type,
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
        """Upload an image for a user from in-memory bytes."""
        url = f"{self.base_url}/UserImage?userId={user_id}"

        headers = {
            "X-Emby-Token": self.api_key,
            "Content-Type": content_type,
        }

        return self._post_image(
            url=url,
            headers=headers,
            data=data,
            encode_base64=True,
            success_message=f"[API] Updated {image_type} image for user {user_id}",
            error_label=f"user {user_id}, type {image_type}",
            action_label=f"user {user_id} (type {image_type})",
            failures=failures,
            failure_entry={
                "user_id": user_id,
                "image_type": image_type,
                "path": None,
            },
            fail_fast_prefix=f"API upload failed for user {user_id} type {image_type}",
        )

    def delete_user_profile_image(self, user_id: str) -> bool:
        """Delete a user's profile image; 404 is treated as success."""
        url = f"{self.base_url}/UserImage?userId={user_id}"
        headers = {"X-Emby-Token": self.api_key}

        if not self._writes_allowed(f"delete profile image for user {user_id}"):
            self.logger.info("DRY RUN - Would delete existing profile image for user %s.", user_id)
            return True

        try:
            resp = requests.delete(
                url,
                headers=headers,
                timeout=self.timeout,
                verify=self.verify_tls,
            )
        except Exception as e:
            self.logger.error("[API-ERROR] Failed to delete profile image for user %s: %s", user_id, e)
            return False

        if resp.status_code == 404:
            return True
        if resp.ok:
            return True

        snippet = (resp.text or "")[:200].replace("\n", " ")
        self.logger.error(
            "[API-ERROR] HTTP %s deleting profile image for user %s: %s",
            resp.status_code,
            user_id,
            snippet,
        )
        return False

    def set_user_profile_image(
        self,
        user_id: str,
        data: bytes,
        content_type: str,
        failures: list[dict[str, Any]] | None = None,
    ) -> bool:
        """Replace a user's profile image (delete existing then upload)."""
        url = f"{self.base_url}/UserImage?userId={user_id}"
        headers = {
            "X-Emby-Token": self.api_key,
            "Content-Type": content_type,
        }

        if not self.delete_user_profile_image(user_id):
            failure_entry = {
                "user_id": user_id,
                "image_type": "Primary",
                "path": None,
                "error": "Failed to delete existing profile image before upload",
            }
            if failures is not None:
                failures.append(failure_entry)
            if self.fail_fast:
                raise RuntimeError(
                    f"API delete failed for user {user_id} profile image; aborting upload"
                )
            return False

        return self._post_image(
            url=url,
            headers=headers,
            data=data,
            encode_base64=True,
            success_message=f"[API] Updated profile image for user {user_id}",
            error_label=f"user {user_id} profile",
            action_label=f"user {user_id} (profile image)",
            failures=failures,
            failure_entry={
                "user_id": user_id,
                "image_type": "Primary",
                "path": None,
            },
            fail_fast_prefix=f"API upload failed for user {user_id} profile image",
        )
