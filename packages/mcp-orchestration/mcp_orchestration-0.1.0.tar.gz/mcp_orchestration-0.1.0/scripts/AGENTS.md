# Automation Scripts for mcp-orchestration

**Purpose**: Reference guide for automation scripts and task runners.

**Parent**: See [../AGENTS.md](../AGENTS.md) for project overview and other topics.

---

## Quick Reference

**Primary Interface**: Use `just --list` to discover all available tasks.

```bash
# Discover all tasks
just --list

# Common tasks
just test              # Run test suite
just check             # Lint + typecheck + format
just pre-merge         # Full pre-merge validation
```

**Design Principle**: `just` is the ergonomic interface. Scripts in `scripts/` are the implementation. Agents should prefer `just` commands when available.

---

## Available Scripts

### Setup & Environment

**`setup.sh`** - One-command project setup
```bash
./scripts/setup.sh

# What it does:
# 1. Creates virtual environment (.venv)
# 2. Installs dependencies (pip install -e ".[dev]")
# 3. Installs pre-commit hooks
# 4. Runs smoke tests
# 5. Displays next steps
```

**`check-env.sh`** - Validate development environment
```bash
./scripts/check-env.sh

# Validates:
# - Python version (3.12+)
# - Required dependencies installed
# - Virtual environment activated
# - Environment variables set
```

**`venv-create.sh`** - Create virtual environment
```bash
./scripts/venv-create.sh
```

**`venv-clean.sh`** - Remove virtual environment
```bash
./scripts/venv-clean.sh
```

---

### Testing & Quality

**`pre-merge.sh`** - Full pre-merge validation
```bash
./scripts/pre-merge.sh

# Runs:
# - pre-commit run --all-files
# - pytest (full test suite)
# - Coverage check (≥85%)
# - Smoke tests
```

**`smoke-test.sh`** - Quick validation (<30 seconds)
```bash
./scripts/smoke-test.sh

# Validates:
# - Package imports successfully
# - Core functionality works
# - No obvious regressions
```

**`integration-test.sh`** - Full integration tests
```bash
./scripts/integration-test.sh

# Runs:
# - Integration test suite
# - End-to-end workflows
# - External dependency tests
```

---

### Development & Debugging

**`dev-server.sh`** - Run MCP server in development mode
```bash
./scripts/dev-server.sh

# Runs server with:
# - Debug logging enabled
# - Auto-reload on code changes
# - Development environment variables
```

**`diagnose.sh`** - Automated diagnostics
```bash
./scripts/diagnose.sh

# Checks:
# - Environment configuration
# - Dependency versions
# - Common issues
# - System health
```

---

### Build & Release

**`build-dist.sh`** - Build distribution packages
```bash
./scripts/build-dist.sh

# Creates:
# - Wheel package (.whl)
# - Source distribution (.tar.gz)
# - Validates package metadata
```

**`bump-version.sh`** - Bump project version
```bash
./scripts/bump-version.sh <major|minor|patch>

# Updates:
# - pyproject.toml version
# - __init__.py __version__
# - CHANGELOG.md (adds entry)
```

---

### MCP-Specific Scripts

**`mcp-tool.sh`** - Scaffold new MCP tool
```bash
./scripts/mcp-tool.sh <tool_name>

# Generates:
# - Tool implementation template
# - Test file
# - Documentation stub
```

**`validate_mcp_names.py`** - Validate MCP naming conventions
```bash
python scripts/validate_mcp_names.py

# Validates:
# - Tool names use namespace prefix
# - Resource URIs follow scheme
# - No naming conflicts
```

**`migrate_namespace.sh`** - Migrate to new namespace
```bash
./scripts/migrate_namespace.sh <old_namespace> <new_namespace>

# Updates:
# - Tool names in code
# - Resource URI schemes
# - Documentation references
# - Test fixtures
```
---

### Documentation Scripts

**`validate_docs.py`** - Validate documentation structure
```bash
python scripts/validate_docs.py

# Validates:
# - Required sections present
# - Links not broken
# - Code examples valid
# - Diátaxis structure followed
```

**`generate_docs_map.py`** - Generate documentation map
```bash
python scripts/generate_docs_map.py

# Generates:
# - DOCUMENTATION_MAP.md
# - Hierarchical doc structure
# - Quick navigation links
```

**`extract_tests.py`** - Extract examples from tests
```bash
python scripts/extract_tests.py

# Extracts:
# - Test cases → documentation examples
# - Validates examples are current
# - Syncs test patterns to docs
```

---

## Script Organization

### Categories

1. **Setup** - `setup.sh`, `check-env.sh`, `venv-*.sh`
2. **Testing** - `*-test.sh`, `pre-merge.sh`
3. **Development** - `dev-server.sh`, `diagnose.sh`
4. **Build/Release** - `build-dist.sh`, `bump-version.sh`
5. **MCP Tools** - `mcp-tool.sh`, `validate_mcp_names.py`, `migrate_namespace.sh`
6. **Documentation** - `validate_docs.py`, `generate_docs_map.py`, `extract_tests.py`### Naming Conventions

- **Shell scripts**: `kebab-case.sh` (e.g., `pre-merge.sh`)
- **Python scripts**: `snake_case.py` (e.g., `validate_docs.py`)
- **Executability**: All scripts are executable (`chmod +x`)

---

## Usage Patterns for AI Agents

### Pattern 1: Environment Setup

```bash
# First-time setup
./scripts/setup.sh

# Validate environment
./scripts/check-env.sh

# Fix issues if validation fails
./scripts/venv-clean.sh
./scripts/venv-create.sh
pip install -e ".[dev]"
```

### Pattern 2: Pre-Commit Workflow

```bash
# Using just (recommended)
just check          # Lint, typecheck, format
just test           # Run tests
just pre-merge      # Full validation

```

### Pattern 3: Debugging

```bash
# Diagnose issues
./scripts/diagnose.sh

# Run server in debug mode
./scripts/dev-server.sh

# Check environment
./scripts/check-env.sh
```

---

## Related Documentation

- **[Main AGENTS.md](../AGENTS.md)** - Project overview, architecture, common tasks
- **[Testing AGENTS.md](../tests/AGENTS.md)** - Testing instructions
- **[Memory System AGENTS.md](../.chora/memory/AGENTS.md)** - Cross-session learning
- **[justfile](../justfile)** - Task definitions (ergonomic interface)
---

**End of Scripts Reference**

For questions or issues not covered here, see the main [AGENTS.md](../AGENTS.md) or run `./scripts/diagnose.sh` for automated diagnostics.
