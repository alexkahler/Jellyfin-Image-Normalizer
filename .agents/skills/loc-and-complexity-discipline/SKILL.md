---
name: loc-and-complexity-discipline
description: "Control implementation-time code growth and structural complexity during active coding. Use when a change is starting to sprawl in LOC, file size, branching, helper layers, or scaffolding, and you need to keep the implementation small, local, and maintainable. This skill is for shaping the code change itself, not for pre-coding risk planning or post-change verification ownership. Don’t use for formatting-only sweeps, docs-only work, or large approved rewrites that are already intentionally sliced and planned under AGENTS.md."
metadata:
  version: "3.0.0"
  updated: "2026-03-07"
  owners:
    - "@codex"
    - "@alexkahler"
  notes: Repo-specific thresholds/tools vary. Before enforcing numeric limits, check AGENTS.md for verification gates and any existing size/complexity tooling (ruff rules, radon, mccabe, pylint, etc.). If the repo defines different LOC/file-size limits, follow those.
compatibility: Assumes a Python-first repo with AGENTS.md, unit tests, and CI verification gates. Requires ability to view diffs (git recommended).
---

# LOC and Complexity Discipline

## Scope and intent

This skill is an **implementation-time complexity control runbook**.

**Use it while coding** when a change is beginning to expand in size, branching, helpers, files, or abstraction layers and needs to be pulled back to the smallest correct shape.

**Goal:** deliver the smallest correct implementation with the smallest reasonable new surface area, while keeping modules readable, testable, and easy to review.

**This skill does not own:**
- pre-coding risk framing, sequencing, rollback planning, or milestone design,
- final verification strategy or proof/reporting ownership,
- style-only cleanup governed by repo lint/format rules.

**Non-goals:**
- Not a style guide (use repo lint/format rules).
- Not a mandate to refactor everything "for cleanliness".
- Not permission to avoid needed tests or verification gates.

---

## Trigger conditions

Use this skill when **any** is true (unless AGENTS.md defines different thresholds):

- **Net new production LOC** is trending above **~100** (exclude tests/docs), or
- A single file is trending above **~300 LOC**, or
- A function/method is trending above **~60–80 lines**, or
- You are adding additional layers ("manager/service/factory/framework/config") to implement a small behavior change, or
- Branching feels "spiky" (multiple nested conditionals, long try/except ladders, many special cases).

---

## Inputs and preconditions

Before editing:

1) **Read AGENTS.md verification gates** and any repo constraints on refactors, module boundaries, layering, or allowed tools.
2) Identify the **minimum behavioral requirement** in one sentence.
3) Identify the **narrowest insertion point** (ideally one function in one file) where the requirement can be met.

---

## Guardrails (hard rules)

### Rule 1 — Prefer the smallest viable technique
Use the first option that works:

1. Adjust an existing conditional or data flow.
2. Add a **small helper** (only if it reduces duplication or clarifies a boundary).
3. Add a **small type** (e.g., dataclass) only if it replaces confusing tuples/parallel lists or improves typing.
4. Split a module only when it is demonstrably oversized or mixed-responsibility.

### Rule 2 — No new layer without a reason you can defend
Do **not** introduce a new class/module/abstraction unless at least one is true:

- It is reused across multiple call sites,
- It creates a clear responsibility boundary that reduces coupling,
- It materially improves testability (and simpler approaches don’t).

### Rule 3 — Delete before you add
If you add code, you must also look for one of:

- dead branches you can remove,
- duplicated logic you can consolidate,
- unused parameters/config,
- redundant indirection.

### Rule 4 — Don’t hide complexity in "configurability"
Avoid introducing config options to dodge a local, deterministic fix unless the repo already treats that surface as public API and the change truly requires configurability.

---

## Workflow

### 1) Restate the requirement (one sentence)
- **Output:** one sentence describing the behavior change (no implementation detail).

### 2) Choose the smallest insertion point
- **Action:** pick the smallest function/module where the behavior can be implemented without new layers.
- **Output:** the file path(s) and function(s) you plan to touch.

### 3) Size the change before coding
- **Action:** estimate whether you can keep net new production LOC under ~100.
- **If not:** slice the work into smaller milestones (each independently verifiable).

### 4) Implement with "remove before add"
- **Action:** implement the change while actively removing dead/duplicate code.
- **Decision rule:**
  - If you feel tempted to add a new abstraction, first try:
    - a small helper function,
    - a clearer data shape,
    - a more local change.

### 5) Complexity checkpoints (while coding)
Use these as prompts to refactor *locally* (not repo-wide):

- If a function exceeds ~60–80 lines: split into helpers by responsibility.
- If nesting exceeds ~3 levels: invert conditionals, early-return, or extract branches.
- If a decision table emerges: convert to a mapping/dispatch table (only if it reduces branching).
- If logic is duplicated twice: extract a helper.

### 6) Verification
Use `references/shared-verification-and-proof-template.md` for the common verification flow:
- run the smallest relevant checks first,
- use `AGENTS.md` as the canonical source for repo gates,
- apply stop-and-fix,
- then record a short verification note.

Additional requirements for this skill:
- verify the changed behavior with the smallest relevant tests for the touched code path,
- keep verification proportional to the scoped implementation change,
- include the completion report items defined in this skill.

---

## Anti-patterns to avoid

❌ "Manager/Service/Coordinator" classes for a single feature  
❌ Frameworks or plugin systems for a one-off case  
❌ Adding config knobs to avoid choosing a clear default behavior  
❌ Copy/paste variants with tiny differences  
❌ "While I’m here…" refactors bundled into the same change  
❌ Splitting files/modules without tests that lock behavior

---

## Verification checklist

- [ ] Diff is scoped to one objective
- [ ] Net new production LOC is reported (exclude tests/docs)
- [ ] Any added helper/type/layer has an explicit justification
- [ ] Tests added/updated for changed behavior (or justification if not possible)
- [ ] Verification followed `references/shared-verification-and-proof-template.md`
- [ ] No unrelated renames/reformatting/moves

---

## Completion criteria (what you must report when using this skill)

When you declare success, you MUST include:

1) **Approx net new production LOC** (exclude tests/docs)  
2) **What you removed** (dead branches, duplicates, scaffolding avoided)  
3) **Why any new helper/type/file/class exists** (1–3 bullets)  
4) **Verification performed** (reference AGENTS.md gates + what subset you ran first)

---

## Troubleshooting

### Symptom: the diff is ballooning
- Likely causes: scope creep, missing boundary, hidden coupling
- Recovery:
  - stop,
  - re-scope to the minimal behavior change,
  - split into milestones (each with its own tests).

### Symptom: you "need" a new framework/layer to proceed
- Likely causes: unclear requirement, missing local helper, over-generalization
- Recovery:
  - write the simplest version first,
  - only generalize after you see duplication across call sites.

### Symptom: splitting a file breaks imports/tests everywhere
- Likely causes: public surface not fenced, too many call sites changed at once
- Recovery:
  - add an adapter/compat layer,
  - split in slices,
  - verify after each slice.

---

## Examples

### SHOULD trigger
- "This change is adding ~200 lines—how do we keep it small?"
- "This module is 900 LOC and hard to navigate; we need to split it safely."
- "I’m about to add a new ‘service’ class—do we really need it?"
- "This fix keeps growing branches and helper functions. Keep the implementation contained."

### SHOULD NOT trigger
- "Please plan the rollout, risks, and rollback for this multi-step change."
- "Please run the repo verification gates and summarize what passed."
- "Please run ruff/format on the repo" (format-only sweep)
- "Implement a new subsystem across multiple packages" (use planning/slicing workflow first)
- "Update documentation only" (docs workflow)

## Changelog
- 2026-03-07 / 3.0.0: Repositioned the skill as implementation-time complexity control, sharpened boundaries against planning and verification skills, and added routing-focused non-trigger examples.
- 2026-03-04 / 2.0.0: Rewritten to be repo-agnostic, added explicit runbook workflow, verification+reporting contract, and portability notes.