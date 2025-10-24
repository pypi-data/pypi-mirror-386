---
title: SIG-liminal-inbox-prototype
status: complete
last_updated: 2025-10-07
---

# SIG-liminal-inbox-prototype

Tracks preparation and ingestion of the liminal-ready bundle for the inbox prototype.

## Artifacts
- Bundle: `var/bundles/liminal/mcp-orchestration-bundle.zip`
- Overview: `docs/reference/overview.md`
- Telemetry: `var/telemetry/events.jsonl`
- Source PR: feature/release-b

## Validation
- Bundle packaged locally and by CI; archived as workflow artifact and attached to the Release B tag.
- Validators executed locally with success (manifest/behavior/scenario) and telemetry events recorded.
- Ingestion confirmed on liminal inbox prototype using bundle `var/bundles/liminal/mcp-orchestration-bundle.zip`.
  - SHA256: `4ea87f798ae0f1d94db83c28f6bf3cd63db2a2a9a7534f30a942a3960eb4ddbd`
  - Release: https://github.com/liminalcommons/mcp-orchestration/releases/tag/release-b

## Confirmation
- 2025-10-07: chora-liminal posted ingestion evidence for the Release B bundle. This signal is now closed with artifacts and references recorded above.

## Status
- complete — ingestion verified; artifacts linked above. Follow-ups tracked in Release C plan (telemetry emitter migration).
