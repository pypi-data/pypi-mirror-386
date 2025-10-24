# MCP Namespace Registry

**Project:** [Your Project Name]
**Namespace:** `[your-namespace]`
**Convention:** Chora MCP Conventions v1.0
**Status:** Active
**Last Updated:** [YYYY-MM-DD]

---

## For LLM Agents: How to Use This Document

This is the **canonical namespace registry** for this project. Use this document to:

1. **Understand the namespace** - All MCP tools and resources are documented here
2. **Register new tools** - Follow the instructions in "Adding Tools" section below
3. **Register new resources** - Follow the instructions in "Adding Resources" section below
4. **Validate changes** - Run validation scripts before committing (if enabled)

**Key Information:**
- Namespace: `[your-namespace]`
- Convention: Chora MCP Conventions v1.0
- Validation: [Enabled/Disabled - check project configuration]
- Namespacing: [Enabled/Disabled - check project configuration]

**Important**: After generating your project, update the placeholders in brackets `[like this]` with your actual project information.

---

## Overview

This document registers the MCP namespace and all tools/resources for this project.

### Naming Modes

**If using namespaced mode:**
- Tools are namespaced to avoid conflicts: `namespace:tool_name`
- Resources use URI scheme: `namespace://type/id`
- Designed for multi-server MCP environments

**If using standalone mode:**
- Tools use simple names without namespace prefix
- Resources use custom URI schemes
- Optimized for single-server deployments

---

## Registered Tools

### Example Tools (Update This Section)

| Tool Name | Full Name | Description | Version |
|-----------|-----------|-------------|---------|
| example_tool | [namespace]:example_tool | Example tool demonstrating naming | 0.1.0 |
| hello_world | [namespace]:hello_world | Simple hello world tool | 0.1.0 |

### How to Add a New Tool

**Step 1: Implement the tool**
- Open file: `src/[package_name]/mcp/server.py`
- Add your tool implementation using the `@server.call_tool` decorator

**Step 2: Name the tool**
- If namespacing is enabled: Use `make_tool_name("your_tool_name")` helper
- If namespacing is disabled: Choose a descriptive snake_case name
- Tool names must:
  - Start with a lowercase letter (a through z)
  - Continue with lowercase letters, digits, or underscores
  - Be descriptive and indicate the tool's purpose

**Step 3: Update this registry**
- Add a row to the "Registered Tools" table above
- Include: tool name, full name (with namespace if applicable), description, version

**Step 4: Validate (if enabled)**
- Run: `python scripts/validate_mcp_names.py`
- Fix any validation errors before committing

**Step 5: Test the tool**
- Run the MCP server locally
- Test using an MCP client (e.g., mcp-n8n, Claude Desktop)
- Verify the tool appears and works as expected

---

## Registered Resources

### Example Resources (Update This Section)

| Resource URI | Type | Description | Version |
|--------------|------|-------------|---------|
| [namespace]://examples/1 | Example | Example resource | 0.1.0 |

### How to Add a New Resource

**Step 1: Implement the resource**
- Open file: `src/[package_name]/mcp/server.py`
- Add your resource implementation using the `@server.list_resources` or `@server.read_resource` decorator

**Step 2: Choose a URI scheme**
- If using URI scheme: `namespace://resource_type/resource_id`
- If using custom scheme: Choose a descriptive, consistent pattern
- Resource URIs must:
  - Be unique across your namespace
  - Follow a consistent structure
  - Be descriptive of the resource type and identifier

**Step 3: Update this registry**
- Add a row to the "Registered Resources" table above
- Include: resource URI, type, description, version

**Step 4: Test the resource**
- Run the MCP server locally
- List resources using an MCP client
- Read specific resources to verify they work

---

## Naming Conventions

### Tool Names

**Format**: `tool_name` (standalone) or `namespace:tool_name` (namespaced)

**Rules**:
- Start with a lowercase letter (a through z)
- Continue with lowercase letters, digits, or underscores
- Use snake_case format (e.g., `create_task`, `list_documents`)
- Be descriptive and action-oriented
- Avoid abbreviations unless widely recognized

**Examples**:
- ✅ `create_task`
- ✅ `list_documents`
- ✅ `parse_markdown`
- ❌ `ct` (too abbreviated)
- ❌ `CreateTask` (wrong case)
- ❌ `create-task` (wrong separator)

### Resource URIs

**Format**: `namespace://resource_type/resource_id`

**Rules**:
- Resource type should be plural (e.g., `tasks`, `documents`)
- Resource ID can be a string or number
- Use consistent structure across all resources
- Make URIs predictable and discoverable

**Examples**:
- ✅ `myproject://tasks/123`
- ✅ `myproject://documents/readme.md`
- ✅ `myproject://users/alice`
- ❌ `myproject://Task/123` (wrong case)
- ❌ `tasks/123` (missing scheme and namespace)

### Namespace

**Format**: Lowercase letters and digits only, 3-20 characters

**Rules**:
- Start with a lowercase letter (a through z)
- Continue with lowercase letters or digits
- No special characters (no underscores, dashes, etc.)
- Should be unique across the MCP ecosystem
- Often derived from project name (e.g., `mcpn8n`, `claudecode`)

**Examples**:
- ✅ `myproject`
- ✅ `awesome123`
- ✅ `xyz`
- ❌ `my-project` (contains dash)
- ❌ `MyProject` (wrong case)
- ❌ `ab` (too short, minimum 3 characters)

---

## Validation

### Automatic Validation (if enabled)

If your project has `mcp_validate_names` enabled:

**Runtime validation**:
- Tool names are validated when registered
- Resource URIs are validated when created
- Invalid names throw exceptions with helpful error messages

**Pre-commit validation**:
- Script: `scripts/validate_mcp_names.py`
- Checks all tool names and resource URIs
- Prevents invalid names from being committed

**To run validation**:
```bash
python scripts/validate_mcp_names.py
```

### Manual Validation (if disabled)

If validation is not enabled:

- Carefully review all tool names and resource URIs
- Follow the conventions documented above
- Test thoroughly to ensure names work as expected
- Consider enabling validation for future projects

---

## Migration Guide

### Changing Namespace

If you need to change your namespace:

**Step 1: Update code**
- Edit `src/[package_name]/mcp/__init__.py`
- Change the `NAMESPACE` constant

**Step 2: Update this file**
- Change all instances of the old namespace to the new one
- Update the namespace in the header

**Step 3: Update tool registrations**
- If using `make_tool_name()`, names update automatically
- If using hardcoded names, update each one manually

**Step 4: Test**
- Run all tests
- Verify MCP server works with new namespace
- Check that clients can discover tools with new names

**Step 5: Notify users**
- Namespace changes are breaking
- Provide migration instructions
- Consider keeping old namespace supported temporarily

### Adding Namespacing

If you started without namespacing and want to add it:

**Step 1: Enable namespacing**
- This requires regenerating from the template with `mcp_enable_namespacing=true`
- Or manually updating the configuration

**Step 2: Update tool names**
- Convert from `tool_name` to `namespace:tool_name`
- Use `make_tool_name()` helper for consistency

**Step 3: Update resource URIs**
- Convert to `namespace://type/id` format
- Ensure consistency across all resources

**Step 4: Update this registry**
- Add "Full Name" column to tools table
- Update resource URI examples

---

## How to Update This File

**When adding tools**:
1. Edit this file: `NAMESPACES.md`
2. Update the "Registered Tools" table
3. Update the "Last Updated" date at the top
4. Commit the changes with a descriptive message

**When adding resources**:
1. Edit this file: `NAMESPACES.md`
2. Update the "Registered Resources" table
3. Update the "Last Updated" date at the top
4. Commit the changes

**When updating metadata**:
- Update the header section (Project, Namespace, Status)
- Update the "Last Updated" date
- Document changes in your project's changelog

---

## References

**Chora MCP Conventions v1.0** - Full specification
https://github.com/liminalcommons/chora-base/blob/main/docs/standards/CHORA_MCP_CONVENTIONS_v1.0.md

**MCP Naming Best Practices** - Practical guide
https://github.com/liminalcommons/chora-base/blob/main/docs/reference/mcp-naming-best-practices.md

**Model Context Protocol** - Core protocol spec
https://modelcontextprotocol.io/

**mcp-n8n Gateway** - Example of namespace routing
https://github.com/liminalcommons/mcp-n8n

---

## Changelog

### [Version] ([Date])
- Initial namespace registration
- Namespace: `[your-namespace]`
- Convention: Chora MCP Conventions v1.0
- Example tools: example_tool, hello_world

---

**Maintained by:** [Your Name] ([your@email.com])

---

## For LLM Agents: Quick Reference

**To add a tool:**
1. Implement in `src/[package]/mcp/server.py`
2. Name it: `make_tool_name("your_tool")` (if namespacing enabled)
3. Add to "Registered Tools" table above
4. Run `python scripts/validate_mcp_names.py` (if validation enabled)
5. Update "Last Updated" date at top of this file

**To add a resource:**
1. Implement in `src/[package]/mcp/server.py`
2. Use URI: `namespace://type/id`
3. Add to "Registered Resources" table above
4. Update "Last Updated" date at top of this file

**To check namespace:**
- Look at the top of this file under "Namespace:"
- Or check `src/[package]/mcp/__init__.py` for the `NAMESPACE` constant

**Naming rules (remember these)**:
- Tool names: `snake_case`, start with letter
- Namespaces: `lowercase`, no special chars, 3-20 chars
- Resource URIs: `namespace://plural_type/id`
