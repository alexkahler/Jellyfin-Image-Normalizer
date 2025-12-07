APP_VERSION = "0.1.1"

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

# Default item types for discovery (movies and series).
DEFAULT_ITEM_TYPES = ["Movie", "Series"]

# Pagination defaults for item discovery.
DEFAULT_DISCOVERY_PAGE_SIZE = 200

FILENAME_CONFIG = {
    "Logo": "logo",
    "Thumb": "landscape",
    "Primary": "profile",
}
