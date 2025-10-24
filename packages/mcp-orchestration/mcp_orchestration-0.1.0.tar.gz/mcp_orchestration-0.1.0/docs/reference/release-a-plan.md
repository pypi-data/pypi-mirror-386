# Release A Plan — MCP Orchestration Onboarding

This plan tracks capability-provider tasks required to complete Chora Release A from the MCP orchestration perspective.

## Objectives
- Adopt Chora manifest/behavior standards.
- Define at least one value scenario demonstrating the capability.
- Integrate and run `chora-validator` in CI.
- Emit change signals documenting readiness.
- Provide manifest/behavior samples for discovery and compatibility checks.

## Work Items
- [x] Update `manifests/star.yaml` with complete metadata (tags, dependencies, telemetry signals).
- [x] Tag behaviors (BDD or JSON) with `@behavior` and `@status` metadata.
- [x] Run `mcp-orchestrator manifest-validate manifests/star.yaml` locally and in CI.
- [x] Add a value scenario definition (metadata + doc + automated test) for `mcp.registry.manage.create-doc`.
- [x] Populate `docs/reference/signals/SIG-capability-onboard.md` with status updates.
- [ ] Add telemetry stubs/logs as per telemetry schema when available. *(Deferred to Release B; see `docs/reference/release-b-plan.md`.)*

## Acceptance Criteria
- Manifest passes Chora validator without overrides.
- Behavior spec exists for each declared capability.
- Value scenario `mcp.registry.manage.create-doc` documented and runnable (manual guide + automated test).
- Change signal `SIG-capability-onboard` marked complete with notes and timestamp.
- CI pipeline runs validator/test suite.

## Verification (Release A Templates Adoption)

- CI workflow added at `.github/workflows/chora-ci.yml` (runs manifest/behavior/scenario validators + pytest).
- Local validator runs (exit code 0):
  - Manifest: `PYTHONPATH=src python -m mcp_orchestrator.cli manifest-validate manifests/star.yaml` → success
  - Behaviors: `PYTHONPATH=src python -m mcp_orchestrator.cli behavior-validate docs/capabilities/behaviors` → success
  - Scenarios: `PYTHONPATH=src python -m mcp_orchestrator.cli scenario-validate manifests/star.yaml` → success
- Pytest: `PYTHONPATH=src pytest -q` → all tests passed locally.

Scenario status: ready (guide and tests referenced; validator passing).

## Release A Closure Summary (Implemented 2025-10-06)
- Shared CI pipeline validates manifest, behaviors, and value scenario on every push.
- Change signal `docs/reference/signals/SIG-capability-onboard.md` marked complete with validator output links.
- Telemetry adoption item migrated to Release B workstream alongside new platform emitter.
