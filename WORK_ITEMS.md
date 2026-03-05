# WORK_ITEMS.md

Execution order (Track 1 slices):
- Slice 1 -> WI-001 Governance scaffolding
- Slice 2 -> WI-002 Parity matrix + behavior inventory
- Slice 3 -> WI-004 CLI/config characterization
- Slice 4 -> WI-003 Imaging characterization + goldens
- Slice 5 -> WI-001 Architecture guard tests (governance extension)
- Slice 6 -> WI-005 Dry-run/write-gate + restore-safety contracts

Iteratively planned slices:
- Slice 7 -> WI-001 Surface Coverage Gate (touches WI-002/WI-004 artifacts)
- Slice 8 -> WI-002 Route-fence runtime enforcement (touches WI-001 governance artifacts)
- Slice 9 -> WI-001 COV-01a Characterization collectability hardening (touches WI-004/WI-005 artifacts)

After Slice 9, subsequent slices remain iterative. Governance-coverage slices
(starting with COV-01b) take precedence before route-fence flip planning.
Route-fence flips must not be planned/executed until Slice 7 Surface Coverage Gate,
Slice 8 runtime route-fence enforcement, and Slice 9 collectability hardening are passing.

The WI numbers represent thematic areas, not execution order.
