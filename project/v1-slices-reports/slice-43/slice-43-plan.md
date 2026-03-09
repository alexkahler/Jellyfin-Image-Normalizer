# Slice 43 Plan v3 (Implementation-Ready) - Same-SHA CI Closure-Discipline Codification

Date: 2026-03-09
Branch: feat/v1-overhaul
HEAD at planning start: 567db11
Starting worktree state: intentionally unclean (`project/v1-slices-reports/slice-43/` scaffold files only)

## 1. Baseline State and Exact Blocker

Artifacts reviewed:
- WORK_ITEMS.md
- project/v1-slices-reports/audits/post_theme_d_next_slice_roadmap.md
- project/v1-slices-reports/slice-42/slice-42-audit.md
- project/verification-contract.yml
- references/shared-verification-and-proof-template.md
- AGENTS.md

Recomputed current posture:
- progression conditions 1-8 and 10: met
- progression condition 9: **unmet** (same-SHA CI evidence expectation not yet explicit in closure discipline)
- route posture remains all `v0`
- readiness remains healthy (`claimed=2`, `validated=2`)

Exact blocker targeted:
- condition 9 only: codify same-SHA CI evidence handling in closure/audit discipline artifacts.

Roadmap-order deviation note (required evidence):
- original roadmap ordering placed test maintainability debt before evidence-freshness discipline;
- current recomputed gate status shows only condition 9 is still blocking progression closure,
- therefore this deviation is gate-critical and evidence-forced, not scope creep;
- maintainability debt is explicitly deferred after gate closure decision.

## 2. Exact In-Scope / Out-of-Scope Files

In-scope files for Slice 43 implementation:
- references/shared-verification-and-proof-template.md
- project/v1-slices-reports/slice-43/slice-43-plan.md
- project/v1-slices-reports/slice-43/slice-43-implementation.md
- project/v1-slices-reports/slice-43/slice-43-audit.md
- WORK_ITEMS.md
- AGENTS.md (only if needed to make expectation explicitly repo-wide/canonical)

Out-of-scope files and work:
- any `src/` runtime code
- any tests/characterization baselines or runtime behavior files
- project/route-fence.md and project/route-fence.json
- project/parity-matrix.md
- project/workflow-coverage-index.json
- project/verification-contract.yml semantics unrelated to closure-discipline wording
- any route flips or route-state edits
- any readiness-claim count changes

## 3. Small-Slice Justification

- one objective, one blocker (condition 9), docs/process codification only.
- no behavioral/runtime/test-surface mutation.
- binary success sentence: "Closure discipline explicitly requires same-SHA CI evidence handling (or explicit inability + residual risk), and no governance/runtime surfaces changed."

## 4. Behavior-Preservation Obligations

- preserve runtime behavior and safety invariants.
- preserve route-fence state and all `v0` routes.
- preserve readiness counters and parity/workflow evidence state.
- avoid redefining readiness gates or relaxing enforcement.

## 5. Honest Remediation Path

1. Add explicit same-SHA CI evidence requirement language to closure/audit discipline artifact(s).
2. Anchor same-SHA evidence requirements to `project/verification-contract.yml` required CI jobs:
   - `test`
   - `security`
   - `quality`
   - `governance`
3. Require exact SHA linkage in closure records when CI evidence exists.
4. Require a minimal closure-evidence record schema in wording, at least:
   - local SHA
   - workflow identity
   - CI run id/url **or** explicit inability statement
   - per-required-job status summary (`test/security/quality/governance`)
   - residual-risk note when CI evidence is unavailable
5. Require explicit documented inability + residual risk note when same-SHA evidence cannot be obtained.
6. Require non-silent handling: closure cannot imply same-SHA evidence if unavailable.
7. Keep wording scoped to future route-work closure discipline; do not mutate route/runtime behavior.
8. Update WORK_ITEMS with condition-9 codification status and defer note for maintainability debt.

## 6. Expected Blocker Contraction and Remaining Blockers

Expected contraction:
- condition 9 moves unmet -> met.

Expected remaining blockers after successful Slice 43:
- none in post-Theme-D progression gate set.
- This slice closes progression condition 9 only and does not claim maintainability debt closure.

Explicit defer note:
- roadmap maintainability-debt work remains valid but no longer gate-blocking for progression closure; it is deferred as follow-on technical debt.

## 7. Exact Audit Verification Commands

- git status --short
- git diff --name-only
- .\.venv\Scripts\python.exe project/scripts/verify_governance.py --check readiness
- .\.venv\Scripts\python.exe project/scripts/verify_governance.py --check parity
- .\.venv\Scripts\python.exe project/scripts/verify_governance.py --check characterization
- .\.venv\Scripts\python.exe project/scripts/verify_governance.py --check architecture
- .\.venv\Scripts\python.exe project/scripts/verify_governance.py --check all

## 8. Targeted Validators for Touched Artifacts

- Text validator for explicit policy presence:
  - `rg -n "same-SHA|same SHA|exact SHA|residual risk|unable to obtain CI evidence|test|security|quality|governance|run id|run url|workflow identity" references/shared-verification-and-proof-template.md AGENTS.md`
- Consistency validator:
  - ensure wording does not claim route flips/readiness activation occurred.

## 9. Rollback Path

If scope drifts or checks regress:
1. revert closure-discipline wording edits only.
2. keep slice-43 reports with blocked/fail-close evidence.
3. do not commit partial policy text that could misstate evidence obligations.

## 10. Exact Next-Step Expectation After Success

- Run progression-gate closure decision from fresh recomputation.
- If condition 9 is confirmed met and 1-8/10 remain met, mark post-Theme-D progression gate satisfied and hand off to dedicated route-progression decision planning (no automatic route flip in this slice).

## 11. Inherited Unresolved Remediation

- test LOC maintainability debt remains outstanding as non-gate follow-on.
- continue preserving evidence-first/fail-closed posture for route-progression planning.

## 12. Scope-Tightening Controls and Fail-Close Criteria

Excluded adjacent work:
- maintainability refactors/splits in this slice
- runtime-gate scope edits
- readiness/route-fence/parity/workflow edits
- route progression/flips

Too-large signals:
- touching runtime or test behavior surfaces
- broad documentation rewrite beyond closure-discipline requirement
- policy edits that mix condition 9 with unrelated governance cleanup

Decomposition signals:
- condition 9 wording cannot be made explicit without broader governance contract rewrite
- AGENTS and shared template requirements conflict in a way that cannot be resolved narrowly

Fail-close criteria:
- any non-doc governance artifact changes outside approved scope
- ambiguous wording that allows silent stale-CI closure claims
- inability to state same-SHA handling explicitly and audibly in closure discipline artifacts
