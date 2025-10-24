# Memory System Guide for mcp-orchestration

**Purpose**: Comprehensive memory system documentation for cross-session learning and knowledge persistence.

**Parent**: See [../../AGENTS.md](../../AGENTS.md) for project overview and other topics.

---

## Quick Reference

- **Query events**: `mcp-orchestration-memory query --type app.failed --since 24h`
- **Search knowledge**: `mcp-orchestration-memory knowledge search --tag error-handling`
- **Create knowledge note**: `echo "content" | mcp-orchestration-memory knowledge create "Title" --tag tag1`
- **Show trace timeline**: `mcp-orchestration-memory trace <trace-id>`

---

## Overview

mcp-orchestration includes a stateful memory infrastructure for cross-session learning and knowledge persistence, implementing A-MEM (Agentic Memory) principles.

**Memory capabilities:**
- **Event Log** - Append-only operation history with trace correlation
- **Knowledge Graph** - Structured learnings with Zettelkasten-style linking
- **Trace Context** - Multi-step workflow tracking via `CHORA_TRACE_ID`
- **Cross-Session Learning** - Avoid repeating mistakes across sessions

---

## Memory Architecture (3-Tier Model)

mcp-orchestration implements a **three-tier memory architecture** optimized for AI agent workflows:

```
┌──────────────────────────────────────────────────────────────┐
│ TIER 1: EPHEMERAL MEMORY (Session Context)                  │
├──────────────────────────────────────────────────────────────┤
│ • Agent's working memory within single conversation         │
│ • Current task context, intermediate results                │
│ • Conversation history (messages, tool calls)               │
│ • Lifetime: Single session only                             │
│ • Storage: Agent's context window (not persisted)           │
└──────────────────────────────────────────────────────────────┘
                         ↓ (session completes)
┌──────────────────────────────────────────────────────────────┐
│ TIER 2: PERSISTENT CONVERSATION MEMORY (Event Log)          │
├──────────────────────────────────────────────────────────────┤
│ • Timestamped operation events (start, complete, fail)      │
│ • Trace-correlated multi-step workflows                     │
│ • Searchable event history (time-based queries)             │
│ • Lifetime: Months (monthly partitions)                     │
│ • Storage: .chora/memory/events/                            │
│ • Use when: Analyzing patterns, debugging recent issues     │
└──────────────────────────────────────────────────────────────┘
                         ↓ (summarize → distill)
┌──────────────────────────────────────────────────────────────┐
│ TIER 3: STRUCTURED KNOWLEDGE (Knowledge Graph)               │
├──────────────────────────────────────────────────────────────┤
│ • Distilled learnings from events (fixes, patterns)         │
│ • Zettelkasten-style bidirectional linking                  │
│ • Tag-based categorization, confidence scores               │
│ • Lifetime: Indefinite (permanent knowledge)                │
│ • Storage: .chora/memory/knowledge/                         │
│ • Use when: Applying proven solutions to new problems       │
└──────────────────────────────────────────────────────────────┘
```

**When agents use each tier:**

| Situation | Tier | Query Pattern |
|-----------|------|---------------|
| **Current task context** | Tier 1 | Access conversation history directly |
| **"What failed last week?"** | Tier 2 | `query_events(status="failure", since_hours=168)` |
| **"How did we solve X before?"** | Tier 3 | `kg.search(tags=["problem-type"], text="solution")` |
| **Debugging recent issue** | Tier 2 | `query_events(trace_id="abc123")` - see full workflow |
| **Learning from mistakes** | Tier 2→3 | Event log → distill → knowledge note |
| **Avoiding repeated errors** | Tier 3 | Query knowledge graph before attempting risky operation |

**Memory flow example:**

1. **Agent executes task** → Ephemeral working memory (Tier 1)
2. **Emit events during workflow** → Event log (Tier 2): `emit_event("task.completed", metadata={...})`
3. **Task fails, agent searches history** → Event log (Tier 2): `query_events(type="task.failed", since_hours=720)`
4. **Agent finds pattern, creates note** → Knowledge graph (Tier 3): `kg.create_note("How to handle timeout in X", tags=["error-handling"])`
5. **Next session encounters similar issue** → Query knowledge (Tier 3): `kg.search(tags=["error-handling"])` → Apply proven solution

**Benefits of tiered architecture:**
- ✅ Fast access to recent events (Tier 2: time-indexed)
- ✅ Semantic search of learnings (Tier 3: tag and content indexed)
- ✅ Automatic context pruning (Tier 1 clears each session)
- ✅ Incremental knowledge building (Tier 2 → Tier 3 distillation)

---

## Memory Location

All memory data stored in `.chora/memory/`:

```
.chora/memory/
├── README.md                    # Memory architecture documentation
├── events/                      # Event log storage (monthly partitions)
│   ├── 2025-01/
│   │   ├── events.jsonl         # Daily aggregated events
│   │   └── traces/              # Per-trace details
│   └── index.json               # Event index (searchable)
├── knowledge/                   # Knowledge graph
│   ├── notes/                   # Individual knowledge notes
│   ├── links.json               # Note connections
│   └── tags.json                # Tag index
├── profiles/                    # Agent-specific profiles
└── queries/                     # Saved queries
```

**Privacy:** Memory directory is in `.gitignore` by default (contains ephemeral learning data, not source code).

---

## Event Log Usage

**Emit events during operations:**

```python
from mcp_orchestration.memory import emit_event, TraceContext

# Start workflow with trace context
with TraceContext() as trace_id:
    # Emit operation events
    emit_event(
        "app.operation_completed",
        trace_id=trace_id,
        status="success",
        operation_name="example",
        duration_ms=1234
    )
```

**Query recent events:**


```python
from mcp_orchestration.memory import query_events

# Find failures in last 24 hours
failures = query_events(
    event_type="app.operation_failed",
    status="failure",
    since_hours=24
)

# Analyze patterns
for failure in failures:
    error = failure["metadata"]["error"]
    print(f"Operation failed: {error}")
```


---

## Knowledge Graph Usage

**Create learning notes:**

```python
from mcp_orchestration.memory import KnowledgeGraph

kg = KnowledgeGraph()

# Create note from learned pattern
note_id = kg.create_note(
    title="[Learning Title]",
    content="[Detailed learning content]",
    tags=["tag1", "tag2"],
    confidence="high"
)
```

**Search knowledge:**

```python
# Find notes by tag
notes = kg.search(tags=["error", "fix"])

# Find notes by content
notes = kg.search(text="timeout")

# Get related notes
related = kg.get_related("note-id", max_distance=2)
```

---

## CLI Tools for Agents

**Query events via bash:**

```bash
# Find recent failures
mcp-orchestration-memory query --type "app.failed" --status failure --since "24h"

# Get all events from last 7 days
mcp-orchestration-memory query --since "7d" --limit 100

# Get events as JSON for processing
mcp-orchestration-memory query --type "app.started" --json
```

**Get trace timeline:**

```bash
# Show workflow timeline
mcp-orchestration-memory trace abc123

# Get trace as JSON
mcp-orchestration-memory trace abc123 --json
```

**Search and manage knowledge:**

```bash
# Find notes about errors
mcp-orchestration-memory knowledge search --tag error

# Create knowledge note
echo "Fix content" | mcp-orchestration-memory knowledge create "Title" --tag tag1 --confidence high

# Show note details
mcp-orchestration-memory knowledge show note-id
```

**View statistics:**

```bash
# Stats for last 7 days
mcp-orchestration-memory stats

# Stats for last 24 hours with JSON output
mcp-orchestration-memory stats --since 24h --json
```

---

## Advanced Memory Query Patterns for Agents

This section provides **production-ready query patterns** for AI agents to effectively use the memory system. These patterns go beyond basic API calls to implement semantic search, temporal analysis, and confidence-filtered queries.

### Pattern 1: Semantic Search (Find Similar Problems)

**Use case:** Agent encounters an error and wants to find similar past issues.


```python
from mcp_orchestration.memory import query_events, KnowledgeGraph

# Step 1: Extract key terms from current error
current_error = "ConnectionTimeout: Failed to connect to database after 30s"
keywords = ["timeout", "database", "connection"]

# Step 2: Search event log for similar failures
similar_events = query_events(
    event_type="app.failed",
    since_hours=720,  # Last 30 days
    metadata_contains=keywords  # Semantic match
)

# Step 3: If events found, check for documented solutions
if similar_events:
    kg = KnowledgeGraph()
    solutions = kg.search(
        tags=["database", "timeout"],
        confidence_min="medium",  # Only proven solutions
        sort_by="confidence_desc"
    )

    if solutions:
        print(f"Found {len(solutions)} documented solutions")
        # Apply highest-confidence solution first
        return solutions[0]
```


**Why this works:** Combines time-based event search (Tier 2) with confidence-filtered knowledge retrieval (Tier 3) to find proven solutions to similar problems.

### Pattern 2: Temporal Analysis (Trend Detection)

**Use case:** Agent detects performance degradation and wants to identify when it started.


```python
from mcp_orchestration.memory import query_events
from datetime import datetime, timedelta

# Query last 14 days of operation metrics
events = query_events(
    event_type="app.operation_completed",
    since_hours=336,  # 14 days
    limit=1000
)

# Analyze trend by day
daily_avg_duration = {}
for event in events:
    day = datetime.fromisoformat(event["timestamp"]).date()
    duration = event["metadata"]["duration_ms"]

    if day not in daily_avg_duration:
        daily_avg_duration[day] = []
    daily_avg_duration[day].append(duration)

# Find degradation point
for day, durations in sorted(daily_avg_duration.items()):
    avg = sum(durations) / len(durations)
    if avg > BASELINE_THRESHOLD * 1.5:  # 50% slower than baseline
        print(f"Performance degraded starting {day}")

        # Query events from that day for root cause
        degradation_events = query_events(
            event_type="app.operation_completed",
            since=day.isoformat(),
            until=(day + timedelta(days=1)).isoformat()
        )
        # Analyze for correlation (code deploy, config change, etc.)
```


**Why this works:** Time-series analysis of event log (Tier 2) to identify inflection points and correlate with environmental changes.

### Pattern 3: Confidence-Filtered Queries

**Use case:** Agent wants to apply only high-confidence learnings to production code.


```python
from mcp_orchestration.memory import KnowledgeGraph

kg = KnowledgeGraph()

# Get only high-confidence solutions for critical operation
solutions = kg.search(
    tags=["error-handling", "production"],
    confidence="high",  # Only apply proven solutions
    updated_since_days=90  # Recent learnings (patterns evolve)
)

# Verify solution before applying
for solution in solutions:
    # Check if solution has been successfully applied recently
    verification_events = query_events(
        event_type="app.fix_applied",
        metadata_match={"solution_id": solution["id"], "outcome": "success"},
        since_hours=168  # Last 7 days
    )

    if verification_events:
        print(f"Solution {solution['id']} verified in production")
        return solution  # Safe to apply
    else:
        # Downgrade confidence if not recently verified
        kg.update_note(solution["id"], confidence="medium")
```


**Why this works:** Combines confidence scoring (Tier 3) with verification from recent events (Tier 2) to ensure safe application of learnings.

### Pattern 4: Multi-Hop Knowledge Traversal

**Use case:** Agent needs deep context about a problem, not just direct matches.


```python
from mcp_orchestration.memory import KnowledgeGraph

kg = KnowledgeGraph()

# Start with initial problem
initial_notes = kg.search(tags=["authentication", "error"])

# Traverse related notes (2 hops)
all_context = []
for note in initial_notes:
    all_context.append(note)

    # Get 1-hop neighbors (directly linked)
    hop1 = kg.get_related(note["id"], max_distance=1)
    all_context.extend(hop1)

    # Get 2-hop neighbors (friends of friends)
    for hop1_note in hop1:
        hop2 = kg.get_related(hop1_note["id"], max_distance=1)
        all_context.extend(hop2)

# Deduplicate and rank by confidence
unique_context = {n["id"]: n for n in all_context}.values()
ranked = sorted(unique_context, key=lambda n: n["confidence"], reverse=True)

# Agent now has comprehensive context from knowledge graph
print(f"Gathered {len(ranked)} related notes for context")
```


**Why this works:** Zettelkasten-style bidirectional linking enables agents to gather comprehensive context beyond exact keyword matches.

### Pattern 5: Hybrid Query (Events + Knowledge)

**Use case:** Agent wants to see both what happened (events) and what was learned (knowledge).


```python
from mcp_orchestration.memory import query_events, KnowledgeGraph

def hybrid_query(problem_type: str, since_hours: int = 168):
    """Query both event log and knowledge graph for comprehensive view."""

    # Part 1: What happened? (Event Log - Tier 2)
    events = query_events(
        event_type=f"app.{problem_type}",
        since_hours=since_hours,
        limit=50
    )

    # Part 2: What did we learn? (Knowledge Graph - Tier 3)
    kg = KnowledgeGraph()
    learnings = kg.search(
        tags=[problem_type],
        confidence_min="medium"
    )

    # Part 3: Cross-reference
    result = {
        "events": events,
        "learnings": learnings,
        "summary": {
            "occurrences": len(events),
            "documented_solutions": len(learnings),
            "most_recent": events[0]["timestamp"] if events else None,
            "highest_confidence_solution": max(learnings, key=lambda l: l["confidence"]) if learnings else None
        }
    }

    return result

# Agent uses hybrid query for comprehensive understanding
insight = hybrid_query("timeout_error", since_hours=720)  # Last 30 days
print(f"{insight['summary']['occurrences']} timeouts, {insight['summary']['documented_solutions']} solutions documented")
```


**Why this works:** Combines raw event data (what happened) with distilled knowledge (what we learned) for agents to make informed decisions.

**When to use which pattern:**

| Situation | Pattern | Why |
|-----------|---------|-----|
| Similar error encountered | Semantic Search | Find proven solutions to analogous problems |
| Performance degrading | Temporal Analysis | Identify when degradation started and correlate |
| Applying fix to production | Confidence-Filtered | Only use verified solutions in critical paths |
| Need deep context | Multi-Hop Traversal | Gather comprehensive understanding via links |
| General investigation | Hybrid Query | See both events and learnings together |

---

## Agent Self-Service: Learning from Past Errors

**When encountering a problem you've seen before:**

1. **Query past events** to find similar failures
2. **Search knowledge** for documented solutions
3. **Review related notes** via bidirectional links
4. **Apply the solution** from past learning
5. **Record outcome** to improve knowledge base

**Example workflow:**

```bash
# Problem: Tool failing with "rate limit exceeded"

# Step 1: Query past rate limit failures
mcp-orchestration-memory query --type "tool.failed" --since 30d | grep "rate limit"

# Step 2: Search knowledge base
mcp-orchestration-memory knowledge search --tag rate-limits --tag troubleshooting

# Step 3: Show specific solution note
mcp-orchestration-memory knowledge show rate-limit-handling

# Step 4: Apply exponential backoff solution (from knowledge note)
# ... implement fix ...

# Step 5: Record successful outcome
echo "Applied exponential backoff from rate-limit-handling note.
Rate limit errors reduced from 50/day to 2/day (96% improvement).
Solution: Added retry logic with delays [1s, 2s, 4s, 8s]." | \
  mcp-orchestration-memory knowledge create "Rate Limit Fix - Exponential Backoff Success" \
    --tag rate-limits --tag performance --tag solved --confidence high

# Step 6: Link to original problem note
mcp-orchestration-memory knowledge link rate-limit-handling rate-limit-fix-success
```

---

## Agent Self-Service: Creating Knowledge from Debugging

**When you solve a non-obvious problem:**

```bash
# After fixing a tricky bug, create knowledge note

# 1. Create note with problem context
echo "## Problem
Tool X was failing intermittently with 'connection timeout'.

## Investigation
- Analyzed events: mcp-orchestration-memory query --type tool.x.failed --since 7d
- Found pattern: Failures only during peak hours (9am-5pm)
- Root cause: Connection pool exhaustion (max 10 connections)

## Solution
Increased connection pool size to 50 in config.
Added connection pool monitoring.

## Validation
- Ran load test: 100 concurrent requests
- Zero timeouts after fix
- Connection pool usage: avg 15/50 (healthy headroom)

## Related
- Connection pool settings: [link to config docs]
- Load testing guide: [link to testing docs]" | \
  mcp-orchestration-memory knowledge create "Tool X Connection Timeout Fix" \
    --tag connection-pool --tag timeout --tag performance --confidence high

# 2. Tag for future retrieval
mcp-orchestration-memory knowledge tag connection-timeout-fix production-issues

# 3. Link to related notes
mcp-orchestration-memory knowledge link connection-timeout-fix connection-pool-config
```

**Benefits of creating knowledge:**
- Future sessions can query this solution
- Avoid repeating the same debugging work
- Build cumulative expertise over time
- Share learnings across agent instances

---

## A-MEM Self-Service Workflow (Agent Learning Loop)

**The agent learning loop implements A-MEM (Agentic Memory) principles:**

```
┌─────────────────────────────────────────────────────────┐
│  1. ENCOUNTER PROBLEM                                   │
│  Agent encounters error, unexpected behavior, or        │
│  performance issue during task execution                │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│  2. QUERY PAST EVENTS (Event Log)                       │
│  Search for similar failures in event history           │
│  mcp-orchestration-memory query --type problem.type --since 30d  │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│  3. SEARCH KNOWLEDGE (Knowledge Graph)                  │
│  Find documented solutions in knowledge base            │
│  mcp-orchestration-memory knowledge search --tag problem_domain  │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│  4. TRAVERSE LINKS (Bidirectional Navigation)           │
│  Follow related notes for deeper context                │
│  mcp-orchestration-memory knowledge show note-id        │
│  (Shows linked notes in "Related" section)              │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│  5. APPLY SOLUTION                                       │
│  Implement the learned fix from knowledge base          │
│  (Code changes, config updates, etc.)                   │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│  6. VALIDATE OUTCOME                                     │
│  Test that solution resolves the problem                │
│  Run tests, check metrics, verify behavior              │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│  7. RECORD LEARNING (Memory Evolution)                   │
│  Create/update knowledge note with outcome              │
│  mcp-orchestration-memory knowledge create "Solution Title"     │
│  Link to original problem note                          │
│  Tag for future retrieval                               │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│  8. CUMULATIVE IMPROVEMENT                               │
│  Future encounters of same problem → query knowledge    │
│  Faster resolution time (no re-debugging)               │
│  Build expertise over multiple sessions                 │
└─────────────────────────────────────────────────────────┘
```

**Example: Applying A-MEM Loop to Performance Issue**

```bash
# 1. ENCOUNTER PROBLEM
# Agent notices: API responses taking >5 seconds (slow)

# 2. QUERY PAST EVENTS
mcp-orchestration-memory query --type "api.slow_response" --since 30d
# Output: Found 15 events of slow responses in past month

# 3. SEARCH KNOWLEDGE
mcp-orchestration-memory knowledge search --tag performance --tag api
# Output: Found 3 notes: "API Caching Strategy", "Connection Pool Tuning", "Query Optimization"

# 4. TRAVERSE LINKS
mcp-orchestration-memory knowledge show api-caching-strategy
# Output shows:
# ## API Caching Strategy
# Problem: API responses slow due to repeated database queries
# Solution: Implemented Redis caching with 5-minute TTL
# Validation: Response time reduced from 5s to 200ms (96% improvement)
# Related: connection-pool-tuning, query-optimization

# 5. APPLY SOLUTION
# Implement Redis caching based on knowledge note guidance
# ... code changes ...

# 6. VALIDATE OUTCOME
# Run load test, measure response times
# Result: Response time now 180ms (97% improvement vs original 5s)

# 7. RECORD LEARNING
echo "## Context
Applied Redis caching to API endpoints based on 'API Caching Strategy' note.

## Implementation
- Added Redis client with 5-minute TTL
- Cached GET endpoints for /users, /products, /orders
- Cache invalidation on POST/PUT/DELETE

## Outcome
- Response time: 5s → 180ms (97% faster)
- Database load: -80% (queries cached)
- Redis memory usage: ~50MB (within budget)

## Refinement from Original
Original note used 5-minute TTL. Found 10-minute TTL works better for this use case.
Updated cache invalidation logic to be more granular.

## Related
- api-caching-strategy (original guide)
- connection-pool-tuning (complementary optimization)
- redis-configuration (cache config details)" | \
  mcp-orchestration-memory knowledge create "API Caching - Production Implementation" \
    --tag performance --tag api --tag caching --tag production --confidence high

# 8. CUMULATIVE IMPROVEMENT
# Link back to original note
mcp-orchestration-memory knowledge link api-caching-strategy api-caching-production

# Tag for production issues
mcp-orchestration-memory knowledge tag api-caching-production solved production-win

# Future sessions encountering slow API will:
# 1. Query events → find "api.slow_response"
# 2. Search knowledge → find "API Caching - Production Implementation"
# 3. See 97% improvement outcome → high confidence solution
# 4. Apply immediately without re-debugging
```

**A-MEM Principles in Action:**

1. **Dynamic Organization** - Agent creates notes, tags, links (not pre-defined schema)
2. **Note Construction** - Structured format with Problem/Solution/Validation
3. **Bidirectional Linking** - Notes reference each other (knowledge graph)
4. **Memory Evolution** - New notes update/refine existing knowledge
5. **Cross-Session Learning** - Future sessions benefit from past learning
6. **Confidence Tracking** - High confidence solutions applied first

See [README.md](README.md) for complete memory architecture documentation.

---

## Troubleshooting

### Memory CLI Errors

**Problem: Memory commands not found**

```bash
# Verify CLI installation
which mcp-orchestration-memory
# Expected: .venv/bin/mcp-orchestration-memory

# If missing, reinstall package with CLI
pip install -e .

# Verify entry point in pyproject.toml
grep -A 5 "\[project.scripts\]" pyproject.toml
# Should contain: mcp-orchestration-memory = "mcp_orchestration.cli.memory:main"
```

**Problem: Query returns empty results**

```bash
# Check event log directory
ls -la .chora/memory/events/
# Expected: Monthly directories (e.g., 2025-01/)

# Check events file exists and has content
cat .chora/memory/events/$(date +%Y-%m)/events.jsonl | wc -l
# If 0, no events emitted yet

# Emit test event to verify system
python -c "from mcp_orchestration.memory import emit_event; emit_event('test.verify', status='success')"

# Query again
mcp-orchestration-memory query --type test.verify
# Should show test event
```

**Problem: JSON parsing errors from CLI**

```bash
# Validate JSONL format in event log
python -c "
import json
with open('.chora/memory/events/2025-01/events.jsonl') as f:
    for i, line in enumerate(f, 1):
        try:
            json.loads(line)
        except json.JSONDecodeError as e:
            print(f'Line {i} invalid: {e}')
"

# If corrupted, backup and recreate
mv .chora/memory/events/2025-01/events.jsonl .chora/memory/events/2025-01/events.jsonl.backup
touch .chora/memory/events/2025-01/events.jsonl
```

### Event Log Troubleshooting

**Problem: Events not appearing in queries**

```bash
# 1. Verify event emission
python -c "
from mcp_orchestration.memory import emit_event
print('Emitting test event...')
emit_event('debug.test', status='success', metadata={'test': 'value'})
print('Event emitted successfully')
"

# 2. Check event log file was written
ls -lh .chora/memory/events/$(date +%Y-%m)/events.jsonl
# Size should increase after emission

# 3. View raw event log
tail -5 .chora/memory/events/$(date +%Y-%m)/events.jsonl

# 4. Query with verbose output
mcp-orchestration-memory query --type debug.test --json | python -m json.tool
```

**Problem: Trace correlation not working**

```bash
# Verify CHORA_TRACE_ID environment variable
echo $CHORA_TRACE_ID
# Should be UUID format if set by TraceContext

# Emit event with explicit trace_id
python -c "
from mcp_orchestration.memory import emit_event, TraceContext
with TraceContext() as trace_id:
    print(f'Trace ID: {trace_id}')
    emit_event('test.trace', trace_id=trace_id, status='success')
"

# Query by trace_id
mcp-orchestration-memory trace <TRACE_ID>
# Should show all events with that trace_id
```

**Problem: Event log too large / performance issues**

```bash
# Check total event count
cat .chora/memory/events/*/events.jsonl | wc -l

# Archive old events (older than 90 days)
mkdir -p .chora/memory/archive
find .chora/memory/events -type d -name "2024-*" -exec mv {} .chora/memory/archive/ \;

# Query stats for retention analysis
mcp-orchestration-memory stats --since 90d
# Review event types, identify noise (e.g., excessive debug events)
```

### Knowledge Graph Troubleshooting

**Problem: Knowledge notes not found in search**

```bash
# 1. List all knowledge notes
ls -la .chora/memory/knowledge/notes/
# Check if note file exists

# 2. Verify note format (YAML frontmatter + markdown)
cat .chora/memory/knowledge/notes/my-note.md
# Expected format:
# ---
# id: my-note
# title: My Note
# tags: [tag1, tag2]
# confidence: medium
# created: 2025-01-17T10:00:00Z
# updated: 2025-01-17T10:00:00Z
# ---
# Content here

# 3. Rebuild tag index if corrupted
python -c "
from mcp_orchestration.memory.knowledge_graph import KnowledgeGraph
kg = KnowledgeGraph()
kg._rebuild_tag_index()  # Internal method - use with caution
print('Tag index rebuilt')
"

# 4. Search again
mcp-orchestration-memory knowledge search --tag my-tag
```

**Problem: Broken bidirectional links**

```bash
# Check links.json structure
cat .chora/memory/knowledge/links.json | python -m json.tool

# Expected format:
# {
#   "note-a": ["note-b", "note-c"],
#   "note-b": ["note-a"],
#   "note-c": ["note-a"]
# }

# Verify linked notes exist
python -c "
import json
with open('.chora/memory/knowledge/links.json') as f:
    links = json.load(f)
    for note, targets in links.items():
        print(f'{note} → {targets}')
        for target in targets:
            path = f'.chora/memory/knowledge/notes/{target}.md'
            if not __import__('os').path.exists(path):
                print(f'  WARNING: {target} does not exist')
"

# Fix broken links
mcp-orchestration-memory knowledge link note-a note-b  # Recreate link
```

**Problem: Tag corruption or duplicates**

```bash
# View tag index
cat .chora/memory/knowledge/tags.json | python -m json.tool

# Find duplicate tags (case-sensitive)
cat .chora/memory/knowledge/tags.json | python -c "
import json, sys
tags = json.load(sys.stdin)
seen = {}
for tag in tags.keys():
    lower = tag.lower()
    if lower in seen:
        print(f'Duplicate: {tag} vs {seen[lower]}')
    seen[lower] = tag
"

# Merge tags if needed
mcp-orchestration-memory knowledge search --tag old-tag
# Create notes with new standardized tag
# Manually remove old tag from tag index
```

### Trace Context Troubleshooting

**Problem: CHORA_TRACE_ID not propagating to subprocesses**

```bash
# Verify TraceContext sets environment variable
python -c "
from mcp_orchestration.memory import TraceContext
import os
with TraceContext() as trace_id:
    print(f'Inside context: {os.environ.get(\"CHORA_TRACE_ID\")}')
    # Should match trace_id
print(f'Outside context: {os.environ.get(\"CHORA_TRACE_ID\")}')
# Should be None or previous value
"

# Test subprocess propagation
python -c "
from mcp_orchestration.memory import TraceContext
import subprocess, os
with TraceContext() as trace_id:
    result = subprocess.run(
        ['python', '-c', 'import os; print(os.environ.get(\"CHORA_TRACE_ID\"))'],
        capture_output=True,
        text=True
    )
    print(f'Trace ID: {trace_id}')
    print(f'Subprocess saw: {result.stdout.strip()}')
    # Should match
"
```

**Problem: Multiple overlapping trace contexts**

```bash
# Anti-pattern: Nested TraceContext (avoid this)
# python -c "
# from mcp_orchestration.memory import TraceContext
# with TraceContext() as trace_1:  # Outer context
#     with TraceContext() as trace_2:  # Inner context overrides
#         emit_event('test')  # Uses trace_2, loses trace_1
# "

# Correct pattern: Single TraceContext per workflow
python -c "
from mcp_orchestration.memory import TraceContext, emit_event
with TraceContext() as trace_id:
    emit_event('workflow.started', trace_id=trace_id)
    # ... all workflow steps ...
    emit_event('workflow.completed', trace_id=trace_id)
# Query workflow by trace_id
"
```

---

## Related Documentation

- **[Main AGENTS.md](../../AGENTS.md)** - Project overview, architecture, common tasks
- **[Testing AGENTS.md](../../tests/AGENTS.md)** - Testing instructions, troubleshooting
- **[scripts/AGENTS.md](../../scripts/AGENTS.md)** - Automation scripts reference

---

**End of Memory System Guide**

For questions or issues not covered here, see the main [AGENTS.md](../../AGENTS.md) or open a GitHub issue.
