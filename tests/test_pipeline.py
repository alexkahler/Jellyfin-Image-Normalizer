import pytest
from pathlib import Path
from unittest.mock import Mock
from typing import cast

from jfin_core import backup as backup_mod
from jfin_core import pipeline as pipeline_mod
from jfin_core.client import JellyfinClient
from jfin_core.config import ModeRuntimeSettings
from jfin_core.discovery import DiscoveredItem
from jfin_core.imaging import ScalePlan
from jfin_core.pipeline import (
    normalize_item_image_api,
    normalize_item_backdrops_api,
    process_single_item_api,
)


class StubClient:
    def __init__(self, image_bytes: bytes):
        self.image_bytes = image_bytes
        self.upload_calls = 0
        self.profile_uploads = 0
        self.last_image_type = None

    def get_item_image(self, item_id: str, image_type: str, index: int | None = None):
        self.last_image_type = image_type
        return self.image_bytes, "image/png"

    def set_item_image_bytes(self, item_id: str, image_type: str, data: bytes, content_type: str, backdrop_index=None, failures=None):
        self.upload_calls += 1
        return True

    def set_user_profile_image(self, user_id: str, data: bytes, content_type: str, failures=None):
        self.profile_uploads += 1
        return True


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
    monkeypatch.setattr(pipeline_mod, "state", state, raising=False)
    return state


@pytest.fixture
def jf_client() -> Mock:
    client = Mock()
    client.set_item_image_bytes.return_value = True
    client.set_user_profile_image.return_value = True
    return client


# =============================================================================
# Tests: normalize_item_image_api and _process_item_image_payload
# =============================================================================


def test_normalize_item_image_api_dry_run_skips_upload(rgb_image_bytes, tmp_path, fake_state: FakeState):
    client = StubClient(rgb_image_bytes(size=(200, 100)))
    item = DiscoveredItem(
        id="item1",
        name="Demo",
        type="Movie",
        parent_id=None,
        library_id=None,
        library_name=None,
        backdrop_count=None,
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
    assert fake_state.stats.successes == 1


def test_process_item_image_payload_dry_run_no_upload(rgb_image_bytes, tmp_path, fake_state: FakeState):
    from jfin_core.pipeline import _process_item_image_payload

    client = StubClient(rgb_image_bytes(size=(200, 100)))
    settings = ModeRuntimeSettings(
        target_width=100,
        target_height=50,
        allow_upscale=False,
        allow_downscale=True,
        jpeg_quality=85,
        webp_quality=80,
        no_padding=False,
    )

    ok = _process_item_image_payload(
        item_id="item-x",
        label="dry-run test",
        image_type="Thumb",
        data=client.image_bytes,
        content_type="image/png",
        mode="thumb",
        settings=settings,
        jf_client=client,  # type: ignore[arg-type]
        dry_run=True,
        force_upload_noscale=False,
        make_backup=False,
        backup_root=tmp_path,
        backup_mode="partial",
    )
    assert ok is True
    assert client.upload_calls == 0
    assert fake_state.stats.successes == 1


# =============================================================================
# Tests: Backup persistence and mode behavior
# =============================================================================


def test_partial_backup_skips_no_scale(rgb_image_bytes, tmp_path):
    client = StubClient(rgb_image_bytes(size=(100, 50)))
    item = DiscoveredItem(
        id="abcd1234",
        name="Demo",
        type="Movie",
        parent_id=None,
        library_id=None,
        library_name=None,
        backdrop_count=None,
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
        backdrop_count=None,
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
        backdrop_count=None,
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


# =============================================================================
# Tests: normalize_item_backdrops_api
# =============================================================================


@pytest.mark.parametrize(
    "case, has_mode_mapping, has_settings, backdrop_count,"
    "fetch_fail_indices, process_fail_indices,"
    "expected_return, expected_warnings, expected_skips, expected_errors, expected_successes",
    [
        # 1) IMAGE_TYPE_TO_MODE does not contain "Backdrop" -> warning + False
        (
            "unsupported_image_type_mapping",
            False,   # has_mode_mapping
            True,    # has_settings (ignored)
            3,       # backdrop_count
            [],
            [],
            False,   # expected_return
            1,       # expected_warnings
            0,       # expected_skips
            0,       # expected_errors
            0,       # expected_successes
        ),
        # 2) No settings for backdrop mode -> warning + False
        (
            "missing_settings_for_backdrop_mode",
            True,
            False,   # has_settings
            3,
            [],
            [],
            False,
            1,
            0,
            0,
            0,
        ),
        # 3) Item has no backdrops (0) -> skip + False
        (
            "no_backdrops_zero",
            True,
            True,
            0,
            [],
            [],
            False,
            0,
            1,  # one skip
            0,
            0,
        ),
        # 4) Item has no backdrops (None) -> skip + False
        (
            "no_backdrops_none",
            True,
            True,
            None,
            [],
            [],
            False,
            0,
            1,
            0,
            0,
        ),
        # 5) All backdrops fetched and processed successfully -> True     
        #    This is the main "happy path" spec for the 5-phase behavior. 
        (
            "all_backdrops_ok",
            True,
            True,
            3,
            [],
            [],
            True,
            0,
            0,
            0,
            3,
        ),
        # 6) One backdrop fetch fails -> record_error + False, no delete/upload
        (
            "fetch_failure_on_one_backdrop",
            True,
            True,
            3,
            [1],   # backdrop index 1 fails to fetch
            [],
            False,
            0,
            0,
            1,     # one error recorded
            0,
        ),
        # 7) Fetch OK but normalization helper fails for one -> False     
        #    (helper is responsible for stats; we only assert return=False and no delete/upload)
        (
            "process_failure_on_one_backdrop",
            True,
            True,
            3,
            [],
            [2],   # processing fails for the 3rd backdrop
            False,
            0,
            0,
            1,
            0,
        ),
    ],
)

def test_normalize_item_backdrops_api_scenarios(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    fake_state: FakeState,
    case: str,
    has_mode_mapping: bool,
    has_settings: bool,
    backdrop_count: int | None,
    fetch_fail_indices: list[int],
    process_fail_indices: list[int],
    expected_return: bool,
    expected_warnings: int,
    expected_skips: int,
    expected_errors: int,
    expected_successes: int,
) -> None:
    """
    Scenario-based test for normalize_item_backdrops_api that verifies:

    - Mode mapping / settings / zero-backdrop fast paths.
    - Phase 1: fetch-all backdrops from indices 0..total-1.
    - Phase 2: normalize-all via _normalize_image_bytes with backdrop_index matching the source index.
    - Phase 3: delete-all originals using delete_image(index=0) exactly 'total' times.
    - Phase 3b: 404 verification via get_item_image(index=0) after deletions.
    - Phase 4: upload-all normalized payloads to fresh indices 0..total-1, in order.
    - Error handling:
      * Any fetch failure aborts with no delete/upload.
      * Any processing failure aborts with no delete/upload.
    """

    # --- Arrange IMAGE_TYPE_TO_MODE and settings ------------------------------

    if has_mode_mapping:
        monkeypatch.setattr(
            pipeline_mod,
            "IMAGE_TYPE_TO_MODE",
            {"Backdrop": "backdrop"},
            raising=False,
        )
        mode_key = "backdrop"
    else:
        # No mapping for Backdrop -> unsupported image type path
        monkeypatch.setattr(
            pipeline_mod,
            "IMAGE_TYPE_TO_MODE",
            {},
            raising=False,
        )
        mode_key = None  # not used

    settings_by_mode: dict[str, ModeRuntimeSettings] = {}
    if has_settings and mode_key is not None:
        # We don't care about the actual fields here because the stubbed
        # _normalize_image_bytes won't touch them.
        dummy_settings = cast(ModeRuntimeSettings, object())
        settings_by_mode[mode_key] = dummy_settings

    total = backdrop_count or 0

    # Item with backdrops
    item = DiscoveredItem(
        id="item123",
        name="Test Item",
        type="Movie",          # or whatever fits your domain
        parent_id=None,
        library_id=None,
        library_name=None,
        backdrop_count=backdrop_count,
        image_types=set(),     # empty is fine for this test
    )

    # Fake Jellyfin client: we want to observe get/delete/upload ordering
    jf_client = Mock(spec=JellyfinClient)
    jf_client.set_item_image_bytes.return_value = True
    jf_client.delete_image.return_value = True
    jf_client.get_item_image_head.return_value = None

    call_index = 0

    # get_item_image logic:
    #  - First 'total' calls correspond to Phase 1 fetches for indices 0..total-1.
    #    For those, we simulate per-index fetch failures based on fetch_fail_indices.
    #  - Any later call (Phase 3b verification) returns None to represent 404 (no image).
    def fake_get_item_image(item_id: str, image_type: str, index: int):
        nonlocal call_index
        current_call = call_index
        call_index += 1

        bc = backdrop_count or 0

        # Phase 1: fetch originals
        if current_call < bc:
            # Simulate fetch failure for specific *source indices*
            if index in fetch_fail_indices:
                return None
            return (f"data-{index}".encode("utf-8"), "image/jpeg")

        # Phase 3b: 404 verification (or any subsequent calls)
        return None

    jf_client.get_item_image.side_effect = fake_get_item_image

    # Stub for _normalize_image_bytes: raises for selected calls, otherwise returns normalized bytes
    process_calls: list[dict] = []
    process_call_index = 0

    def fake_normalize_image_bytes(**kwargs):
        nonlocal process_call_index
        current = process_call_index
        process_call_index += 1
        process_calls.append(kwargs)
        if current in process_fail_indices:
            raise RuntimeError(f"normalize failed at call {current}")

        plan = ScalePlan(
            decision="SCALE_DOWN",
            scale=1.0,
            new_width=100,
            new_height=50,
            orig_width=100,
            orig_height=50,
        )
        backdrop_idx = kwargs.get("backdrop_index") or 0
        payload = f"normalized-{backdrop_idx}".encode("utf-8")
        return plan, payload, "image/jpeg"

    monkeypatch.setattr(
        pipeline_mod,
        "_normalize_image_bytes",
        fake_normalize_image_bytes,
        raising=False,
    )

    # --- Act ------------------------------------------------------------------

    result = normalize_item_backdrops_api(
        item=item,
        settings_by_mode=settings_by_mode,
        jf_client=jf_client,
        dry_run=False,
        force_upload_noscale=False,
        make_backup=False,
        backup_root=tmp_path,
        backup_mode="partial",
    )

    # --- Assert: return value & stats -----------------------------------------

    assert result is expected_return, case
    assert fake_state.stats.warnings == expected_warnings, case
    assert fake_state.stats.skips == expected_skips, case
    assert len(fake_state.stats.errors) == expected_errors, case
    assert fake_state.stats.successes == expected_successes, case

    # --- Short-circuit for the simple fast-path cases -------------------------

    if not has_mode_mapping:
        # Unsupported image type: no work done
        jf_client.get_item_image.assert_not_called()
        jf_client.delete_image.assert_not_called()
        jf_client.set_item_image_bytes.assert_not_called()
        assert process_calls == []
        return

    if has_mode_mapping and not has_settings:
        # No settings: no work done
        jf_client.get_item_image.assert_not_called()
        jf_client.delete_image.assert_not_called()
        jf_client.set_item_image_bytes.assert_not_called()
        assert process_calls == []
        return

    if total == 0:
        # No backdrops: nothing to do
        jf_client.get_item_image.assert_not_called()
        jf_client.delete_image.assert_not_called()
        jf_client.set_item_image_bytes.assert_not_called()
        assert process_calls == []
        return

    # --- Normal backdrop path: inspect phases & ordering ----------------------

    # Helper: did we inject any fetch failure?
    has_fetch_failure = bool(fetch_fail_indices)
    has_process_failure = bool(process_fail_indices)

    if has_fetch_failure or has_process_failure:
        # In any early failure (fetch or normalize):
        #  - No delete_image calls.
        #  - No uploads.
        assert jf_client.delete_image.call_count == 0, case
        assert jf_client.set_item_image_bytes.call_count == 0, case

        if has_fetch_failure:
            # We abort during fetch phase at the first failing backdrop index.
            # At least one get_item_image call should exist, but fewer than 'total'
            assert jf_client.get_item_image.call_count <= total, case
            # We don't need strong ordering assertions here; just ensure we never
            # reached delete/upload.
        else:
            # Fetches all, then process fails; we should have fetched all originals.
            assert jf_client.get_item_image.call_count >= total, case
            first_calls = jf_client.get_item_image.call_args_list[:total]
            indices = [call.kwargs["index"] for call in first_calls]
            assert indices == list(range(total)), case

        # The normalization helper should have been called once per fetched backdrop until failure.
        for idx, kwargs in enumerate(process_calls):
            assert kwargs["backdrop_index"] == idx, case
        return

    # Happy path: all backdrops fetch and normalize successfully.

    # Phase 1: fetch-all originals
    # We expect at least 'total' calls, first 'total' are fetches for indices 0..total-1.
    assert jf_client.get_item_image.call_count >= total, case 
    first_calls = jf_client.get_item_image.call_args_list[:total]
    fetch_indices = [call.kwargs["index"] for call in first_calls]
    assert fetch_indices == list(range(total)), case

    # Phase 2: normalize-all via helper; ensure backdrop_index matches source index
    assert len(process_calls) == total, case
    process_backdrop_indices = [kwargs["backdrop_index"] for kwargs in process_calls]
    assert process_backdrop_indices == list(range(total)), case

    # Phase 3: delete-all originals using delete_image(index=0) exactly 'total' times
    assert jf_client.delete_image.call_count == total, case
    
    def _delete_index(call):
        if "index" in call.kwargs:
            return call.kwargs["index"]
        if "image_index" in call.kwargs:
            return call.kwargs["image_index"]
        return call.args[2]

    delete_indices = [_delete_index(call) for call in jf_client.delete_image.call_args_list]
    assert delete_indices == [0] * total, case

    # Phase 3b: ensure we verify via HEAD call for index 0
    jf_client.get_item_image_head.assert_called_once()
    verify_call = jf_client.get_item_image_head.call_args
    assert verify_call.kwargs["index"] == 0, case

    # Phase 4: upload-all to new indices 0..total-1
    assert jf_client.set_item_image_bytes.call_count == total, case
    upload_calls = jf_client.set_item_image_bytes.call_args_list
    upload_backdrop_indices = [call.kwargs["backdrop_index"] for call in upload_calls]
    assert upload_backdrop_indices == list(range(total)), case

    # Order guarantee: upload index i corresponds to source index i
    # (we encoded src index into the fake data as "data-{index}" so we can check
    # that the call ordering matches; this verifies the preserve-order behavior).
    upload_payloads = [call.kwargs["data"] for call in upload_calls]
    expected_payloads = [f"normalized-{i}".encode("utf-8") for i in range(total)]
    assert upload_payloads == expected_payloads, case

    # No uploads should happen before all deletions are issued.
    # We can enforce this by inspecting the global mock call sequence.
    all_calls = jf_client.mock_calls
    first_delete_idx = next(i for i, c in enumerate(all_calls) if c[0] == "delete_image")
    first_upload_idx = next(i for i, c in enumerate(all_calls) if c[0] == "set_item_image_bytes")
    assert first_delete_idx < first_upload_idx, case


def test_normalize_item_backdrops_api_dry_run_skips_normalization(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fake_state: FakeState) -> None:
    """
    Dry-run mode should fetch metadata but skip normalization, deletions, and uploads.
    """
    item = DiscoveredItem(
        id="dry1",
        name="Dry Run",
        type="Movie",
        parent_id=None,
        library_id=None,
        library_name=None,
        backdrop_count=2,
        image_types={"Backdrop"},
    )
    settings_by_mode = {"backdrop": cast(ModeRuntimeSettings, object())}
    monkeypatch.setattr(
        pipeline_mod,
        "IMAGE_TYPE_TO_MODE",
        {"Backdrop": "backdrop"},
        raising=False,
    )

    jf_client = Mock(spec=JellyfinClient)
    jf_client.get_item_image.return_value = (b"data", "image/jpeg")

    normalize_called = False

    def fake_normalize_image_bytes(**kwargs):
        nonlocal normalize_called
        normalize_called = True
        raise AssertionError("normalize should not be called in dry-run")

    monkeypatch.setattr(
        pipeline_mod,
        "_normalize_image_bytes",
        fake_normalize_image_bytes,
        raising=False,
    )

    ok = normalize_item_backdrops_api(
        item=item,
        settings_by_mode=settings_by_mode,
        jf_client=jf_client,
        dry_run=True,
        force_upload_noscale=False,
        make_backup=False,
        backup_root=tmp_path,
        backup_mode="partial",
    )

    assert ok is True
    assert normalize_called is False
    assert fake_state.stats.successes == 2
    jf_client.delete_image.assert_not_called()
    jf_client.set_item_image_bytes.assert_not_called()


def test_normalize_item_backdrops_api_partial_upload_failure_keeps_staging(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    fake_state: FakeState,
) -> None:
    item = DiscoveredItem(
        id="item-fail",
        name="Upload Fail",
        type="Movie",
        parent_id=None,
        library_id=None,
        library_name=None,
        backdrop_count=2,
        image_types={"Backdrop"},
    )
    settings_by_mode = {"backdrop": cast(ModeRuntimeSettings, object())}
    monkeypatch.setattr(
        pipeline_mod,
        "IMAGE_TYPE_TO_MODE",
        {"Backdrop": "backdrop"},
        raising=False,
    )

    jf_client = Mock(spec=JellyfinClient)
    jf_client.delete_image.return_value = True
    jf_client.get_item_image_head.return_value = None

    def fake_get_item_image(item_id: str, image_type: str, index: int):
        return (f"data-{index}".encode("utf-8"), "image/jpeg")

    jf_client.get_item_image.side_effect = fake_get_item_image

    def fake_normalize_image_bytes(**kwargs):
        plan = ScalePlan(
            decision="SCALE_DOWN",
            scale=1.0,
            new_width=100,
            new_height=50,
            orig_width=100,
            orig_height=50,
        )
        idx = kwargs.get("backdrop_index") or 0
        payload = f"normalized-{idx}".encode("utf-8")
        return plan, payload, "image/jpeg"

    monkeypatch.setattr(
        pipeline_mod,
        "_normalize_image_bytes",
        fake_normalize_image_bytes,
        raising=False,
    )

    def fake_set_item_image_bytes(*_args, **kwargs):
        if kwargs.get("backdrop_index") == 1:
            return False
        return True

    jf_client.set_item_image_bytes.side_effect = fake_set_item_image_bytes

    ok = normalize_item_backdrops_api(
        item=item,
        settings_by_mode=settings_by_mode,
        jf_client=jf_client,
        dry_run=False,
        force_upload_noscale=False,
        make_backup=False,
        backup_root=tmp_path,
        backup_mode="partial",
    )

    assert ok is False
    staging_dir = tmp_path / "staging" / item.id
    assert staging_dir.exists()
    assert (staging_dir / "0.jpg").exists()
    assert (staging_dir / "1.jpg").exists()


def test_normalize_item_backdrops_api_staging_extension_failure_aborts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    fake_state: FakeState,
) -> None:
    item = DiscoveredItem(
        id="item-extfail",
        name="Ext Fail",
        type="Movie",
        parent_id=None,
        library_id=None,
        library_name=None,
        backdrop_count=1,
        image_types={"Backdrop"},
    )
    settings_by_mode = {"backdrop": cast(ModeRuntimeSettings, object())}
    monkeypatch.setattr(
        pipeline_mod,
        "IMAGE_TYPE_TO_MODE",
        {"Backdrop": "backdrop"},
        raising=False,
    )

    jf_client = Mock(spec=JellyfinClient)
    jf_client.get_item_image.return_value = (b"data", "image/unknown")

    def raise_ext(_ct):
        raise ValueError("cannot guess")

    monkeypatch.setattr(
        pipeline_mod,
        "guess_extension_from_content_type",
        raise_ext,
        raising=False,
    )

    ok = normalize_item_backdrops_api(
        item=item,
        settings_by_mode=settings_by_mode,
        jf_client=jf_client,
        dry_run=False,
        force_upload_noscale=False,
        make_backup=False,
        backup_root=tmp_path,
        backup_mode="partial",
    )

    assert ok is False
    assert len(fake_state.stats.errors) == 1
    assert not (tmp_path / "staging" / item.id).exists()


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
    assert pipeline_mod.state.stats.successes == 1


def test_process_single_item_backdrop_uses_backdrop_tags_from_item(rgb_image_bytes, tmp_path):
    class BackdropClient(StubClient):
        def __init__(self, image_bytes: bytes):
            super().__init__(image_bytes)
            self.image_indices: list[int | None] = []

        def get_item(self, item_id: str):
            return {
                "Name": "Demo",
                "Type": "Movie",
                "ParentId": None,
                "BackdropImageTags": ["a", "b"],
            }

        def get_item_image(
            self, item_id: str, image_type: str, index: int | None = None
        ):
            self.last_image_type = image_type
            self.image_indices.append(index)
            return self.image_bytes, "image/png"

    client = BackdropClient(rgb_image_bytes(size=(200, 100)))
    settings_by_mode = {
        "backdrop": ModeRuntimeSettings(
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
        mode="backdrop",
        settings_by_mode=settings_by_mode,
        jf_client=client,  # type: ignore[arg-type]
        dry_run=True,
        force_upload_noscale=False,
        make_backup=False,
        backup_root=tmp_path,
        backup_mode="partial",
    )

    assert ok is True
    assert client.last_image_type == "Backdrop"
    assert client.image_indices == [0, 1]
    assert pipeline_mod.state.stats.successes == 2


def test_single_item_counted_once_across_multiple_modes(rgb_image_bytes, tmp_path):
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
        ),
        "logo": ModeRuntimeSettings(
            target_width=100,
            target_height=50,
            allow_upscale=False,
            allow_downscale=True,
            jpeg_quality=85,
            webp_quality=80,
            no_padding=False,
        ),
    }

    ok_thumb = process_single_item_api(
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
    ok_logo = process_single_item_api(
        item_id="item123",
        mode="logo",
        settings_by_mode=settings_by_mode,
        jf_client=client,  # type: ignore[arg-type]
        dry_run=True,
        force_upload_noscale=False,
        make_backup=False,
        backup_root=tmp_path,
        backup_mode="partial",
    )

    assert ok_thumb is True
    assert ok_logo is True
    assert pipeline_mod.state.stats.processed == 1
    assert pipeline_mod.state.stats.images_found == 2
    assert pipeline_mod.state.stats.successes == 2
