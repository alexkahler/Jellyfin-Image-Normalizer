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
- Slice 10 -> WI-001 COV-01b Characterization runtime gate (warn ratchet, safety_contract scope)
- Slice 11 -> WI-001 COV-02 Backdrop workflow sequence governance gate (phase-1 warn ratchet, run|backdrop scope)
- Slice 12 -> WI-001 COV-03 Route-fence readiness semantics gate (claim-scoped runtime proof, no route flips)
- Slice 13 -> WI-001 COV-04 Backdrop trace contract (dual-proof, observed-vs-baseline)
- Slice 14 -> WI-001 COV-05 Blueprint topology drift guard (governance docs-topology contract)

Theme A iteration status (Governance Contract Posture Recovery):
- Slice 15 -> Theme A A-01 Imaging LOC closure (completed; commit `1813243`)
- Slice 16 -> Theme A A-02 Backup LOC closure (completed; commit `b1c6c29`)
- Slice 17 -> Theme A A-03 Medium-coupling closure slot 1 (`client.py`) (completed; commit `b496423`)
- Slice 18 -> Theme A A-04 Medium-coupling closure slot 2 (`config.py`) (completed; commit `3716216`)
- Slice 19 -> Theme A A-05 High-coupling closure slot 1 (`pipeline.py`) (blocked; split to `A-05a`/`A-05b` required before proceeding)
- Slice 20 -> Theme A A-05a Pipeline LOC closure split tranche 1 (`pipeline.py` backdrop seam extraction) (completed; commit `bba7dda`)
- Slice 21 -> Theme A A-05b Pipeline LOC closure split tranche 2 (`pipeline.py` blocker closure) (completed; commit `313c252`)
- Slice 22 -> Theme A A-06 High-coupling closure slot 2 (`cli.py`) (completed; commit `1cf1c70`)
- Slice 23 -> Theme A A-07 Residual blocker closure + GG-001 gate (completed; commit `<pending>`)

After Slice 9, subsequent slices remain iterative. Governance-coverage slices
(starting with COV-01b) take precedence before route-fence flip planning.
Route-fence flips must not be planned/executed until Slice 7 Surface Coverage Gate,
Slice 8 runtime route-fence enforcement, and Slice 9 collectability hardening are passing.

The WI numbers represent thematic areas, not execution order.
