@behavior:MCP.REGISTRY.MANAGE
@status:draft
Feature: Manage MCP server registry
  As an orchestrator
  I want to manage MCP servers in a registry
  So that clients can discover and use them consistently

  Background:
    Given an empty MCP server registry

  Scenario: Register a new MCP server
    When I register a server with id "example.srv" and endpoint "https://mcp.example.test"
    Then the registry contains server "example.srv" with endpoint "https://mcp.example.test"

  Scenario: Prevent duplicate server registration
    Given a server "dup.srv" exists in the registry
    When I attempt to register server "dup.srv" again
    Then the operation fails with reason "already_exists"

  Scenario: List registered servers
    Given servers exist in the registry
      | id          | endpoint                         |
      | a.srv       | https://a.test                   |
      | b.srv       | https://b.test                   |
    When I list servers
    Then I see at least the following servers
      | id          |
      | a.srv       |
      | b.srv       |

  Scenario: Unregister a server
    Given a server "to-remove.srv" exists in the registry
    When I unregister server "to-remove.srv"
    Then the registry does not contain server "to-remove.srv"

