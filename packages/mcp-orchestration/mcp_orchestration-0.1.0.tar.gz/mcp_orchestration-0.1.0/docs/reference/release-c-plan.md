---
title: Release C Plan — Platform Emitter Migration & Runtime Interop
status: draft
version: 0.1.0
last_updated: 2025-10-07
---

# Release C Plan — MCP Orchestration

This plan tracks MCP orchestration preparation for Release C, focusing on migrating telemetry to the platform `TelemetryEmitter` and aligning with runtime interop workstreams described in ecosystem documents.

Aligns with:
- docs/ecosystem/solution-approach-report.md (Release C goals: protocol-first pilot, hardened indexer)
- docs/ecosystem/solution-neutral-intent.md (capability/behavior/value scenario definitions)

## Objectives
- Replace local telemetry shim with platform `TelemetryEmitter`; standardize event schema/labels.
- Validate telemetry through CI and include dashboard pointers once available.
- Keep repository overview current; maintain freshness gate.
- Coordinate with discovery/indexer changes as needed for capability publication.

## Work Items
- [ ] Import and wire platform `TelemetryEmitter` (config via env/secrets as required).
- [ ] Update docs/how-to/telemetry.md to reflect platform emitter usage.
- [ ] Update CI to exercise platform emitter and archive samples.
- [ ] Add migration note and link to platform change signal `SIG-telemetry-adoption`.
- [ ] Confirm no schema deviations; document any via change signals.
 - [ ] Remove local shim (`src/mcp_orchestrator/telemetry.py`) after migration; update tests accordingly.
 - [ ] Add backout plan (toggle to local shim) if platform emitter is unavailable.
 - [ ] Bump version and annotate changelog/release notes with migration details.

## Backlog / Follow-ups
- Add dashboard link(s) once platform telemetry dashboards are available.
- Coordinate with discovery/indexer team for any related schema or index updates.

## Acceptance Criteria
1. CLI emits platform-compliant telemetry; local and CI validation succeed.
2. Documentation updated; signals reference cross-repo adoption.
3. Overview freshness gate retained; zero drift in manifests/scenarios.

## Evidence & Links
- Platform signal: `SIG-telemetry-adoption` (referenced from capability signal).
- Telemetry samples archived in CI artifacts.
