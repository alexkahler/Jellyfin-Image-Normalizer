import pytest
from pathlib import Path
from unittest.mock import Mock

from jfin_core import backup as backup_mod
from jfin_core.backup import (
    backup_path_for_image,
    guess_extension_from_content_type,
    image_type_from_filename,
    normalize_backup_mode,
    restore_from_backups,
    restore_single_item_from_backup,
    save_backup,
    should_backup_for_plan,
)
from jfin_core.client import JellyfinClient


def test_should_backup_for_plan_modes():
    assert should_backup_for_plan("SCALE_UP", "partial") is True
    assert should_backup_for_plan("SCALE_DOWN", "partial") is True
    assert should_backup_for_plan("NO_SCALE", "partial") is False
    assert should_backup_for_plan("NO_SCALE", "full") is True


def test_normalize_backup_mode_defaults_to_partial():
    assert normalize_backup_mode("full") == "full"
    assert normalize_backup_mode(None) == "partial"
    assert normalize_backup_mode("unsupported") == "partial"


@pytest.mark.parametrize(
    "item_id, image_type, backdrop_index, ext, expected_rel",
    [
        ("abc123", "Logo", None, ".png", Path("ab") / "abc123" / "logo.png"),
        ("321bca", "Thumb", None, ".jpg", Path("32") / "321bca" / "landscape.jpg"),
        ("451bok", "Backdrop", 0, ".jpg", Path("45") / "451bok" / "backdrop.jpg"),
    ],
)
def test_backup_path_for_image(tmp_path: Path, item_id: str, image_type: str, ext: str, expected_rel: Path, backdrop_index: int | None) -> None:
    path = backup_path_for_image(tmp_path, item_id, image_type, ext, backdrop_index)

    expected = tmp_path / expected_rel
    assert path == expected
    assert expected.parent.exists()
    assert not expected.exists()


@pytest.mark.parametrize(
    "item_id, image_type, content_type, backdrop_index, expected_stem",
    [
        # Backdrop index 3
        ("abc123", "Backdrop", "image/jpeg", 3, "backdrop3"),
        # Logo
        ("321acb", "Logo", "image/png", None, "logo"),
        # Profile
        ("bac543", "Primary", "image/jpeg", None, "profile"),
        # Thumb
        ("321acb", "Thumb", "image/jpeg", None, "landscape"),
        
        ("432fda", "Backdrop", "image/jpeg", 0, "backdrop"),
    ],
)
def test_save_backup_writes_files(
    tmp_path: Path,
    item_id: str,
    image_type: str,
    content_type: str,
    backdrop_index: int | None,
    expected_stem: str,
) -> None:
    data = b"dummybytes"

    path = save_backup(
        backup_root=tmp_path,
        item_id=item_id,
        image_type=image_type,
        data=data,
        content_type=content_type,
        backdrop_index=backdrop_index,
    )

    ext = guess_extension_from_content_type(content_type)
    expected = tmp_path / item_id[:2] / item_id / f"{expected_stem}{ext}"

    # Path should be correct
    assert path == expected
    # Parent dir should exist
    assert expected.parent.exists()
    # File should exist and contain the data
    assert expected.exists()
    assert expected.read_bytes() == data


@pytest.mark.parametrize(
    "filename, expected, should_raise",
    [
        ("backdrop1.jpg", "Backdrop", False),
        ("logo.png", "Logo", False),
        ("landscape.jpg", "Thumb", False),
        ("profile.jpg", "Primary", False),
        ("backdrop.jpg", "Backdrop", False),
        ("primary.jpg", None, True),
        ("unknownfile.png", None, True),
    ],
)
def test_image_type_from_filename(filename: str, expected: str | None, should_raise: bool) -> None:
    if should_raise:
        with pytest.raises(ValueError):
            image_type_from_filename(filename)
    else:
        assert image_type_from_filename(filename) == expected
        

@pytest.mark.parametrize(
    "content_type, expected_ext",
    [
        ("image/png", ".png"),
        ("image/jpeg", ".jpg"),
        ("image/jpg", ".jpg"),
        ("image/webp", ".webp"),
        # realistic variants
        ("IMAGE/PNG", ".png"),
        ("image/jpeg; charset=utf-8", ".jpg"),
        ("image/webp;quality=90", ".webp"),
    ],
)
def test_guess_extension_from_content_type_valid(
    content_type: str,
    expected_ext: str,
) -> None:
    assert guess_extension_from_content_type(content_type) == expected_ext


@pytest.mark.parametrize(
    "content_type",
    [
        None,
        "",
        "application/octet-stream",
        "image/gif",
        "text/plain",
    ],
)
def test_guess_extension_from_content_type_invalid(content_type: str | None) -> None:
    with pytest.raises(ValueError):
        guess_extension_from_content_type(content_type)


class FakeStats:
    def __init__(self) -> None:
        self.processed = 0
        self.successes = 0
        self.errors: list[tuple[tuple, dict]] = []
        self.warnings = 0
        self.skips = 0
        self._processed_item_ids: set[str] = set()

    def record_item_processed(self, item_id: str) -> None:
        if not item_id:
            return
        if item_id in self._processed_item_ids:
            return
        self._processed_item_ids.add(item_id)
        self.processed += 1

    def record_success(self) -> None:
        self.successes += 1

    def record_warning(self, count_processed: bool | None = None) -> None:
        self.warnings += 1

    def record_skip(self, count_processed: bool | None = None) -> None:   
        self.skips += 1

    def record_error(self, *args, **kwargs) -> None:
        self.errors.append((args, kwargs))


class FakeLog:
    def critical(self, *args, **kwargs): ...
    def error(self, *args, **kwargs): ...
    def debug(self, *args, **kwargs): ...
    def info(self, *args, **kwargs): ...
    def warning(self, *args, **kwargs): ...
    def exception(self, *args, **kwargs): ...


class FakeState:
    def __init__(self) -> None:
        self.log = FakeLog()
        self.stats = FakeStats()
        self.api_failures: list[str] = []

    def latest_api_error(self, before_failures: int) -> str | None:
        return None


@pytest.fixture
def fake_state(monkeypatch: pytest.MonkeyPatch) -> FakeState:
    state = FakeState()
    monkeypatch.setattr(backup_mod, "state", state, raising=False)
    return state


@pytest.fixture
def jf_client() -> Mock:
    client = Mock(spec=JellyfinClient)
    client.set_item_image_bytes.return_value = True
    client.set_user_profile_image.return_value = True
    return client
# =============================================================================

# Tests: restore_from_backups
# =============================================================================

@pytest.mark.parametrize(
    "case,"
    "filenames,"
    "operations,"
    "dry_run,"
    "expected_item_calls,"
    "expected_profile_calls,"
    "expected_successes,"
    "expected_errors",
    [
        # 1) Single backdrop.jpg (no index)
        (
            "single_backdrop_plain",
            ["backdrop.jpg"],
            ["backdrop"],
            False,
            [("Backdrop", 0)],
            0,
            1,
            0,
        ),
        # 2) Multiple indexed backdrops: backdrop1 + backdrop2 -> OK
        (
            "multiple_indexed_backdrops_ok",
            ["backdrop.jpg", "backdrop1.jpg"],
            ["backdrop"],
            False,
            [("Backdrop", 0), ("Backdrop", 1)],
            0,
            2,
            0,
        ),
        # 3) Invalid combo: backdrop.jpg + backdrop2.jpg -> should fail (no uploads)
        (
            "mixed_plain_and_indexed_backdrop_invalid",
            ["backdrop.jpg", "backdrop2.jpg"],
            ["backdrop"],
            False,
            [],
            0,
            0,
            1,  # expect at least one error recorded
        ),
        # 4) Mode filters operations: only logo allowed
        (
            "mode_filters_operations",
            ["logo.png", "landscape.jpg", "backdrop.jpg", "backdrop1.jpg"],
            ["logo"],
            False,
            [("Logo", None)],   # only logo is restored
            0,
            1,
            0,
        ),
        # 5) Honors dry_run: finds all eligible files but does not upload
        (
            "honors_dry_run",
            ["logo.png", "landscape.jpg", "backdrop.jpg", "backdrop1.jpg"],
            ["logo", "thumb", "backdrop"],
            True,
            [("Logo", None), ("Thumb", None), ("Backdrop", 0), ("Backdrop", 1)],
            0,
            4,   # four would-be restores -> four successes in dry_run
            0,
        ),
        # 6) Unknown files are ignored (no uploads, no errors)
        (
            "unknown_files_ignored",
            ["banner.jpg", "my_image.png"],
            ["logo", "thumb", "backdrop", "profile"],
            False,
            [],
            0,
            0,
            0,
        ),
        # 7) All four files present and found
        (
            "all_four_files_found",
            ["logo.png", "landscape.jpg", "backdrop.jpg", "backdrop1.jpg"],
            ["logo", "thumb", "backdrop"],
            False,
            [("Logo", None), ("Thumb", None), ("Backdrop", 0), ("Backdrop", 1)],
            0,
            4,
            0,
        ),
        # 8) Two profile images (jpg + png):
        #    only one should be uploaded and one error recorded about duplicates
        (
            "profile_jpg_and_png",
            ["profile.jpg", "profile.png"],
            ["profile"],
            False,
            [],
            1,   # only one profile upload
            1,   # one success
            1,   # one error recorded (e.g. "multiple profile backups found")
        ),
        # 9) Mixed valid and invalid files: only valid backdrops are restored
        (
            "mixed_valid_and_invalid_backdrops",
            ["backdrop.jpg", "my_image.jpg"],
            ["backdrop"],
            False,
            [("Backdrop", 0)],
            0,
            1,   # one successful restore
            0,   # no errors; junk is just ignored
        ),
    ],
)
def test_restore_from_backups_scenarios(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    fake_state: FakeState,
    case: str,
    filenames: list[str],
    operations: list[str],
    dry_run: bool,
    expected_item_calls: list[tuple[str, int | None]],
    expected_profile_calls: int,
    expected_successes: int,
    expected_errors: int,
) -> None:
    """
    Scenario-based test for restore_from_backups that covers:
    - mode filtering via `operations`
    - dry_run behavior
    - unknown filenames being ignored
    - backdrop index handling (single and multiple)
    - logo, profile, and landscape/thumb handling
    - multi-file scenarios per item
    """
    # --- Patch helpers / globals used by restore_from_backups -----------------
    # image_type_from_filename:
    #  - Backdrops (with or without index) -> "Backdrop"
    #  - logo.png -> "Logo"
    #  - profile.(jpg|png) -> "Profile"
    #  - landscape.jpg -> "Thumb"
    #  - Everything else -> None (ignored)
    def fake_image_type_from_filename(fname: str) -> str | None:
        f = fname.lower()
        if f.startswith("backdrop") and f.endswith(".jpg"):
            return "Backdrop"
        if f == "logo.png":
            return "Logo"
        if f.startswith("profile.") and (f.endswith(".jpg") or f.endswith(".png")):
            return "Profile"
        if f == "landscape.jpg":
            return "Thumb"
        return None
    monkeypatch.setattr(
        backup_mod,
        "image_type_from_filename",
        fake_image_type_from_filename,
        raising=False,
    )
    # Map image types to "modes" used in the operations filter
    monkeypatch.setattr(
        backup_mod,
        "IMAGE_TYPE_TO_MODE",
        {
            "Backdrop": "backdrop",
            "Logo": "logo",
            "Profile": "profile",
            "Thumb": "thumb",
        },
        raising=False,
    )
    # content_type_from_extension: keep it simple
    def fake_content_type_from_extension(ext: str) -> str:
        if ext == ".png":
            return "image/png"
        return "image/jpeg"
    monkeypatch.setattr(
        backup_mod,
        "content_type_from_extension",
        fake_content_type_from_extension,
        raising=False,
    )
    # --- Arrange backup directory structure -----------------------------------
    backup_root = tmp_path
    item_id = "abc123"
    item_dir = backup_root / item_id[:2] / item_id
    item_dir.mkdir(parents=True)
    data = b"dummybytes"
    for fname in filenames:
        (item_dir / fname).write_bytes(data)
    # --- Fake Jellyfin client -------------------------------------------------
    jf_client = Mock(spec=JellyfinClient)
    jf_client.set_item_image_bytes.return_value = True
    jf_client.set_user_profile_image.return_value = True
    # --- Act ------------------------------------------------------------------
    restore_from_backups(
        backup_root=backup_root,
        jf_client=jf_client,
        operations=operations,
        dry_run=dry_run,
    )
    # --- Assert: stats --------------------------------------------------------
    assert fake_state.stats.successes == expected_successes, case
    assert len(fake_state.stats.errors) == expected_errors, case
    # --- Assert: client calls -------------------------------------------------
    if dry_run:
        # In dry-run mode, no uploads should be attempted
        assert jf_client.set_item_image_bytes.call_count == 0, case
        assert jf_client.set_user_profile_image.call_count == 0, case
        return
    # Non-dry-run: check profile vs item calls
    assert jf_client.set_user_profile_image.call_count == expected_profile_calls, case
    assert jf_client.set_item_image_bytes.call_count == len(expected_item_calls), case
    # Check image_type + backdrop_index combos for item calls
    actual_item_calls: list[tuple[str, int | None]] = []
    for _args, kwargs in jf_client.set_item_image_bytes.call_args_list:
        actual_item_calls.append((kwargs["image_type"], kwargs["backdrop_index"]))
        # Also sanity-check that item_id and data are correct
        assert kwargs["item_id"] == item_id
        assert kwargs["data"] == data
        assert kwargs["content_type"] in ("image/jpeg", "image/png")
        assert "failures" in kwargs
    assert sorted(actual_item_calls) == sorted(expected_item_calls), case
    # Profile calls: just basic sanity-checks if any are expected
    if expected_profile_calls:
        for _args, kwargs in jf_client.set_user_profile_image.call_args_list:
            assert kwargs["user_id"] == item_id
            assert kwargs["data"] == data
            assert kwargs["content_type"] in ("image/jpeg", "image/png")
            assert "failures" in kwargs

# Tests: restore_single_from_backup
# =============================================================================

@pytest.mark.parametrize(
    "case, filenames, mode, dry_run,"
    "expected_item_calls, expected_profile_calls,"
    "expected_return, expected_successes",
    [
        # 1) Simple logo restore
        (
            "logo_normal",
            ["logo.png"],
            "logo",
            False,
            [("Logo", None)],
            0,
            True,
            1,
        ),
        # 2) Thumb via landscape.jpg
        (
            "thumb_landscape",
            ["landscape.jpg"],
            "thumb",
            False,
            [("Thumb", None)],
            0,
            True,
            1,
        ),
        # 3) Single backdrop.jpg -> Backdrop with index 0
        # Counterpart: test_restore_from_backups_scenarios::single_backdrop_plain
        (
            "backdrop_single_plain",
            ["backdrop.jpg"],
            "backdrop",
            False,
            [("Backdrop", 0)],
            0,
            True,
            1,
        ),
        # 4) Multiple backdrops: backdrop1 + backdrop2 -> indices 1 and 2
        # Counterpart: test_restore_from_backups_scenarios::multiple_indexed_backdrops_ok
        (
            "backdrop_multiple_indexed",
            ["backdrop.jpg", "backdrop1.jpg"],
            "backdrop",
            False,
            [("Backdrop", 0), ("Backdrop", 1)],
            0,
            True,
            2,
        ),
        # 5) Invalid files only -> nothing restored
        (
            "invalid_files_only",
            ["my_image.jpg", "landscape.png"],
            "backdrop",
            False,
            [],
            0,
            False,
            0,
        ),
        # 6) Dry-run: multiple backdrops, no uploads but returns True
        # Counterpart: test_restore_from_backups_scenarios::honors_dry_run
        (
            "dry_run_backdrops",
            ["backdrop.jpg", "backdrop1.jpg"],
            "backdrop",
            True,
            [],
            0,
            True,
            2,  # two "would restore" successes
        ),
        # 7) Profile restore (user profile image)
        (
            "profile_restore",
            ["profile.png"],
            "profile",
            False,
            [],
            1,
            True,
            1,
        ),
        # 8) Invalid combo: backdrop.jpg + backdrop2.jpg -> error / no restore
        # Counterpart: test_restore_from_backups_scenarios::mixed_plain_and_indexed_backdrop_invalid
        (
            "backdrop_mixed_plain_and_indexed_invalid",
            ["backdrop.jpg", "backdrop2.jpg"],
            "backdrop",
            False,
            [],
            0,
            False,  # should return False
            0,      # no successes
        ),
        # 9) Mode does not match available files: logo exists, but mode is thumb
        (
            "mode_mismatch_no_backup",
            ["logo.png"],
            "thumb",
            False,
            [],
            0,
            False,  # no suitable backup for 'thumb'
            0,
        ),
        # 10) Mixed valid and invalid files: only valid backdrop is restored
        # Counterpart: test_restore_from_backups_scenarios::mixed_valid_and_invalid_backdrops
        (
            "backdrop_mixed_valid_and_invalid",
            ["backdrop.jpg", "my_image.jpg"],
            "backdrop",
            False,
            [("Backdrop", 0)],
            0,
            True,
            1,
        ),
        # 11) Duplicate profile images (jpg + png): only one uploaded
        # Counterpart: test_restore_from_backups_scenarios::profile_jpg_and_png
        (
            "profile_duplicate_single",
            ["profile.jpg", "profile.png"],
            "profile",
            False,
            [],   # expected_item_calls
            1,    # one profile upload
            True, # return value
            1,    # one success
        ), 
    ],
)
def test_restore_single_from_backup_scenarios(
    tmp_path: Path,
    fake_state: FakeState,
    jf_client: Mock,
    case: str,
    filenames: list[str],
    mode: str,
    dry_run: bool,
    expected_item_calls: list[tuple[str, int | None]],
    expected_profile_calls: int,
    expected_return: bool,
    expected_successes: int,
) -> None:
    """
    Scenario-based spec for future restore_single_from_backup behavior.
    It verifies that:
    - dry_run is honored (no client calls, but success recorded and True returned)
    - correct backup files are located for a given target_id
    - single backdrop.jpg is treated as Backdrop index 0
    - multiple backdrops (backdrop.jpg, backdrop1.jpg, ...) get correct indices
    - invalid files (e.g., my_image.jpg, landscape.png) do not trigger restores
    - logo, thumb (landscape.jpg), and profile go through the correct Jellyfin API
    """
    # Arrange: create expected backup directory layout
    backup_root = tmp_path
    target_id = "abc123"
    item_dir = backup_root / target_id[:2] / target_id
    item_dir.mkdir(parents=True)
    data = b"dummybytes"
    for fname in filenames:
        (item_dir / fname).write_bytes(data)
    # Act
    result = restore_single_item_from_backup(
        backup_root=backup_root,
        jf_client=jf_client,
        mode=mode,
        target_id=target_id,
        dry_run=dry_run,
        backdrop_index=None,  # future implementation should compute indices itself
    )
    # Assert: return value + stats
    assert result is expected_return, case
    assert fake_state.stats.successes == expected_successes, case
    if dry_run:
        # In dry-run mode, no uploads should be attempted
        assert jf_client.set_item_image_bytes.call_count == 0, case
        assert jf_client.set_user_profile_image.call_count == 0, case
        return
    # Non-dry-run: check profile vs item calls
    assert jf_client.set_user_profile_image.call_count == expected_profile_calls, case
    assert jf_client.set_item_image_bytes.call_count == len(expected_item_calls), case
    # Check image_type + backdrop_index combos for item calls
    actual_item_calls: list[tuple[str, int | None]] = []
    for _args, kwargs in jf_client.set_item_image_bytes.call_args_list:
        actual_item_calls.append((kwargs["image_type"], kwargs["backdrop_index"]))
        # sanity: target and data
        assert kwargs["item_id"] == target_id
        assert kwargs["data"] == data
        assert kwargs["content_type"] in ("image/jpeg", "image/png")
        assert "failures" in kwargs
    # Compare expected vs actual item calls (order-insensitive)
    assert sorted(actual_item_calls) == sorted(expected_item_calls), case
    # Profile calls sanity-check, if any
    if expected_profile_calls:
        for _args, kwargs in jf_client.set_user_profile_image.call_args_list:
            assert kwargs["user_id"] == target_id
            assert kwargs["data"] == data
            assert kwargs["content_type"] in ("image/jpeg", "image/png")
            assert "failures" in kwargs
