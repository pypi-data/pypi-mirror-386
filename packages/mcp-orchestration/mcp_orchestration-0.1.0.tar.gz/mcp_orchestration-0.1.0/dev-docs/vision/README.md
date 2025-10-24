# Vision Documents - mcp-orchestration

This directory contains **vision documents** that describe potential future capabilities and evolutionary directions for mcp-orchestration. Vision documents are exploratory, not committed features.

---

## What Are Vision Documents?

Vision documents capture **long-term thinking** about how mcp-orchestration might evolve beyond the current committed roadmap. They serve several purposes:

1. **Strategic Context for Agents** - Help AI coding agents make architecture decisions that keep future doors open
2. **Alignment Documentation** - Record the founding vision and strategic direction for the project
3. **Decision Frameworks** - Provide explicit criteria for when to build future capabilities
4. **Exploration Space** - Allow thinking about possibilities without committing to timelines

### Vision vs. Roadmap

| Aspect | Vision Documents (This Directory) | Roadmap ([ROADMAP.md](../../ROADMAP.md)) |
|--------|----------------------------------|------------------------------------------|
| **Nature** | Exploratory, aspirational | Committed, time-bound |
| **Certainty** | Possible future directions | Committed deliverables |
| **Timeline** | Waves (post-milestone) | Specific versions/dates |
| **Audience** | Internal planning, AI agents | Public communication, users |
| **Changes** | Fluid, revised quarterly | Stable, changes = scope change |
| **Purpose** | Guide design decisions | Track delivery progress |

**Key Principle:** Vision documents inform architecture choices *today* without building future features *now*.

---

## Purpose: Guide Strategic Design Decisions

Vision documents help answer questions like:

- **For humans:** "Should I refactor this module now, or defer it?"
- **For AI agents:** "Does this implementation block future capabilities I see in the vision?"
- **For teams:** "Is this technical debt acceptable given our long-term direction?"

### Example Scenario

**Situation:** You're building an MCP tool that returns simple text responses.

**Without Vision:**

```python
def get_info(query: str) -> str:
    # Returns plain string
    return f"Result: {query}"
```


**With Vision (knows Wave 3 adds structured data):**

```python
def get_info(query: str) -> dict:
    # Returns structured data (extensible for Wave 3)
    return {
        "result": f"Result: {query}",
        "metadata": {"timestamp": now(), "version": "1.0"}
    }
```


**Outcome:** Current work delivers value *and* Wave 3 doesn't require breaking changes.

---

## Structure: Capability Waves

Vision documents are organized into **capability waves** - thematic groups of related features that build on each other:

```
Wave 1: Foundation (Current)
  ↓
Wave 2: Integration (Post-v1.0)
  ↓
Wave 3: Intelligence (Post-v2.0)
  ↓
Wave 4: Ecosystem (Post-v3.0)
```

Each wave includes:

1. **Capability Theme** - High-level description of what the wave enables
2. **Motivation** - Why this capability matters (user needs, market signals)
3. **Technical Sketch** - High-level implementation approach (not detailed specs)
4. **Decision Criteria** - Explicit go/no-go criteria for building this wave
5. **Success Metrics** - How to measure if the wave delivered value
6. **Dependencies** - What must be true before this wave (prior waves, external factors)

### Wave Lifecycle

```
EXPLORATORY → VALIDATED → COMMITTED → DELIVERED → ARCHIVED
     ↑                                                 ↓
     └─────────────── DEFERRED ←───────────────────────┘
```

- **Exploratory:** Brainstorming, no validation (all waves start here)
- **Validated:** User research confirms demand (move to roadmap consideration)
- **Committed:** Moved to ROADMAP.md with timeline (no longer "vision")
- **Delivered:** Shipped in a release (archive wave from vision docs)
- **Deferred:** Explicitly decided not to pursue (archive with rationale)
- **Archived:** Historical record in `vision/archive/` directory

---

## Decision Framework: When to Build a Wave

Use this framework when a milestone completes and you're considering the next wave:

### Step 1: Check Decision Criteria

Each wave has explicit criteria. Example:

**Wave 2 Criteria:**
- ✅ Wave 1 delivered and stable
- ✅ 50+ active users requesting integration features
- ✅ Backend APIs available and documented
- ❌ Team capacity available (3+ months)

**Decision:** 3/4 criteria met → Wave 2 remains exploratory (validate team capacity first)

### Step 2: Apply Go/No-Go Framework

```
┌─────────────────────────────────────────────────────┐
│ 1. User Demand Signal?                              │
│    NO → DEFER (no user pull)                        │
│    YES → Continue ↓                                  │
├─────────────────────────────────────────────────────┤
│ 2. Technical Validation Complete?                   │
│    NO → VALIDATE (spike/prototype first)            │
│    YES → Continue ↓                                  │
├─────────────────────────────────────────────────────┤
│ 3. Dependencies Ready?                              │
│    NO → DEFER (wait for dependencies)               │
│    YES → Continue ↓                                  │
├─────────────────────────────────────────────────────┤
│ 4. Team Capacity Available?                         │
│    NO → DEFER (focus on current roadmap)            │
│    YES → COMMIT TO ROADMAP                          │
└─────────────────────────────────────────────────────┘
```

### Step 3: Document Decision

**If COMMIT:**
1. Move wave from `dev-docs/vision/` to [ROADMAP.md](../../ROADMAP.md)
2. Add timeline and version target
3. Create GitHub milestone
4. Archive wave in `vision/archive/WAVE-NAME.md` with "Status: Committed to Roadmap"

**If DEFER:**
1. Update wave status in vision doc: `**Status:** Deferred (YYYY-MM-DD)`
2. Add rationale: "User demand below threshold (15 users, need 50+)"
3. Set review date: "Review again after v1.5.0 ships"

**If VALIDATE:**
1. Create spike/prototype task
2. Update wave status: `**Status:** Under Validation (spike in progress)`
3. Define validation criteria

---

## Quarterly Review Process

Vision documents are living documents reviewed quarterly:

### Review Schedule

- **Q1 (January):** Review after v1.0 release
- **Q2 (April):** Review after v1.5 release
- **Q3 (July):** Review after v2.0 release
- **Q4 (October):** Review after v2.5 release

### Review Checklist

- [ ] **User Signals:** Any new demand for exploratory waves? (GitHub issues, feedback)
- [ ] **Technical Landscape:** Dependencies changed? (APIs available, libraries mature)
- [ ] **Delivered Waves:** Move shipped waves to archive
- [ ] **Deferred Waves:** Re-evaluate deferred waves (user demand grown?)
- [ ] **New Waves:** Any new capability themes emerging?
- [ ] **Decision Criteria:** Update criteria based on learnings

### Review Output

Update vision document with:

```markdown
## Review History

### 2025-10-19 (Q4 Review)

**Decisions:**
- Wave 2 (Integration): COMMITTED to v1.5.0 roadmap (50+ users requesting)
- Wave 3 (Intelligence): DEFERRED until Wave 2 ships (dependency)
- Wave 4 (Ecosystem): Updated decision criteria (API partners now available)

**New Waves:**
- Wave 5 (Mobile): Added exploratory wave based on 12 GitHub issues

**Archived Waves:**
- Wave 1 (Foundation): Delivered in v1.0.0 (archived to vision/archive/)
```

---

## Archive Policy

### When to Archive

Archive waves when:

1. **Delivered:** Wave shipped in a release
2. **Deferred Permanently:** Explicit decision not to pursue (market changed, better alternative)
3. **Superseded:** New approach replaces old wave (capture learnings)

### Archive Structure

```
dev-docs/vision/archive/
├── WAVE-01-FOUNDATION.md         # Delivered in v1.0.0
├── WAVE-02-WEBSOCKET-SUPPORT.md  # Deferred (WebRTC chosen instead)
└── WAVE-03-CUSTOM-PROTOCOL.md    # Superseded (MCP became standard)
```

### Archive Format

Each archived wave includes:

```markdown
# Wave 1: Foundation

**Status:** Delivered in v1.0.0 (2025-10-19)

**Original Vision:** [Copy original wave content]

**Outcome:**
- Delivered features: [List]
- Variance from vision: [What changed and why]
- Success metrics: [Actual vs. target]
- Learnings: [What we learned for future waves]

**Archive Date:** 2025-10-19
**Reason:** Delivered
```

---

## How to Use Vision Documents

### For Human Developers

**When planning architecture:**
1. Read current wave in vision doc
2. Check if design serves both present and future
3. Apply decision framework: "Refactor now or defer?"
4. Document decision (ADR or knowledge note)

**When reviewing PRs:**
1. Ask: "Does this block future capabilities?"
2. Check: "Is this refactoring strategic or premature?"
3. Validate: "Decision aligned with vision framework?"

### For AI Coding Agents

**When implementing features:**
1. Check [AGENTS.md](../../AGENTS.md) Section 3: Strategic Design
2. Read vision document for context
3. Apply architecture check: "Does this block future waves?"
4. If refactoring needed, check decision framework
5. Document choice in knowledge note (if `include_memory_system=true`)

**When encountering design decision:**
1. Query event log for similar past decisions:
   ```bash
   mcp_orchestration-memory query --type architecture.decision --since 90d
   ```
2. Search knowledge for architectural notes:
   ```bash
   mcp_orchestration-memory knowledge search --tag architecture --tag vision
   ```
3. Apply learning to current decision
4. Record new decision for future reference

---

## Internal vs. External Communication

### Internal Use (This Directory)

Vision documents in `dev-docs/vision/` are **internal planning tools**:

- Exploratory, fluid thinking
- Explicit about uncertainty ("might", "could", "if")
- Technical implementation sketches
- Go/no-go decision criteria

**Audience:** Maintainers, AI agents, internal contributors

### External Communication (ROADMAP.md, README.md)

For public-facing docs, extract **committed portions only**:

- [ROADMAP.md](../../ROADMAP.md) - Committed features with timelines
- [README.md](../../README.md) - Current capabilities only
- GitHub Issues - User-facing feature proposals

**Audience:** Users, external contributors, community

### Example Translation

**Vision Document (Internal):**
> Wave 3 explores adding real-time streaming capabilities. This might use WebSockets or Server-Sent Events, depending on browser support in 2026. Decision criteria: 100+ users requesting, WebSocket libraries mature.

**ROADMAP.md (External, after commitment):**
> **v2.0 (Q3 2026):** Real-time streaming support via WebSockets. Enables live data updates and bi-directional communication.

**README.md (External, after delivery):**
> - ✅ **Real-Time Streaming** - WebSocket support for live data updates

---

## Template: Create New Vision Document

To create a new vision document:

1. Copy `CAPABILITY_EVOLUTION.example.md` to `YOUR_CAPABILITY.md`
2. Replace example waves with your project's capability themes
3. Adjust decision criteria for your project type
4. Add/remove waves as needed (3-5 waves typical)
5. Update this README.md if you add new vision docs

**Minimal Vision (1-2 waves):**
- Small projects may only need Wave 1 (Current) + Wave 2 (Next)
- Focus on decision criteria over elaborate technical sketches

**Comprehensive Vision (4-6 waves):**
- Complex projects may map multi-year evolution
- Each wave should still be actionable (not abstract)

---

## Related Documentation

- [ROADMAP.md](../../ROADMAP.md) - Committed features and timelines
- [AGENTS.md](../../AGENTS.md) - Machine-readable agent instructions (Section 3: Strategic Design)
- [CHANGELOG.md](../../CHANGELOG.md) - Historical record of delivered features
- [.chora/memory/](../../.chora/memory/) - Agent memory system for decision tracking
### How-To Guides

- [Maintain Vision Documents](https://github.com/liminalcommons/chora-base/blob/main/docs/how-to/06-maintain-vision-documents.md) - Detailed maintenance guide
- [Vision-Driven Development](https://github.com/liminalcommons/chora-base/blob/main/docs/explanation/vision-driven-development.md) - Philosophy and best practices

---

## Example: CAPABILITY_EVOLUTION.md

See [CAPABILITY_EVOLUTION.example.md](CAPABILITY_EVOLUTION.example.md) for a complete example vision document with:

- 4 capability waves (Foundation → Integration → Intelligence → Ecosystem)
- Decision criteria templates
- Success metrics examples
- Quarterly review process
- Technical sketches

**Customize it** for your project by replacing example waves with your actual capabilities.

---

**Last Updated:** 2025-10-19 (update manually during quarterly reviews)
**Template Version:** chora-base v1.3.0
**Status:** Living document (review quarterly)

🧭 Vision documents guide strategic decisions without committing to timelines.
