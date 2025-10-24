---
title: Create MCP Registry Documentation Entry
status: draft
last_updated: 2025-10-05
---

# How To: Create Registry Documentation Entry

This guide covers the value scenario `mcp.registry.manage.create-doc`.

Objective: Produce a discoverable documentation entry for an MCP server in the registry so users can find connection parameters and usage notes.

Prerequisites
- Access to the MCP registry store (local or remote)
- The orchestrator CLI `mcp-orchestrator`

Steps
1. Identify the server ID and endpoint. Example: `example.srv`, `https://mcp.example.test`.
2. Use the orchestrator to register the server (or ensure it exists):
   - `mcp-orchestrator` (or API) to add/update the entry.
3. Create a documentation page or section for the server in your docs site.
   - Include: server ID, endpoint, auth requirements, supported tools, contact/owner.
4. Verify the entry appears in your docs navigation and search.

Expected Result
- The server `example.srv` is present in the registry and a docs entry exists with endpoint and basic usage details.

Automation Notes
- See BDD feature in `docs/capabilities/behaviors/mcp-registry-manage.feature`.
- A stub automated test exists in `tests/value-scenarios/test_create_doc.py`.

