MODE_CONFIG = {
    "logo": {
        "filename": "logo.png",
    },
    "thumb": {
        "filename": "landscape.jpg",
    },
    "profile": {
        "filename": "profile",
    },
}

DEFAULT_CONFIG_NAME = "config.toml"
VALID_MODES = set(MODE_CONFIG.keys())

IMAGE_TYPE_TO_MODE = {
    "Logo": "logo",
    "Thumb": "thumb",
    "Primary": "profile",
}

MODE_TO_IMAGE_TYPE = {
    "logo": "Logo",
    "thumb": "Thumb",
    "profile": "Primary",
}

# Discovery constraints: collection types and item/image mappings.
ALLOWED_COLLECTION_TYPES = {"movies", "tvshows"}
# Jellyfin item types intentionally limited for safety (movies/series only).
INCLUDE_ITEM_TYPES = ["Movie", "Series", "Season", "Episode"]

# Pagination defaults for item discovery.
DEFAULT_DISCOVERY_PAGE_SIZE = 200

FILENAME_CONFIG = {
    "Logo": "logo",
    "Thumb": "landscape",
    "Primary": "profile",
}
