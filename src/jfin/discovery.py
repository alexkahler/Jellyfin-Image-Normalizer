from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Iterable

from . import state
from .config import DiscoverySettings
from .constants import DEFAULT_DISCOVERY_PAGE_SIZE


@dataclass
class LibraryRef:
    """Lightweight reference to a Jellyfin library discovered from Jellyfin."""

    id: str
    name: str
    collection_type: str | None


@dataclass
class DiscoveredItem:
    """Container for items discovered with desired image types."""

    id: str
    name: str
    type: str
    parent_id: str | None
    library_id: str | None
    library_name: str | None
    backdrop_count: int | None
    image_types: set[str] = field(default_factory=set)

    def add_image_type(self, image_type: str) -> None:
        """Mark that this item has a given image type tag."""
        self.image_types.add(image_type)


def _normalize_library_name(text: str) -> str:
    """Strip emoji/punctuation and case-fold to normalize names like 'dY?z | Crispyroll'."""
    lowered = text.casefold()
    return re.sub(r"[^a-z0-9]+", "", lowered)


def discover_libraries(
    jf_client: Any,
    discovery: DiscoverySettings,
) -> list[LibraryRef]:
    """List media folders and optionally filter by name."""
    if not discovery.library_names:
        state.log.info("No library filters provided; skipping library lookup and querying all items.")
        return []

    resp = jf_client.list_media_folders()
    if not resp or "Items" not in resp:
        state.log.critical("Could not list media folders from Jellyfin.")
        state.stats.record_error("discovery", "Failed to list media folders")
        raise SystemExit(1)

    items = resp.get("Items") or []
    names_filter = {_normalize_library_name(name) for name in discovery.library_names}
    if discovery.library_names:
        state.log.info(
            "Library filter configured: raw=%s normalized=%s",
            discovery.library_names,
            sorted(names_filter),
        )

    libraries: list[LibraryRef] = []
    for item in items:
        lib_id = item.get("Id")
        if not lib_id:
            continue
        name = item.get("Name") or "<unknown>"
        collection_type_raw = item.get("CollectionType")
        collection_type = collection_type_raw.lower() if isinstance(collection_type_raw, str) else None

        if names_filter and _normalize_library_name(name) not in names_filter:
            continue

        libraries.append(
            LibraryRef(
                id=lib_id,
                name=name,
                collection_type=collection_type,
            )
        )

    if discovery.library_names and not libraries:
        state.log.critical(
            "Library filters present (%s) but none matched active libraries.",
            ", ".join(discovery.library_names),
        )
        state.stats.record_error("discovery", "Library filters did not match any library")
        raise SystemExit(1)

    if names_filter:
        state.log.info(
            "Library filter active; selected %s/%s libraries: %s",
            len(libraries),
            len(items),
            ", ".join(lib.name for lib in libraries),
        )

    state.log.info(
        "Discovered %s libraries via /Library/MediaFolders.",
        len(libraries),
    )
    return libraries


def _item_backdrop_count(item: dict[str, Any]) -> int:
    """Return how many backdrop tags the item exposes, treating missing values as zero."""
    tags = item.get("BackdropImageTags") or []
    if isinstance(tags, list):
        return len(tags)
    return 0


def _item_has_image_type(item: dict[str, Any], image_type: str) -> bool:
    """Determine whether the discovered entry exposes an image of the requested type."""
    if image_type == "Backdrop":
        return _item_backdrop_count(item) > 0
    image_tags = item.get("ImageTags") or {}
    return image_type in image_tags


def discover_library_items(
    jf_client: Any,
    library: LibraryRef | None,
    discovery: DiscoverySettings,
) -> list[DiscoveredItem]:
    """Discover items inside a library that have any of the requested image types."""
    items: dict[str, DiscoveredItem] = {}
    enabled_types = list(discovery.enable_image_types)
    if not enabled_types:
        state.log.info("No image types requested; skipping item discovery.")
        return []

    page_size = DEFAULT_DISCOVERY_PAGE_SIZE
    start_index = 0
    total_records: int | None = None
    label = f"library '{library.name}'" if library else "all libraries"
    state.log.info("Scanning %s for image types %s (page_size=%s)", label, ",".join(enabled_types), page_size)

    while True:
        resp = jf_client.query_items(
            parent_id=library.id if library else None,
            include_item_types=discovery.include_item_types,
            enable_image_types=",".join(enabled_types),
            recursive=discovery.recursive,
            start_index=start_index,
            limit=page_size,
        )

        if resp is None:
            state.stats.record_error(
                label,
                f"Failed to query items for image types {enabled_types} (page start {start_index})",
            )
            break

        raw_items = resp.get("Items") or []
        for raw in raw_items:
            item_id = raw.get("Id")
            if not item_id:
                continue
            
            backdrop_count = _item_backdrop_count(raw)

            matching_types = [it for it in enabled_types if _item_has_image_type(raw, it)]
            if not matching_types:
                continue

            if item_id not in items:
                items[item_id] = DiscoveredItem(
                    id=item_id,
                    name=raw.get("Name") or "<unknown>",
                    type=raw.get("Type") or "Unknown",
                    parent_id=raw.get("ParentId"),
                    library_id=library.id if library else None,
                    library_name=library.name if library else None,
                    backdrop_count=None
                )
                
            
            item = items[item_id]
            if backdrop_count and "Backdrop" in enabled_types:
                # keep max in case of multiple pages
                item.backdrop_count = max(item.backdrop_count or 0, backdrop_count)
                
            for image_type in matching_types:
                item.add_image_type(image_type)

        state.log.info(
            "%s: fetched %s items (start=%s), unique with target images so far: %s",
            label,
            len(raw_items),
            start_index,
            len(items),
        )

        if not raw_items:
            break

        total_records = resp.get("TotalRecordCount", total_records)
        start_index += len(raw_items)

        if total_records is not None:
            if start_index >= total_records:
                break
        else:
            if len(raw_items) < page_size:
                break

    state.log.info("%s: %s items with target images.", label, len(items))
    return list(items.values())


def discover_all_library_items(
    jf_client: Any,
    libraries: list[LibraryRef] | None,
    discovery: DiscoverySettings,
) -> list[DiscoveredItem]:
    """Aggregate discovered items across all selected libraries."""
    if not libraries:
        return discover_library_items(jf_client, None, discovery)

    all_items: list[DiscoveredItem] = []
    for library in libraries:
        library_items = discover_library_items(jf_client, library, discovery)
        all_items.extend(library_items)
    return all_items


def profile_display_name(user: dict[str, Any]) -> str:
    """Human-readable label for a user including name and id."""
    name = user.get("Name") or "<unknown>"
    user_id = user.get("Id") or "?"
    return f"{name} ({user_id})"


def find_user_by_name(users: Iterable[dict[str, Any]], username: str) -> dict[str, Any] | None:
    """Locate a user by Name (case-insensitive) from a user list."""
    username_lower = username.lower()
    for user in users:
        name = (user.get("Name") or "").lower()
        if name == username_lower:
            return user
    return None
