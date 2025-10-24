# Testing Guide for mcp-orchestration

**Purpose**: Comprehensive testing instructions for AI agents and human developers.

**Parent**: See [../AGENTS.md](../AGENTS.md) for project overview and other topics.

---

## Quick Reference

- **Run all tests**: `just test`
- **Run with coverage**: `just test-coverage`
- **Smoke tests**: `just smoke`
- **Pre-merge check**: `just pre-merge`

---

## Testing Instructions

### Run All Tests

```bash
# Using just (recommended)
just test

# Direct pytest
pytest

# With coverage report
just test-coverage
# OR
pytest --cov=mcp_orchestration --cov-report=term-missing
```

### Smoke Tests (Quick Validation)

```bash
# Fast smoke tests (<30 seconds)
just smoke

# Direct pytest
pytest tests/smoke/ -v
```

### Test Categories

```bash
# Unit tests only
pytest tests/ -k "not integration and not smoke" -v

# Integration tests
pytest tests/integration/ -v

# Specific test file
pytest tests/test_example.py -v

# Specific test function
pytest tests/test_example.py::test_function -v
```

### Pre-Commit Hooks

```bash
# Run all pre-commit checks
just pre-commit
# OR
pre-commit run --all-files

# Install hooks (one-time setup)
pre-commit install

# Run specific hook
pre-commit run ruff --all-files
pre-commit run mypy --all-files
```

### Linting & Type Checking

```bash
# All quality checks (lint + typecheck + format)
just check

# Individual checks
just lint       # Ruff linting
just typecheck  # Mypy type checking
just format     # Ruff formatting

# Manual commands
ruff check src/mcp_orchestration tests/
mypy src/mcp_orchestration
ruff format src/mcp_orchestration tests/

# Auto-fix linting issues
ruff check --fix src/mcp_orchestration tests/
```

### Coverage Requirements

- **Overall coverage:** ≥85%
- **Critical paths:** 100% ([list critical paths])
- **[Module name]:** ≥90% ([describe module])

### Pre-Merge Verification

```bash
# Full verification before submitting PR
just pre-merge

# Equivalent to:
# - pre-commit run --all-files
# - pytest (smoke + full test suite)
# - coverage check
```

### System-Level Validation (Super-Tests)

**Philosophy:** Test workflows and system behavior, not just individual units.

Super-tests validate **end-to-end scenarios** that users actually experience, rather than granular unit tests. This approach catches integration issues, configuration problems, and emergent behavior that unit tests miss.

**When to write super-tests:**
- ✅ Before releasing a new feature (does the full workflow work?)
- ✅ After fixing a bug (does the scenario now succeed end-to-end?)
- ✅ When adding integrations (do all components work together?)
- ✅ For critical user journeys (can users accomplish their goals?)

**Example super-test patterns:**

```bash
# Run system-level validation
just super-test

# What this validates:
# 1. Full application startup and initialization
# 2. End-to-end workflow completion
# 3. Integration between all components
# 4. Configuration loading and environment setup
# 5. Error handling in realistic scenarios
```

**MCP Server Super-Test Example:**
```python
# tests/super/test_full_workflow.py
def test_mcp_server_lifecycle():
    """Validate complete MCP server lifecycle: start → register tools → execute → shutdown."""
    # Start server
    server = create_server()

    # Verify all tools registered
    tools = server.list_tools()
    assert len(tools) == EXPECTED_TOOL_COUNT

    # Execute representative workflow
    result = server.call_tool("primary_tool", {"param": "value"})
    assert result.success

    # Verify side effects (files written, state updated, etc.)
    assert expected_output_exists()

    # Clean shutdown
    server.shutdown()
```

**Benefits of super-tests:**
- 🎯 Catch integration bugs unit tests miss
- 🎯 Validate realistic user scenarios
- 🎯 Test configuration and environment setup
- 🎯 Verify error handling in context
- 🎯 Build confidence before releases

**Balance with unit tests:**
- **Unit tests:** Fast, focused, validate logic in isolation (70-80% of tests)
- **Super-tests:** Slower, comprehensive, validate workflows (20-30% of tests)

Use both. Unit tests give fast feedback during development. Super-tests give confidence before deployment.

---

## Running Tests for Specific Modules

```bash
# Test specific module
pytest tests/test_mcp_orchestration_module.py -v

# Test with coverage for module
pytest tests/test_module.py --cov=mcp_orchestration.module --cov-report=term-missing

# Test specific function
pytest tests/test_module.py::test_function_name -vv

# Run with debugger on failure
pytest tests/test_module.py --pdb
```

---

## Fixing Linting/Type Errors

```bash
# Auto-fix linting issues
ruff check --fix src/mcp_orchestration

# Format code
ruff format src/mcp_orchestration

# Check types and show errors
mypy src/mcp_orchestration --pretty --show-error-codes

# Fix specific type error
# Add type: ignore[error-code] comment to problematic line
```

---

## Troubleshooting

### Test Failures

```bash
# Run specific test with verbose output
pytest tests/test_example.py::test_function -vvs

# Show full error trace
pytest --tb=long

# Run with debugger
pytest --pdb

# Check test coverage
pytest --cov=mcp_orchestration --cov-report=term-missing

# Clean test cache
pytest --cache-clear
rm -rf .pytest_cache __pycache__
```

### Type Checking Errors

```bash
# Run mypy with verbose output
mypy src/mcp_orchestration --show-error-codes --pretty

# Check specific file
mypy src/mcp_orchestration/[module].py

# Ignore specific error (if intentional)
# Add to line:
# type: ignore[error-code]

# Update mypy configuration
# Edit [tool.mypy] in pyproject.toml
```

### Coverage Drop

```bash
# Show missing coverage lines
pytest --cov=mcp_orchestration --cov-report=term-missing

# Generate HTML report
pytest --cov=mcp_orchestration --cov-report=html
open htmlcov/index.html

# Check coverage for specific module
pytest --cov=mcp_orchestration.[module] --cov-report=term-missing

# Identify untested code
coverage report --show-missing
```

### Pre-Commit Hook Failures

```bash
# Run specific hook
pre-commit run ruff --all-files
pre-commit run mypy --all-files

# Update hook versions
pre-commit autoupdate

# Bypass hooks (emergency only, NOT recommended)
git commit --no-verify

# Clear pre-commit cache
pre-commit clean
```

---

## Related Documentation

- **[Main AGENTS.md](../AGENTS.md)** - Project overview, architecture, common tasks
- **[Memory System AGENTS.md](../.chora/memory/AGENTS.md)** - Cross-session learning, knowledge management
- **[scripts/AGENTS.md](../scripts/AGENTS.md)** - Automation scripts reference

---

**End of Testing Guide**

For questions or issues not covered here, see the main [AGENTS.md](../AGENTS.md) or open a GitHub issue.
