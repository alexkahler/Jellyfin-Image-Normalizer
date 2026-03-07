# Track-1 Next Iteration Roadmap (Revised, Audit-Aligned)

Date: 2026-03-07  
Source of gap identification: `project/v1-slices-reports/audits/governance-gap-audit-2026-03-07.md` (authoritative)

## 1. Migration Phase Classification

- Current phase: **Governance completion** (governance infrastructure exists, but aggregate contract posture is not fully green and readiness validation is vacuous).
- Target phase after this iteration: **Route readiness validation** (active, non-vacuous readiness claims; no route flips).

## 2. Slice Themes for the Next Iteration

### Theme A - Governance Contract Posture Recovery
- Governance gaps addressed: **GG-001, GG-008**
- Focus:
  - Restore green aggregate governance posture.
  - Attach CI required-job evidence for the same revision.
- Required outcome:
  - `verify_governance.py --check all` passes.

### Theme B - Workflow Readiness Baseline Unblock
- Governance gaps addressed: **GG-004** (blocking portion)
- Focus:
  - Resolve readiness-blocking workflow debt on the current claim path.
  - Ensure readiness validator can evaluate real claim candidates.
- Required outcome:
  - Readiness-blocking debt no longer prevents claim evaluation.

### Theme C - Route-Readiness Activation and Accountability
- Governance gaps addressed: **GG-002, GG-003**
- Focus:
  - C1: Replace placeholder route-fence ownership metadata (`WI-00X`) with real ownership claims.
  - C2: Activate first readiness claims so validation is no longer vacuous.
- Required outcome:
  - `verify_governance.py --check readiness` reports `claimed_rows > 0` and `validated_rows > 0`.

### Theme D - Workflow Readiness Coverage Expansion (Post-Activation)
- Governance gaps addressed: **GG-004** (breadth portion)
- Focus:
  - Minimal multi-cell workflow readiness evidence expansion after activation succeeds.
  - Improve route-fence progression confidence beyond single-cell readiness evidence.
- Required outcome:
  - Readiness evidence coverage extends beyond the current single-cell baseline.

## 3. Ordering Rationale

Planned order: **A -> B -> C -> D**

- A first: GG-001 is a migration-blocking aggregate gate failure and must be cleared before readiness progression is trusted.
- B before C: GG-004 includes an explicit readiness-blocking workflow debt; unblock readiness input surface before activating claims.
- C after B: ownership accountability and real claims are meaningful only when workflow readiness debt is no longer claim-blocking.
- D last: breadth expansion follows proven activation and non-vacuous readiness validation.

## 4. Dependencies Between Themes

- Theme B depends on Theme A.
- Theme C depends on Theme B.
- Within Theme C:
  - C1 (ownership completeness) precedes C2 (first readiness claims).
- Theme D depends on Theme C.

## 5. Explicit Guardrails for This Iteration

- No architecture redesign.
- No new governance systems unless directly required by authoritative audit findings.
- No route flips in this iteration:
  - Route rows remain `v0`.
  - This iteration activates readiness validation only.

## 6. Explicit Gap Coverage and Deferrals

Addressed this iteration:
- **GG-001** via Theme A.
- **GG-008** via Theme A.
- **GG-004** via Theme B (blocking closure) and Theme D (minimal breadth expansion).
- **GG-002** via Theme C1.
- **GG-003** via Theme C2.

Deferred to later iterations:
- **GG-005** deferred because runtime characterization breadth is lower priority than migration-blocking readiness activation.
- **GG-006** deferred because observability governance depth is lower priority than restoring active readiness validation.
- **GG-007** deferred because architecture ratchet debt is not the highest-impact blocker for this iteration's readiness activation objective.
