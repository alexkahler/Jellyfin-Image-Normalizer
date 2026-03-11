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
- Slice 23 -> Theme A A-07 Residual blocker closure + GG-001 gate (completed; commit `db7bf05`)
- Slice 24 -> Theme A A-08 Same-SHA CI proof + GG-008 gate (blocked; same-SHA CI run `22809696578` for `7e837f9` has required job `quality` failure on 2026-03-08)
- Slice 25 -> Theme A A-08 quality remediation attempt (superseded/noncompliant historical work; relied on LOC-evasion tactics)
- Slice 26 -> Theme A anti-evasion governance codification + honest LOC rebaseline (conditionally compliant; Theme A and A-08 remain open; next: Slice 27 anti-evasion enforcement parity)
- Slice 27 -> Theme A anti-evasion enforcement parity in governance checks (completed; fail-closed `loc/all` enforcement active; next: Slice 28 config tranche remediation)
- Slice 28 -> Runtime evasion remediation tranche 1 (config pair) (completed; commit `7514668`)
- Slice 29a -> Runtime evasion remediation tranche 2a (`client_http` first, decomposed) (completed; commit `5572ff2`)
- Slice 29b -> Runtime evasion remediation tranche 2b (`client.py`) (completed; commit `7e35f1e`)
- Slice 30 -> Runtime evasion remediation tranche 3 (CLI pair) historical blocked-state capture (committed evidence only; commit `500a3cd`)
- Slice 30a -> Runtime evasion remediation tranche 3a (`cli.py` first, decomposed) (completed; commit `ec9edba`)
- Slice 30b -> Runtime evasion remediation tranche 3b (`cli_runtime.py`) (completed; commit `7fc7db7`)
- Slice 31 -> Pipeline evasion remediation tranche 3c (`pipeline.py` first) (completed; commit `fdcd44c`)
- Slice 32 -> Pipeline evasion remediation tranche 3d (`pipeline_backdrops.py`) (completed; commit `68e5b0d`)
- Slice 33 -> A-08 same-SHA CI proof + Theme A closure gate (completed; commit `c77a57b`; run `22826331766` for SHA `c77a57bccf24d70fcf5b9a1784f3075ab8dd01c7` has required jobs `test/security/quality/governance` all successful; GG-001 closed; GG-008 closed; Theme A closed)

Theme B iteration status (Workflow Readiness Baseline Unblock):
- Slice 34 -> Theme B unblock: close `run|backdrop` readiness debt contract (completed; commit `3c37c44`; `DEBT-BACKDROP-ID-SPLIT-001` closed; GG-004 blocking portion closed; Theme B closed; next: Theme C1 route-fence ownership accountability for `run|backdrop`)

Theme C iteration status (Route-Readiness Activation and Accountability):
- Slice 35 -> Theme C1 route-fence ownership accountability for `run|backdrop` (completed; canonical owner claim `WI-00X -> Slice-35`; claimed-ready placeholder ownership now machine-blocked; Theme C remains open; next: Slice 36 Theme C2 canonical first-claim activation)
- Slice 36 -> Theme C2 canonical first-claim activation on `run|backdrop` (completed; canonical readiness now non-vacuous `claimed_rows=1`, `validated_rows=1`; `route` preserved at `v0`; Theme C closed; next gate: Theme D only if explicitly authorized)

Theme D iteration status (Workflow Readiness Coverage Expansion, post-activation):
- Slice 37 -> Theme D minimal second-cell workflow-readiness coverage expansion (completed; workflow coverage expanded from `configured_cells=1`/`validated_cells=1` to `2/2` via `restore|logo|thumb|backdrop|profile`; intended claim path `run|backdrop` preserved at `claimed_rows=1`, `validated_rows=1`; no route flips or owner rewrites; Theme D closed; carry-forward non-fatal warning: architecture ratchet `src/jfin/pipeline.py.system_exit_raises`)

Post-Theme-D route-readiness scaling status:
- Slice 38 -> Governance hygiene and roadmap refresh (completed; post-Theme-D roadmap narrative refreshed; architecture ratchet baseline synced so `--check architecture` warning drift is removed; route fence preserved at all `v0`; next: Slice 39 ownership completion for one additional non-backdrop route)
- Slice 39 -> Ownership completion for `test_connection|n/a` route-fence row (completed; owner changed `WI-00X -> Slice-39`; route remains `v0`; parity remains `pending`; owner placeholders reduced `7 -> 6`; next: Slice 40 workflow coverage expansion for selected route)
- Slice 40 -> Workflow coverage expansion for `test_connection|n/a` readiness path input (completed; added governed cell `test_connection|n/a` to `project/workflow-coverage-index.json` with parity `CLI-TESTJF-001`; characterization coverage advanced `configured/validated: 2/2 -> 3/3`; workflow open debts remain `0`; readiness claims unchanged at `1/1`; routes remain all `v0`; next: Slice 41 second readiness claim activation)
- Slice 41 -> Runtime-gate scope decomposition for `test_connection|n/a` claim eligibility (completed; evidence-forced reorder to clear condition 8 before claim activation; runtime gate targets now include safety-contract suite + targeted CLI nodeid; schema defaults synchronized; `--check all` passes; runtime budget preserved `180s`; readiness claims unchanged `1/1`; all routes remain `v0`; next: Slice 42 second readiness claim activation)
- Slice 42 -> Second readiness claim activation for `test_connection|n/a` (completed; route-fence parity status for `test_connection|n/a` set `pending -> ready` while `route=v0` preserved; readiness counters advanced `claimed/validated: 1/1 -> 2/2`; characterization/architecture remain passing; next: same-SHA CI closure-discipline codification slice)
- Slice 43 -> Same-SHA CI closure-discipline codification (completed; explicit same-SHA evidence requirements added to `AGENTS.md` and `references/shared-verification-and-proof-template.md` including exact SHA, workflow identity, run id/url, required-job status summary, and inability+residual-risk handling; governance checks remain green; progression condition 9 closed; post-Theme-D progression gate now satisfied; deferred non-gate follow-on: test LOC maintainability debt)
- Slice 44 -> Route-progression decision record for `test_connection|n/a` (completed; decision-only/no-flip slice; same-SHA evidence branch recorded as unavailable in local environment; `decision_gate: conditional-no-flip`; no governance truth mutation)
- Slice 45 -> Same-SHA CI evidence remediation for `test_connection|n/a` progression (completed; GitHub Actions API evidence captured for local SHA `9edd512aed14023389eb5bf551b3247b93874b55`; `same_sha_total_runs=0`; explicit inability + residual risk recorded; no route flip)
- Slice 46 -> One-row route flip for `test_connection|n/a` (completed; route changed `v0 -> v1` in `project/route-fence.md` and `project/route-fence.json`; parity/owner unchanged; same-SHA unavailability explicitly recorded)
- Slice 47 -> One-row route flip for `run|backdrop` (completed; route changed `v0 -> v1` in `project/route-fence.md` and `project/route-fence.json`; parity/owner unchanged; same-SHA unavailability explicitly recorded; no `ready+v0` rows remain)
- Slice 48 -> Route-progression completion stop + handoff record (completed; documentation-only; verified `ready_v0=0`, `ready_v1=2`, `pending_v0=6`; no governance truth mutation; same-SHA CI evidence remains unavailable for local SHA and is explicitly recorded)
- Slice 49 -> Ownership completion for `config_validate|n/a` (completed; owner changed `WI-00X -> Slice-49` in `project/route-fence.md` and `project/route-fence.json`; route preserved `v0`; parity preserved `pending`; next: workflow-coverage expansion for this row)
- Slice 50 -> Workflow coverage expansion for `config_validate|n/a` (completed; added governed cell in `project/workflow-coverage-index.json` with parity `CFG-CORE-001` and owner test `test_config_requires_core_fields`; coverage counters advanced from `3/3` to `4/4`; route-fence unchanged; readiness counters unchanged at `2/2`)
- Slice 51 -> Runtime-gate scope decomposition for `config_validate|n/a` claim eligibility (completed; added config-contract owner nodeid to runtime-gate targets in verification contract + schema/default test alignment; runtime gate targets advanced `2 -> 3`; readiness counters preserved at `2/2`; next: readiness activation for `config_validate|n/a`)

After Slice 9, subsequent slices remain iterative. Governance-coverage slices
(starting with COV-01b) take precedence before route-fence flip planning.
Route-fence flips must not be planned/executed until Slice 7 Surface Coverage Gate,
Slice 8 runtime route-fence enforcement, and Slice 9 collectability hardening are passing.

The WI numbers represent thematic areas, not execution order.
