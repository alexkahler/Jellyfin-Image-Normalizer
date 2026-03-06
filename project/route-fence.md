# Route Fence

This table tracks command/mode strangler routing ownership and parity readiness.

Readiness semantics:
- `parity status` values are `pending|ready`.
- `ready` is machine-validated by governance checks against workflow/parity/runtime evidence.
- `route=v1` requires `parity status=ready`.

<!-- ROUTE_FENCE_TABLE_START -->
| command | mode | route(v0\|v1) | owner slice | parity status |
| --- | --- | --- | --- | --- |
| run | logo | v0 | WI-00X | pending |
| run | thumb | v0 | WI-00X | pending |
| run | backdrop | v0 | WI-00X | pending |
| run | profile | v0 | WI-00X | pending |
| restore | logo\|thumb\|backdrop\|profile | v0 | WI-00X | pending |
| test_connection | n/a | v0 | WI-00X | pending |
| config_init | n/a | v0 | WI-00X | pending |
| config_validate | n/a | v0 | WI-00X | pending |
<!-- ROUTE_FENCE_TABLE_END -->
