# Capability: MCP Registry Manage

Provides registry lifecycle operations for MCP servers.

## Behaviors
- @behavior:MCP.REGISTRY.MANAGE
- @status:draft

Behavior Specs:
- docs/capabilities/behaviors/mcp-registry-manage.feature

## Value Scenarios
- ID: mcp.registry.manage.create-doc — Status: ready
  - Guide: docs/how-to/create-doc.md
  - Tests: tests/value-scenarios/test_create_doc.py; references BDD feature above

## Integrations
- CLI: mcp-orchestrator manifest-validate
- MCP tools: forthcoming
