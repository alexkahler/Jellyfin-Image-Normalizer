# Repo Map

Quick orientation map for the Jellyfin Image Normalizer repository.

## Top-Level Structure

| Path | Short Description |
| --- | --- |
| `src/jfin/` | Core Python package: CLI, pipeline orchestration, Jellyfin API client, config, imaging, backup, and route-fence runtime checks. |
| `tests/` | Unit/integration tests for runtime modules plus governance checks. |
| `tests/characterization/` | Characterization contract harnesses and tests (CLI, config, imaging, safety). |
| `tests/golden/` | Golden image fixtures and expected outputs used by imaging tests. |
| `project/` | Governance artifacts (verification contract, parity/route-fence baselines) and validator scripts. |
| `plans/` | Work item and slice planning documents. |
| `docs/` | User/developer documentation, technical notes, and visual comparison assets. |
| `.agents/skills/` | Local skill definitions used by coding agents in this repository. |
| `.github/workflows/` | CI pipeline definitions and enforcement wiring. |
| `backup/` | Local backup/staging data used by backup/restore workflows. |
| `README.md` | Project overview, setup, and usage entrypoint for contributors/users. |
| `AGENTS.md` | Canonical in-repo operating contract for agent behavior and verification expectations. |
| `WORK_ITEMS.md` | Work tracking summary tied to planned slices/tasks. |
| `CHANGELOG.md` | Change history and release notes. |

## Core Runtime Modules (`src/jfin/`)

| Module | Purpose |
| --- | --- |
| `cli.py` | Main CLI entrypoint and command wiring. |
| `pipeline.py` | End-to-end orchestration of discovery, transform, and upload behavior. |
| `client.py` | Jellyfin HTTP API access layer and request semantics. |
| `config.py` | Configuration schema/loading/validation. |
| `discovery.py` | Item/library discovery logic from Jellyfin. |
| `imaging.py` | Image normalization and format/size processing logic. |
| `backup.py` | Backup/restore snapshot handling helpers. |
| `route_fence.py` | Runtime API route safety enforcement helpers. |
| `logging_utils.py` | Logging configuration/utilities. |
| `state.py` | Execution state model helpers. |
| `constants.py` | Shared constants used across runtime modules. |
| `__main__.py` | `python -m jfin` module launcher. |

