# Slice 71 Plan v3 (Final) - Post-Flip Completion-Stop / Roadmap Decision Update (Documentation/Evidence Closure)

Date: 2026-03-11  
Branch: `feat/v1-overhaul`  
Planning review status: v3 final.

## 1) Slice ID and title
- Slice 71
- Post-flip completion-stop / roadmap decision update

## 2) Goal / objective
- Complete a bounded, documentation-first closure slice after Slice 70's approved one-row flip for `config_init|n/a`.
- Record a completion-stop baseline snapshot and an explicit next-step roadmap decision without introducing new runtime/test or governance-truth mutations.
- Preserve current target-row state as evidence-only context: `config_init|n/a -> route=v1, owner_slice=Slice-57, parity_status=ready`.

## 3) In-scope / out-of-scope
### In scope
- Slice 71 report artifacts (`plan`, `implementation`, `audit`).
- Documentation/evidence capture proving current baseline and no protected-file mutation.
- Post-audit orchestration-only status/next-pointer synchronization in `WORK_ITEMS.md`.

### Out of scope
- Any `src/` or `tests/` edits.
- Any route-fence mutation (`project/route-fence.md`, `project/route-fence.json`).
- Any parity/workflow/verification-contract/CI workflow mutation:
  - `project/parity-matrix.md`
  - `project/workflow-coverage-index.json`
  - `project/verification-contract.yml`
  - `.github/workflows/ci.yml`
- Any same-SHA recollection loop or new progression/flip work in this slice.

## 4) Tight writable allowlist by role
- Planning worker: `project/v1-slices-reports/slice-71/slice-71-plan.md` only.
- Implementation worker: `project/v1-slices-reports/slice-71/slice-71-implementation.md` only.
- Audit worker: `project/v1-slices-reports/slice-71/slice-71-audit.md` only.
- Orchestration thread only (after explicit audit PASS): `WORK_ITEMS.md` one-line append only (exactly one new Slice 71 line with closure + next pointer; no historical rewrites).

## 5) Measurable acceptance criteria
1. Slice 71 implementation and audit artifacts exist and stay documentation/evidence-only.
2. Implementation report records baseline snapshot from route-fence JSON with:
   - `ready_v0=0`
   - `ready_v1=4`
   - `pending_v0=4`
3. Implementation report records current `config_init|n/a` row as `v1 | Slice-57 | ready` in markdown and JSON evidence.
4. Implementation report contains exactly one token line: `completion_stop: recorded`.
5. Implementation report contains exactly one single-line pointer token:
   - `next_slice_pointer: Slice 72 - one-row ownership/readiness-prep follow-on (no route flip).`
6. Protected-file diff proof is empty for out-of-scope governance truth files, CI workflow, `src/`, and `tests/`.
7. Governance verification commands pass: `--check readiness`, `--check parity`, `--check all`.
8. Audit report records explicit PASS before any `WORK_ITEMS.md` edit.
9. Before post-audit append, `WORK_ITEMS.md` duplicate guard is satisfied:
   - `preexisting_slice71_line_count=0`
10. If `WORK_ITEMS.md` is updated, it is orchestration-only, post-audit, and limited to exactly one new Slice 71 line (`closure + next: Slice 72 ...`) with no historical rewrites/removals, and append proof shows:
   - `work_items_line_delta=+1`
   - `work_items_added_lines_count=1`
   - `work_items_removed_lines_count=0`
   - `slice71_work_items_line_count=1`

## 6) Ordered implementation steps
1. Capture execution-time baseline evidence (SHA + readiness counters + `config_init|n/a` row state).
2. Run protected-file diff checks to prove no out-of-scope mutations.
3. Run governance checks (`readiness`, `parity`, `all`) and record outputs.
4. Write `slice-71-implementation.md` with completion-stop statement and roadmap decision update, including exactly-once tokens:
   - `completion_stop: recorded`
   - `next_slice_pointer: Slice 72 - one-row ownership/readiness-prep follow-on (no route flip).`
5. Audit worker verifies criteria independently and writes `slice-71-audit.md` with explicit PASS/FAIL.
6. Only after audit PASS, orchestration may append exactly one new Slice 71 line to `WORK_ITEMS.md` (closure + next pointer), with no historical rewrites.

## 7) Risk/guardrails + fail-closed triggers
- Risk: context rot through broad roadmap edits.  
  Guardrail: keep scope to one closure objective and one next-pointer decision.
- Risk: accidental governance/runtime mutation during documentation work.  
  Guardrail: strict allowlist + protected-file diff proof.
- Risk: baseline drift from concurrent work.  
  Guardrail: fail closed if execution-time baseline mismatches expected values.

Fail-closed triggers (any trigger => stop and do not progress mutation/closure claims):
- Any edit to out-of-scope governance truth files, CI workflow, `src/`, or `tests/`.
- Any `WORK_ITEMS.md` edit before explicit Slice 71 audit PASS.
- Execution-time baseline mismatch without explicit re-plan (`ready_v0!=0`, `ready_v1!=4`, `pending_v0!=4`, or `config_init|n/a` not `v1|Slice-57|ready`).
- Missing/duplicate/malformed implementation tokens:
  - `completion_stop: recorded` appears not exactly once.
  - `next_slice_pointer: Slice 72 - one-row ownership/readiness-prep follow-on (no route flip).` appears not exactly once.
- `WORK_ITEMS.md` pre-append duplicate guard fails (`preexisting_slice71_line_count != 0`).
- `WORK_ITEMS.md` post-audit change is not append-only single-line behavior (`work_items_line_delta != +1`, `work_items_added_lines_count != 1`, or `work_items_removed_lines_count != 0`).
- `WORK_ITEMS.md` post-append duplicate guard fails (`slice71_work_items_line_count != 1`).
- Governance check failure (`readiness`, `parity`, or `all`).
- Any request to include additional route-fence/parity/workflow/verification-contract mutation in this slice.

## 8) Suggested next slice
- Slice 72 (recommended, bounded): one-row ownership/readiness-prep roadmap follow-on for a single pending route-fence row (no route flip), chosen by orchestration based on lowest blast radius.

## 9) Verification commands (PowerShell)
```powershell
# Baseline snapshot + target row proof
$sha = (git rev-parse HEAD).Trim()
$json = Get-Content -Raw project/route-fence.json | ConvertFrom-Json
$rows = $json.rows
$readyV0 = @($rows | Where-Object { $_.parity_status -eq 'ready' -and $_.route -eq 'v0' }).Count
$readyV1 = @($rows | Where-Object { $_.parity_status -eq 'ready' -and $_.route -eq 'v1' }).Count
$pendingV0 = @($rows | Where-Object { $_.parity_status -eq 'pending' -and $_.route -eq 'v0' }).Count
$configInit = $rows | Where-Object { $_.command -eq 'config_init' -and $_.mode -eq 'n/a' }
"sha=$sha"
"ready_v0=$readyV0"
"ready_v1=$readyV1"
"pending_v0=$pendingV0"
$configInit | Select-Object command, mode, route, owner_slice, parity_status
Select-String -Path project/route-fence.md -Pattern '^\|\s*config_init\s*\|\s*n/a\s*\|\s*v1\s*\|\s*Slice-57\s*\|\s*ready\s*\|'

# Scope/diff proof (protected files + runtime/tests)
git diff --name-only
git diff -- project/route-fence.md project/route-fence.json project/parity-matrix.md project/workflow-coverage-index.json project/verification-contract.yml .github/workflows/ci.yml src tests WORK_ITEMS.md

# Governance checks
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check readiness
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check parity
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check all

# Implementation token cardinality proof
$impl = 'project/v1-slices-reports/slice-71/slice-71-implementation.md'
"completion_stop_exact_count=$((Select-String -Path $impl -Pattern '^completion_stop:\s*recorded\s*$').Count)"
"completion_stop_any_count=$((Select-String -Path $impl -Pattern '^completion_stop:\s*').Count)"
"next_slice_pointer_exact_count=$((Select-String -Path $impl -Pattern '^next_slice_pointer:\s*Slice 72 - one-row ownership/readiness-prep follow-on \(no route flip\)\.\s*$').Count)"
"next_slice_pointer_any_count=$((Select-String -Path $impl -Pattern '^next_slice_pointer:\s*').Count)"

# Audit PASS gate before any WORK_ITEMS update
Select-String -Path project/v1-slices-reports/slice-71/slice-71-audit.md -Pattern '^Explicit verdict:\s*\*\*PASS\*\*|^Final verdict:\s*\*\*PASS\*\*'
git diff --name-only -- WORK_ITEMS.md

# WORK_ITEMS single-line append-only proof (post-audit orchestrator step)
# Pre-append duplicate guard (must be 0)
"preexisting_slice71_line_count=$((Select-String -Path WORK_ITEMS.md -Pattern '^- Slice 71 -> ').Count)"
$beforeCount = (Get-Content WORK_ITEMS.md).Count
# ...append exactly one Slice 71 line...
$afterCount = (Get-Content WORK_ITEMS.md).Count
"work_items_line_delta=$('{0:+#;-#;0}' -f ($afterCount - $beforeCount))"
$wDiff = git diff --unified=0 -- WORK_ITEMS.md
"work_items_added_lines_count=$((($wDiff | Select-String -Pattern '^\+[^+]').Matches.Count))"
"work_items_removed_lines_count=$((($wDiff | Select-String -Pattern '^\-[^-]').Matches.Count))"
"slice71_work_items_line_count=$((Select-String -Path WORK_ITEMS.md -Pattern '^- Slice 71 -> ').Count)"
Select-String -Path WORK_ITEMS.md -Pattern '^- Slice 71 -> .*next:\s*Slice 72\b.*$'
```

## 10) Evidence/report output paths
- Plan: `project/v1-slices-reports/slice-71/slice-71-plan.md`
- Implementation report: `project/v1-slices-reports/slice-71/slice-71-implementation.md`
- Audit report: `project/v1-slices-reports/slice-71/slice-71-audit.md`
- Post-audit orchestration update target: `WORK_ITEMS.md`

## 11) Split-if-too-large rule
Split immediately and defer if any of the following appears necessary:
- Any mutation beyond closure/documentation objective (including route-fence/parity/workflow/verification-contract/CI changes).
- Any runtime/test edits.
- Any additional same-SHA evidence collection/remediation loop.
- Any multi-objective roadmap rewrite beyond a single bounded next-pointer decision.

If split is triggered, keep Slice 71 limited to documentation/evidence closure only, record explicit deferral, and create the next numbered slice for the deferred mutation objective.
