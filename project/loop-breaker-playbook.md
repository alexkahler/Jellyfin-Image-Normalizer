# Loop-Breaker Playbook for Same-SHA Evidence Loops

Last updated: 2026-03-11
Source slices: 67-68 (`config_init|n/a`)

## Purpose

Define a reusable fail-closed pattern for breaking repeated `same_sha_branch: evidence-unavailable` continuation loops during route-progression work.

## When to Trigger This Playbook

Trigger loop-breaker handling when all are true:

1. Multiple consecutive slices for the same target row report `same_sha_branch: evidence-unavailable`.
2. Decision token remains `decision_gate: conditional-no-flip` with no new external action.
3. Same inability reason repeats (for example, no same-SHA runs visible for local SHA).

Do not plan another same-objective continuation slice until loop-breaker flow is executed.

## Required Loop-Breaker Flow

1. Freeze one immutable anchor SHA for evidence collection.
2. Keep scope to one target row and one objective.
3. Execute external-unblock action for the anchor SHA (for example, push branch, CI trigger coverage fix).
4. Query same-SHA CI runs for exact `head_sha=<anchor_sha>`.
5. Branch to one terminal outcome:
   - `same_sha_branch: evidence-complete` with run id/url and required-job summary.
   - `same_sha_branch: blocked-external` with explicit inability reason and resume condition.
6. Record exactly one decision token:
   - `decision_gate: eligible-for-flip-proposal` for evidence-complete and passing required jobs.
   - `decision_gate: blocked-no-flip` for blocked-external.

`decision_gate: conditional-no-flip` is not a valid terminal outcome for a loop-breaker slice.

## Guardrails

- No route-fence/parity/workflow-contract mutation in loop-breaker evidence slices.
- No runtime/test code edits.
- Record uniqueness proofs:
  - `decision_token_match_count=1`
  - `same_sha_branch_match_count=1`
- If evidence is unavailable, do not imply same-SHA validation occurred.

## Required Evidence Fields

- local SHA
- anchor SHA
- workflow identity
- CI run id/url (when available)
- per-required-job status summary (`test`, `security`, `quality`, `governance`) when available
- inability reason and residual risk when unavailable
- terminal marker pair (`same_sha_branch`, `decision_gate`)
- explicit resume condition for blocked-external outcome

## Resume Policy After Blocked-External

If terminal outcome is `same_sha_branch: blocked-external`:

1. Next slice must target the external prerequisite only.
2. Do not run another continuation-style evidence slice until prerequisite is completed.
3. Re-attempt same-SHA evidence collection only after prerequisite completion is documented.

## Example Reference

- Slice 67: loop-breaker anchor + external-unblock execution + terminal `blocked-external`.
- Slice 68: prerequisite completion by adding `feat/v1-overhaul` to CI workflow trigger branches.
