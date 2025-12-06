from pathlib import Path

from jfin_core import state
from jfin_core.config import ModeRuntimeSettings
from jfin_core.discovery import DiscoveredItem
from jfin_core.pipeline import normalize_item_image_api, restore_from_backups, process_single_item_api, restore_single_from_backup


class StubClient:
    def __init__(self, image_bytes: bytes):
        self.image_bytes = image_bytes
        self.upload_calls = 0
        self.profile_uploads = 0
        self.last_image_type = None

    def get_item_image(self, item_id: str, image_type: str):
        self.last_image_type = image_type
        return self.image_bytes, "image/png"

    def set_item_image_bytes(self, item_id: str, image_type: str, data: bytes, content_type: str, failures=None):
        self.upload_calls += 1
        return True

    def set_user_profile_image(self, user_id: str, data: bytes, content_type: str, failures=None):
        self.profile_uploads += 1
        return True


def test_normalize_item_image_api_dry_run_skips_upload(rgb_image_bytes, tmp_path):
    client = StubClient(rgb_image_bytes(size=(200, 100)))
    item = DiscoveredItem(
        id="item1",
        name="Demo",
        type="Movie",
        parent_id=None,
        library_id=None,
        library_name=None,
        image_types={"Thumb"},
    )
    settings_by_mode = {
        "thumb": ModeRuntimeSettings(
            target_width=100,
            target_height=50,
            allow_upscale=False,
            allow_downscale=True,
            jpeg_quality=85,
            webp_quality=80,
            no_padding=False,
        )
    }

    ok = normalize_item_image_api(
        item=item,
        image_type="Thumb",
        settings_by_mode=settings_by_mode,
        jf_client=client,  # type: ignore[arg-type]
        dry_run=True,
        force_upload_noscale=False,
        make_backup=False,
        backup_root=tmp_path,
        backup_mode="partial",
    )

    assert ok is True
    assert client.upload_calls == 0
    assert state.stats.successes == 1


def test_restore_from_backups_filters_operations(tmp_path):
    backup_root = tmp_path / "backup"
    target_dir = backup_root / "ab" / "abcdef"
    target_dir.mkdir(parents=True)
    (target_dir / "logo.png").write_bytes(b"logo-bytes")
    (target_dir / "landscape.jpg").write_bytes(b"thumb-bytes")

    client = StubClient(b"")

    restore_from_backups(
        backup_root=backup_root,
        jf_client=client,  # type: ignore[arg-type]
        operations=["logo"],
        dry_run=False,
    )

    assert client.upload_calls == 1
    assert client.profile_uploads == 0


def test_restore_from_backups_honors_dry_run(tmp_path):
    backup_root = tmp_path / "backup"
    target_dir = backup_root / "ab" / "abcdef"
    target_dir.mkdir(parents=True)
    (target_dir / "logo.png").write_bytes(b"logo-bytes")

    client = StubClient(b"")

    restore_from_backups(
        backup_root=backup_root,
        jf_client=client,  # type: ignore[arg-type]
        operations=["logo"],
        dry_run=True,
    )

    assert client.upload_calls == 0
    assert state.stats.successes == 1


def test_process_single_item_uses_direct_item_id(rgb_image_bytes, tmp_path):
    client = StubClient(rgb_image_bytes(size=(200, 100)))
    settings_by_mode = {
        "thumb": ModeRuntimeSettings(
            target_width=100,
            target_height=50,
            allow_upscale=False,
            allow_downscale=True,
            jpeg_quality=85,
            webp_quality=80,
            no_padding=False,
        )
    }

    ok = process_single_item_api(
        item_id="item123",
        mode="thumb",
        settings_by_mode=settings_by_mode,
        jf_client=client,  # type: ignore[arg-type]
        dry_run=True,
        force_upload_noscale=False,
        make_backup=False,
        backup_root=tmp_path,
        backup_mode="partial",
    )

    assert ok is True
    assert client.last_image_type == "Thumb"
    assert client.upload_calls == 0


def test_restore_single_from_backup_item(tmp_path):
    backup_root = tmp_path / "backup"
    target_dir = backup_root / "it" / "item1234"
    target_dir.mkdir(parents=True)
    (target_dir / "logo.png").write_bytes(b"logo-bytes")

    client = StubClient(b"")
    ok = restore_single_from_backup(
        backup_root=backup_root,
        jf_client=client,  # type: ignore[arg-type]
        mode="logo",
        target_id="item1234",
        dry_run=False,
    )

    assert ok is True
    assert client.upload_calls == 1
    assert state.stats.successes == 1


def test_partial_backup_skips_no_scale(rgb_image_bytes, tmp_path):
    client = StubClient(rgb_image_bytes(size=(100, 50)))
    item = DiscoveredItem(
        id="abcd1234",
        name="Demo",
        type="Movie",
        parent_id=None,
        library_id=None,
        library_name=None,
        image_types={"Thumb"},
    )
    settings_by_mode = {
        "thumb": ModeRuntimeSettings(
            target_width=100,
            target_height=50,
            allow_upscale=False,
            allow_downscale=False,
            jpeg_quality=85,
            webp_quality=80,
            no_padding=False,
        )
    }

    ok = normalize_item_image_api(
        item=item,
        image_type="Thumb",
        settings_by_mode=settings_by_mode,
        jf_client=client,  # type: ignore[arg-type]
        dry_run=False,
        force_upload_noscale=False,
        make_backup=True,
        backup_root=tmp_path,
        backup_mode="partial",
    )

    backup_file = tmp_path / "ab" / "abcd1234" / "landscape.png"
    assert ok is True
    assert client.upload_calls == 0
    assert backup_file.exists() is False


def test_backup_updates_when_scaled_image_changes(rgb_image_bytes, tmp_path):
    client = StubClient(rgb_image_bytes(size=(400, 200)))
    item = DiscoveredItem(
        id="logo1234",
        name="Demo Logo",
        type="Movie",
        parent_id=None,
        library_id=None,
        library_name=None,
        image_types={"Logo"},
    )
    settings_by_mode = {
        "logo": ModeRuntimeSettings(
            target_width=200,
            target_height=100,
            allow_upscale=False,
            allow_downscale=True,
            jpeg_quality=85,
            webp_quality=80,
            no_padding=False,
        )
    }

    first_ok = normalize_item_image_api(
        item=item,
        image_type="Logo",
        settings_by_mode=settings_by_mode,
        jf_client=client,  # type: ignore[arg-type]
        dry_run=False,
        force_upload_noscale=False,
        make_backup=True,
        backup_root=tmp_path,
        backup_mode="partial",
    )
    backup_file = tmp_path / "lo" / "logo1234" / "logo.png"
    first_bytes = backup_file.read_bytes()

    client.image_bytes = rgb_image_bytes(size=(400, 200), color=(0, 255, 0))
    second_ok = normalize_item_image_api(
        item=item,
        image_type="Logo",
        settings_by_mode=settings_by_mode,
        jf_client=client,  # type: ignore[arg-type]
        dry_run=False,
        force_upload_noscale=False,
        make_backup=True,
        backup_root=tmp_path,
        backup_mode="partial",
    )

    assert first_ok is True and second_ok is True
    assert backup_file.read_bytes() != first_bytes


def test_full_backup_saves_no_scale_images(rgb_image_bytes, tmp_path):
    client = StubClient(rgb_image_bytes(size=(120, 60)))
    item = DiscoveredItem(
        id="full1234",
        name="Full Backup",
        type="Movie",
        parent_id=None,
        library_id=None,
        library_name=None,
        image_types={"Thumb"},
    )
    settings_by_mode = {
        "thumb": ModeRuntimeSettings(
            target_width=120,
            target_height=60,
            allow_upscale=False,
            allow_downscale=False,
            jpeg_quality=85,
            webp_quality=80,
            no_padding=False,
        )
    }

    ok = normalize_item_image_api(
        item=item,
        image_type="Thumb",
        settings_by_mode=settings_by_mode,
        jf_client=client,  # type: ignore[arg-type]
        dry_run=False,
        force_upload_noscale=False,
        make_backup=True,
        backup_root=tmp_path,
        backup_mode="full",
    )

    backup_file = tmp_path / "fu" / "full1234" / "landscape.png"
    assert ok is True
    assert client.upload_calls == 0
    assert backup_file.exists() is True
