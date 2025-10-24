---
title: Release Plan B — Telemetry & Liminal Integration
status: in_progress
version: 0.2.0
last_updated: 2025-10-07
---

# Release Plan B — MCP Orchestration

This plan operationalizes the Release B scope for the mcp-orchestration capability provider, aligned with ecosystem intent and approach documents. It captures objectives, current status, verification evidence, and next steps.

Aligns with:
- docs/ecosystem/solution-neutral-intent.md (capability/behavior/manifest/value-scenario definitions; change signals)
- docs/ecosystem/solution-approach-report.md (Release B objectives and change signals; naming conventions)

## Objectives
- Emit telemetry for key CLI flows using a shared emitter (initial shim, platform emitter next).
- Publish and enforce repository overview freshness alongside manifests and value scenarios.
- Package liminal-ready bundles (manifest + overview + telemetry + signals) for inbox ingestion.
- Track progress via change signals and keep documentation up to date.

## Workstreams & Status

### 1) Telemetry Adoption
- [x] CLI emits events to `var/telemetry/events.jsonl` for `manifest-validate`, `behavior-validate`, `scenario-validate`.
- [x] Documented usage and event shape: `docs/how-to/telemetry.md`.
- [x] CI uploads telemetry events as artifact.
- [ ] Migrate to platform TelemetryEmitter (replace shim and update docs/CI).

### 2) Repository Overview Publication
- [x] Generator script: `scripts/generate_repo_overview.py` → `docs/reference/overview.md`.
- [x] README links to overview and telemetry how-to.
- [x] CI freshness gate regenerates overview and fails if stale.

### 3) Liminal Bundle Prep
- [x] Bundle created with manifest, overview, signal, and telemetry under `var/bundles/liminal/`.
- [x] How-to updated: `docs/how-to/share-with-liminal.md` (local + CI packaging).
- [x] CI packages and uploads `liminal-bundle` artifact.
- [ ] Verify ingestion on liminal inbox prototype and record result.

### 4) Governance & Signals
- [x] Weekly progress captured in `docs/reference/signals/SIG-capability-onboard.md`.
- [x] Liminal ingest signal created: `docs/reference/signals/SIG-liminal-inbox-prototype.md` (prepared).
- [ ] Reference platform signal `SIG-telemetry-adoption` once published.

## Acceptance Criteria
1. Telemetry events generated for validator commands; basic emitter outputs tested.
2. Repository overview kept in sync with manifest and scenarios (CI enforcement).
3. Liminal bundle available and validated by inbox prototype; evidence recorded in signals.
4. Release documentation updated with links to telemetry, overview, and bundle.

## Evidence & Artifacts
- Telemetry: `var/telemetry/events.jsonl`
- Overview: `docs/reference/overview.md`
- Bundle (zip): `var/bundles/liminal/mcp-orchestration-bundle.zip`
- Signals: `docs/reference/signals/SIG-capability-onboard.md`, `docs/reference/signals/SIG-liminal-inbox-prototype.md`
- CI: `.github/workflows/chora-ci.yml`

## Verification (Latest)
- Validators (local):
  - `PYTHONPATH=src python -m mcp_orchestrator.cli manifest-validate manifests/star.yaml` → success
  - `PYTHONPATH=src python -m mcp_orchestrator.cli behavior-validate docs/capabilities/behaviors` → success
  - `PYTHONPATH=src python -m mcp_orchestrator.cli scenario-validate manifests/star.yaml` → success
- Tests: `PYTHONPATH=src pytest -q` → passing
- Overview: generated and checked by CI freshness gate
- Bundle: packaged locally and in CI (uploaded as `liminal-bundle`)

## Implementation Notes
- CLI emits events via local shim `mcp_orchestrator.telemetry` to ensure a stable JSONL format for Release B.
- Freshness gate: CI regenerates overview and fails on diff to prevent stale docs in PRs.
- Naming follows `solution-approach-report.md` conventions (e.g., `mcp.registry.manage`, `SIG.*`).

## Next Steps
- Replace emitter shim with platform TelemetryEmitter and update docs/CI; cross-reference platform `SIG-telemetry-adoption`.
- Validate liminal inbox ingestion; mark `SIG-liminal-inbox-prototype` complete with evidence.
- Continue weekly progress entries in `SIG-capability-onboard` while Release B is active.

