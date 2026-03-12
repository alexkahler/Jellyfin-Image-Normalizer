# Route Fence

This table tracks command/mode strangler routing ownership and parity readiness.

Readiness semantics:
- `parity status` values are `pending|ready`.
- `ready` is machine-validated by governance checks against workflow/parity/runtime evidence.
- `route=v1` requires `parity status=ready`.

<!-- ROUTE_FENCE_TABLE_START -->
| command | mode | route(v0\|v1) | owner slice | parity status |
| --- | --- | --- | --- | --- |
| run | logo | v1 | Slice-72 | ready |
| run | thumb | v0 | Slice-73 | pending |
| run | backdrop | v1 | Slice-35 | ready |
| run | profile | v0 | Slice-74 | pending |
| restore | logo\|thumb\|backdrop\|profile | v0 | Slice-75 | pending |
| test_connection | n/a | v1 | Slice-39 | ready |
| config_init | n/a | v1 | Slice-57 | ready |
| config_validate | n/a | v1 | Slice-49 | ready |
<!-- ROUTE_FENCE_TABLE_END -->

