---
title: mcp-orchestration Documentation Standard
type: process
status: current
audience: all
last_updated: 2025-10-23
version: 1.0.0
---

# mcp-orchestration Documentation Standard

**Purpose:** Define documentation structure, formats, and processes for mcp-orchestration
**Framework:** Diátaxis (documentation system) + Documentation as Product
**Status:** Active

---

## Table of Contents

1. [Overview](#overview)
2. [Diátaxis Framework](#diátaxis-framework)
3. [Directory Structure](#directory-structure)
4. [Frontmatter Schema](#frontmatter-schema)
5. [Document Templates](#document-templates)
6. [Writing Standards](#writing-standards)
7. [Automation & Validation](#automation--validation)
8. [Maintenance](#maintenance)

---

## Overview

### Philosophy: Documentation as Product

mcp-orchestration treats documentation as a first-class product deliverable:
- **Documentation is written BEFORE code** (Documentation Driven Design)
- **Documentation serves as executable specification** (test extraction)
- **Documentation stays synchronized** (automated validation)
- **Documentation serves two audiences:**
  1. **Human Developers** - Learning, understanding, decision-making
  2. **AI Agents** - Task execution, reference lookup, machine-readable instructions

### Core Principles

1. **User Intent** - Organize by what users want to DO, not by technical topics
2. **Executable Examples** - All code examples must be testable
3. **Cross-References** - Related docs must link to each other
4. **Maintenance** - Clear ownership, update schedules, staleness warnings
5. **Accessibility** - Clear audience targeting (beginners vs. advanced)

---

## Diátaxis Framework

mcp-orchestration organizes documentation by **user intent**, following the [Diátaxis framework](https://diataxis.fr/):

### The Four Document Types

| Type | Purpose | User Intent | Structure |
|------|---------|-------------|-----------|
| **Tutorial** | Learning-oriented | "Teach me" | Step-by-step lessons with expected output |
| **How-To Guide** | Task-oriented | "Show me how to solve X" | Problem → Solution variations |
| **Reference** | Information-oriented | "What parameters does this take?" | Specifications, API docs, schemas |
| **Explanation** | Understanding-oriented | "Why does this work this way?" | Concepts, context, design decisions |

### When to Use Each Type

**Tutorial:**
- ✅ First-time user onboarding
- ✅ Learning a new feature end-to-end
- ✅ Building confidence through success
- ❌ NOT for solving specific problems (use How-To)

**How-To Guide:**
- ✅ Solving a specific problem
- ✅ Achieving a particular goal
- ✅ Multiple approaches to same problem
- ❌ NOT for teaching concepts (use Tutorial)

**Reference:**
- ✅ API documentation
- ✅ Configuration options
- ✅ Schema specifications
- ❌ NOT for explaining why (use Explanation)

**Explanation:**
- ✅ Architecture decisions
- ✅ Design patterns
- ✅ System context and history
- ❌ NOT for step-by-step instructions (use Tutorial)

---

## Directory Structure

### Three-Directory Organization

mcp-orchestration separates documentation into three distinct directories:

```
mcp-orchestration/
├── user-docs/                # End-user documentation (using the product)
│   ├── tutorials/            # Learning-oriented
│   ├── how-to/               # Task-oriented
│   ├── reference/            # Information-oriented
│   └── explanation/          # Understanding-oriented
│
├── project-docs/             # Project management (planning the product)
│   ├── ROADMAP.md
│   ├── sprints/              # Sprint planning (if using agile)
│   ├── releases/             # Release notes, checklists
│   └── decisions/            # Architecture Decision Records (ADRs)
│
└── dev-docs/                 # Developer documentation (building the product)
    ├── CONTRIBUTING.md       # How to contribute
    ├── DEVELOPMENT.md        # Developer setup deep-dive
    ├── TROUBLESHOOTING.md    # Common development issues
    ├── vision/               # Vision documents (strategic design)
    └── workflows/            # Development workflows (BDD, TDD, DDD)
```

### Directory Purpose

| Directory | Audience | Purpose | Examples |
|-----------|----------|---------|----------|
| `user-docs/` | End users | How to **use** the product | API docs, tutorials, guides |
| `project-docs/` | PM, stakeholders | How to **plan** the product | Roadmap, ADRs, releases |
| `dev-docs/` | Contributors | How to **build** the product | Setup, contributing, vision |

---

## Frontmatter Schema

All documentation files MUST include YAML frontmatter for machine-readability.

### Required Fields (All Documents)

```yaml
---
title: "Document Title"                  # Human-readable title
type: tutorial | how-to | reference | explanation | process | project | decision
status: current | draft | deprecated      # Lifecycle status
last_updated: YYYY-MM-DD                  # ISO 8601 date
---
```

### Optional Fields

```yaml
---
# Audience & Context
audience: beginners | intermediate | advanced | maintainers | all

# Navigation & Discovery
tags: [tag1, tag2, tag3]                 # Searchable tags
related:                                  # Cross-references (relative paths)
  - ../how-to/related-task.md
  - ../../reference/api-spec.md

# For Tutorials & How-To Guides
estimated_time: "30 minutes"              # How long to complete
prerequisites:                            # What to know/have first
  - tutorials/01-basics.md
  - Basic Python knowledge

# For Reference Docs
version: 1.0.0                            # API/schema version
test_extraction: true                     # Has executable examples for testing

# Metadata
created: YYYY-MM-DD                       # Original creation date
author: "Team Name"                       # Original author
maintainer: "Current Owner"               # Who maintains this doc
---
```

### Frontmatter Examples

**Tutorial:**
```yaml
---
title: "Getting Started with mcp-orchestration"
type: tutorial
status: current
audience: beginners
last_updated: 2025-10-23
estimated_time: "20 minutes"
prerequisites:
  - Python 3.11+ installed
related:
  - ../how-to/common-workflows.md
  - ../reference/api-reference.md
---
```

**How-To Guide:**
```yaml
---
title: "How to Configure Custom Backends"
type: how-to
status: current
audience: intermediate
last_updated: 2025-10-23
tags: [configuration, backends, customization]
related:
  - ../reference/configuration-schema.md
  - ../tutorials/01-getting-started.md
---
```

**Reference:**
```yaml
---
title: "API Reference v1.0"
type: reference
status: current
audience: all
last_updated: 2025-10-23
version: 1.0.0
test_extraction: true
tags: [api, reference]
related:
  - ../how-to/api-usage.md
---
```

---

## Document Templates

### Tutorial Template

```markdown
---
title: "Tutorial: {Name}"
type: tutorial
status: current
audience: beginners | intermediate
last_updated: YYYY-MM-DD
estimated_time: "XX minutes"
prerequisites: []
related: []
---

# Tutorial: {Name}

## What You'll Build

Brief description of the end result (1-2 sentences).

## What You'll Learn

- Skill 1
- Skill 2
- Skill 3

## Prerequisites

- [ ] Prerequisite 1
- [ ] Prerequisite 2

## Time Required

Approximately XX minutes

---

## Step 1: {Action}

**What we're doing:** Brief explanation

**Code:**
\`\`\`bash
# Copy-pasteable command
command --with-flags
\`\`\`

**Expected output:**
\`\`\`
✓ Success message
\`\`\`

**Explanation:** Why this step matters, what it does

---

## Step 2: {Action}

(Continue with numbered steps...)

---

## What You've Learned

- Summary of skills acquired
- What you can do now

## Next Steps

- [ ] Tutorial 2: Advanced topic
- [ ] How-to Guide: Solve specific problem
- [ ] Build your own variation

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Common error | How to fix |

---

## Related Documentation

- [How-To: Related Task](../how-to/...)
- [Reference: API Used](../reference/...)
```

### How-To Guide Template

```markdown
---
title: "How to {Task}"
type: how-to
status: current
audience: intermediate
last_updated: YYYY-MM-DD
tags: []
related: []
---

# How to {Task}

## Problem

Brief description of the problem this guide solves (2-3 sentences).

## Solution Overview

High-level approach (bullet points).

## Prerequisites

- [ ] Prerequisite 1
- [ ] Prerequisite 2

---

## Approach 1: {Method Name} (Recommended)

**When to use:** Situation where this approach works best

**Steps:**

1. Do this
   \`\`\`bash
   command
   \`\`\`

2. Then this
   \`\`\`python
   code_example()
   \`\`\`

3. Finally this

**Pros:**
- ✅ Advantage 1
- ✅ Advantage 2

**Cons:**
- ❌ Limitation 1

---

## Approach 2: {Alternative Method}

**When to use:** Different situation

**Steps:** ...

---

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| Error X | Reason | Fix Y |

---

## Related Documentation

- [Tutorial: Learn the Basics](../tutorials/...)
- [Reference: API Documentation](../reference/...)
```

### Reference Template

```markdown
---
title: "{API/Schema Name}"
type: reference
status: current
audience: all
last_updated: YYYY-MM-DD
version: X.Y.Z
test_extraction: true
tags: []
related: []
---

# {API/Schema Name}

## Overview

Brief description (1-2 sentences).

**Status:** ✅ Stable | ⚠️ Beta | 🚧 Experimental
**Version:** X.Y.Z
**Last Updated:** YYYY-MM-DD

---

## Specification

### Parameters

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `param1` | string | Yes | – | Description |
| `param2` | number | No | `0` | Description |

### Response Schema

\`\`\`json
{
  "field1": "value",
  "field2": 123
}
\`\`\`

---

## Examples

### Example 1: {Common Use Case}

\`\`\`python
# Executable example
result = api_call(
    param1="value",
    param2=123
)
# Expected result
assert result["field1"] == "value"
\`\`\`

### Example 2: {Edge Case}

\`\`\`python
# Error handling
result = api_call(invalid_param="bad")
# Returns: {"error": "Invalid parameter"}
\`\`\`

---

## Related Documentation

- [How-To: Use This API](../how-to/...)
- [Explanation: Why This Design](../../dev-docs/explanation/...)
```

### Explanation Template

```markdown
---
title: "{Concept/Decision Title}"
type: explanation
status: current
audience: intermediate | advanced
last_updated: YYYY-MM-DD
tags: []
related: []
---

# {Concept Name}

## Overview

What is this concept/decision? (2-3 sentences)

## Context

**Problem:** What problem does this solve?

**Constraints:** What limitations did we work within?

**Alternatives Considered:** What else did we evaluate?

---

## The Solution

### High-Level Approach

Description with diagrams if applicable.

### Key Decisions

1. **Decision:** What we chose
   - **Rationale:** Why we chose it
   - **Trade-offs:** What we gave up

2. **Decision:** ...

---

## How It Works

Technical deep-dive (as needed for understanding).

---

## Benefits & Limitations

**Benefits:**
- ✅ Benefit 1
- ✅ Benefit 2

**Limitations:**
- ❌ Limitation 1
- ⚠️ Trade-off 1

---

## Related Documentation

- [Reference: Architecture](../reference/architecture.md)
- [How-To: Implement This](../../user-docs/how-to/...)
```

---

## Writing Standards

### General Principles

1. **Clarity First**
   - Use simple language
   - Define technical terms on first use
   - One idea per paragraph

2. **Active Voice**
   - ✅ "Run the command"
   - ❌ "The command should be run"

3. **Present Tense**
   - ✅ "The system validates input"
   - ❌ "The system will validate input"

4. **Consistency**
   - Use same terminology throughout
   - Follow naming conventions
   - Maintain consistent structure

### Code Blocks

**All code blocks MUST specify language:**

```markdown
✅ GOOD:
\`\`\`python
def example():
    return "testable"
\`\`\`

❌ BAD:
\`\`\`
def example():
    return "not testable"
\`\`\`
```

**Executable examples MUST be complete:**

```python
# ✅ GOOD: Complete, runnable
from mcp_orchestration.api import process

def main():
    result = process(input="test")
    assert result["status"] == "success"

# ❌ BAD: Missing imports, incomplete
result = process(...)
assert result["status"]
```

### Cross-References

**Use relative paths:**
```markdown
✅ GOOD: [How-To Guide](../how-to/solve-problem.md)
❌ BAD: [How-To Guide](/user-docs/how-to/solve-problem.md)
```

**Link to specific sections:**
```markdown
[API Schema](../reference/api-schema.md#field-definitions)
```

**Required links:**
- Related tutorials (in how-to guides)
- Related how-to guides (in tutorials)
- API reference (in tutorials and how-to guides)
- Explanation context (in reference docs)

---

## Automation & Validation

### Available Scripts

#### 1. Validate Documentation

**File:** `scripts/validate_docs.py`

**Purpose:** Check documentation quality

**Checks:**
- All docs have frontmatter
- Required fields present
- Frontmatter schema valid
- No broken internal links
- Staleness warnings (>90 days)
- Related links are bidirectional

**Usage:**
```bash
python scripts/validate_docs.py
# Exit code 0 = pass, 1 = fail
```

#### 2. Generate Documentation Map

**File:** `scripts/generate_docs_map.py`

**Purpose:** Auto-generate DOCUMENTATION_MAP.md from frontmatter

**Usage:**
```bash
python scripts/generate_docs_map.py
# Outputs: DOCUMENTATION_MAP.md
```

#### 3. Extract Tests from Documentation

**File:** `scripts/extract_tests.py`

**Purpose:** Extract code examples for testing

**Process:**
1. Find docs with `test_extraction: true`
2. Parse code blocks with language tags
3. Generate test file: `tests/integration/test_from_docs.py`
4. Run tests in CI

**Usage:**
```bash
python scripts/extract_tests.py
pytest tests/integration/test_from_docs.py
```

### CI Integration

Documentation quality is enforced in CI via `.github/workflows/docs-quality.yml`:

**Checks:**
1. ✅ Frontmatter schema valid
2. ✅ No broken internal links
3. ✅ Documentation examples work (extracted tests pass)
4. ✅ Related links bidirectional
5. ⚠️ Staleness warnings (>90 days since update)

**Enforcement:**
- ❌ Block merge if validation fails
- ⚠️ Warning if staleness detected (doesn't block)


---

## Maintenance

### Update Schedule

| Document Type | Update Frequency | Trigger |
|---------------|-----------------|---------|
| Tutorials | As features change | Feature owners |
| How-To guides | As needed | Maintainers |
| Reference | With every API change | API owners |
| Explanation | Major changes only | Architects |
| Project docs | Sprint/release cycle | Project lead |

### Staleness Policy

**Definition:** Document not updated in >90 days

**Action:**
1. CI generates warning (doesn't block)
2. Assigned to original author for review
3. Options:
   - Update content → reset timer
   - Mark as `status: deprecated` → move to archived/
   - Confirm still accurate → add "reviewed: YYYY-MM-DD" to frontmatter

### Deprecation Process

**Step 1: Mark as Deprecated**
```yaml
status: deprecated
deprecated_date: YYYY-MM-DD
replacement: path/to/new-doc.md
```

**Step 2: Add Deprecation Notice**
```markdown
> ⚠️ **DEPRECATED:** This document is deprecated as of YYYY-MM-DD.
> Use [{New Doc}](path/to/new-doc.md) instead.
```

**Step 3: Archive** (after 90 days)
```bash
mv user-docs/old-doc.md archived/old-doc.md
```

---

## Quality Checklist

### Before Creating a New Doc

- [ ] Determine Diátaxis type (tutorial/how-to/reference/explanation)
- [ ] Choose correct directory (user-docs/, project-docs/, dev-docs/)
- [ ] Use appropriate template
- [ ] Fill all required frontmatter fields
- [ ] Add cross-references to related docs

### Before Committing Doc Changes

- [ ] Run `python scripts/validate_docs.py`
- [ ] Verify code examples are testable
- [ ] Check internal links work
- [ ] Update `last_updated` field
- [ ] Run extracted tests (if `test_extraction: true`)

### During PR Review

- [ ] Frontmatter schema valid
- [ ] Code examples follow standards
- [ ] Cross-references bidirectional
- [ ] Writing is clear and concise
- [ ] Examples are complete and copy-pasteable

---

## Quick Reference

### Document Type Decision Tree

```
What's the user's goal?
│
├─ Learn a new skill/feature?
│  └─ Tutorial (step-by-step with expected output)
│  └─ Location: user-docs/tutorials/
│
├─ Solve a specific problem?
│  └─ How-To Guide (problem → solution variations)
│  └─ Location: user-docs/how-to/ or dev-docs/
│
├─ Look up API/specification?
│  └─ Reference (spec with executable examples)
│  └─ Location: user-docs/reference/
│
├─ Understand why/how system works?
│  └─ Explanation (concepts, architecture, decisions)
│  └─ Location: user-docs/explanation/ or dev-docs/
│
└─ Plan project/make decision?
   └─ Project doc (roadmap, ADR, sprint)
   └─ Location: project-docs/
```

### Frontmatter Quick Reference

```yaml
# REQUIRED (all docs)
---
title: "Document Title"
type: tutorial | how-to | reference | explanation | process | project | decision
status: current | draft | deprecated
last_updated: YYYY-MM-DD
---

# OPTIONAL (add as needed)
audience: beginners | intermediate | advanced | maintainers | all
tags: [tag1, tag2]
related: [../path/to/doc1.md, ../path/to/doc2.md]

# For tutorials/how-to
estimated_time: "30 minutes"
prerequisites: [tutorial1.md, "Tool installed"]

# For reference docs
version: 1.0.0
test_extraction: true
```

---

**Version:** 1.0.0
**Last Updated:** 2025-10-23
**Maintained By:** mcp-orchestration team
**Status:** Active

---

## Related Documentation

- [README.md](README.md) - Project overview
- [AGENTS.md](AGENTS.md) - Machine-readable instructions for AI agents
- [dev-docs/CONTRIBUTING.md](dev-docs/CONTRIBUTING.md) - How to contribute
- [dev-docs/DEVELOPMENT.md](dev-docs/DEVELOPMENT.md) - Developer deep dive
