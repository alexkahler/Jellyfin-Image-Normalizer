# Slice 70 Plan v3 (Final) - One-Row Progression Proposal for `config_init|n/a` (`v0 -> v1`) with Explicit Approval Gate

Date: 2026-03-11  
Branch: `feat/v1-overhaul`  
Planning review status: v3 final.

## 1) Slice ID and Title
- Slice 70
- One-row progression proposal for `config_init|n/a` (`v0 -> v1`) with explicit approval gate

## 2) Goal / Objective
Keep scope to one objective: handle proposal + approval-gate flow for a single route progression candidate (`config_init|n/a`), and permit route-fence mutation only when the in-slice approval gate is satisfied.

## 3) In-Scope / Out-of-Scope
### In scope
- Validate prerequisite evidence from Slice 69 for progression eligibility.
- Evaluate explicit approval gate for one-row route mutation.
- If and only if gate passes, apply one-row route change for `config_init|n/a` in both route-fence artifacts (`v0 -> v1`), preserving owner/parity.
- Produce Slice 70 artifacts (`plan`, `implementation`, `audit`).

### Out of scope
- Any runtime or test source edits (`src/`, `tests/`).
- Any mutation to governance truth outside the one allowed row mutation when gate-approved.
- Any multi-row route change.
- Any owner/parity change on `config_init|n/a`.
- Any CI workflow, verification-contract, or parity-matrix edits in this slice.

## 4) Tight Writable Allowlist by Role
- Planning worker: `project/v1-slices-reports/slice-70/slice-70-plan.md` only.
- Implementation worker:
  - Always allowed: `project/v1-slices-reports/slice-70/slice-70-implementation.md`.
  - Conditionally allowed (only after gate PASS): `project/route-fence.md`, `project/route-fence.json` for one-row route mutation on `config_init|n/a` only.
- Audit worker: `project/v1-slices-reports/slice-70/slice-70-audit.md` only.
- Orchestration thread only (after explicit audit PASS): `WORK_ITEMS.md` status/next-pointer update.

## 5) Explicit Approval Gate (Required Before Any Route Mutation)
Approval input contract (mandatory):
- Implementation must consume an orchestration-provided approval directive for Slice 70:
  - `approval_signal: granted` or `approval_signal: denied`
- Implementation cannot self-authorize route mutation.
- `approval_source` must record the provided orchestration directive source verbatim.

Plan-pinned directive source for this specific Slice 70 run:
- `approval_source_expected: "Orchestration directive (2026-03-11): continue the next iteration slice."`
- Expected gate input for this run: `approval_signal: granted`, unless contradictory evidence appears during implementation/audit.

Gate is PASS only when all conditions below are true:
1. Explicit execution authorization is recorded by orchestration for this slice:
   - `approval_signal: granted`
   - `approval_source` exactly equals `approval_source_expected`
2. Slice 69 terminal markers are evidence-complete and eligible:
   - exactly one `same_sha_branch: evidence-complete`
   - exactly one `decision_gate: eligible-for-flip-proposal`
3. Slice 69 audit verdict is explicit PASS.
4. Baseline target row is unchanged pre-mutation in both artifacts:
   - `config_init|n/a -> route=v0, owner_slice=Slice-57, parity_status=ready`
5. No out-of-scope file diff is present before applying row mutation.

Permission rule:
- Implementation report must record gate-evaluation fields exactly once:
  - `approval_signal` (`granted` or `denied`)
  - `approval_source` (verbatim orchestration directive source statement)
  - `gate_result` (`PASS` or `DENY`)
- Route mutation is permitted only after `gate_result: PASS` is recorded with `approval_signal: granted`.
- If explicit approval signal is absent or not granted, gate result must be DENY even when Slice 69 evidence is otherwise eligible.
- If any gate condition fails or is unverifiable, gate is DENY and slice must fail closed with no route mutation.

## 6) Acceptance Criteria (Measurable)
1. Slice 70 implementation records explicit gate evaluation with PASS or DENY and evidence for each gate condition.
2. Implementation report includes exactly one of each gate field:
   - `approval_signal` (`granted` or `denied`)
   - `approval_source` (verbatim orchestration directive source statement)
   - `gate_result` (`PASS` or `DENY`)
3. `approval_source` in implementation report exactly matches `approval_source_expected` from this plan and appears exactly once.
4. If gate is DENY, `project/route-fence.md` and `project/route-fence.json` remain unchanged.
5. If gate is PASS, exactly one row changes in both route-fence artifacts:
   - target row: `config_init|n/a`
   - route only: `v0 -> v1`
6. On gate PASS path, `owner_slice` remains `Slice-57` and `parity_status` remains `ready` in both artifacts.
7. No other route-fence rows change.
8. No changes occur in out-of-scope governance truth files, runtime code, or tests.
9. Governance checks pass: `--check readiness`, `--check parity`, `--check all`.
10. Audit report is explicit PASS before any `WORK_ITEMS.md` update.

## 7) Ordered Implementation Steps
1. Capture baseline proofs:
   - Slice 69 markers and audit verdict.
   - Current `config_init|n/a` row in markdown and JSON route-fence.
2. Evaluate the explicit approval gate condition-by-condition and record exactly-once fields:
   - `approval_signal`
   - `approval_source` (verbatim from orchestration directive source)
   - `gate_result`
3. If gate DENY:
   - record fail-closed outcome,
   - do not mutate route-fence artifacts,
   - proceed to verification + report.
4. If gate PASS:
   - edit only target row route value in both route-fence artifacts (`v0 -> v1`),
   - keep owner/parity unchanged.
5. Capture one-row diff proof and protected-file no-mutation proof.
6. Run governance verification commands and record outputs.
7. Write `slice-70-implementation.md` and hand off to audit worker.

## 8) Risks / Guardrails + Fail-Closed Triggers
Risks and guardrails:
- Risk: gate bypass and premature governance mutation.  
  Guardrail: no route-fence edit allowed before explicit Gate PASS evidence is recorded.
- Risk: accidental multi-row or field-drift mutation.  
  Guardrail: enforce single-row diff proof and explicit owner/parity invariants.
- Risk: scope creep into unrelated governance/runtime artifacts.  
  Guardrail: protected-file diff checks must be empty outside allowlist.

Fail-closed triggers (any trigger => stop mutation path):
- Missing/duplicate Slice 69 marker evidence or wrong marker values.
- Missing, duplicated, or ambiguous approval fields (`approval_signal`, `approval_source`, `gate_result`).
- Mismatch between recorded `approval_source` and plan-defined `approval_source_expected`.
- Slice 69 audit not explicit PASS.
- Baseline row mismatch from expected precondition (`v0 | Slice-57 | ready`).
- Any route mutation attempted while `gate_result: DENY`.
- Any attempted edit outside conditional allowlist.
- Any multi-row route-fence diff or owner/parity drift on target row.
- Any runtime/test source edit.
- Any required governance check failure.

## 9) Suggested Next Slice
- Slice 71 (bounded follow-on):
  - If Slice 70 gate PASS + one-row mutation + audit PASS: post-flip completion-stop / roadmap decision update.
  - If Slice 70 gate DENY: blocker-remediation slice limited to unmet gate condition(s), with no route mutation.

## 10) Verification Commands (PowerShell)
```powershell
# Slice 69 evidence gate proof
Select-String -Path project/v1-slices-reports/slice-69/slice-69-implementation.md -Pattern '^same_sha_branch:\s*evidence-complete\s*$'
Select-String -Path project/v1-slices-reports/slice-69/slice-69-implementation.md -Pattern '^decision_gate:\s*eligible-for-flip-proposal\s*$'
Select-String -Path project/v1-slices-reports/slice-69/slice-69-audit.md -Pattern '^Explicit verdict:\s*\*\*PASS\*\*|^Final verdict:\s*\*\*PASS\*\*'

# Marker uniqueness checks (Slice 69 implementation)
$s69 = 'project/v1-slices-reports/slice-69/slice-69-implementation.md'
"same_sha_branch_count=$((Select-String -Path $s69 -Pattern '^same_sha_branch:\s*').Count)"
"decision_gate_count=$((Select-String -Path $s69 -Pattern '^decision_gate:\s*').Count)"

# Approval-gate field checks (Slice 70 implementation)
$s70 = 'project/v1-slices-reports/slice-70/slice-70-implementation.md'
"approvalSourceExpected=Orchestration directive (2026-03-11): continue the next iteration slice."
"approval_signal_allowed_count=$((Select-String -Path $s70 -Pattern '^approval_signal:\s*(granted|denied)\s*$').Count)"
"approval_source_count=$((Select-String -Path $s70 -Pattern '^approval_source:\s*.+$').Count)"
"approval_source_exact_match_count=$((Select-String -Path $s70 -Pattern '^approval_source:\s*Orchestration directive \(2026-03-11\): continue the next iteration slice\.\s*$').Count)"
"gate_result_allowed_count=$((Select-String -Path $s70 -Pattern '^gate_result:\s*(PASS|DENY)\s*$').Count)"
"approval_signal_any_count=$((Select-String -Path $s70 -Pattern '^approval_signal:\s*').Count)"
"approval_source_any_count=$((Select-String -Path $s70 -Pattern '^approval_source:\s*').Count)"
"gate_result_any_count=$((Select-String -Path $s70 -Pattern '^gate_result:\s*').Count)"

# Baseline row proof (pre-mutation)
Select-String -Path project/route-fence.md -Pattern '^\|\s*config_init\s*\|\s*n/a\s*\|\s*v0\s*\|\s*Slice-57\s*\|\s*ready\s*\|'
$rf = Get-Content -Raw project/route-fence.json | ConvertFrom-Json
$rf.rows | Where-Object { $_.command -eq 'config_init' -and $_.mode -eq 'n/a' } |
  Select-Object command, mode, route, owner_slice, parity_status

# Scope/diff proof
git diff --name-only
git diff -- project/route-fence.md project/route-fence.json project/parity-matrix.md project/workflow-coverage-index.json project/verification-contract.yml .github/workflows/ci.yml src tests WORK_ITEMS.md

# One-row diff proof (required only on gate PASS path)
git diff -- project/route-fence.md project/route-fence.json

# Governance checks
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check readiness
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check parity
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check all
```

## 11) Evidence / Report Paths
- Plan: `project/v1-slices-reports/slice-70/slice-70-plan.md`
- Implementation: `project/v1-slices-reports/slice-70/slice-70-implementation.md`
- Audit: `project/v1-slices-reports/slice-70/slice-70-audit.md`

## 12) Split-if-too-large Rule
Split immediately if any of these occur:
- Work expands beyond proposal/approval-gate handling for one target row.
- Additional governance-truth mutations are proposed beyond conditional one-row route change.
- Runtime/test edits become necessary.
- Gate-remediation requires external prerequisites or broader policy changes.

If split is triggered, keep Slice 70 as gate-evaluation-only with explicit fail-closed record and no route mutation.
