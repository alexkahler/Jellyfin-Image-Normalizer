# Using This Routing Artifact in Your Repository

This note is meant to live **alongside the skill** as a practical adoption guide for repository maintainers. It explains how to integrate the routing artifact into a real repo without turning it into another skill or overloading `AGENTS.md`.

## What this artifact is for

The routing artifact exists to help a repository use the skill library more consistently. Its job is to clarify:

* which skill should lead in a given situation,
* when another skill should act as a companion,
* which nearby skills are easy to confuse but should not lead,
* and when work should hand off from one skill to another as the task changes phase.

This is **catalog guidance**, not a task procedure. It helps the agent choose and combine skills correctly. It should not replace the actual `SKILL.md` files.

---

## Where the shared routing document should live

The shared routing document should exist **once** at the repository level, in whatever location your repo already uses for shared reference or documentation files.

Common examples:

* `repo-root/references/skill-catalog-routing.md`
* `repo-root/references/catalog-routing.md`
* `repo-root/docs/skill-catalog-routing.md`
* `repo-root/docs/catalog-routing.md`

Use the location that best matches the repository’s existing documentation structure. Do **not** create duplicate copies of the routing document inside individual skill folders.

---

## Should `AGENTS.md` be updated?

Yes, but only in a small, policy-level way.

`AGENTS.md` should not absorb the full routing matrix. It should only carry the minimum always-on guidance needed to make the repository skill-aware. The goal is to make the agent aware that:

* the repository uses a skill catalog,
* a shared routing document exists,
* skill choice should follow primary / companion / near-miss / handoff logic,
* and repository-wide invariant rules still belong in `AGENTS.md`, while task-specific workflows belong in skills.

In other words:

* **`AGENTS.md` = policy, repo conventions, invariant expectations**
* **skills = procedures**
* **routing artifact = how to choose and compose skills**

---

## Where to update `AGENTS.md`

Add a short section near the top of the root `AGENTS.md`, in a place where it will be seen early but will not crowd out the rest of the file.

Best placement:

* after `## Purpose and scope`, or
* after `## Repository expectations`,
* before detailed repo commands, file layouts, or operational instructions

That keeps the routing policy visible and high-signal.

---

## Recommended `AGENTS.md` section

You can add a section like this:

```md
## Skill selection and routing

This repository uses a skill library for task-scoped procedures.

Rules:
- Keep repo-wide invariant rules in this AGENTS.md.
- Use skills for task-specific workflows and deeper procedures.
- When multiple skills appear relevant, consult the repository’s shared skill catalog routing document and follow its:
  - primary skill rules,
  - companion skill rules,
  - near-miss exclusions,
  - handoff / escalation rules.
- Prefer the most phase-specific and domain-specific skill over a broader default.
- Do not duplicate full skill procedures into AGENTS.md; use this file for policy and repo conventions only.

Minimum routing order:
1. Check whether the task is primarily planning, implementation-shaping, verification, contract change, refactor, or docs synchronization.
2. Select the primary skill accordingly.
3. Load companion skills only when the routing document says they compose.
4. If the task changes phase, hand off to the next appropriate skill rather than forcing one skill to cover the whole lifecycle.
```

This is enough for most repositories.

---

## How much should you add to `AGENTS.md`?

Choose the smallest option that fits your repo.

### Minimal option

Use this when you want the lightest integration possible.

Add:

* one short `Skill selection and routing` section,
* one pointer to the repository’s shared skill catalog routing document

This is enough if your repo has only a few skills or only occasional skill use.

### Stronger option

Use this when your repo depends heavily on skills and you want catalog maintenance to stay consistent over time.

Add the routing section above, plus a maintenance section like this:

```md
## Skill catalog maintenance

When changing the skill library:
- Update the repository’s shared skill catalog routing document if a skill’s scope, primary role, companion role, near-miss boundary, or handoff behavior changes.
- Update affected skill descriptions when routing distinctions change.
- Add or update near-miss examples in the relevant `SKILL.md`.
- If repo structure or commands referenced by a skill change, update AGENTS.md and the skill in the same change.
```

This helps prevent drift between the repo, the routing artifact, and the skills themselves.

### Nested `AGENTS.md` option

Use this in large or multi-area repos.

Example layout:

```text
/AGENTS.md
/references/skill-catalog-routing.md
/services/api/AGENTS.md
/tools/data/AGENTS.md
```

In this setup:

* the root `AGENTS.md` defines the general routing policy,
* subtree `AGENTS.md` files add local preferences and constraints,
* repo-area guidance stays close to the code it governs.

This is usually better than cramming subsystem-specific routing into the root file.

---

## What should not go into `AGENTS.md`

Do not put the full routing matrix into `AGENTS.md`.

Do not copy each skill’s workflow into `AGENTS.md`.

Do not make `AGENTS.md` the only place where routing logic lives.

That creates three problems:

* it weakens progressive disclosure,
* it duplicates maintenance work,
* and it blurs the line between policy and procedure.

Keep `AGENTS.md` short and durable. Keep the routing matrix in the shared routing artifact. Keep step-by-step task behavior in the skill itself.

---

## Should repo-specific skills be included?

Yes, but as an extension layer.

The base routing artifact should remain generic and reusable across repositories. If your repo has local skills, those skills should be represented in the routing system, but they should not be mixed into the base catalog without clear separation.

The best model is:

* keep the main routing artifact as the base catalog guide,
* add a repo-specific routing overlay,
* reference that overlay from `AGENTS.md`

This preserves the generic skill library while allowing precise local behavior.

---

## Recommended repository structure

Keep the routing layers separate:

* `AGENTS.md` holds always-on repo policy and routing reminders.
* The shared skill catalog routing document lives once at the repository level, usually in `docs/`, `references/`, or a similar shared documentation folder.
* Each skill keeps its own `SKILL.md` in the repo’s established skill location.

Example:

```text
AGENTS.md
references/skill-catalog-routing.md
.agents/skills/<skill-name>/SKILL.md
```

If repo-specific overlays are needed:

```text
AGENTS.md
references/skill-catalog-routing.md
references/skill-catalog-routing.repo.md
.agents/skills/<skill-name>/SKILL.md
```

---

## How to include repo-specific skills

For each repo-specific skill, add it to the repo overlay using the same routing shape as the base catalog.

Each entry should include:

* **Primary use**
* **Choose first when**
* **Typical companion(s)**
* **Near-miss that should not lead**
* **Handoff / escalation**

That keeps the repo-specific layer compatible with the generic one.

### Example

```md
# Repo-specific routing additions

## `update-foo-service-contracts`

- Primary use: Repo-specific workflow for changing Foo service request/response contracts.
- Choose first when: Editing `services/foo/api/`, schema objects, service adapters, or compatibility tests.
- Typical companions: `docs-self-healing-update-loop`, `verification-gates-and-diff-discipline`
- Near-miss that should not lead: `cli-and-config-contract` when the change is internal service protocol rather than CLI/config
- Handoff / escalation: Hand off to docs sync after behavior is finalized; hand off to verification for contract and compatibility checks.
```

---

## Where repo-specific skills should be referenced

### In the routing artifact

Yes. This is the main place they should be described.

This is where you encode how repo-specific skills relate to the generic library and when they should take precedence.

### In `AGENTS.md`

Yes, but briefly.

You only need a short pointer such as:

```md
For repo-specific workflows, prefer the local routing overlay in the repository’s shared routing docs.
Repo-specific skills take precedence over generic skills when they more precisely match the affected subsystem.
```

That is enough to establish the rule without duplicating the full overlay.

### In each repo-specific `SKILL.md`

Yes.

Each repo-specific skill should make its boundaries explicit. It should include:

* clear use-when guidance,
* clear do-not-use-when guidance,
* nearby skills that are easy to confuse with it,
* companion relationships,
* and boundaries relative to generic skills

That makes routing more reliable both for humans and for the agent.

---

## Precedence rule for repo-specific skills

Use this rule in the repo overlay, and optionally also in `AGENTS.md`:

> When a repo-specific skill and a generic library skill both match, prefer the repo-specific skill if it more precisely names the subsystem, file area, framework, or operational workflow involved. Use the generic skill as a companion or overlay when needed.

This is just the general “prefer the narrower, more specific skill” rule applied to repository-local skills.

---

## Maintenance workflow

Use the following loop to keep the routing layer correct over time.

### When adding a repo-specific skill

1. Create the new `SKILL.md`.
2. Write a sharply scoped description.
3. Add should-trigger and near-miss examples.
4. Add an entry to the repo routing overlay.
5. Update `AGENTS.md` only if repo-wide routing expectations changed.

### When changing a repo-specific skill

1. Update the skill description.
2. Update near-miss and boundary language.
3. Update the repo routing entry.
4. Update `AGENTS.md` only if the repo-wide policy changed.

### When deprecating a repo-specific skill

1. Mark the skill deprecated.
2. Remove or mark its routing entry as deprecated.
3. Point to the replacement in the overlay and skill.
4. Update `AGENTS.md` only if the deprecation changes always-on repo behavior.

---

## Recommended adoption pattern

For most repositories, the best setup is:

* add a short routing policy to `AGENTS.md`,
* keep the main routing matrix in a shared repo-level routing document,
* keep repo-specific routing in a separate repo-level overlay if needed,
* and keep the actual procedures inside each `SKILL.md`

That gives you a clean separation of concerns:

```text
AGENTS.md                              -> always-on policy and repo conventions
references/skill-catalog-routing.md    -> generic routing matrix
references/skill-catalog-routing.repo.md -> repo-specific routing overlay
.agents/skills/<skill-name>/SKILL.md   -> task procedures
```

---

## Final recommendation

Use this artifact as a **side-car integration guide**, not as another operational skill.

Update `AGENTS.md`, but only lightly.

Keep the shared routing document in a repo-level `docs/`, `references/`, or similar shared documentation location.

Include repo-specific skills, but only through a clearly separated overlay.

Do not turn `AGENTS.md` into a second routing matrix, do not duplicate the shared routing document into skill folders, and do not create a routing skill just to route to other skills. The routing layer works best as shared repository documentation that helps the agent and maintainers use the skill library correctly.
