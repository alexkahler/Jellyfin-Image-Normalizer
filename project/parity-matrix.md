# Parity Matrix

This matrix tracks Track 1 behavior preservation decisions and test ownership.

| behavior_id | baseline_source | current_result | status | owner_test | approval_ref | notes | migration_note |
| --- | --- | --- | --- | --- | --- | --- | --- |
| CLI-RESTORE-001 | tests/test_jfin.py::test_validate_restore_all_args_blocks_operational_flags | matches-baseline | preserved | tests/test_jfin.py::test_validate_restore_all_args_blocks_operational_flags | n/a | Seeded in WI-002. | - |
| CLI-GENCFG-001 | tests/test_jfin.py::test_validate_generate_config_args_blocks_operational_flags | matches-baseline | preserved | tests/test_jfin.py::test_validate_generate_config_args_blocks_operational_flags | n/a | Seeded in WI-002. | - |
| CLI-TESTJF-001 | tests/test_jfin.py::test_validate_test_jf_args_blocks_operational_flags | matches-baseline | preserved | tests/test_jfin.py::test_validate_test_jf_args_blocks_operational_flags | n/a | Seeded in WI-002. | - |
| CLI-SINGLE-001 | tests/test_jfin.py::test_single_requires_explicit_mode | matches-baseline | preserved | tests/test_jfin.py::test_single_requires_explicit_mode | n/a | Seeded in WI-002. | - |
| CLI-OVERRIDE-001 | tests/test_jfin.py::test_warn_unused_cli_overrides_incompatible_flags | matches-baseline | preserved | tests/test_jfin.py::test_warn_unused_cli_overrides_incompatible_flags | n/a | Seeded in WI-002. | - |
| CLI-ASPECT-001 | tests/test_jfin.py::test_warn_unrecommended_aspect_ratios_warns_on_mismatch | matches-baseline | preserved | tests/test_jfin.py::test_warn_unrecommended_aspect_ratios_warns_on_mismatch | n/a | Seeded in WI-002. | - |
| CFG-TOML-001 | tests/test_config.py::test_load_config_from_path_rejects_non_toml | matches-baseline | preserved | tests/test_config.py::test_load_config_from_path_rejects_non_toml | n/a | Seeded in WI-002. | - |
| CFG-TOML-002 | tests/test_config.py::test_load_config_from_path_parses_toml_and_builds_mode | matches-baseline | preserved | tests/test_config.py::test_load_config_from_path_parses_toml_and_builds_mode | n/a | Seeded in WI-002. | - |
| CFG-TYPE-001 | tests/test_config.py::test_validate_config_types_rejects_invalid_types | matches-baseline | preserved | tests/test_config.py::test_validate_config_types_rejects_invalid_types | n/a | Seeded in WI-002. | - |
| CFG-CORE-001 | tests/test_config.py::test_validate_config_types_requires_core_fields | matches-baseline | preserved | tests/test_config.py::test_validate_config_types_requires_core_fields | n/a | Seeded in WI-002. | - |
| CFG-OPS-001 | tests/test_config.py::test_parse_operations_dedupes_and_orders | matches-baseline | preserved | tests/test_config.py::test_parse_operations_dedupes_and_orders | n/a | Seeded in WI-002. | - |
| CFG-DISC-001 | tests/test_config.py::test_build_discovery_settings_maps_modes_and_filters | matches-baseline | preserved | tests/test_config.py::test_build_discovery_settings_maps_modes_and_filters | n/a | Seeded in WI-002. | - |
| CFG-OVERRIDE-001 | tests/test_config.py::test_apply_cli_overrides_applies_target_size_per_mode | matches-baseline | preserved | tests/test_config.py::test_apply_cli_overrides_applies_target_size_per_mode | n/a | Seeded in WI-002. | - |
| API-QUERY-001 | tests/test_client.py::test_query_items_builds_expected_params | matches-baseline | preserved | tests/test_client.py::test_query_items_builds_expected_params | n/a | Seeded in WI-002. | - |
| API-WRITE-001 | tests/test_client.py::test_post_image_base64_payload | matches-baseline | preserved | tests/test_client.py::test_post_image_base64_payload | n/a | Seeded in WI-002. | - |
| API-DRYRUN-001 | tests/test_client.py::test_dry_run_blocks_post | matches-baseline | preserved | tests/test_client.py::test_dry_run_blocks_post | n/a | Seeded in WI-002. | - |
| API-DELETE-001 | tests/test_client.py::test_delete_image_parametrized | matches-baseline | preserved | tests/test_client.py::test_delete_image_parametrized | n/a | Seeded in WI-002. | - |
| API-GETIMG-001 | tests/test_client.py::test_get_item_image_returns_content_type | matches-baseline | preserved | tests/test_client.py::test_get_item_image_returns_content_type | n/a | Seeded in WI-002. | - |
| API-RETRY-001 | tests/test_client.py::test_get_retries_on_failure | matches-baseline | preserved | tests/test_client.py::test_get_retries_on_failure | n/a | Seeded in WI-002. | - |
| DISC-LIB-001 | tests/test_discovery.py::test_discover_libraries_filters_names | matches-baseline | preserved | tests/test_discovery.py::test_discover_libraries_filters_names | n/a | Seeded in WI-002. | - |
| DISC-LIB-002 | tests/test_discovery.py::test_discover_libraries_skips_unsupported_collection_types | matches-baseline | preserved | tests/test_discovery.py::test_discover_libraries_skips_unsupported_collection_types | n/a | Seeded in WI-002. | - |
| DISC-ITEM-001 | tests/test_discovery.py::test_discover_library_items_paginates | matches-baseline | preserved | tests/test_discovery.py::test_discover_library_items_paginates | n/a | Seeded in WI-002. | - |
| DISC-ITEM-002 | tests/test_discovery.py::test_discover_library_items_maps_image_types | matches-baseline | preserved | tests/test_discovery.py::test_discover_library_items_maps_image_types | n/a | Seeded in WI-002. | - |
| IMG-SCALE-001 | tests/test_imaging.py::test_make_scale_plan_upscale | matches-baseline | preserved | tests/test_imaging.py::test_make_scale_plan_upscale | n/a | Seeded in WI-002. | - |
| IMG-NOSCALE-001 | tests/test_imaging.py::test_handle_no_scale_dry_run_skips_upload | matches-baseline | preserved | tests/test_imaging.py::test_handle_no_scale_dry_run_skips_upload | n/a | Seeded in WI-002. | - |
| IMG-LOGO-001 | tests/test_imaging.py::test_remove_padding_from_logo_crops_transparent_border | matches-baseline | preserved | tests/test_imaging.py::test_remove_padding_from_logo_crops_transparent_border | n/a | Seeded in WI-002. | - |
| IMG-CROP-001 | tests/test_imaging.py::test_cover_and_crop_respects_target_size | matches-baseline | preserved | tests/test_imaging.py::test_cover_and_crop_respects_target_size | n/a | Seeded in WI-002. | - |
| IMG-ENCODE-001 | tests/test_imaging.py::test_encode_image_to_bytes_roundtrip | matches-baseline | preserved | tests/test_imaging.py::test_encode_image_to_bytes_roundtrip | n/a | Seeded in WI-002. | - |
| PIPE-DRYRUN-001 | tests/test_pipeline.py::test_normalize_item_image_api_dry_run_skips_upload | matches-baseline | preserved | tests/test_pipeline.py::test_normalize_item_image_api_dry_run_skips_upload | n/a | Seeded in WI-002. | - |
| PIPE-BACKUP-001 | tests/test_pipeline.py::test_partial_backup_skips_no_scale | matches-baseline | preserved | tests/test_pipeline.py::test_partial_backup_skips_no_scale | n/a | Seeded in WI-002. | - |
| PIPE-BACKDROP-001 | tests/test_pipeline.py::test_normalize_item_backdrops_api_scenarios | matches-baseline | preserved | tests/test_pipeline.py::test_normalize_item_backdrops_api_scenarios | n/a | Seeded in WI-002. | - |
| PIPE-SINGLE-001 | tests/test_pipeline.py::test_process_single_item_uses_direct_item_id | matches-baseline | preserved | tests/test_pipeline.py::test_process_single_item_uses_direct_item_id | n/a | Seeded in WI-002. | - |
| PIPE-COUNT-001 | tests/test_pipeline.py::test_single_item_counted_once_across_multiple_modes | matches-baseline | preserved | tests/test_pipeline.py::test_single_item_counted_once_across_multiple_modes | n/a | Seeded in WI-002. | - |
| BKP-MODE-001 | tests/test_backup.py::test_should_backup_for_plan_modes | matches-baseline | preserved | tests/test_backup.py::test_should_backup_for_plan_modes | n/a | Seeded in WI-002. | - |
| BKP-PATH-001 | tests/test_backup.py::test_backup_path_for_image | matches-baseline | preserved | tests/test_backup.py::test_backup_path_for_image | n/a | Seeded in WI-002. | - |
| RST-BULK-001 | tests/test_backup.py::test_restore_from_backups_scenarios | matches-baseline | preserved | tests/test_backup.py::test_restore_from_backups_scenarios | n/a | Seeded in WI-002. | - |
| RST-SINGLE-001 | tests/test_backup.py::test_restore_single_from_backup_scenarios | matches-baseline | preserved | tests/test_backup.py::test_restore_single_from_backup_scenarios | n/a | Seeded in WI-002. | - |
