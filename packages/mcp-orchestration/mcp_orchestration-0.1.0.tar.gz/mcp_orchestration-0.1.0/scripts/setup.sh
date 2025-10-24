#!/usr/bin/env bash
# setup.sh - One-command project setup for mcp-orchestration
#
# Usage: ./scripts/setup.sh

set -euo pipefail

echo "=== mcp-orchestration Setup Script ==="
echo ""

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check Python version
echo -e "${YELLOW}Checking Python version...${NC}"
PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
REQUIRED_VERSION="3.11"

if ! python -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)"; then
    echo -e "${RED}Error: Python 3.11+ is required. Current version: ${PYTHON_VERSION}${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python ${PYTHON_VERSION}${NC}"
echo ""

# Install just command runner (primary development interface)
echo -e "${YELLOW}Installing 'just' command runner...${NC}"
if ! command -v just &> /dev/null; then
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS: Try brew first, fallback to curl
        if command -v brew &> /dev/null; then
            echo "  Using Homebrew..."
            brew install just
        else
            echo "  Using curl installer..."
            curl --proto '=https' --tlsv1.2 -sSf https://just.systems/install.sh | bash -s -- --to ~/.local/bin
            export PATH="$HOME/.local/bin:$PATH"
        fi
    else
        # Linux/Other: Use curl installer
        echo "  Using curl installer..."
        curl --proto '=https' --tlsv1.2 -sSf https://just.systems/install.sh | bash -s -- --to ~/.local/bin
        export PATH="$HOME/.local/bin:$PATH"
    fi

    if command -v just &> /dev/null; then
        echo -e "${GREEN}✓ just installed successfully${NC}"
        just --version
    else
        echo -e "${RED}✗ Failed to install just${NC}"
        echo "  Please install manually:"
        echo "    macOS:   brew install just"
        echo "    Linux:   cargo install just"
        echo "    Other:   https://github.com/casey/just#installation"
        echo ""
    fi
else
    echo -e "${GREEN}✓ just already installed${NC}"
    just --version
fi
echo ""

# Install Python dependencies
echo -e "${YELLOW}Installing Python dependencies...${NC}"
pip install -e ".[dev]"
echo -e "${GREEN}✓ Dependencies installed${NC}"
echo ""

# Setup pre-commit hooks
echo -e "${YELLOW}Installing pre-commit hooks...${NC}"
if command -v pre-commit &> /dev/null; then
    pre-commit install
    echo -e "${GREEN}✓ Pre-commit hooks installed${NC}"
else
    echo -e "${YELLOW}Warning: pre-commit not found. Run 'pip install pre-commit' to enable git hooks.${NC}"
fi
echo ""

# Check for environment file
echo -e "${YELLOW}Checking environment configuration...${NC}"
if [ ! -f .env ]; then
    echo -e "${YELLOW}Warning: .env file not found.${NC}"
    echo "  Copy .env.example to .env and configure:"
    echo "  cp .env.example .env"
    echo ""
    echo "  Required environment variables:"
    echo "  - ANTHROPIC_API_KEY (for Chora Composer backend)"
    echo "  - CODA_API_KEY (for Coda MCP backend)"
else
    echo -e "${GREEN}✓ .env file found${NC}"
fi
echo ""

# Run quality checks
echo -e "${YELLOW}Running quality checks...${NC}"
if command -v just &> /dev/null; then
    just check
else
    echo "Running linting..."
    ruff check src/mcp_orchestration tests || true
    echo ""
    echo "Running type checking..."
    mypy src/mcp_orchestration || true
fi
echo -e "${GREEN}✓ Quality checks complete${NC}"
echo ""

# Run tests
echo -e "${YELLOW}Running tests...${NC}"
pytest
echo -e "${GREEN}✓ Tests passed${NC}"
echo ""

# Summary
echo "=== Setup Complete ==="
echo ""
echo "Development commands (via 'just'):"
echo "  just --list       # Show all available commands"
echo "  just test         # Run test suite"
echo "  just lint         # Check code style"
echo "  just pre-merge    # Run all checks before PR"
echo "  just run          # Start the application"
echo ""
echo "For help: just help"
echo ""
echo -e "${GREEN}Ready to develop!${NC}"
