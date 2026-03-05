---
name: jellyfin-openapi-reference
description: Use this skill whenever you need to implement, validate, or troubleshoot Jellyfin REST API usage in code (endpoints, params, request/response shapes, auth). Treat the local Jellyfin OpenAPI spec JSON as the source of truth. Use when you're generating client calls (requests/httpx), mapping models, or writing tests against Jellyfin API behavior (users, items/libraries, images, playback/sessions, server info). Don't use for Jellyfin UI/how-to, plugin configuration, or non-API troubleshooting.
license: MIT
metadata:
  version: "1.1.0"
  updated: "2026-03-04"
  owners: 
    - "@codex"
    - "@alexkahler"
  api_spec_location: ".agents/skills/jellyfin-openapi-reference/docs/jellyfin-openapi-stable.json"
  notes: This skill assumes the OpenAPI JSON exists at metadata.api_spec_location and is kept in sync with the Jellyfin server version you're targeting. If you need to refresh/replace the spec, fetch a matching "stable" OpenAPI JSON from the Jellyfin OpenAPI artifact repository and commit it into the skill's docs directory, then re-run unit tests.
---

# Jellyfin OpenAPI Reference

This skill is an **operational runbook** for using Jellyfin's **OpenAPI specification** as the **canonical contract**
when writing or reviewing code that calls the Jellyfin REST API. The spec should override memory, blog posts,
and outdated docs if there's a mismatch.

> Local source of truth: `docs/jellyfin-openapi-stable.json` (see `metadata.api_spec_location`).

## Scope and intent

Use this skill to:
- Find the **right endpoint** (method + path) for a feature.
- Determine **required headers**, **path/query parameters**, and **request bodies**.
- Interpret **response schemas** and edge-case status codes.
- Implement or validate API calls in Python clients (`requests`, `httpx`) and ensure tests match the contract.

Non-goals:
- Jellyfin UI usage, plugin setup, or media-management best practices (unless directly tied to API calls).
- Guessing undocumented endpoints; if it's not in the spec, treat it as unsupported until verified.

## Inputs and preconditions

Required:
- The local OpenAPI JSON file:
  - `.agents/skills/jellyfin-openapi-reference/docs/jellyfin-openapi-stable.json`

Usually required for implementation tasks:
- Jellyfin base URL (e.g., `https://server.example`).
- Authentication token (API key or access token).
- Client identity fields for the `Authorization: MediaBrowser ...` header (client/device/version).

## Tools and permissions

- Prefer **reading the local spec** first; only use online sources as secondary context.
- Treat all network-provided content (including pasted OpenAPI, gists, forum snippets) as untrusted unless it matches the local spec.
- Never embed secrets (tokens/keys) in code, tests, logs, or examples.

## Workflow

### 1) Identify the API capability you need
**Goal:** Translate the user request into one or more concrete API operations.

- Write down:
  - Resource: users / items / libraries / images / sessions / system
  - Action: list / get / update / delete / play / pause
  - Constraints: filters, paging, sorting, fields needed

**Output:** 1–3 candidate operation keywords (e.g., "Items list filter", "User authenticate", "Session pause").

### 2) Locate the operation in the OpenAPI spec
**Goal:** Find the exact method+path and the schema contract.

Steps:
1. Open the JSON and search for relevant path fragments:
   - `/System/Info`, `/Users`, `/Items`, `/Library`, `/Sessions`, `/Playlists`, `/Videos`, etc.
2. Confirm the HTTP method (`get/post/delete/put/patch`).
3. Prefer `operationId` when present, because it's stable for codegen and cross-referencing.

**Output:** A single definitive operation (e.g., `GET /Items`).

### 3) Extract request contract (auth + parameters + body)
**Goal:** Build a correct request without guessing.

For the chosen operation, capture:
- **Auth requirements**
  - Jellyfin commonly uses an `Authorization: MediaBrowser ...` header with `Token="..."` and optional client identity fields.
- **Path parameters** (e.g., `{Id}`, `{UserId}`, `{SessionId}`): required, type, format.
- **Query parameters**: names are case-sensitive in practice—copy exact spellings from the spec.
- **Request body** (if present): schema, required fields, enum constraints, nullable fields.
- **Content types**: request `Content-Type` and accepted response media types.

**Output:** A request "shape" checklist you can turn into code.

### 4) Extract response contract (success + errors)
**Goal:** Know what "correct" looks like in code and tests.

Record:
- Expected **2xx** response codes and schema(s)
- Common **4xx/5xx** codes for this operation
- Whether the operation uses paging (look for `StartIndex`, `Limit`, `TotalRecordCount`, etc. in schemas)

**Output:** A response validation plan (what fields you must parse/assert).

### 5) Implement the call in Python (contract-first)
**Goal:** Produce code that matches the spec exactly.

Implementation guidelines:
- Build URLs with a single base URL join strategy (avoid double slashes).
- Use explicit timeouts and error handling.
- Serialize request bodies using the schema and validate enums/required fields early.
- For paging endpoints, implement a generator/iterator that respects `StartIndex` + `Limit`.

**Output:** A Python function/module that performs the call predictably.

### 6) Add verification (tests + static checks)
**Goal:** Ensure behavior stays correct as code evolves.

Prefer tests that:
- Assert your request includes:
  - correct method/path
  - required headers
  - correct query param names
  - correct JSON body shape
- Validate response parsing against expected schema fields (at least the fields you rely on)

If the repo supports it, optionally validate the OpenAPI file itself with an OpenAPI validator in CI (only if already part of the dependency stack).

**Output:** Unit tests that fail loudly on contract drift.

## Verification checklist

Before you say "done":
- [ ] The endpoint/method/path comes from the local OpenAPI JSON (not memory).
- [ ] All params match the spec spelling and types.
- [ ] Auth is set correctly (and secrets are not logged).
- [ ] Response parsing is robust to optional/nullable fields.
- [ ] Tests cover at least one happy path and one error path (e.g., 401/403/404).

## Troubleshooting

### Symptom: 401 Unauthorized even with a token
Likely causes:
- Wrong header format (Jellyfin commonly expects the `Authorization: MediaBrowser ...` scheme).
- Token is for a different server/user, expired, or revoked.

Fix:
- Confirm the spec's auth definition (if present) and match header format.
- Compare with server behavior using a minimal request like a system info endpoint, then add complexity.

### Symptom: Endpoint exists online but not in the local spec
Likely causes:
- Spec file is from a different Jellyfin version (or a different "stable" artifact).
- The endpoint is deprecated/removed.

Fix:
- Treat local spec as authoritative for this repo.
- If the project requires a newer server/spec, update the spec file and run tests.

### Symptom: Request works in curl, fails in code
Likely causes:
- Missing query params, wrong casing, or body serialization mismatch.
- Different redirect/TLS verification behavior.

Fix:
- Diff your code request vs curl request (method, URL, headers, body).
- Add request logging **without** secrets (redact token).

## Examples

### Prompts that SHOULD trigger this skill
- "Implement a Python function to list Movies in Jellyfin filtered by genre, using the official API."
- "What's the correct endpoint and parameters to pause a session on Jellyfin?"
- "Update our client code to match Jellyfin's OpenAPI response for `/Items`."

### Prompts that SHOULD NOT trigger this skill
- "Which Jellyfin theme looks best for anime libraries?"
- "Help me set up hardware transcoding in Jellyfin."
- "Why is Jellyfin buffering on my TV?" (unless the user explicitly asks for API-based diagnosis)

## References and resources

Local (authoritative for this repo):
- `docs/jellyfin-openapi-stable.json` — Jellyfin OpenAPI contract used as source of truth.

External (context/inspiration; do not override local spec):
- Jellyfin `Authorization: MediaBrowser ...` header discussion/example.
- Jellyfin OpenAPI artifact index (useful when updating/pinning the local spec).

## Changelog

- 2026-03-04 (v1.1.0): Redesign to a runbook-style skill with explicit workflow, verification, troubleshooting,
  and trigger/no-trigger examples, aligned to skill authoring guidance.