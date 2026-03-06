## Slice 13: COV-04 Backdrop Trace Contract (Dual-Proof, Observed-vs-Baseline)

### Summary
1. Scope remains `run|backdrop` / `PIPE-BACKDROP-001` only.
2. COV-04 adds a new blocking structured-trace contract for the migrated row, while Slice 11 legacy sequence checks remain active and `warn`.
3. Readiness semantics from Slice 12 remain unchanged; this slice only strengthens characterization evidence depth.
4. Truth direction is explicit: observed characterization output is validated against baseline trace expectations.

### Contract Changes
1. Add optional `expected_observations.trace` for safety rows, with required `trace.events` when present.
2. Event schema for each trace entry:
   - required keys: `phase`, `index`, `action`, `result`, `details`
   - `phase` enum: `fetch|normalize|delete|verify|upload|finalize`
   - `index`: non-negative int or `null`
   - `action` and `result`: non-empty strings
   - `details`: object with phase-specific required keys:
     - `fetch`: `source_index`
     - `normalize`: `source_index`, `target_index`
     - `delete`: `target_index`
     - `verify`: `target_index`, `status_code`
     - `upload`: `source_index`, `target_index`
     - `finalize`: `retained`, `failure_kind`
3. Backward-compat policy:
   - trace optional for all safety rows repo-wide in Slice 13.
   - if trace exists on any safety row, schema-validity is blocking (intentional global hygiene tightening).
   - only `PIPE-BACKDROP-001` must include trace and must satisfy blocking trace invariants.
4. Remove semantic duplication risk:
   - no separate baseline `trace.assertions` object in this slice.
   - expected invariants are derived from baseline `trace.events`, and compared against observed trace-derived invariants.

### Implementation Changes
1. Schema/governance core:
   - update `characterization_contract` safety schema for `trace.events` + phase-specific `details`.
   - update `characterization_checks` with new blocking taxonomy:
     - `workflow_coverage.contract_trace_missing`
     - `workflow_coverage.contract_trace_schema`
     - `workflow_coverage.contract_trace_assertion_failed`
   - keep existing COV-02 legacy sequence diagnostics/taxonomy/severity unchanged.
2. Evidence comparison model:
   - add deterministic normalization/projection function for backdrop trace invariants:
     - fetch source indices dense ordered
     - normalize source->target mapping
     - post-delete verify status (404) on index 0 semantics
     - upload target indices dense ordered
     - repeated delete-target index 0 semantics
     - delete-before-upload ordering
     - staging retained on partial upload failure
   - compare `projection(observed_trace_events)` exactly to `projection(expected_baseline_trace_events)` for `PIPE-BACKDROP-001`.
3. Characterization/baseline updates:
   - migrate `PIPE-BACKDROP-001` in safety baseline to structured trace events.
   - update backdrop characterization test to emit observed trace events from actual mocked flow and enforce exact projection equality against baseline.
   - keep legacy `calls`/`ordering` evidence in place for temporary dual-proof compatibility.
4. Reporting scope (explicitly in-scope):
   - update `governance_checks` output with trace-contract status/counters.
   - add/update governance output tests accordingly.
5. Scope control:
   - keep shared default fixture payloads legacy-compatible.
   - use backdrop-specific or opt-in helpers for trace payload generation.
   - adding a dedicated trace-focused test module is intentional and documented as a bounded deviation from the original minimal file list.

### Test Plan
1. Add/strengthen tests for:
   - missing trace on `PIPE-BACKDROP-001` -> blocking failure.
   - malformed trace on backdrop -> blocking schema failure.
   - malformed optional trace on non-migrated safety row -> blocking schema failure.
   - absent trace on non-migrated safety rows -> allowed.
   - trace invariant mismatch on backdrop -> `contract_trace_assertion_failed`.
   - valid backdrop trace + unchanged legacy evidence -> pass.
2. Verification commands:
   - targeted pytest for trace schema/check/reporting + backdrop characterization tests first.
   - `verify_governance --check characterization`
   - `verify_governance --check readiness`
   - `verify_governance --check parity`
   - `verify_governance --check all`
   - full verification-contract command set for regression visibility.
3. Baseline expectations (as of March 6, 2026):
   - `pytest -q` currently passes (`339 passed`).
   - `ruff format --check .` currently fails on `tests/test_characterization_checks_safety.py`.
   - `verify_governance --check all` currently fails on pre-existing `src/jfin/*` LOC blockers and existing test LOC warnings.
   - Slice 13 acceptance requires no new persistent failures beyond this baseline profile.

### Assumptions and Defaults
1. `COV-02` dependency remains satisfied; workflow mapping scope stays `run|backdrop` only.
2. Slice 13 does not change route-fence readiness logic or route values.
3. Default chosen to avoid self-consistency-only validation: observed-vs-baseline comparison is the enforcement source, not baseline-internal trace coherence alone.
