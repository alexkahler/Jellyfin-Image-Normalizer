Here’s the updated report with your fixes integrated **in-place**, keeping content, eliminating contradictions, and avoiding duplication. I only added what’s necessary to address the five issues + the three "small edits," while preserving your structure.

---

# Governance Coverage Roadmap Report (Track-1)

Date: 2026-03-05
Scope: v0→v1 migration governance coverages (report-only; no route flips)

## 1) Evidence Snapshot (Current Repo State)

Command evidence gathered on 2026-03-05:

1. `PYTHONPATH=src .\.venv\Scripts\python.exe project/scripts/verify_governance.py --check parity` → **PASS**
2. `PYTHONPATH=src .\.venv\Scripts\python.exe project/scripts/verify_governance.py --check characterization` → **PASS** (`unmapped_* = 0`, `parity_test_linkage_gaps = 0`)
3. `PYTHONPATH=src .\.venv\Scripts\python.exe project/scripts/verify_governance.py --check all` → **FAIL** (LOC blocker in `src/jfin/*`)
4. `PYTHONPATH=src .\.venv\Scripts\python.exe -m pytest` → **FAIL** (`9 failed, 282 passed`), concentrated in characterization message-collection assertions

Primary audit linkage source: `project/v1-slices-reports/v1-unknown-unknowns-audit-2026-03-05.md` (UU-001..UU-006).

> **Evidence citation style for this report:** repo-relative file references + section context. No absolute OS paths and no `#L` anchors (line numbers may be mentioned informally as context but not used as hard links).

---

## 2) Current-State Coverage Assessment

### Coverage 1: Workflow sequence coverage gate

Status: **Partially exists**

Evidence present:

* Required intent exists in `project/v1-plan.md` (Backdrop transaction acceptance; Track-1 parity requirements).
* Parity ownership exists for backdrop flow in `project/parity-matrix.md` (`PIPE-BACKDROP-001`).
* Baseline exists in `tests/characterization/baselines/safety_contract_baseline.json`.
* Deep sequence assertions exist, but only in non-parity unit tests (`tests/test_pipeline.py` includes multiple backdrop transaction assertions).

Gap:

* Parity-owned characterization currently captures **counts + coarse ordering token**, not full transaction protocol invariants.

Audit mapping:

* UU-003, UU-006.

**Explicit artifact decision (to prevent ambiguity):**
Workflow-sequence coverage will be implemented via **both**:

1. **An explicit per-cell workflow coverage index**: `project/workflow-coverage-index.json` (new)
2. **Schema support for protocol traces** where scalar maps/token lists are insufficient (safety/characterization schema + baseline updates)

**Uniqueness / non-duplication contract (to prevent drift):**

* `project/workflow-coverage-index.json` uniquely owns:
  **route-fence cell → required parity IDs + required characterization suites (nodeids or suite paths) + optional required observability items**.
* It must **not** duplicate surface coverage mappings (CLI/config token inventory remains solely in `project/surface-coverage-index.json`), and it must **not** replace parity ownership (still in `project/parity-matrix.md`).

---

### Coverage 2: Flip readiness coverage (route-fence semantic gating)

Status: **Partially exists**

Evidence present:

* Route-fence artifacts exist and are synchronized: `project/route-fence.md`, `project/route-fence.json`.
* Runtime fail-closed dispatch exists: `src/jfin/cli.py`, `src/jfin/route_fence.py`.
* Governance checks enforce schema/sync: `project/scripts/parity_checks.py`.

Gap:

* `parity_status` is shape-validated, but **not semantically validated** against parity evidence.

Audit mapping:

* UU-004.

---

### Coverage 3: Characterization reliability coverage (drift + collectability + completeness)

Status: **Partially exists**

Evidence present:

* Characterization artifact/linkage checks exist: `project/scripts/characterization_checks.py`.
* Surface completeness counters exist: `project/scripts/surface_coverage_checks.py`.
* Governance output reports counters: `project/scripts/governance_checks.py`.

Gaps:

* Collectability/runtime reliability is **not** a governance gate; linkage can pass while full characterization execution still fails.
* Full pytest failures show message-capture drift in characterization harness/test paths.
* Doc topology drift remains in blueprint paths (`project/v1-plan.md` vs canonical notes in `docs/TECHNICAL_NOTES.md`).

Audit mapping:

* UU-001, UU-005.

**Clarification (to avoid "green while wrong" confusion):**

* Today `verify_governance --check characterization` is a **linkage/surface completeness gate**, not a runtime equivalence gate.

**Split into two sub-controls (design requirement):**

* **3a) Collectability/linkage control**: nodeids exist, collect-only works, and suites are included in `project/verification-contract.yml`.
* **3b) Runtime signal control**: a small, named subset of high-risk characterization suites must execute green in CI and be surfaced explicitly by governance.

---

### Coverage 4: Schema expressiveness coverage (protocol/trace invariants)

Status: **Partially exists**

Evidence present:

* Safety baseline schema validation exists: `project/scripts/characterization_contract.py`.

Gap:

* Safety schema constrains observations to scalar mappings and tokenized ordering, limiting direct encoding of structured transaction traces.

Audit mapping:

* UU-006, UU-003.

---

## 3) Closure Rules and Prevented Failure Modes

1. **Workflow sequence gate closure rule**
   `PIPE-BACKDROP-001` may be marked **preserved** only if parity-owned characterization asserts (at minimum): fetch order, source-index normalization, delete-by-index-0 semantics, 404 verification, dense upload index order, and failure retention.
   Failure mode prevented: backdrop protocol regressions that still satisfy count-only assertions.

2. **Flip readiness closure rule**
   No route-fence row may be marked readiness-complete or flipped to `route=v1` unless machine checks prove mapped parity IDs are preserved / match baselines with valid owner tests and required runtime characterization suites passing for that specific cell.
   Failure mode prevented: manual readiness overclaims that bypass parity evidence.

3. **Characterization reliability closure rule**
   Characterization is "reliable" only when linkage checks pass **and** designated characterization suites execute and pass under governance/CI (not just collectable).
   Failure mode prevented: green metadata with drifting, flaky, or failing characterization behavior.

4. **Schema expressiveness closure rule**
   Safety contracts must support structured trace assertions for transactional flows, not only scalar objects or token lists.
   Failure mode prevented: critical protocol invariants that cannot be represented or gated.

---

## 4) Prioritized Slice Candidates (Risk-First)

Note: No candidate below flips route rows to `v1`.
Prerequisite context only (not a roadmap slice): UU-002 LOC blocker in `src/jfin/*`.

> **Global slice constraint (applies to every COV item below):**
> **This change must be green on current HEAD (except known LOC), or introduced via a warn→block ratchet** so we do not accumulate new persistent governance failures on top of the known LOC baseline.

---

### COV-01a — Characterization Collectability Hardening (UU-001)

Objective:

* Restore deterministic message collection and ensure characterization references are collectable and contract-listed.
* Tighten wording: **upgrade characterization governance from linkage-only to linkage+collectability** (runtime execution is handled in COV-01b).

Files/artifacts to touch:

* `tests/characterization/_harness.py`
* `project/scripts/governance_checks.py`
* `project/verification-contract.yml`
* Plus:

  * `tests/characterization/safety_contract/test_safety_contract_api.py`
  * `tests/characterization/safety_contract/test_safety_contract_restore.py`
  * `tests/test_governance_checks.py`

New/updated checks (governance + CI):

* Tighten collectability/linkage checks: nodeid existence + `pytest --collect-only` resolution + verification-contract inclusion.
* Ensure governance surfaces collectability failures deterministically (so `--check characterization` / `--check all` expose the issue as a clear gate).

Tests/baselines to strengthen:

* Harness tests to assert stable message collection source/path.
* Normalization rules documented if re-baselining is required.

Acceptance criteria:

* Current 9 failing characterization tests pass **OR** are re-baselined with explicitly documented normalization changes.
* Governance output includes an explicit "collectability/linkage OK" signal.
* `verify_governance --check characterization` and `--check all` surface collectability failures deterministically.

Dependencies:

* None.

---

### COV-01b — Characterization Runtime Gate (UU-001 / UU-005)

Objective:

* Add a CI-enforced runtime characterization signal for high-risk parity items (beyond collectability/linkage).

Files/artifacts to touch:

* `project/scripts/characterization_checks.py` and/or `project/scripts/governance_checks.py`
* `project/verification-contract.yml`

New/updated checks (governance + CI):

* Add a runtime characterization subcheck (targeted owner suites) and include it in `--check all`.
* Keep CI invocation unchanged (`verify_governance.py --check all`), but with expanded enforcement behavior.

**Runtime budget / scoping rule (to preserve the <10 min policy):**

* The runtime gate must be a **tiny explicit allowlist**, e.g.:

  * a single suite folder like `tests/characterization/safety_contract/`, or
  * an explicit list of nodeids owned by safety-critical parity IDs.
* The slice must record the expected runtime and ratchet scope only after it consistently fits the Track-1 verification budget.

Tests/baselines to add or strengthen:

* Governance wiring tests that the runtime gate runs, reports pass/fail, and fails deterministically when suites fail.

Acceptance criteria:

* Governance output includes explicit pass/fail for runtime characterization execution.
* Failures are actionable and tied to parity IDs / named suites.
* Runtime gate stays within the Track-1 verification budget (or is split further).

Dependencies:

* COV-01a.

---

### COV-02 — Backdrop Workflow Sequence Governance Gate (UU-003)

Objective:

* Promote high-value backdrop sequencing invariants from unit-only coverage into parity-owned characterization governance.

Files/artifacts to touch:

* `project/workflow-coverage-index.json` (new; per-cell requirements)
* `tests/characterization/baselines/safety_contract_baseline.json`
* `tests/characterization/safety_contract/test_safety_contract_pipeline.py`
* `project/scripts/characterization_checks.py`
* `tests/test_characterization_checks_safety.py`

New/updated checks (governance + CI):

* Add explicit governance validation that `PIPE-BACKDROP-001` encodes required sequence evidence fields.
* Use workflow-coverage index to require that `run|backdrop` cell includes sequence parity IDs + required tests.

Tests/baselines to add or strengthen (parity-owned characterization evidence):

* fetch index order
* normalize source-index mapping
* post-delete 404 verification
* dense upload indices preserving order
* delete-before-upload ordering
* staging retention on partial upload failure

Acceptance criteria:

* Any regression in these sequence invariants fails **parity-owned characterization** checks.
* `PIPE-BACKDROP-001` cannot pass governance with count-only evidence.

Dependencies:

* COV-01a (and ideally COV-01b).

---

### COV-03 — Route-Fence Semantic Readiness Gate (UU-004)

Objective:

* Enforce route readiness semantics against parity evidence instead of free-text `parity_status`.

**Important note (to avoid "no flips" ambiguity):**

* This is **metadata semantics hardening**. It does not flip routes, but it *does* change what "ready" means and can block/enable future flips.

Files/artifacts to touch:

* `project/scripts/parity_contract.py`
* `project/scripts/parity_checks.py`
* `tests/test_parity_checks.py`
* `project/route-fence.md` (documentation semantics only; no route value flips)
* (If introduced by COV-02) `project/workflow-coverage-index.json`

New/updated checks (governance + CI):

* Add semantic readiness validator mapping route rows to parity IDs/owner-test evidence.
* Require machine-verifiable parity proof for readiness-complete states.

Tests/baselines to add or strengthen:

* Negative tests for readiness overclaim, missing parity evidence, mismatched owner linkage.

Acceptance criteria:

* Readiness overclaims fail `verify_governance --check parity` (or an explicit new readiness check).
* No route row changes to `v1` in this slice.

Dependencies:

* COV-01a.

---

### COV-04 — Safety Schema Expressiveness Upgrade (UU-006)

Objective:

* Extend safety characterization schema so transactional protocol traces are representable and enforceable.

Files/artifacts to touch:

* `project/scripts/characterization_contract.py`
* `project/scripts/characterization_checks.py`
* `tests/test_characterization_checks_safety.py`
* `tests/characterization/baselines/safety_contract_baseline.json`

New/updated checks (governance + CI):

* Validate structured safety trace objects (phase/index/action/result semantics).
* Maintain backward compatibility policy while ratcheting required expressiveness for safety-critical rows.

Tests/baselines to add or strengthen:

* Schema-positive and schema-negative tests for trace payloads.
* Migrate `PIPE-BACKDROP-001` baseline representation to structured trace assertions.

Acceptance criteria:

* Structured trace invariants are validated in governance checks.
* Protocol invariants are no longer limited to scalar maps/token lists.

Dependencies:

* COV-02.

---

### COV-05 — Blueprint Topology Drift Guard (UU-005)

Objective:

* Align blueprint documentation with canonical characterization suite layout and prevent future drift.

Files/artifacts to touch:

* `project/v1-plan.md`
* `docs/TECHNICAL_NOTES.md`
* `project/scripts/governance_checks.py` (or characterization check layer)
* `tests/test_governance_checks.py` (or characterization-governance tests)

New/updated checks (governance + CI):

* Add lightweight doc-contract check for canonical characterization suite topology references.

  * No doc-grepping required: implement as a small "must-exist path list" / canonical-path assertion in governance.

Tests/baselines to add or strengthen:

* Governance test that fails when blueprint paths diverge from canonical suite locations.

Acceptance criteria:

* `project/v1-plan.md` and `docs/TECHNICAL_NOTES.md` agree on suite topology.
* Path drift is CI-detectable.

Dependencies:

* None.

---

## 5) Backstop Blind-Spot List (Beyond the Four Required Coverages)

Each item includes capture pattern: parity IDs + tests + gates, mapped to existing UU items.
This list is **required** and includes **≥ 5 items**.

1. Deprecated key compatibility drift (extends UU-005)

* Capture via new `CFG-DEPRECATED-*` parity IDs, config characterization cases in `tests/characterization/config_contract/`, and required-ID enforcement in `project/scripts/characterization_contract.py` + `characterization_checks.py`.

2. Restore edge-cases when Jellyfin UUIDs change (extends UU-003, UU-006)

* Capture via `RST-UUIDMAP-*` parity IDs, restore safety characterization additions in `tests/characterization/safety_contract/test_safety_contract_restore.py`, and structured trace assertions in safety baseline schema.

3. Dual write-gate enforcement across all write paths (extends UU-001, UU-003)

* Capture via expanded `API-DRYRUN-*`/`PIPE-DRYRUN-*` parity IDs, added characterization API/pipeline tests, and runtime characterization gate inclusion in `verify_governance --check all`.

4. Log/summary semantics and message-channel stability (extends UU-001)

* Capture via `OBS-SUMLOG-*` parity IDs, observability characterization baselines, and collectability checks that assert expected messages are harvestable from the active logging path.

5. Route-table runtime-gating completeness (extends UU-004)

* Capture via parity/governance rule that each route-fence row must map to runtime-gated entrypoints or an explicit non-runtime exemption, verified in route-fence parity tests and runtime route tests.

6. Backup/restore caveat enforcement for UUID remap limitations (extends UU-003, UU-005)

* Capture via dedicated parity ID(s) for restore caveat messaging, characterization assertion of user-visible warning semantics, and docs-contract checks to keep caveat text synchronized.

---

## 6) Recommended Execution Order

Risk-first order:

1. COV-01a
2. COV-01b
3. COV-02
4. COV-03
5. COV-04
6. COV-05

Rationale:

* First restore reliable characterization signal collection (collectability/linkage).
* Then add a deterministic runtime characterization gate (scoped to budget).
* Then close backdrop transaction unknown-unknowns.
* Then harden flip readiness semantics (metadata semantics hardening).
* Then improve schema expressiveness supporting richer invariants.
* Finally lock documentation topology to prevent planning drift.

---

## Public Interface/Type Changes Expected Across Roadmap

1. Route-fence artifact semantics will gain machine-checkable readiness linkage fields or equivalent normalized metadata contract.
2. Workflow coverage will gain a per-cell requirements artifact: `project/workflow-coverage-index.json`.
3. Safety characterization schema will gain structured trace shape for transactional invariants.
4. Governance check surface will gain:

* collectability/linkage enforcement,
* runtime characterization execution gate (budget-scoped),
* docs-topology drift check.

---

## Test Plan for the Roadmap Work

1. Targeted gates per slice first, then full contract:
   `verify_governance --check parity`, `--check characterization`, linkage+collectability checks, runtime characterization gate, then `--check all`.
2. Full verification contract command set remains final acceptance.
3. No route row may be set to `v1` in any roadmap slice.

---

## Definition of Done (for this Report)

The Governance Coverage Roadmap Report is considered complete only when it contains:

1. A coverage matrix (coverage → exists/partial/missing → evidence).
2. Closure rules (gate phrasing) for each coverage.
3. A slice-candidate roadmap with acceptance criteria and dependencies.
4. A mapping table: **UU → coverage gap → closure rule → slice candidate(s)**.
5. A required backstop blind-spot list with **≥ 5 items**.

---

## Assumptions and Defaults

1. Prioritization is **risk-first**.
2. UU-002 LOC blocker is tracked as **prerequisite context only**, not a roadmap slice here.
3. Scope is governance-coverage roadmap/reporting only; no implementation of route flips.
4. Existing audit (`UU-001..UU-006`) is authoritative risk register baseline for this report.
