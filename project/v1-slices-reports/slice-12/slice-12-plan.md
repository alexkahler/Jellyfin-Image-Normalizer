## Slice 12 Plan (Final): COV-03 Readiness Semantics With Claim-Scoped Runtime Proof

### Summary
1. Keep COV-03 as metadata semantics hardening only: no route flips, no route-table column expansion.
2. Enforce `parity status` as `pending|ready` and make readiness claims machine-validated from workflow + parity evidence.
3. Keep runtime-target authority in `project/verification-contract.yml`; readiness consumes runtime results per claim (cell-scoped), not globally.

### Interface/Contract Changes
1. Route-fence semantics:
   - `parity status` enum: `pending|ready` (markdown + JSON validation).
   - Readiness claim predicate: row is claimed-ready if `parity status=ready` or `route=v1`.
   - Consistency rule: `route=v1` requires `parity status=ready`.
2. Workflow index remains linkage-only (`project/workflow-coverage-index.json`):
   - no `required_runtime_targets` addition.
   - existing `required_parity_ids`, `required_owner_tests`, and `future_split_debt.readiness_blocking` stay canonical.
3. Baseline-linked rule is concrete for readiness:
   - required parity row exists, `status=preserved`, `current_result=matches-baseline`, and `baseline_source` resolves to existing baseline case.
4. Owner-linkage rule is subset-based (not set-equality):
   - workflow required owner tests must resolve and be represented by parity-owner evidence for required parity IDs.

### Implementation Changes
1. Add readiness semantic validation in governance/parity checks (including `project/route-fence.json` sync path):
   - block unmapped `ready` claims (`command|mode` not in workflow index),
   - block open readiness debt (`readiness_blocking=true` and debt not `closed`),
   - block parity/owner/baseline linkage failures with deterministic readiness error taxonomy.
2. Runtime overlay is explicitly claim-scoped:
   - derive claim targets from `characterization_runtime_gate_targets` that cover that claim’s owner-test paths,
   - require all claim parity IDs to appear in runtime mapped parity IDs,
   - fail claim only on runtime diagnostics intersecting claim targets,
   - ignore runtime diagnostics for unrelated targets/cells.
3. Add minimal structured runtime diagnostics (internal reporting object) so readiness can filter runtime failures by target without parsing free text.
4. Keep Slice-10 behavior unchanged:
   - characterization runtime gate remains warn-ratchet globally,
   - only readiness claims become blocking when their own runtime proof is insufficient.

### Test Plan
1. Add readiness tests for:
   - invalid status token, `route=v1` without `ready`, unmapped `ready`,
   - missing parity IDs, non-preserved parity, invalid baseline link,
   - owner-test linkage subset failure, readiness-blocking debt open,
   - positive ready path with full linkage proof.
2. Add claim-scoped runtime overlay tests:
   - unrelated runtime warning does not fail claim,
   - claim-target runtime failure fails claim,
   - missing runtime mapping for claim parity IDs fails claim.
3. Verification order:
   - targeted pytest for readiness/parity/governance tests,
   - `verify_governance.py --check parity`,
   - `verify_governance.py --check all`,
   - full verification command set as defined by `project/verification-contract.yml` (CI authority).

### Rollback and Assumptions
1. Rollback:
   - remove readiness semantic enforcement and runtime-overlay wiring,
   - restore prior parity-status permissiveness and remove readiness taxonomy assertions.
2. Assumptions:
   - workflow coverage in Slice 12 remains `run|backdrop` scoped; all other rows must stay `pending`,
   - no route-row `v1` changes are made in this slice.
