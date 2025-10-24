# AGENTS.md

This file provides machine-readable instructions for AI coding agents working with mcp-orchestration.

---

## Project Overview

**mcp-orchestration** is a Model Context Protocol (MCP) server that provides [describe your server's capabilities].

**Core Architecture:** [Describe your architecture pattern]
- [Key architecture point 1]
- [Key architecture point 2]
- [Key architecture point 3]

**Key Components:**
- **Main Module** (`[main_module].py`) - [Description]
- **[Component 2]** (`[module].py`) - [Description]
- **[Component 3]** (`[module].py`) - [Description]

### Strategic Context

**Current Priority:** [Describe current sprint/milestone focus]
- See [ROADMAP.md](ROADMAP.md) for committed work
- Focus: [List 2-3 key deliverables]

**Long-Term Vision:** [Describe evolutionary direction]
- See [dev-docs/vision/](dev-docs/vision/) for future capabilities
- Waves: [List 2-4 high-level capability themes]

**Design Principle:** Deliver current commitments while keeping future doors open.
- Don't build future features now
- Do design extension points and document decisions
- Do refactor when it serves both present and future

---

## Documentation Structure (Nearest File Wins)

**mcp-orchestration uses nested AGENTS.md files** for focused, topic-specific guidance.

**Discovery principle**: Agents should read the AGENTS.md file nearest to the code they're working on.

### Available Guides

- **[AGENTS.md](AGENTS.md)** (this file) - Project overview, architecture, PR workflow, common tasks
- **[tests/AGENTS.md](tests/AGENTS.md)** - Testing guide (run tests, coverage, linting, troubleshooting)
- **[.chora/memory/AGENTS.md](.chora/memory/AGENTS.md)** - Memory system (event log, knowledge graph, A-MEM workflows)
- **[scripts/AGENTS.md](scripts/AGENTS.md)** - Automation scripts reference

**When to use which guide:**

| Working on... | Read... |
|---------------|---------|
| Writing/running tests | [tests/AGENTS.md](tests/AGENTS.md) |
| Cross-session learning, memory queries | [.chora/memory/AGENTS.md](.chora/memory/AGENTS.md) |
| Docker builds, container deployment | [docker/AGENTS.md](docker/AGENTS.md) |
| Automation scripts, justfile tasks | [scripts/AGENTS.md](scripts/AGENTS.md) |
| Architecture, PRs, project structure | [AGENTS.md](AGENTS.md) (this file) |

---

## Dev Environment Tips

### Prerequisites
- **Python 3.12+** required (3.12+ recommended)
- **Git** for version control
- **just** (optional but recommended) - Task runner for common commands
- **[Add project-specific prerequisites]**

### Installation

```bash
# Clone repository
git clone https://github.com/liminalcommons/mcp-orchestration.git
cd mcp-orchestration

# One-command setup (recommended)
./scripts/setup.sh

# Manual setup alternative
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -e ".[dev]"
pre-commit install
```

### Environment Variables

Create a `.env` file in project root:

```env
# Application configuration
MCP_ORCHESTRATION_LOG_LEVEL=INFO     # DEBUG, INFO, WARNING, ERROR, CRITICAL
MCP_ORCHESTRATION_DEBUG=0             # Set to 1 for debug mode

# Add your environment variables here
```

### Client Configuration

#### Claude Desktop (macOS)

**Development Mode (Editable Install):**
```json
{
  "mcpServers": {
    "mcp-orchestration-dev": {
      "command": "/path/to/mcp-orchestration/.venv/bin/python",
      "args": ["-m", "mcp_orchestration.server"],
      "cwd": "/path/to/mcp-orchestration",
      "env": {
        "MCP_ORCHESTRATION_DEBUG": "1"
      }
    }
  }
}
```

**Production Mode (Installed Package):**
```json
{
  "mcpServers": {
    "mcp-orchestration": {
      "command": "mcp-orchestration",
      "args": [],
      "env": {}
    }
  }
}
```

**Config file location:** `~/Library/Application Support/Claude/claude_desktop_config.json`

#### Cursor

See `.config/cursor-mcp.example.json` for complete examples.

**Config file location:** `~/.cursor/mcp.json`

---

## PR Instructions

### Branch Naming

```
feature/descriptive-name     # New features
fix/issue-description        # Bug fixes
hotfix/critical-fix          # Production hotfixes
docs/documentation-update    # Documentation only
refactor/code-improvement    # Refactoring
```

### Commit Message Format

Follow **Conventional Commits** style:

```
type(scope): brief description

Detailed explanation of changes (if needed)

Closes #issue-number
```

**Types:** `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `perf`

**Scopes:** [List your project-specific scopes]

**Examples:**
```
feat(core): add new feature X

Implement feature X with comprehensive error handling
and unit tests.

Closes #23

---

fix(server): handle edge case gracefully

When [condition], system now [behavior] instead of
crashing.

Fixes #45
```

### PR Checklist

**Before opening PR:**
- [ ] Branch is up to date with `main`
- [ ] All tests pass locally (`just test`)
- [ ] Coverage maintained or improved (≥85%)
- [ ] Linting passes (`just lint`)
- [ ] Type checking passes (`just typecheck`)
- [ ] Pre-commit hooks pass (`just pre-commit`)
- [ ] Code formatted (`just format`)
**Documentation (if applicable):**
- [ ] README.md updated (if user-facing changes)
- [ ] AGENTS.md updated (if agent workflow changes)
- [ ] API reference docs updated (if new tools/capabilities)
- [ ] CHANGELOG.md entry added (for releases)

**Testing:**
- [ ] Unit tests added/updated
- [ ] Integration tests added (if applicable)
- [ ] Smoke tests pass (`just smoke`)
- [ ] Manual testing completed

**Review:**
- [ ] Self-review completed
- [ ] Code follows project style guide
- [ ] No debug code or commented-out code
- [ ] Error messages are clear and actionable
- [ ] Logging statements use appropriate levels

### Quality Gates (must pass)

1. **Lint:** `ruff check` → No errors
2. **Format:** `ruff format --check` → Formatted
3. **Types:** `mypy` → Type safe
4. **Tests:** All tests pass
5. **Coverage:** ≥85%
6. **Pre-commit:** All hooks pass

### PR Review Process

- **Required approvals:** 1+ reviewer
- **Merge strategy:** Squash and merge (clean history)
- **CI/CD:** All quality gates must pass
- **Timeline:** Most PRs reviewed within 24-48 hours

### CI/CD Expectations

**When enabled** (`include_github_actions: true`), this project includes automated quality gates that agents should be aware of.

**GitHub Actions workflows:**

1. **test.yml** - Full test suite on every push/PR
   - Runs: `pytest` with coverage
   - Required: ≥85% coverage
   - Triggers: Push to all branches, pull requests

2. **lint.yml** - Code quality checks
   - Runs: `ruff check`, `ruff format --check`, `mypy`
   - Required: No linting errors, formatted code, type-safe
   - Triggers: Push to all branches, pull requests

3. **smoke.yml** - Quick smoke tests
   - Runs: Fast validation tests (<30s)
   - Required: Basic functionality works
   - Triggers: Every push (fast feedback)

5. **release.yml** - Automated releases
   - Runs: Version bump, changelog, PyPI publish
   - Required: Tests pass, version valid, PyPI credentials configured
   - Triggers: Manual workflow dispatch, tags

6. **codeql.yml** - Security scanning
   - Runs: CodeQL analysis for vulnerabilities
   - Required: No critical security issues
   - Triggers: Weekly schedule, pull requests

7. **dependency-review.yml** - Dependency vulnerabilities
   - Runs: Dependency vulnerability scanning
   - Required: No high/critical vulnerabilities in new dependencies
   - Triggers: Pull requests
**What CI will check before merge:**

```bash
# Locally verify CI will pass
just pre-merge

# This runs the same checks as CI:
# 1. Linting: ruff check → No errors
# 2. Formatting: ruff format --check → Code formatted
# 3. Type checking: mypy → Type-safe
# 4. Tests: pytest → All tests pass
# 5. Coverage: pytest --cov → ≥85%
```

**For agents:** Run `just pre-merge` before creating PRs to avoid CI failures.

**CI failure recovery:**
1. Check workflow logs in GitHub Actions tab
2. Run failing command locally to reproduce
3. Fix issue and push new commit (CI will re-run)
4. If tests pass locally but fail in CI, check for environment differences

---

## Architecture Overview

[Describe your project's architecture here. Include diagrams, key design patterns, and architectural decisions.]

### Key Design Patterns

- **[Pattern 1]:** [Description]
- **[Pattern 2]:** [Description]
- **[Pattern 3]:** [Description]

### Configuration Management

[Describe how configuration works in your project, including environment variables, config files, etc.]

---

## Key Constraints & Design Decisions

### Target Audience

MCP server orchestration and management tools

**CRITICAL:** mcp-orchestration is designed for **LLM-intelligent MCP clients** (Claude Desktop, Cursor, Roo Code).

- ✅ **FOR LLM agents** - Claude Desktop, Cursor, custom MCP clients
- ✅ **FOR programmatic use** - Python API, automation workflows
- ❌ **NOT for human CLI users** - No interactive wizards or watch modes

**Implication:** All features prioritize agent ergonomics over human UX.

### [Additional Constraints]

[Document your project-specific constraints and design decisions here.]

---

## Strategic Design

### Balancing Current Priorities with Future Vision

**The Balance:**
- ✅ **Deliver:** Ship current commitments on time
- ✅ **Design for evolution:** Keep future doors open (extension points)
- ✅ **Refactor strategically:** When it serves both present and future
- ❌ **NOT:** Premature optimization, gold plating, scope creep

**Key Insight:** Build for today, design for tomorrow. Don't implement Wave 2 features in Wave 1, but don't paint yourself into corners either.

### Vision-Aware Implementation Pattern

**When implementing features, ask:**

1. **Architecture Check:** "Does this design block future capabilities in [dev-docs/vision/](dev-docs/vision/)?"
   - ✅ YES → Refactor before implementing
   - ✅ NO → Proceed

2. **Refactoring Signal:** "Should I refactor this now?"
   ```
   ┌─────────────────────────────────────────────────────┐
   │ Does it help current work (Wave 1)?                 │
   │   NO → DEFER (focus on current deliverables)       │
   │   YES → Continue ↓                                  │
   ├─────────────────────────────────────────────────────┤
   │ Does it unblock future capabilities?                │
   │   YES → LIKELY REFACTOR (strategic investment)     │
   │   NO → Continue ↓                                   │
   ├─────────────────────────────────────────────────────┤
   │ Cost vs. benefit?                                    │
   │   HIGH COST → DEFER (wait for Wave 2 commitment)   │
   │   LOW COST → REFACTOR (small prep, big payoff)     │
   └─────────────────────────────────────────────────────┘
   ```

3. **Decision Documentation:** Where to record decisions
- **Knowledge notes:** `mcp_orchestration-memory knowledge create "Decision: [topic]"`
   - **Tags:** Use `architecture`, `vision`, `wave-N` tags for discoverability
### Practical Examples

**Example: Building Tool Interface**

**Scenario:** Wave 1 needs simple tool responses. Wave 2 vision includes tool chaining.

**❌ DON'T (Premature Optimization):**
```python
# DON'T build tool chaining now
async def get_data(query: str) -> str:
    # Implements full chaining system (Wave 2 feature)
    return chain_tools([tool_a, tool_b])(query)  # Not needed yet!
```

**✅ DO (Extension Point):**
```python
# DO return structured data (enables future chaining)
async def get_data(query: str) -> dict:
    """Returns structured response (extensible for Wave 2)."""
    return {
        "result": process_query(query),
        "metadata": {"timestamp": now(), "version": "1.0"}
    }
    # Wave 2 can add: "next_tool": "tool_b", "chain_id": "..."
```

### Refactoring Decision Framework

**Use this checklist before refactoring:**

- [ ] **Current Work:** Does this help Wave 1 deliverables?
- [ ] **Future Vision:** Check [dev-docs/vision/](dev-docs/vision/) - does this prepare for next wave?
- [ ] **Cost Assessment:** Low cost (<2 hours) or high cost (>1 day)?
- [ ] **Decision:** Apply framework above → Refactor now or defer?
- [ ] **Documentation:** Record decision (knowledge note)

### Capturing Knowledge for Future Agents

**Use A-MEM (Agentic Memory) patterns:**

1. **Emit Events:** Track architectural decisions
   ```python
   from mcp_orchestration.memory import emit_event

   emit_event(
       event_type="architecture.decision",
       data={
           "decision": "Use dict returns for tool extensibility",
           "rationale": "Enables Wave 2 tool chaining",
           "wave": "wave-2-preparation"
       },
       status="success"
   )
   ```

2. **Create Knowledge Notes:**
   ```bash
   echo "Decision: Tool Response Format

   Context: Wave 1 tools return simple data, Wave 2 vision includes tool chaining.

   Decision: Return dict (not str) from all tools.

   Rationale:
   - Low cost refactor (1 hour)
   - Unblocks Wave 2 tool chaining
   - Backward compatible (wrap str in dict)

   Tags: architecture, vision, wave-2, tools
   " | mcp_orchestration-memory knowledge create "Tool Response Format"
   ```

3. **Link to Vision:**
   - Reference vision waves in knowledge notes
   - Tag notes with `wave-N` for future discoverability
   - Query past decisions: `mcp_orchestration-memory knowledge search --tag wave-2`

### Quick Reference: Strategic Design Checklist

**Before implementing any feature:**

1. ✅ **Check ROADMAP.md:** Is this in current committed work?
2. ✅ **Check vision:** Does this align with evolutionary direction?
3. ✅ **Apply framework:** Refactor now or defer? (use flowchart above)
4. ✅ **Document:** Record decision for future agents
5. ✅ **Code:** Implement with extension points, not future features

**Remember:** Deliver today, design for tomorrow. No gold plating!

---

## Common Tasks for Agents


### Task Discovery (START HERE)

**First step when working in this project: Discover available tasks**

```bash
just --list
```

This provides a machine-readable catalog of all development tasks.

**Why `just` for agents:**
- **Self-documenting**: `just --list` reveals all tasks instantly (no prose parsing)
- **Consistent**: Same commands across all chora-base projects
- **Structured**: Machine-parseable task catalog
- **Composable**: `just --show <task>` reveals implementation details
- **Transferable**: Commands learned here work in all chora-base projects

**Pattern**: Always start with `just --list` when working in a new chora-base project. Store commands as ecosystem-wide patterns, not project-specific.

**Example workflow:**
```bash
# Discover tasks
just --list
# Output: test, lint, pre-merge, build, etc.

# Understand a specific task
just --show pre-merge
# Output: shows it runs ./scripts/pre-merge.sh

# Execute
just pre-merge
```

**Memory note**: Store as:
```json
{
  "ecosystem": "chora-base",
  "discovery_command": "just --list",
  "common_tasks": {
    "test": "just test",
    "pre_merge": "just pre-merge",
    "build": "just build"
  },
  "applies_to": "all_chora_base_projects"
}
```

This knowledge transfers to mcp-n8n, chora-compose, and all future chora-base projects.

### Adding a New MCP Tool

**Before you start**: Read [NAMESPACES.md](NAMESPACES.md) for naming conventions and namespace registry.

1. Create tool function in `src/mcp_orchestration/tools/your_tool.py`
2. Register tool with `@mcp.tool()` decorator3. Use `make_tool_name("your_tool")` for consistent namespacing
4. Add memory integration (emit events)
5. Add unit test in `tests/unit/test_your_tool.py`
6. Add integration test with memory validation
7. Update README.md tool list
8. **Update [NAMESPACES.md](NAMESPACES.md) registry** - Add your tool to the table
9. Run tests: `just test`

**Example:**
```python
from mcp_orchestration.memory import emit_event, TraceContext
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("mcp-orchestration")

@mcp.tool()
async def your_tool(param: str) -> dict:
    """Your tool description.

    Args:
        param: Parameter description

    Returns:
        Result dictionary
    """
# Emit start event
    emit_event("tool.your_tool.started", status="pending", metadata={"param": param})

try:
        # Your tool logic here
        result = process(param)
# Emit success event
        emit_event("tool.your_tool.completed", status="success", metadata={"result_count": len(result)})
return {"success": True, "data": result}
    except Exception as e:
# Emit failure event
        emit_event("tool.your_tool.failed", status="failure", metadata={"error": str(e)})
return {"success": False, "error": str(e)}
```

### Documentation System

**When enabled** (`include_documentation_standard: true`), this project includes machine-readable documentation with health metrics and programmatic querying.

**Discovery:**
```bash
# Documentation commands
just --list | grep docs

# Available commands (via scripts):
# - python scripts/docs_metrics.py    Generate health metrics
# - python scripts/query_docs.py      Query docs programmatically
# - python scripts/extract_tests.py   Extract test scenarios
```

**Common workflows:**

```bash
# Check documentation health
python scripts/docs_metrics.py

# Query documentation (JSON API for AI agents)
python scripts/query_docs.py function get_example

# Extract test scenarios from docstrings
python scripts/extract_tests.py

# View metrics report
cat DOCUMENTATION_METRICS.md
```

**Documentation health scoring:**
- **90-100:** Excellent (comprehensive, up-to-date)
- **70-89:** Good (minor gaps)
- **50-69:** Needs improvement (significant gaps)
- **0-49:** Critical (major documentation debt)

**For agents:** Use `query_docs.py` to programmatically discover functions, parameters, return types, and examples without parsing source code.

**Adopter responsibilities (wiring required):**
- [ ] Write comprehensive docstrings following NumPy/Google style
- [ ] Include `# TEST:` markers in docstrings for extractable scenarios
- [ ] Review DOCUMENTATION_METRICS.md quarterly and address gaps
- [ ] Add examples to critical functions (user-facing API)

**See:** [DOCUMENTATION_STANDARD.md](DOCUMENTATION_STANDARD.md) for complete documentation guidelines.

### Debugging Common Issues

```bash
# Check logs
just logs  # If justfile has log task
# OR
tail -f logs/mcp_orchestration.log

# Test single component
python -m mcp_orchestration.module_name

# Check environment
env | grep MCP_ORCHESTRATION

# Validate configuration
python -c "from mcp_orchestration import config; print(config)"
```

### Design Decision: Check Against Vision

**When:** Before making architectural decisions or significant refactors

**Steps:**

1. **Check current priority:**
   ```bash
   cat ROADMAP.md | head -50
   # Current: [Your current sprint/milestone]
   ```

2. **Check long-term vision:**
   ```bash
   cat dev-docs/vision/CAPABILITY_EVOLUTION.md | head -100
   # Future waves: [Your capability themes]
   ```

3. **Apply decision framework:**
   - **Does this help current work?** (YES → continue)
   - **Does this align with vision?** (YES → good sign)
   - **Cost vs. benefit?** (LOW COST → likely proceed)

4. **Document decision:**
```bash
   # Create knowledge note
   echo "Decision: [Your decision]

   Context: [Current situation]

   Decision: [What you decided]

   Rationale:
   - Helps Wave 1 deliverables: [How]
   - Aligns with Wave 2 vision: [Which capability]
   - Low cost: [Effort estimate]

   Outcome: [Expected result]

   Tags: architecture, vision, wave-N, decision
   " | mcp_orchestration-memory knowledge create "Decision: [Topic]"
   ```
5. **Link to vision:**
   - If prepares for future waves, note it in documentation
- Add tags to knowledge notes for discoverability: `wave-2`, `architecture`, `vision`
- Update vision document if decision affects feasibility

**Example Decision:**

**Scenario:** Should we refactor tool responses from `str` to `dict`?

1. **Current work:** Wave 1 needs simple responses → `str` works
2. **Vision:** Wave 2 includes tool chaining → needs structured data (`dict`)
3. **Cost:** Low (1-2 hours to refactor)
4. **Decision:** ✅ REFACTOR NOW (serves both present and future)

---

## Project Structure

```
mcp-orchestration/
├── src/mcp_orchestration/       # Main source code
│   ├── __init__.py
│   ├── server.py               # MCP server entry point
│   ├── memory/                 # Agent memory system
│   │   ├── event_log.py
│   │   ├── knowledge_graph.py
│   │   └── trace.py
│   └── [your modules]
├── tests/                      # Test suite
│   ├── smoke/                  # Smoke tests (<30s)
│   ├── integration/            # Integration tests
│   └── test_*.py               # Unit tests
├── scripts/                    # Automation scripts
│   ├── setup.sh                # One-command setup
│   ├── venv-create.sh          # Create virtual environment
│   └── [other scripts]
├── docs/                       # Documentation
│   ├── DEVELOPMENT.md          # Developer deep dive
│   └── TROUBLESHOOTING.md      # Problem-solution guide
├── .github/workflows/          # CI/CD pipelines
│   ├── test.yml                # Test workflow
│   └── lint.yml                # Lint workflow
├── .chora/memory/              # Agent memory (gitignored)
│   ├── README.md               # Memory architecture docs
│   ├── events/                 # Event log (JSONL format)
│   ├── knowledge/              # Knowledge notes (YAML frontmatter)
│   │   ├── notes/*.md          # Individual notes
│   │   ├── links.json          # Bidirectional links
│   │   └── tags.json           # Tag index
│   └── profiles/               # Agent-specific profiles
├── pyproject.toml              # Python packaging & tool config
├── justfile                    # Task runner commands
├── .env.example                # Example environment variables
├── .gitignore                  # Git ignore patterns
├── README.md                   # Human-readable project overview
├── AGENTS.md                   # This file (machine-readable instructions)
├── CONTRIBUTING.md             # Contribution guidelines
└── LICENSE                     # MIT license
```

### Knowledge Note Metadata Standards

Knowledge notes (`.chora/memory/knowledge/notes/*.md`) use **YAML frontmatter** following Zettelkasten best practices for machine-readable metadata.

**Required Frontmatter Fields:**
- `id`: Unique note identifier (kebab-case)
- `created`: ISO 8601 timestamp
- `updated`: ISO 8601 timestamp
- `tags`: Array of topic tags for search/organization

**Optional Frontmatter Fields:**
- `confidence`: `low` | `medium` | `high` - Solution reliability
- `source`: `agent-learning` | `human-curated` | `external` | `research`
- `linked_to`: Array of related note IDs (bidirectional linking)
- `status`: `draft` | `validated` | `deprecated`
- `author`: Agent or human creator
- `related_traces`: Array of trace IDs that led to this knowledge

**Example Knowledge Note:**

```markdown
---
id: api-timeout-solution
created: 2025-01-17T10:00:00Z
updated: 2025-01-17T12:30:00Z
tags: [troubleshooting, api, performance]
confidence: high
source: agent-learning
linked_to: [connection-pool-tuning, retry-patterns]
status: validated
author: claude-code
related_traces: [abc123, def456]
---

# API Timeout Solution

## Problem
API calls timing out after 30s during high load...

## Solution
Increase timeout to 60s and implement retry with exponential backoff...

## Evidence
- Trace abc123: Successful completion at 45s
- Trace def456: Successful completion at 52s
- Load test: 98% success rate with new settings
```

**Why YAML Frontmatter?**
- ✅ **Semantic Search**: Query by confidence, tags, or date (`grep "confidence: high"`)
- ✅ **Tool Compatibility**: Works with Obsidian, Zettlr, LogSeq, Foam
- ✅ **Knowledge Graph**: Enables bidirectional linking and visualization
- ✅ **Agent Decision-Making**: Filter by confidence level for solution reliability

**Reference:** See [.chora/memory/README.md](.chora/memory/README.md) for complete schema documentation.

---

## Documentation Philosophy

### Diátaxis Framework

mcp-orchestration documentation follows the [Diátaxis framework](https://diataxis.fr/), serving **two first-class audiences**:

1. **Human Developers** - Learning, understanding, decision-making
2. **AI Agents** - Task execution, reference lookup, machine-readable instructions

**Four Quadrants:**

| Type | Purpose | Primary Audience | When to Use |
|------|---------|------------------|-------------|
| **Tutorials** | Learning-oriented | Humans (new users) | "I want to learn how mcp-orchestration works" |
| **How-To Guides** | Task-oriented | Humans + Agents | "I want to accomplish a specific task" |
| **Reference** | Information-oriented | Humans + Agents | "I need to look up a fact/command/API" |
| **Explanation** | Understanding-oriented | Humans | "I want to understand why/how this works" |

### For AI Agents (Recommended Reading Order)

**When starting work on mcp-orchestration:**

1. **Start here:** AGENTS.md (this file) - Machine-readable project instructions
2. **Quick reference:** How-To Guides - Executable task recipes
   - How to add new features
   - How to run tests
   - How to deploy
3. **Lookup facts:** Reference Docs - API specs, configuration options, commands
4. **Skip:** Tutorials (for human learning) and Explanations (conceptual background)

**Example: Agent workflow for "Add new feature X"**

```bash
# 1. Read AGENTS.md section: "Common Tasks for Agents" → "Adding a New MCP Tool"
# 2. Follow steps 1-7 (create file, register tool, add tests, etc.)
# 3. If unclear on testing: Consult "Testing Instructions" section in AGENTS.md
# 4. If need API reference: Read relevant module docstrings or Reference docs
# 5. Run pre-merge: `just pre-merge` (from AGENTS.md "Pre-Merge Verification")
```

### For Human Developers (Recommended Learning Path)

**New to mcp-orchestration:**

1. **README.md** - Project overview, quick start (5 minutes)
2. **Tutorial** - Guided learning experience (30-60 minutes)
3. **DEVELOPMENT.md** - Developer deep dive (architecture, debugging)
4. **How-To Guides** - Task-specific recipes (as needed)
5. **Reference Docs** - Lookup API details (as needed)
6. **Explanation Docs** - Understand design decisions (optional)

### Documentation Hierarchy

```
docs/
├── README.md                   # Human entry point (project overview)
├── AGENTS.md                   # Agent entry point (this file)
├── CONTRIBUTING.md             # Human contributor guide
├── DEVELOPMENT.md              # Developer deep dive
├── TROUBLESHOOTING.md          # Problem-solution guide
└── [additional docs]/
```

**Quick Reference:**

- **For agents:** AGENTS.md → How-To Guides → Reference Docs
- **For humans:** README → Tutorials → How-To Guides → Explanations

### DDD/BDD/TDD Workflow

This project follows the Chora ecosystem's integrated DDD/BDD/TDD workflow:

1. **DDD Phase** - Write API reference docs FIRST (documentation-driven design)
2. **BDD Phase** - Write scenarios SECOND (behavior-driven development)
3. **TDD Phase** - Red-Green-Refactor THIRD (test-driven development)
4. **CI Phase** - Automated quality gates
5. **Merge & Release** - Semantic versioning

**Why this order matters:**

- **Docs first** ensures clear API design before implementation
- **Scenarios second** captures expected behavior as executable specs
- **Tests third** drives implementation with fast feedback loop
- **CI validates** all quality gates pass before merge
- **Semantic versioning** communicates changes to users

**For agents:** Follow this workflow when adding new features. Write docs → scenarios → tests → implementation.

---

## Troubleshooting

### Application Won't Start

```bash
# Check Python version
python --version  # Must be 3.12+

# Check virtual environment
which python  # Should be .venv/bin/python

# Reinstall dependencies
./scripts/venv-create.sh

# Check environment variables
cat .env

# Test application directly
python -m mcp_orchestration.server```

---

## Related Resources

- **Repository:** https://github.com/liminalcommons/mcp-orchestration
- **Chora Base Template:** https://github.com/liminalcommons/chora-base
- **Chora Composer:** https://github.com/liminalcommons/chora-composer
- **Chora Platform:** https://github.com/liminalcommons/chora-platform
- **MCP Specification:** https://modelcontextprotocol.io/
---

**Version:** 0.1.0
**Last Updated:** [Update date]
**Format:** AGENTS.md standard (OpenAI/Google/Sourcegraph)
🤖 Generated with [chora-base](https://github.com/liminalcommons/chora-base) template
