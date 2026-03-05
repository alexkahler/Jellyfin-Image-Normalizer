---
name: jellyfin-api-client-safety
description: Use this skill when changing Jellyfin API client request semantics in Python (auth headers, retries/backoff, timeouts, TLS verification, redirects, dry-run/write gates), especially in src/jfin/client.py or any module that centralizes HTTP behavior. Use to make changes safely with bounded retries, idempotency-aware rules, and test-backed verification. Don't use for adding new Jellyfin endpoints (use the OpenAPI reference skill) or for non-client application logic.
license: MIT
metadata:
  version: "1.1.0"
  updated: "2026-03-04"
  owners: 
    - "@codex"
    - "@alexkahler"
  primary_files: "src/jfin/client.py"
  notes: This skill is implementation-agnostic (works with either v0 or v1 request stacks). If the client uses a specific retry library (e.g., urllib3/tenacity/httpx retry middleware), ensure that library's semantics are reflected in tests and that method scoping is explicit rather than relying on defaults.
---

# Jellyfin API Client Safety Playbook

A runbook for **safe, test-driven changes** to the Jellyfin API client's HTTP behavior: retries/backoff,
timeouts, TLS verification, auth headers, redirect handling, and write safety (dry-run + write gates).  
Skills should read like an operational runbook with explicit scope, steps, and verification. :contentReference[oaicite:0]{index=0}

## Scope and intent

### Use this skill when you modify
- Retry/backoff behavior (what is retried, when, and how often)
- Timeouts (connect/read/total), redirects, TLS verification, proxies
- Authentication header construction and token handling
- Dry-run enforcement, write gates, and "safe default" behaviors
- Shared error handling and structured logging around HTTP failures

### Don't use this skill for
- Implementing or choosing Jellyfin endpoints/parameters (use the OpenAPI reference skill)
- App-level business logic that is not part of the HTTP client layer

## Safety principles

1. **Dry-run is a hard stop for writes.**  
   Any request classified as "write" must be blocked when dry-run is enabled.

2. **Retries must be bounded and method-scoped.**  
   Retries should be explicitly limited (count + backoff), and should not silently expand to non-idempotent
   methods.

3. **Auth must be correct and non-leaky.**  
   Never log tokens; redact any auth-bearing headers in logs, exceptions, or test snapshots.

4. **Prefer explicitness over library defaults.**  
   Default retry behavior varies across libraries and versions; changes should declare allowed methods and
   status codes explicitly and cover them with tests.

## Inputs and preconditions

Before changing code:
- Identify the primary client entrypoint(s), typically `src/jfin/client.py` (see `metadata.primary_files`).
- Find existing configuration knobs:
  - dry-run flag
  - retry count/backoff settings
  - timeout settings
  - TLS verification settings
- Confirm how HTTP is implemented (e.g., `requests`, `httpx`, or a wrapper around urllib3).

## Definitions

### Classify request intent
Use these categories to drive safe defaults:

- **Read (generally safe to retry):**
  - `GET`, `HEAD`, `OPTIONS`
- **Write (dangerous to retry without strong controls):**
  - `POST`, `PUT`, `PATCH`, `DELETE`

> If the code uses non-standard "write" endpoints behind `GET` (rare but possible), treat them as write and
> gate them via explicit allowlists.

### Idempotency rule of thumb
- **Retry allowed by default:** reads and explicitly idempotent writes.
- **Retry forbidden by default:** non-idempotent writes unless you have a reliable idempotency key strategy
  or the server guarantees idempotency for that operation.

## Workflow

### 1) Map the change to risk
**Goal:** Make the smallest safe change with predictable blast radius.

- List which behaviors you are changing (retries, timeouts, auth, TLS, gating).
- Identify which call sites are affected (central client vs per-call overrides).
- Determine whether this change can cause:
  - duplicate writes
  - longer hangs (timeouts/backoff)
  - auth failures across all endpoints
  - security weakening (TLS verify off, redirect leaks)

**Expected output:** A short "risk map" that names the affected behaviors and the worst plausible failure mode.

---

### 2) Confirm request classification and write gates
**Goal:** Ensure writes are correctly identified and blocked in dry-run.

- Locate the decision point that determines:
  - "is this a write?"
  - "should dry-run block this?"
- Enforce:
  - default = **block writes**
  - allow write only if **explicitly enabled**
- Ensure the error raised is consistent and testable (typed exception or stable message).

**Expected output:** A single, centralized classification + gating rule.

---

### 3) Make retries explicit and bounded
**Goal:** Prevent accidental expansion of retries.

- Explicitly define:
  - allowed methods (e.g., `{"GET", "HEAD"}` by default)
  - status code allowlist (e.g., 429, 502, 503, 504) *only if intended*
  - max retry attempts (finite)
  - backoff strategy (bounded; include jitter only if already standard in repo)
- For writes:
  - default = **no retries**
  - if enabling retries, require one of:
    - idempotency keys + server support, or
    - strict "retry only on connect timeout before request sent" semantics (if your stack can prove this)

**Expected output:** Retry logic that is method-scoped and cannot retry forever.

---

### 4) Update timeouts and TLS safely
**Goal:** Improve resilience without weakening security.

- Timeouts:
  - use explicit values (connect/read/total depending on client)
  - avoid "no timeout" unless there is a strong reason and tests cover it
- TLS verification:
  - default = verify on
  - if supporting verify-off, require explicit opt-in and warn via logs (without secrets)
- Redirects:
  - avoid leaking tokens across hosts via redirects
  - ensure auth is not attached to redirected requests to different origins (if applicable)

**Expected output:** Safe defaults and explicit opt-ins for risky behaviors.

---

### 5) Add/extend tests first-class
**Goal:** Ensure changes are enforced and don't regress.

Minimum tests to add/update:
- Dry-run blocks write methods (and cannot be bypassed by new code paths)
- Retry behavior:
  - retries occur for intended methods/statuses
  - retries do **not** occur for non-idempotent methods by default
  - bounded attempts (assert max calls)
- Auth header:
  - correct header structure for known cases
  - tokens are redacted in logs/errors
- Timeout/TLS:
  - timeouts are passed to the HTTP library correctly
  - verify flag wiring is correct (default secure)

**Expected output:** Unit tests that fail loudly if safety rules are violated.

---

### 6) Run verification gates
**Goal:** Match repo "definition of done" patterns.

- Run the repo's verification gates described in `AGENTS.md` (tests, lint, type checks, etc.).
- Ensure CI-equivalent checks pass locally.

**Expected output:** Green test suite and stable client behavior.

## Verification checklist

Before declaring success:
- [ ] Dry-run **hard-blocks** all write-classified requests
- [ ] Retry configuration is **explicit** (methods + statuses) and **bounded**
- [ ] No retries for non-idempotent methods unless explicitly justified and tested
- [ ] Auth tokens are never logged and are redacted in error paths
- [ ] Timeouts/TLS settings preserve secure defaults
- [ ] Unit tests cover: gating, retries, auth, and failure behavior

## Troubleshooting

### Symptom: Writes happen during dry-run
Likely cause:
- Write classification is incomplete (missed `PUT/PATCH` or a helper bypasses the gate)

Fix:
- Centralize classification + gating in one place
- Add a regression test that asserts the blocked call path

---

### Symptom: Duplicate actions after transient failures
Likely cause:
- Retries expanded to `POST/DELETE` or write-like operations

Fix:
- Restrict allowed retry methods
- Add tests that assert "no retries" for writes

---

### Symptom: Requests hang longer than expected
Likely cause:
- No timeout, or backoff + retries multiplied total time

Fix:
- Add explicit timeouts
- Bound total retries and ensure backoff is capped
- Add a test that asserts the maximum number of attempts

---

### Symptom: Random 401s across the app after auth change
Likely cause:
- Header construction changed shape or token plumbing broke

Fix:
- Add focused unit tests for header composition
- Ensure redaction logic doesn't accidentally remove the header on outbound calls

## Examples

### SHOULD trigger
- "Increase the retry backoff in src/jfin/client.py without retrying POST requests."
- "Add per-request timeouts to the Jellyfin client and ensure tests cover it."
- "Fix auth header formatting and make sure tokens never appear in logs."

### SHOULD NOT trigger
- "Which Jellyfin endpoint returns the user's favorites?"
- "Add a new API call to fetch item images."
- "Change how we sort media items in the UI."

## References and resources

- `AGENTS.md` — verification gates and repo-wide safety rules (always follow)
- `src/jfin/client.py` — primary implementation surface for this skill (see `metadata.primary_files`)

## Changelog

- 2026-03-04 (v1.1.0): Rewritten as an execution-focused runbook with explicit scope, decision rules,
  verification, troubleshooting, and trigger examples, aligned to skill authoring guidance.