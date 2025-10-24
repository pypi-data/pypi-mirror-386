# mcp-orchestration task automation
#
# This justfile provides the primary developer interface for this project.
# All development tasks are accessed via 'just <task>'.
#
# Quick start:
#   just --list     # Show all available commands
#   just help       # Show common workflows
#   just test       # Run test suite
#
# Installation: Automatically handled by ./scripts/setup.sh
# More info: https://github.com/casey/just

# Default recipe (show available commands)
default:
    @just --list

# Show help and common workflows
help:
    @echo "=== mcp-orchestration - Development Commands ==="
    @echo ""
    @echo "Quick validation:"
    @echo "  just test           # Run test suite (~1 min)"
    @echo "  just smoke          # Quick smoke tests (~10 sec)"
    @echo "  just lint           # Check code style"
    @echo ""
    @echo "Before creating PR:"
    @echo "  just pre-merge      # Run all checks (required)"
    @echo ""
    @echo "Building & releasing:"
    @echo "  just build          # Build distribution packages"
    @echo "  just prepare patch  # Prepare patch release"
    @echo ""
    @echo "Full command list:"
    @just --list

# Install all dependencies (including dev)
install:
    pip install -e ".[dev]"

# Install pre-commit hooks
setup-hooks:
    pre-commit install

# Environment management
venv-create:
    ./scripts/venv-create.sh

venv-clean:
    ./scripts/venv-clean.sh

check-env:
    ./scripts/check-env.sh

# Run all tests
test:
    pytest

# Run smoke tests (quick validation)
smoke:
    ./scripts/smoke-test.sh

# Safety & Recovery (Phase 2)
rollback:
    ./scripts/rollback-dev.sh

verify-stable:
    ./scripts/verify-stable.sh

# Run pre-merge validation (lint + test + coverage ≥85%)
# Required before creating pull request (~2 minutes)
pre-merge:
    ./scripts/pre-merge.sh

# Version Management (Phase 3)
bump-major:
    ./scripts/bump-version.sh major

bump-minor:
    ./scripts/bump-version.sh minor

bump-patch:
    ./scripts/bump-version.sh patch

prepare-release TYPE:
    ./scripts/prepare-release.sh 

# Run tests with coverage
test-coverage:
    pytest --cov=mcp_orchestration --cov-report=html --cov-report=term

# Run linting (ruff)
lint:
    ruff check src/mcp_orchestration tests

# Run linting with auto-fix
lint-fix:
    ruff check --fix src/mcp_orchestration tests

# Run code formatting (black)
format:
    black src/mcp_orchestration tests

# Run type checking (mypy)
typecheck:
    mypy src/mcp_orchestration

# Run all quality checks (lint + typecheck + format check)
check: lint typecheck
    black --check src/mcp_orchestration tests

# Run pre-commit on all files
pre-commit:
    pre-commit run --all-files

# Start the gateway server
run:
    mcp-orchestration

# Start the gateway with debug logging
run-debug:
    MCP_N8N_LOG_LEVEL=DEBUG MCP_N8N_DEBUG=1 mcp-orchestration

# Clean build artifacts
clean:
    rm -rf build/
    rm -rf dist/
    rm -rf *.egg-info/
    rm -rf .pytest_cache/
    rm -rf .mypy_cache/
    rm -rf .ruff_cache/
    rm -rf htmlcov/
    find . -type d -name __pycache__ -exec rm -rf {} +

# Full setup (install + hooks + check)
setup: install setup-hooks
    @echo "✓ Setup complete! Run 'just test' to verify."

# Pre-push checks (run before committing)
verify: pre-commit smoke test
    @echo "✓ All checks passed!"

# Build & Release (Phase 3)
# Build distribution packages (wheel + sdist)
# Output: dist/*.whl and dist/*.tar.gz
build:
    ./scripts/build-dist.sh

# Publish to TestPyPI (for testing before production release)
publish-test:
    ./scripts/publish-test.sh

# Publish to production PyPI
publish-prod:
    ./scripts/publish-prod.sh

release TYPE:
    @echo "Starting full release workflow for  version..."
    just prepare-release 
    just build
    @echo ""
    @echo "Build complete. Test on TestPyPI first:"
    @echo "  just publish-test"
    @echo ""
    @echo "After verifying, publish to production:"
    @echo "  just publish-prod"

# Developer Tools (Phase 4)
diagnose:
    ./scripts/diagnose.sh

dev-server:
    ./scripts/dev-server.sh

docs:
    @echo "Opening documentation..."
    @echo ""
    @echo "Available documentation:"
    @echo "  - README.md - Project overview"
    @echo "  - CONTRIBUTING.md - Contribution guidelines"
    @echo "  - ARCHITECTURE.md - System architecture"
    @echo "  - docs/DEVELOPMENT.md - Developer guide"
    @echo "  - docs/TROUBLESHOOTING.md - Problem solving"
    @echo "  - docs/RELEASE_CHECKLIST.md - Release process"

# Show environment info
info:
    @echo "Python version:"
    @python --version
    @echo ""
    @echo "Package info:"
    @pip show mcp-orchestration || echo "Package not installed"
    @echo ""
    @echo "Environment variables:"
    @env | grep MCP_ORCHESTRATION || echo "No MCP_ORCHESTRATION_* variables set"
