"""Provide Jellyfin client image-operation mixin wrappers."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from . import client_image_ops


class JellyfinClientOpsMixin:
    """Expose image-operation wrapper methods on the client type."""

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
        """Run query items."""
        return client_image_ops.query_items(
            cast(Any, self),
            parent_id=parent_id,
            include_item_types=include_item_types,
            enable_image_types=enable_image_types,
            recursive=recursive,
            start_index=start_index,
            limit=limit,
        )

    def get_item(self, item_id: str) -> dict[str, Any] | None:
        """Get item."""
        return client_image_ops.get_item(cast(Any, self), item_id=item_id)

    def get_item_image(
        self, item_id: str, image_type: str, index: int | None = None
    ) -> tuple[bytes, str] | None:
        """Get item image."""
        return client_image_ops.get_item_image(
            cast(Any, self), item_id, image_type, index
        )

    def get_item_image_head(
        self,
        item_id: str,
        image_type: str,
        index: int | None = None,
        retry: bool = True,
    ) -> tuple[bytes, str] | None:
        """Get item image head."""
        return client_image_ops.get_item_image_head(
            cast(Any, self), item_id, image_type, index, retry
        )

    def get_user_image(self, user_id: str) -> tuple[bytes, str] | None:
        """Get user image."""
        return client_image_ops.get_user_image(cast(Any, self), user_id=user_id)

    def set_item_image_bytes(
        self,
        item_id: str,
        image_type: str,
        data: bytes,
        content_type: str,
        backdrop_index: int | None,
        failures: list[dict[str, Any]] | None = None,
    ) -> bool:
        """Set item image bytes."""
        return client_image_ops.set_item_image_bytes(
            cast(Any, self),
            item_id,
            image_type,
            data,
            content_type,
            backdrop_index,
            failures,
        )

    def set_item_image(
        self,
        item_id: str,
        image_type: str,
        image_path: Path,
        backdrop_index: int | None,
        failures: list[dict[str, Any]] | None = None,
    ) -> bool:
        """Set item image."""
        return client_image_ops.set_item_image(
            cast(Any, self),
            item_id,
            image_type,
            image_path,
            backdrop_index,
            failures,
        )

    def set_user_image_bytes(
        self,
        user_id: str,
        image_type: str,
        data: bytes,
        content_type: str,
        failures: list[dict[str, Any]] | None = None,
    ) -> bool:
        """Set user image bytes."""
        return client_image_ops.set_user_image_bytes(
            cast(Any, self),
            user_id,
            image_type,
            data,
            content_type,
            failures,
        )

    def set_user_profile_image(
        self,
        user_id: str,
        data: bytes,
        content_type: str,
        failures: list[dict[str, Any]] | None = None,
    ) -> bool:
        """Set user profile image."""
        return client_image_ops.set_user_profile_image(
            cast(Any, self),
            user_id=user_id,
            data=data,
            content_type=content_type,
            failures=failures,
        )
