# mcp-orchestration

MCP server orchestration and management tools

## Overview

**mcp-orchestration** is a Model Context Protocol (MCP) server that provides centralized configuration management and orchestration for MCP client applications. It enables cryptographically signed, content-addressable storage of client configurations with automated diff detection and update recommendations.

This project follows the MCP specification and can be integrated with:
- Claude Desktop
- Cursor
- Other MCP-compatible clients

## Features

- **Cryptographic Signatures** - Ed25519 signatures for configuration integrity and authenticity
- **Content-Addressable Storage** - SHA-256 based artifact identification for immutable configs
- **Multi-Client Registry** - Support for multiple MCP clients (Claude Desktop, Cursor) with profile-based configs
- **Configuration Diff** - Intelligent comparison with field-level change detection
- **MCP Tools & Resources** - 4 tools (list_clients, list_profiles, get_config, diff_config) and 2 resources
- **CLI Initialization** - Quick-start command to generate signed sample configurations
- **Comprehensive Testing** - 67 passing tests with full integration coverage
## Installation

### From PyPI (Recommended)

```bash
pip install mcp-orchestration
```

### From Source

```bash
# Clone repository
git clone https://github.com/liminalcommons/mcp-orchestration.git
cd mcp-orchestration

# Install with development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks (for contributors)
pre-commit install
```

### Initialize Configuration Storage

After installation, generate signed sample configurations:

```bash
mcp-orchestration-init
```

This creates:
- Ed25519 signing keys at `~/.mcp-orchestration/keys/`
- Sample configurations for supported clients
- Content-addressable artifact storage

## Configuration

### Environment Variables

Create a `.env` file:

```env
# Application configuration
MCP_ORCHESTRATION_LOG_LEVEL=INFO

# Add your configuration here
```

### Client Configuration

#### Claude Desktop (macOS)

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "mcp-orchestration": {
      "command": "python3",
      "args": ["-m", "mcp_orchestrator.mcp.server"],
      "env": {
        "PYTHONPATH": "/path/to/mcp-orchestration/src"
      }
    }
  }
}
```

For installed package (after PyPI release):
```json
{
  "mcpServers": {
    "mcp-orchestration": {
      "command": "mcp-orchestration"
    }
  }
}
```

#### Cursor IDE

Add to Cursor settings JSON:

```json
{
  "mcp": {
    "servers": {
      "mcp-orchestration": {
        "command": "python3",
        "args": ["-m", "mcp_orchestrator.mcp.server"]
      }
    }
  }
}
```
## Usage

Once configured in your MCP client (Claude Desktop, Cursor, etc.), the following tools are available:

### MCP Tools

**list_clients** - List all supported MCP client families:
```
Returns: client_id, display_name, platform, capabilities, profiles
```

**list_profiles** - List profiles for a specific client:
```
Input: client_id (e.g., "claude-desktop")
Returns: profile_id, display_name, artifact_id, signature
```

**get_config** - Retrieve a signed configuration artifact:
```
Input: client_id, profile_id (default: "default"), artifact_id (optional)
Returns: Full signed artifact with payload, signature, metadata
```

**diff_config** - Compare local config against stored version:
```
Input: client_id, profile_id, local_payload
Returns: Diff status (up-to-date/outdated/diverged), changes, recommendation
```

### CLI Commands

```bash
# Initialize configuration storage with sample configs
mcp-orchestration-init

# Initialize to custom location
mcp-orchestration-init --storage-path /custom/path

# Regenerate existing configurations
mcp-orchestration-init --regenerate
```
## Development

### Quick Reference

**Discover all available commands:**
```bash
just --list
```

**Common tasks:**
```bash
just test            # Run test suite
just lint            # Check code style
just pre-merge       # Run all checks (required before PR)
just build           # Build distribution packages
just help            # Show common workflows
```

The [justfile](justfile) is self-documenting - run `just` or `just --list` to see all commands.

### Common Workflows

**Running tests:**
```bash
just test           # Full test suite
just smoke          # Quick smoke tests (~10 sec)
just test-coverage  # With coverage report
```

**Code quality:**
```bash
just lint           # Check style
just lint-fix       # Auto-fix issues
just format         # Format code
just typecheck      # Type checking
just check          # All quality checks
```

**Before creating PR:**
```bash
just pre-merge      # Run lint + test + coverage (required)
```

**Building & releasing:**
```bash
just build                  # Build distribution packages
just prepare-release patch  # Bump version, update CHANGELOG
just publish-test           # Publish to TestPyPI
just publish-prod           # Publish to PyPI
```

**Application:**
```bash
just run            # Start the application
mcp-orchestration  # Or run directly
```

### Without `just` (Fallback)

If `just` installation fails, use commands directly:

| Task | Command |
|------|---------|
| Run tests | `pytest` |
| Build | `./scripts/build-dist.sh` |
| Lint | `ruff check src/mcp_orchestration tests` |
| Format | `black src/mcp_orchestration tests` |
| Pre-merge | `./scripts/pre-merge.sh` |
| Type check | `mypy src/mcp_orchestration` |

See [justfile](justfile) for complete command mappings.
## Documentation

This project follows the [Diátaxis framework](https://diataxis.fr/) with three documentation directories:

### For End Users (user-docs/)
Learn how to **use** mcp-orchestration:
- **[Getting Started Tutorial](user-docs/tutorials/01-getting-started.md)** - Learn the basics
- **[How-To Guides](user-docs/how-to/)** - Solve specific problems
- **[API Reference](user-docs/reference/)** - Look up specifications
- **[Explanations](user-docs/explanation/)** - Understand concepts

### For Project Planning (project-docs/)
Project roadmap and architecture decisions:
- **[ROADMAP.md](project-docs/ROADMAP.md)** - Long-term vision and milestones
- **[Release Notes](project-docs/releases/)** - Version history and changes
- **[Architecture Decisions](project-docs/decisions/)** - ADRs and design choices

### For Contributors (dev-docs/)
Learn how to **build** mcp-orchestration:
- **[CONTRIBUTING.md](dev-docs/CONTRIBUTING.md)** - Contribution guidelines
- **[DEVELOPMENT.md](dev-docs/DEVELOPMENT.md)** - Developer setup and architecture
- **[TROUBLESHOOTING.md](dev-docs/TROUBLESHOOTING.md)** - Common development issues
- **[Vision Documents](dev-docs/vision/)** - Strategic design guidance
### For AI Coding Agents
- **[AGENTS.md](AGENTS.md)** - Machine-readable instructions (OpenAI/Google standard)
**Documentation Standard:**
- **[DOCUMENTATION_STANDARD.md](DOCUMENTATION_STANDARD.md)** - Writing guidelines and templates

## Project Principles

This project follows best practices for:

- **Code Quality** - Linting (ruff), formatting (black), type checking (mypy)
- **Testing** - Comprehensive test suite with 85%+ coverage
- **Documentation** - Clear, up-to-date documentation following Diátaxis framework
- **Agentic Coding** - Machine-readable instructions, stateful memory for AI agents
## License

MIT License - see [LICENSE](LICENSE)
## Related Projects

- [chora-base](https://github.com/liminalcommons/chora-base) - Python project template
- [chora-composer](https://github.com/liminalcommons/chora-composer) - Configuration-driven artifact generation
- [chora-platform](https://github.com/liminalcommons/chora-platform) - Shared platform tooling

---

🤖 Generated with [chora-base](https://github.com/liminalcommons/chora-base) template
