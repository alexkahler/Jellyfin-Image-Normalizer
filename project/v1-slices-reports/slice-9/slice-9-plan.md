## Slice 9: COV-01a Characterization Collectability Hardening

### Summary
1. Strengthen characterization governance from linkage-only to linkage+collectability for parity-owned characterization rows.
2. Fix deterministic message capture for the known 9 failing characterization tests.
3. Keep scope to governance/testing hardening only: no route flips, no runtime behavior changes.

### Key Changes
1. **Collectability gate scope and rule**
   - Scope is **only parity-owned characterization `owner_test` references** (`tests/characterization/*` rows already required by parity linkage).
   - Remove allowlist behavior entirely; any unresolved `owner_test` collectability is a blocking governance error.
   - Collectability is defined as: nodeid resolves under repo-root invocation with pinned context:  
     `PYTHONPATH=src ./.venv/bin/python -m pytest --collect-only -q <nodeid>`.

2. **Deterministic governance failure taxonomy + output**
   - Emit stable, per-behavior failure classes (invalid owner ref, missing file, missing symbol, collect-only unresolved).
   - Add explicit success signal in governance output: `collectability/linkage OK`.
   - Make this signal and failure formatting test-enforced in governance tests so it cannot regress silently.

3. **Message capture hardening (root cause for current 9 fails)**
   - Add a scoped harness collector (fixture/context-managed lifecycle) that captures intended logger records deterministically.
   - Enforce isolation: install/uninstall per test, no global handler leakage, logger filtering only for intended sources.
   - Use this collector in CLI/safety characterization tests that assert expected messages.

4. **Normalization + targeted rebaseline discipline (explicit requirement)**
   - Document normalization policy (what is normalized vs not normalized).
   - Allow rebaseline only for directly affected characterization baselines (CLI/safety), with explicit rationale.
   - Require deterministic diff summary of changed expected message tokens in slice report/PR notes.
   - Add a precision regression test (negative control) so tokenization does not become overly permissive.

5. **Contract surface**
   - **No schema expansion of `project/verification-contract.yml`** in Slice 9.
   - CI/governance command surface remains unchanged; behavior is tightened inside existing characterization governance checks.

### Public Interface Impact
1. No runtime CLI/API interface changes.
2. Governance output surface changes: explicit collectability/linkage signal and deterministic collectability error classes.

### Test Plan
1. Targeted characterization tests covering current failing CLI/safety message assertions.
2. New/updated characterization-governance unit tests for collectability pass/fail classes.
3. Governance output tests asserting explicit `collectability/linkage OK` signal.
4. Full verification checks:
   - `PYTHONPATH=src ./.venv/bin/python -m pytest`
   - `./.venv/bin/python project/scripts/verify_governance.py --check characterization`
   - `./.venv/bin/python project/scripts/verify_governance.py --check all`  
   Expected: no new persistent failures beyond known pre-existing LOC blockers.

### Assumptions and Defaults
1. Canonical ID is `COV-01a`.
2. Collectability is parity-owner-nodeid based (not runtime suite execution; runtime gate remains COV-01b).
3. Targeted rebaseline is allowed but tightly constrained and documented.
4. Runtime code changes are out of scope unless a minimal testability fix is required and behavior-preserving.
