# Repository Overview — MCP Orchestration

- id: `mcp-orchestration`
- version: `0.0.1`
- owner: `team-mcp`
- lifecycle_stage: `operate`
- tags: chora, capability-provider, mcp, registry, orchestration

## Capabilities
- `mcp.registry.manage`
  - behavior: `MCP.REGISTRY.MANAGE` status=`draft` ref=`docs/capabilities/mcp-registry-manage.md`

## Value Scenarios
- `mcp.registry.manage.create-doc` — status=`ready`
  - guide: `docs/how-to/create-doc.md`
  - test: `tests/value-scenarios/test_create_doc.py`
  - test: `docs/capabilities/behaviors/mcp-registry-manage.feature`

## Telemetry Signals
- `SIG.capability.mcp.registry.onboard` — status=`in_progress` doc=`docs/reference/signals/SIG-capability-onboard.md`

## Dependencies
- `chora-validator` type=`tool` version=`>=0.0.1` scope=`dev`
- `mcp.runtime` type=`service` version=`>=1.0.0` scope=`runtime`

