# SIG-capability-onboard

Tracks onboarding of manifests/behaviors to Chora platform standards.

## Tasks
- [x] Validate star.yaml against chora-validator
- [x] Implement behaviors/interfaces
- [x] Emit onboarding signal once complete

## Validation Log
- 2025-10-06: Manifest: `PYTHONPATH=src python -m mcp_orchestrator.cli manifest-validate manifests/star.yaml` → success.
- 2025-10-06: Behaviors: `PYTHONPATH=src python -m mcp_orchestrator.cli behavior-validate docs/capabilities/behaviors` → success.
- 2025-10-06: Scenarios: `PYTHONPATH=src python -m mcp_orchestrator.cli scenario-validate manifests/star.yaml` → success for `mcp.registry.manage.create-doc`.
- 2025-10-06: Pytest: `PYTHONPATH=src pytest -q` → all tests passed.

## Notes
- Manifest enriched with tags, dependencies (tooling/runtime), and telemetry signal `SIG.capability.mcp.registry.onboard`.
- Behavior definitions added under `docs/capabilities/behaviors/` using Gherkin for `MCP.REGISTRY.MANAGE`.
- Value scenario `mcp.registry.manage.create-doc` added with guide and stub test; will connect to full automation in CI.

## Status
- closed (Release A complete)
- Release B: telemetry integration started; events emitted to `var/telemetry/events.jsonl` and uploaded via CI artifact.
- Overview generated at `docs/reference/overview.md`.

### Release B Log — 2025-10-07
- Validators: manifest, behaviors, scenarios → success (local).
- Telemetry events written (see `var/telemetry/events.jsonl`).
- Overview generated (`docs/reference/overview.md`).
- Liminal bundle packaged (`var/bundles/liminal/mcp-orchestration-bundle.zip`).
- Liminal signal created: `docs/reference/signals/SIG-liminal-inbox-prototype.md` (status: prepared).

### Weekly Progress — 2025-10-07
- Implemented CI overview freshness gate.
- Prepared liminal bundle and created ingestion signal.
- Next: coordinate `SIG-telemetry-adoption` with platform and migrate to platform emitter.

### Weekly Progress — 2025-10-07 (closure validation)
- Validators: manifest, behaviors, scenarios → success.
- Pytest: all tests passed.
- Telemetry counts (JSONL): `manifest.validate=1`, `behavior.validate=1`, `scenario.validate=1`.
- Liminal bundle SHA256: `4ea87f798ae0f1d94db83c28f6bf3cd63db2a2a9a7534f30a942a3960eb4ddbd` (size: 2432 bytes).
- Pending coordination: reference platform `SIG-telemetry-adoption` once confirmed.

### Coordination — 2025-10-07
- Platform signal confirmed: `SIG-telemetry-adoption` (referenced by Release B digest). This repo emits telemetry per shared guidance and will track migration to the shared emitter in Release C.
