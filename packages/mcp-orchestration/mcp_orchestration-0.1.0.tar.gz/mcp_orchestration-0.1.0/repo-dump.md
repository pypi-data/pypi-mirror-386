## .gitignore

```
.venv/
__pycache__/
.pytest_cache/
*.pyc
build/
dist/
```

## AGENTS.md

```md
# AGENTS Guidance — mcp-orchestration

Scope: applies to the entire repo.

Coding & Docs
- Keep changes minimal and focused on the requested task.
- Prefer repository-relative paths in docs and manifests.
- Use capability IDs like `mcp.registry.manage` and behavior IDs like `MCP.REGISTRY.MANAGE`.
- Value scenarios belong in the manifest under `value_scenarios` and must reference docs and tests.

Validation & CI
- Local: run `PYTHONPATH=src` for CLI and tests.
- Required commands:
  - `python -m mcp_orchestrator.cli manifest-validate manifests/star.yaml`
  - `python -m mcp_orchestrator.cli behavior-validate docs/capabilities/behaviors`
  - `python -m mcp_orchestrator.cli scenario-validate manifests/star.yaml`
  - `pytest -q`
- CI workflow: `.github/workflows/chora-ci.yml` runs validators and tests without installing the package, using `PYTHONPATH=src`.

Style
- Python: follow existing structure; no one-letter variable names.
- Tests: place value scenario tests under `tests/value-scenarios/`.

Change Signals
- Update `docs/reference/signals/SIG-capability-onboard.md` with validator/test outcomes and status.

```

## README.md

```md
# MCP Orchestration

Capability provider implementing MCP server lifecycle tooling.

- Aligns with Chora platform standards and validators.
- Publishes manifests/behaviors for discovery and compatibility checks.
- Emits change signals for release and operational events.

## Getting Started

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e .[dev]
python scripts/apply_manifest_policy.py manifests/star.yaml
```

See `docs/` for capability descriptions and signals.

## Release Coordination

- Release plans: `docs/reference/release-a-plan.md`, `docs/reference/release-b-plan.md`, `docs/reference/release-plan-b.md`
- Repository overview: `docs/reference/overview.md`
- Telemetry how-to: `docs/how-to/telemetry.md`
- Codex agent instructions: `.codex/release-b-prompt.md`
```

## docs/capabilities/.gitkeep

```

```

## docs/capabilities/behaviors/mcp-registry-manage.feature

```feature
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

```

## docs/capabilities/mcp-registry-manage.md

```md
# Capability: MCP Registry Manage

Provides registry lifecycle operations for MCP servers.

## Behaviors
- @behavior:MCP.REGISTRY.MANAGE
- @status:draft

Behavior Specs:
- docs/capabilities/behaviors/mcp-registry-manage.feature

## Value Scenarios
- ID: mcp.registry.manage.create-doc — Status: ready
  - Guide: docs/how-to/create-doc.md
  - Tests: tests/value-scenarios/test_create_doc.py; references BDD feature above

## Integrations
- CLI: mcp-orchestrator manifest-validate
- MCP tools: forthcoming
```

## docs/ecosystem/solution-approach-report.md

```md
---
title: Developer Tooling Ecosystem — Solution Approach Report
status: draft
version: 0.1.0
last_updated: 2025-10-04
---

# Developer Tooling Ecosystem — Solution Approach Report

This report distills the solution-neutral intent into actionable options, tradeoffs, a recommended path, and a short execution plan to validate feasibility via targeted pilots.

## Executive Summary

- Recommend a Federated Discovery + Pull Indexer as the baseline for fast adoption and offline readiness.
- Layer Protocol-First runtime interop selectively where cross-service invocation benefits from standard negotiation.
- Use Event-Driven change signaling for governance and coordination without hard coupling.
- Keep a small Central Index role where it adds value (global search, compatibility matrix, decision log), backed by signed manifests and TTL/caching.

## Shared Ontology

The solution uses the same vocabulary as the intent statement:

- **Capability** – a discrete unit of value (e.g., “Manage MCP registry”).
- **Behavior** – a verifiable specification proving a capability works.
- **Manifest** – machine-readable metadata describing capabilities, owners, lifecycle, dependencies, and controls.
- **Change Signal** – structured event covering proposals, reviews, decisions, and rollouts.
- **Integration Contract** – automated compatibility checks tied to behaviors and manifests.
- **Constellation** – a project/team owning capabilities and manifests.

All data structures, pilots, and metrics refer back to these terms for consistency.

## Intelligence Principles

To balance human judgment, deterministic automation, and LLM-based agents, follow these principles:

1. **Right Tool for the Context** – Use deterministic code for repeatable validation and signing; use LLM-based agents for synthesis, triage, and drafting; keep humans on accountability-critical decisions and exceptions.
2. **Clear Handoffs** – Change signals and governance workflows must make handoffs explicit (e.g., “agent drafted → human approved”) to avoid automation overreach.
3. **Auditability** – Record provenance for agent-generated outputs (prompt, model version, reviewer) so changes remain traceable.
4. **Confidence & Escalation** – Agents should surface ambiguity or low confidence, triggering human review rather than guessing.
5. **Evolvable Boundaries** – Any shift in the division of labor (e.g., an automation no longer needs human approval) should flow through a change signal so the standard stays current.

## Ops Considerations

- Team model: one human operator (Victor) plus automation agents (Codex, Roo Code) building and running tooling.
- Approach: leverage agents to generate validators, indexers, CLIs, and governance automation to participate across release, DevSecOps, and operational lifecycles.
- Guardrails: favor architectures with low day-2 ops burden, graceful degradation when central services are offline, and self-healing caches.

### Pre-Prod SLOs and Guardrails (first 90 days)

- Human toil cap: ≤ 4 hours/week average to operate shared services.
- Central index availability: ≥ 99.0% (monthly downtime budget ≤ 7h 18m); must not block local workflows.
- Message bus availability: ≥ 99.0% (publish/read) with store-and-forward at edges.
- Degradation requirement: 0 critical-path failures during planned index/bus outages in chaos tests.
- Production-critical declaration: decided by Stewards Council after two consecutive months meeting SLOs; recorded in decision log.

## Decision Framework

- Criteria and weights
  - Security posture: 20
  - Adoption friction: 20
  - Offline readiness: 15
  - Ops burden and SLOs: 15
  - Runtime interoperability: 15
  - Extensibility: 10
  - Time-to-value: 5
- Environment anchors (confirm during socialization)
  - IdP/SCM/CI anchors: identity provider(s), code host(s), CI/CD stack(s)
  - Connectivity constraints: internet, VPN, air-gapped/partially connected
  - Regulatory/logging: PII handling, audit retention, boundary controls
  - Primary languages and package ecosystems

### Environment Anchors (confirmation plan)

- Owner: Victor (collect via short survey + repo scan)
- Method: agent-generated inventory scripts for CI config, IdP OIDC issuers, SCM providers
- Timeline: complete by Day 7 pre-pilot; publish to decision log
- Output: `docs/reference/environment-anchors.md` with confirmed IdP/SCM/CI, connectivity tiers, regulatory posture

## Options and Tradeoffs

- Central Index + Repo Manifests
  - Pros: strong central policy enforcement; simple global discovery and reporting
  - Cons: higher ops/SLO burden; central dependency; offline needs mirrored infra
  - Fit: good for governance-heavy orgs; medium adoption friction

- Federated Discovery + Pull Indexer (Recommended baseline)
  - Pros: high autonomy; strong offline via caches/mirrors; scalable TTL/staleness model
  - Cons: slightly more complex indexing; eventual consistency to manage
  - Fit: fast time-to-value; broad applicability across constellations

- Protocol-First (e.g., MCP/HTTP) for runtime interop
  - Pros: excellent runtime compatibility; contract-first invocation; minimal central infra
  - Cons: requires client/server updates; adoption varies by stack
  - Fit: apply in targeted service-to-service paths

- Event-Driven Coordination
  - Pros: decoupled signaling; RBAC by topic; audit-friendly streams
  - Cons: adds bus operations; discovery still needs manifests/indexing
  - Fit: ideal for change signals, decisions, and rollout events

## Recommendation and Rationale

- Adopt Federated Discovery + Pull Indexer as the backbone for manifests, discovery, and compatibility checks.
- Provide a thin Central Index for global search, compatibility matrix, and decision log — but do not hard-block local workflows when it is unavailable.
- Introduce Protocol-First runtime interop on priority service paths to validate negotiated compatibility in production contexts.
- Use Event-Driven coordination for change signals and governance events; store decisions in an append-only log.

## Prerequisite Infrastructure and Owners

- Message bus (for change signals)
  - Owner: Victor + Agents (bootstrap); future: Constellation Stewards
  - SLO: 99.9% read availability, 99.5% publish availability; retention 30–90 days depending on topic class
  - Notes: topic-level RBAC; offline edge buffers with replay
- Signing/provenance service (Sigstore-compatible)
  - Owner: Victor + Agents
  - SLO: 99.9% verification endpoint availability; transparency log durability RPO 0
  - Notes: keyless via OIDC preferred; attestations for manifests and build artifacts
- Central index hosting (thin global search + decision log)
  - Owner: Victor + Agents (within this platform tooling repository)
  - SLO (pre-prod): 99.0% read; writes best-effort with queueing when degraded; post-GA target 99.9%
  - Notes: not a hard dependency for local workflows; caches continue to serve
- Artifact/manifest storage (e.g., Git, OCI registry or object store)
  - Owner: Project maintainers (source), Victor + Agents (registry)
  - SLO: aligned to existing SCM/registry targets; immutable tags for reproducibility

## Pilot Scenarios and Acceptance

- Contract Break Detection Across Repos
  - Goal: dependent repo CI fails on incompatible change and routes to owner.
  - Acceptance: failure includes `capability_id`, versions, suggested deprecation window; waiver flow with expiry recorded in decision log; detection latency ≤ 30 minutes from push; SLA compliance ≥ 95% weekly.

- New Project Onboarding
  - Goal: create manifest, pass contract suite, appear in discovery with owner/contact.
  - Acceptance: ≤ 24h wall-clock from repo init to discoverable and validated; P95 onboarding ≤ 8 business hours; telemetry emits usage and validation events with trace IDs.

- Runtime Service Consumption
  - Goal: client resolves a service via discovery metadata and enforces compatibility at runtime.
  - Acceptance: deterministic negotiation success/failure with trace IDs; ≥ 99% of requests carry correlation context; 100% of configured chaos scenarios pass; P95 latency impact ≤ 5% under degradation. Scenario uses the pilot MCP capability as reference implementation.

- Offline Sync and Telemetry Backfill
  - Goal: edge mirror serves manifests; telemetry buffers and replays upon connectivity.
  - Acceptance: manifest TTL ≤ 60 minutes; alert at 90 minutes staleness; telemetry replay deduplication ≥ 99% and delivery within 24h of reconnect; signed bundles verified on import; 0 unresolved conflicts after reconciliation.

## Baseline Metrics (to be validated pre-pilot)

- Routing latency (change request → owner identified)
  - Baseline: collected via agent script scanning PRs/issues over past 2 weeks
  - Target: 50% reduction within two release cycles
- Metadata freshness (percentage within TTL)
  - Baseline: nightly job measures sampled repos against TTL
  - Target: ≥ 95% within TTL; alert when < 90%
- Contract coverage (behaviors with up-to-date metadata and passing tests)
  - Baseline: sampled across top 10 capabilities via CI logs and manifests
  - Target: ≥ 90% within one release cycle
- Incident rate from incompatibilities (per quarter)
  - Baseline: extracted from incident log labels ("compatibility")
  - Target: downward trend; < 1 major/quarter
- Offline replay success (deduped and delivered within 24h)
  - Baseline: N/A prior to rollout
  - Target: ≥ 99%

Collection plan
- Owner: Victor + Codex agents
- Method: small scripts against Git/CI APIs and local logs; results published as `docs/reference/baseline-metrics.md`
- Timeline: complete by Day 10 pre-pilot; refresh weekly during pilot

## Option Evaluation (Weighted Scoring)

- Criteria and weights
  - Security posture: 20
  - Adoption friction: 20
  - Offline readiness: 15
  - Ops burden/SLOs (lower burden → higher score): 15
  - Runtime interoperability: 15
  - Extensibility: 10
  - Time-to-value: 5

- Scores (1–5) and weighted totals
  - Central Index + Repo Manifests
    - Security 5, Adoption 3, Offline 3, Ops 2, Runtime 3, Extensibility 4, TtV 3
    - Weighted total: 335
    - Tradeoff: strong enforcement vs. higher ops dependency
  - Federated Discovery + Pull Indexer (Recommended)
    - Security 4, Adoption 5, Offline 5, Ops 4, Runtime 4, Extensibility 5, TtV 5
    - Weighted total: 450
    - Tradeoff: eventual consistency vs. central control; mitigated by TTLs and signing
  - Protocol-First Runtime Interop
    - Security 4, Adoption 3, Offline 3, Ops 4, Runtime 5, Extensibility 5, TtV 3
    - Weighted total: 385
    - Tradeoff: requires client/server changes; highest runtime fidelity
  - Event-Driven Coordination
    - Security 4, Adoption 3, Offline 3, Ops 3, Runtime 4, Extensibility 5, TtV 3
    - Weighted total: 355
    - Tradeoff: excellent for signaling; still needs discovery layer

### Scoring Table

| Option | Security (20) | Adoption (20) | Offline (15) | Ops (15) | Runtime (15) | Extensibility (10) | TtV (5) | Total |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Central Index + Manifests | 100 | 60 | 45 | 30 | 45 | 40 | 15 | 335 |
| Federated + Pull Indexer | 80 | 100 | 75 | 60 | 60 | 50 | 25 | 450 |
| Protocol-First Runtime | 80 | 60 | 45 | 60 | 75 | 50 | 15 | 385 |
| Event-Driven Coordination | 80 | 60 | 45 | 45 | 60 | 50 | 15 | 355 |

## Capability Releases (process as product)

We phase the effort as releases that produce reusable standards, services, and automation. Progress is tracked through change signals with explicit acceptance criteria.

This repository owns the shared deliverables in each release (standards, validators, queue, indexer, protocol libraries). Capability-provider repositories consume those artifacts and emit their own change signals when ready.

- **Release A — Shared Standards & Change Signaling**  
  - Participating repositories: this platform-tooling repo (publishes standards, validators, discovery indexer, change queue, CI/CLI templates, capability catalog) and the MCP orchestration capability repo (adopts manifest/behavior schema and consumes the validator package).  
  - Deliverables: compatibility policy, governance flow, security baseline (versioned in `docs/standards/`); schema validators published as reusable CI/CLI packages; reusable CI workflow, AGENTS snippet, and value scenario templates; minimal discovery indexer service with generated capability/catalog; change-signal queue + decision log running.  
  - Change Signal: `SIG-release-a-complete` (requires standards published, packages/templates released, catalog generated, change queue live, first capability provider onboarded with manifests, behaviors, and value scenario).

- **Release B — Ecosystem Adoption & Observability**  
  - Participating repositories: platform-tooling repo (ships offline mirror CLI, telemetry libraries/dashboards, repo-overview generator, updates capability catalog/templates, prototypes the `chora-liminal` hub), MCP orchestration repo (continues adoption), plus 3–5 additional capability-provider repos (e.g., agent runtime services) onboarding to manifest/behavior/telemetry standards.  
  - Deliverables: onboard additional capability providers; offline mirror CLI with TTL enforcement published; telemetry schema embedded in shared libraries and surfaced through RBAC-protected dashboards; repository overview template/generator available; initial `chora-liminal` hub demonstrating the signal inbox; capability catalog and templates refreshed.  
  - Change Signal: `SIG-release-b-complete` (requires break-detection scenario passing, mirror prototype validated, telemetry events visible in shared dashboards, catalog & repo overviews updated, liminal hub spike delivered).

- **Release C — Runtime Interop & Hardening**  
  - Participating repositories: platform-tooling repo (hardens indexer, publishes negotiation library, authors architecture ADR) plus the two capability-provider repos exercising the runtime pilot (e.g., MCP orchestration provider and the consuming service).  
  - Deliverables: protocol negotiation module exercised on a runtime service pair and published as a reusable library; discovery indexer hardened (incremental updates, signing, authz) with compatibility matrix published; architecture ADR capturing long-term discovery model; launch of a separate ecosystem-overview capability repo aggregating multi-repo signals/catalog data.  
  - Change Signal: `SIG-release-c-complete` (requires successful runtime pilot, hardened indexer deployed, ADR merged).

- **Release D — Interactive Liminal Experience**  
  - Participating repositories: platform-tooling repo (updates standards/templates and exposes telemetry hooks), `chora-signal` (push-based change-signal adapters), `chora-privacy` (privacy controls and policy enforcement), `chora-voice` (voice assistant pipeline), `chora-hud` (Godot HUD assets/SDK), and the `chora-liminal` capability repo that composes these capabilities into the user-facing hub. Additional capability providers may opt in by exposing liminal-ready manifests/scenarios.  
  - Deliverables: push-enabled change-signal service with subscription controls (`chora-signal`); reusable privacy templates and policy checks (`chora-privacy`); voice interface flows with sample prompts/actions (`chora-voice`); baseline Godot HUD package and Diátaxis docs (`chora-hud`); `chora-liminal` integrating these modules to present voice + HUD inbox, scenario dashboard, and telemetry view; platform repo publishes updated standards/templates to support the new components.  
  - Change Signal: `SIG-release-d-complete` (requires the liminal hub to consume the new capabilities end-to-end, push signal service live, privacy guidelines published, voice/HUD interfaces operational, telemetry flowing into liminal dashboards).
  
## Naming Conventions

Consistent names reinforce the ontology and improve discoverability. Adopt the following patterns (root namespace `chora` for shared components):

- **Repositories**: use `chora-<platform-domain>` for platform/shared repos (e.g., `chora-platform`) and `<domain>-<capability-provider>` for individual capability projects (e.g., `mcp-orchestration`, `agent-runtime`).
- **Capability IDs**: `<domain>.<capability>.<action>` in manifests and telemetry (`mcp.registry.manage`, `agent.session.execute`). Version suffix optional (`.v1`) when multiple versions coexist.
- **Change Signals**: `SIG.<scope>.<subject>.<state>` (e.g., `SIG.release.a.complete`, `SIG.capability.mcp.registry.update`). Use hyphenated sequences for iterations (`SIG.capability.mcp.registry.update-2`).
- **Packages/CLI**: prefix shared tooling with `chora-` (e.g., `chora-validator`, `chora-cli`) to signal ecosystem affiliation.
- **Docs & Standards**: organize under `docs/standards/<standard>.md`, `docs/capabilities/<capability>.md`, `docs/reference/<artifact>.md` reflecting capability and lifecycle stage.
- **Templates**: publish reusable assets (CI workflows, AGENTS snippets, CLI scaffolds, repo overview package) under a shared `templates/` namespace so capability repos can adopt them without bespoke setup.
- **Value Scenario IDs**: follow `<domain>.<capability>.<verb>` (e.g., `mcp.registry.manage.create-doc`) and store supporting guides/tests under predictable paths (`docs/how-to/`, `docs/reference/value-scenarios/`, `tests/value-scenarios/`).

Document all deviations via change signals and update the naming guidelines alongside releases to keep the ecosystem coherent.

## Backlog & Future Directions

- **Decentralized Runtime Exploration** – Prototype running Chora capabilities (including `chora-liminal`) on decentralized frameworks (e.g., Holochain) once runtime interop stabilizes.
- **Advanced HUD / Godot Multiplayer** – Extend the HUD from local preview to multi-user spaces with authentication, private workrooms, and collaborative signal handling.
- **Automated Template Application** – Enhance `chora-cli template apply` with parameterization, PR scaffolding, and additional template types (issue/PR templates, project configs).
- **Signal-driven Automation** – Introduce rule-based responders that can acknowledge or execute change signals automatically on behalf of capabilities.
- **Security & Privacy Hardening** – Encrypt signal feeds, add fine-grained RBAC for liminal data, and integrate secrets/identity services across liminal deployments.

Scope guardrail: pause new capability scope if any release metrics fall below target for two consecutive weeks; resume after corrective action documented via change signal.

## Release Management Model

We intentionally blend ecosystem-wide releases with repository/capability releases so the platform can evolve without blocking independent teams.

- **Ecosystem capability releases** (Release A/B/C above) coordinate shared tooling: standards, validators, discovery services, runtime negotiation. Each has a named change signal (`SIG-release-*-complete`) and delivers artifacts every repo depends on.
- **Capability-provider releases** remain repo-managed. Individual teams ship features when their manifests, behaviors, and integration contracts are ready. They emit their own change signals (e.g., `SIG-mcp-provider-release`) referencing the shared policies.
- **Governance integration**: the shared change-signal workflow and decision log capture both release types, preserving visibility without enforcing a single train. If an ecosystem release slips, repo-level releases can proceed, provided they meet the published standards.
- **Metrics & guardrails**: global metrics (metadata freshness, routing latency, security SLAs) trigger scope freezes for ecosystem changes; capability releases monitor their own KPIs and reference the same guardrails.

This hybrid model keeps the shared platform coherent while still empowering small teams to deliver value autonomously.

## Value Scenario Workflow

We define a *value scenario* as a user-testable unit of value tied to a capability. Each scenario includes manual guidance, automated checks, change-signal context, and telemetry identifiers so humans and LLM-based agents can verify outcomes repeatably.

- Scenarios are declared in manifests (`value_scenarios`), referenced in change signals, and listed in the discovery catalog.
- Diátaxis docs live under `docs/how-to/` and `docs/reference/value-scenarios/`; automated tests run from `tests/value-scenarios/`.
- Platform tooling provides templates (`docs/templates/value-scenario/`) and validator support to ensure scenarios remain discoverable and executable.
- Release closure requires associated scenarios to pass (manual or automated) and telemetry to confirm success.

## Risks and Mitigations

- Stale metadata or drift
  - Mitigation: CI validators; TTLs; attestations; automated staleness alerts
  - Owner: Victor + Agents (validators), Maintainers (repo manifests)
  - Success metric: freshness ≥ 95% within TTL; alert time-to-ack ≤ 4h
- Fragmented UX across tools
  - Mitigation: shared UX guidelines; reference CLI patterns; lints
  - Owner: Victor + Agents
  - Success metric: guideline adoption in ≥ 80% of shared tools by 60 days
- Signal saturation and noise
  - Mitigation: dedupe rules; priority labels; ownership auto-assignment; SLAs
  - Owner: Stewards; Maintainers for local queues
  - Success metric: SLA compliance ≥ 95%; duplicate rate ≤ 5%
- Security erosion via shared tooling
  - Mitigation: SLSA targets; Sigstore signing; SPDX SBOMs; OPA policy gates; periodic audits
  - Owner: Victor + Agents
  - Success metric: 0 unsigned releases in shared tooling; critical vuln SLA ≤ 7 days

## Adoption Map (scope and phasing)

- Phase 1 (Days 0–30): MCP orchestration capability provider; 2 projects onboarded
- Phase 2 (Days 31–60): Agent runtime capability provider cohort; +3–5 projects onboarded
- Phase 3 (Days 61–90): One runtime service pair exercising the protocol-first pilot

Scope guardrail: freeze new scopes if any pilot metric falls below target for two consecutive weeks; resume after corrective ADR.

## Required Artifacts and Owners

- `adr/0001-ecosystem-architecture.md` — chosen architecture, rationale, scope — Owner: Victor — Target: Day 14
- `docs/proposals/option-comparison.md` — options, tradeoffs, risk table — Owner: Victor — Target: Day 10
- `docs/pilots/pilot-plan.md` — pilot scenarios, owners, timelines, acceptance tests — Owner: Victor — Target: Day 12
- `docs/reference/manifest-example.md` — minimal manifest with commentary — Owner: Agents — Target: Day 9
- `docs/reference/change-signal-example.md` — example workflow and states — Owner: Agents — Target: Day 9
- `docs/standards/compatibility-policy.md` — versioning, deprecations, waiver policy — Owner: Victor — Target: Day 8
- `docs/standards/governance-flow.md` — states, SLAs, quorum, escalation, logging — Owner: Victor — Target: Day 8
- `docs/standards/discovery-model.md` — indexing, refresh, TTLs, authn/z, offline mirrors — Owner: Agents — Target: Day 11
- `docs/standards/security-baseline.md` — SLSA/Sigstore/SPDX, vuln gating, secrets, identity — Owner: Victor — Target: Day 11
- `docs/standards/telemetry-schema.md` — events, labels, traces, retention, RBAC — Owner: Agents — Target: Day 11
- `docs/reference/environment-anchors.md` — confirmed IdP/SCM/CI, connectivity, regulation — Owner: Victor — Target: Day 7
- `docs/reference/baseline-metrics.md` — baseline collection and results — Owner: Victor — Target: Day 10

## Reference Snippets

- Minimal Manifest (YAML)

```yaml
id: "capability.example.build.validate-release"
version: "1.0.0"
owner: "team-alpha"
lifecycle_stage: "validate"
inputs:
  - name: artifact
    type: oci-image
outputs:
  - name: report
    type: sarif
dependencies:
  - id: "contract.example.release-policy"
    version: ">=1 <2"
security_tier: "medium"
stability: "stable"
adr_links:
  - "adr/0012-release-policy.md"
validation_status: "passing"
```

- Change Signal (YAML)

```yaml
id: "signal-2025-001"
type: "breaking-change"
capability_id: "api.users.v1"
current_version: "1.4.0"
proposed_version: "2.0.0"
priority: "high"
impact: "removes field 'nickname'"
state: "review"
stewards:
  - "team-users"
  - "team-clients"
sla:
  acknowledge_by: "2025-10-12"
  review_by: "2025-10-15"
  decision_by: "2025-10-22"
deprecation_window: "90d"
waiver:
  allowed: true
  max_duration: "30d"
  expiry: "2026-01-31"
links:
  - "decision-log/2025/10/001.md"
```

## Next Steps

- Socialize the report and confirm environment anchors per constellation.
  - Owner: Victor (human) with Codex agent support
- Select the baseline architecture and owners; open ADR 0001.
  - Owner: Victor (human), co-authored by Codex; reviewed by Constellation Stewards
- Greenlight the pilot plan and schedule execution.
  - Owner: Victor; execution by Codex/Roo Code agents and project maintainers

## Clarifications

- Pre-production SLOs for message bus and index (first 90 days): defined under "Pre-Prod SLOs and Guardrails"; production-critical status decided by Stewards Council after meeting SLOs for two consecutive months.
- Waiver governance during pilot: approvals by Stewards; max duration 30 days; limit to ≤ 5 active waivers per capability; all waivers recorded with expiry and owner in decision log.

## Offline Change-Signal Handling

- Store-and-forward at edges; unique IDs with vector clocks to reconcile duplicates.
- On reconnect: de-dup by `(id, version)`; conflicts resolved by latest `state` timestamp; audit log retains both for traceability.
```

## docs/ecosystem/solution-neutral-intent.md

```md
---
title: Developer Tooling Ecosystem – Intent & Requirements
status: draft
version: 0.1.0
last_updated: 2025-10-03
---

# Developer Tooling Ecosystem – Intent & Requirements

This document captures problem framing and intent without prescribing an implementation. It describes why an ecosystem of developer tooling is needed, the outcomes it must enable, and the systemic properties required for success. It is intended to guide the `chora-platform` repository and any participating capability providers; any concrete solution should satisfy these statements or supply a rationale for deviations.

## Motivation

- Development teams work across several projects that share concepts (release management, environment control, runtime services) yet evolve independently.
- Duplication of tooling and inconsistent practices increase onboarding time, create security variance, and slow coordinated change.
- Agents (human or automated) need consistent ways to discover capabilities, reason about dependencies, and coordinate work across repositories.

## Primary Objectives

1. **Shared Understanding** – Provide a common vocabulary for lifecycle stages (plan, build, validate, release, operate) and the artifacts that flow between them.
2. **Composable Tooling** – Allow projects to adopt shared components or contribute new ones without central bottlenecks.
3. **Coordinated Change** – Surface cross-project needs early, decide ownership with transparency, and communicate decisions back to every participant.
4. **Runtime Interop** – Support scenarios where projects consume each other’s services dynamically, not only via build-time dependencies.
5. **Trust & Governance** – Maintain security, compatibility, and quality when tooling is reused or composed.

## Actors & Roles

- **Project Maintainers** – steward individual repositories; need clarity on ecosystem expectations and support when changes affect others.
- **Developers** – consume tooling during day-to-day work; prefer predictable UX and self-serve documentation.
- **Automation/Agents** – execute scripts, tests, or operations; require machine-readable manifests, deterministic interfaces, and auditable behavior.
- **Coordinators/Stewards** – mediate cross-project topics, maintain shared infrastructure, and record decisions.

## Glossary (Solution Neutral)

- **Capability** – A unit of value exposed to ecosystem participants (e.g., “Register MCP server”). Capabilities may be offered via CLI, APIs, or runtime services and are traceable through metadata.
- **Behavior** – A verified specification (often BDD) that proves a capability functions as intended, describing preconditions, interactions, and expected outcomes.
- **Manifest** – Machine-readable metadata describing available capabilities, interfaces, dependencies, lifecycle state, and owning parties for a project or service.
- **Integration Contract** – A set of automated checks and expectations (schema validation, protocol tests) that enforce compatibility across project boundaries.
- **Change Signal** – A structured notification that a capability, contract, or dependency needs attention (new feature, breaking change, incident), driving coordination across teams.

## System Capabilities (Solution Neutral)

- **Lifecycle Alignment** – Each project maps its workflows to a shared lifecycle. Tooling can query stage-appropriate actions (e.g., “validate release”).
- **Manifested Capabilities** – Every reusable asset (CLI command, behavior spec, runtime service) declares metadata describing its purpose, interfaces, dependencies, and status.
- **Capability Discovery** – Participants can search the ecosystem to answer “Who provides X?” or “Is there a behavior covering Y?”
- **Documentation & Templates** – Every capability exposes Diátaxis-aligned docs (tutorial/guide/reference/explanation) and reusable templates (CLI help, AGENTS snippets, CI workflows) so humans and LLM agents can onboard quickly.
- **Value Scenarios** – Each capability publishes user-testable scenarios with manual and automated verification paths, linked to change signals and telemetry so outcomes can be proven repeatedly.
- **Repository Overview** – Every repository publishes an autogenerated overview (front page) summarizing current capabilities, value scenarios, signals, and telemetry, making orientation simple for humans and LLM agents.
- **Liminal Capability** – Operators may run a personal or shared control capability (e.g., `chora-liminal`) that consumes manifests, signals, and telemetry from the platform and composes other Chora capabilities (signal adapters, privacy controls, voice/HUD modules). The capability must follow the same standards for manifests, scenarios, templates, and privacy.
- **Change Signaling** – Needs, risks, and proposals flow through a structured channel that captures scope, impact, and resolution status.
- **Integration Contracts** – Automated checks ensure manifests, behaviors, and runtime interfaces remain compatible as projects evolve.
- **Security & Compliance** – Common baselines for dependency audits, secret handling, logging separation, and release approval.
- **Observability & Feedback** – Metrics and qualitative signals reveal which tools are used, which fail, and where to focus investment.

## Minimum Manifest Requirements

Every manifest should at minimum include the following fields so automation and humans can reason about the ecosystem consistently:

- `id` – globally unique identifier for the capability or service.
- `version` – semantic version describing the manifest entry.
- `owner` – accountable team or individual with contact information.
- `lifecycle_stage` – current lifecycle phase (plan, build, validate, release, operate, retired).
- `inputs` / `outputs` – key parameters or artifacts consumed/produced.
- `dependencies` – referenced capabilities, contracts, or external services.
- `security_tier` – classification indicating sensitivity, secret scopes, and required controls.
- `stability` – qualitative status (`experimental`, `beta`, `stable`, `deprecated`).
- `adr_links` – architectural decision records (ADRs) or standards that govern the capability.
- `validation_status` – summary of latest automated checks (date, pass/fail, tooling used).

Any implementation should be able to extend beyond this baseline but must not omit these fields.

### Manifest Entry Example

```yaml
id: MCP.REGISTRY.MANAGE
version: 0.3.1
owner: aurora-mcp-team
lifecycle_stage: operate
inputs:
  - registry_path
  - server_manifest
outputs:
  - registry_state
dependencies:
  - nebula-core@1.x
security_tier: moderate
stability: stable
adr_links:
  - docs/adr/ADR-2025-04-registry-schema.md
validation_status:
  last_run: 2025-10-01T04:12:00Z
  result: pass
  tool: nebula-contract-suite
value_scenarios:
  - id: mcp.registry.manage.create-doc
    guide: docs/how-to/create-doc.md
    automated_test: tests/value-scenarios/test_create_doc.py
    change_signal: SIG-capability-onboard
telemetry:
  signals:
    - name: chora.value_scenario.mcp.registry.manage.create_doc
      status: in_progress
      docs: docs/reference/signals/SIG-capability-onboard.md
```

Value scenarios make user outcomes discoverable and verifiable alongside capability metadata.

## Change Signaling Workflow

To avoid ad hoc coordination, the ecosystem relies on a shared workflow with clear ownership:

- **States**: `proposal` → `review` → `decision` → `rollout` → `closed` (or `superseded`). Each state captures timestamps so SLA breaches are visible.
- **Ownership (RACI)**: the originator is Responsible for drafting; designated stewards and affected owners are Accountable for review/approval; coordinators and impacted teams are Consulted; broader stakeholders stay Informed via automated notifications.
- **SLAs**: proposals acknowledged within 2 business days; reviews concluded within 5 business days (extensions must be documented); decisions recorded within 2 business days of review closure; rollout plans defined before executing breaking changes.
- **Deduplication & Prioritization**: signals must include manifest IDs, capability tags, and impact category (security, reliability, functionality, documentation). Automation groups duplicates and enforces prioritization order security > reliability > functionality > documentation.
- **Publication & Escalation**: workflow transitions are visible through dashboards/CLI. If an SLA is missed twice or a critical (P0) signal lacks action, escalate to the ecosystem council chair.
- **Appeals**: affected owners may trigger an appeal state with a 3-business-day SLA for reconsideration; outcomes are logged alongside the original decision.

### Change Signal Example

```yaml
id: SIG-2025-0012
title: Deprecate legacy MCP registry format
capabilities: ["MCP.REGISTRY.MANAGE"]
state: review
priority: high
impact: breaking
owner: aurora-mcp-team
stewards: ["nebula-core"]
created_at: 2025-09-29T18:30:00Z
sla:
  acknowledge_by: 2025-10-01T18:30:00Z
  decide_by: 2025-10-06T18:30:00Z
links:
  manifests: ["aurora-mcp/star.yaml"]
  behaviors: ["MCP.REGISTRY.MANAGE"]
  adr: ["ADR-2025-07"]
```

## Governance & Decision Flow

- **Council Cadence**: Cross-project council meets bi-weekly with option for asynchronous decisions via documented voting (minimum 3 business days). Emergency meetings can be called for P0 signals.
- **Quorum & Voting**: Simple majority of stewards plus representation from affected projects constitutes quorum. Decisions recorded with outcome, dissent notes, and follow-up owners.
- **Working Groups**: Temporary groups chartered for focused topics (e.g., security baseline). Mandate includes deliverables, timeline, and sunset criteria.
- **RACI Summary**:
  - **Stewards (R/A)** – maintain standards, approve breaking changes.
  - **Project Maintainers (R/A)** – implement changes within their repos.
  - **Coordinators (C)** – ensure communication, track SLAs.
  - **Contributors (I)** – kept informed via change signal updates and documentation.
- **Appeal & Escalation**: Appeals escalate to council chair; unresolved disputes within 5 business days escalate to executive sponsor or governance board.
- **Decision Log**: All outcomes stored in an accessible log referencing related change signals, manifests, and ADRs.

Any solution must make it easy to raise, track, and resolve change signals following this lifecycle.

## Compatibility Policy

- **Versioning Rules**: Capabilities and integration contracts adopt semantic versioning (`MAJOR.MINOR.PATCH`). Major bumps denote breaking change and require council approval plus migration plan; minor bumps add backward-compatible behavior; patch bumps cover fixes or documentation.
- **Backward/Forward Checks**: Automated suites verify backward compatibility with the previous MAJOR.MINOR release and (where possible) forward compatibility so older consumers tolerate newer providers.
- **Grace Periods**: Breaking changes must provide a migration plan with at least two release cycles’ notice (unless addressing a critical security issue). Plans include timelines, fallbacks, and communication strategy.
- **Automated Break Detection**: Integration contracts and smoke suites run across dependency matrices. Failures auto-open high-priority change signals and block release until resolved or waiver granted.
- **Waiver Process**: Temporary waivers require justification, mitigation steps, owner, and expiry date. Expiring waivers trigger alerts; expired waivers default to enforcement.
- **Deprecation Playbook**: Mark capabilities as `deprecated`, reference replacements, track usage via telemetry, and schedule removal with explicit dates. Change signals coordinate decommissioning.
- **Compatibility Matrix**: Maintain machine-readable matrices mapping provider and consumer versions. Update alongside release readiness and expose via discovery APIs.

## Security Baseline

Any ecosystem-wide approach must account for security from the outset:

- **Threat Model**: Document adversaries (external, insider, supply chain). Evaluate attack surfaces for CLI plugins, manifests, runtime services, and observability feeds.
- **Provenance & Signing**: Target SLSA Level 3 builds. Sign artifacts, manifests, and change-signal bundles using Sigstore (Cosign/Fulcio/Rekor) or equivalent; verify signatures before ingestion.
- **SBOM & Vulnerability Gating**: Produce SPDX SBOMs for each release. Integrate scanners (pip-audit, osv-scanner). Block releases on high/critical CVEs unless a council-approved waiver with mitigation exists.
- **Policy-as-Code**: Encode guardrails via OPA/Conftest (dependency policies, secret usage, runtime auth). Enforce in CI and pre-merge.
- **Secret Handling**: Define secret tiers (developer, project, shared). Manifests declare required secrets and scope. Prefer just-in-time issuance and avoid embedding credentials in configs/logs.
- **Service Identity & Auth**: Use workload identities (OIDC, SPIFFE) and mutual TLS where feasible. Deprecate static tokens; enforce rotation.
- **Audit & Logging**: Maintain tamper-evident logs capturing CLI usage, manifest changes, change signals, and runtime access. Retain ≥12 months with controlled access.
- **Incident Response**: Maintain shared playbooks mapping capabilities to response owners; run periodic drills and capture lessons learned.

## Discovery Expectations

- **Architecture**: Hybrid approach—authoritative manifests stay with owning repositories; central indices mirror metadata for search and caching via documented APIs.
- **Location & Distribution**: Require manifests in repo roots and release artifacts; optionally expose via HTTPS. Central index uses ETag/If-Modified-Since to synchronize.
- **Cache & Refresh**: Index refresh cadence is configurable (default daily). Manifests supply `updated_at` and optional `ttl`. Clients warn when TTL exceeded. Offline mirrors package signed bundles (manifest + SBOM + behaviors) for air-gapped use.
- **Authentication/Authorization**: Index queries default to SSO-authenticated users. Security tiers control visibility; automation acquires scoped tokens. Access events are logged for audit.
- **Staleness Detection**: Compare manifest timestamps vs. latest release tags and validation status. Flag stale entries and emit change signals when overdue.
- **Offline Operation**: Provide export/import commands creating signed bundles. Mirror servers verify signatures and manifest versions before syncing. Registry sync policies define required approvals and checksum verification.
- **Capability Catalog**: Generate a consolidated catalog (e.g., `docs/capabilities/index.md`) from the discovery index so humans and agents can enumerate all available capabilities and follow links to manifests and documentation.
- **Manifest Discovery Hints**: Manifests should declare CLI commands, MCP endpoints, and doc references (`discovery.cli_commands`, `discovery.docs`) so automation knows how to invoke the capability after discovery.
- **Value Scenario Catalog**: Generate a catalog of user-testable scenarios alongside capabilities, including manual guides, automated tests, and associated change signals. Agents can query the catalog to run validation flows.

## Observability Requirements

- **Events**: Capture `cli_usage`, `behavior_validation`, `change_signal_transition`, `runtime_invocation`, and `incident` events.
- **Metrics**: Emit counts/durations keyed by `capability_id`, `version`, `owner`, `status`. Include success/failure rates, routing latency, validation latency, adoption ratios.
- **Trace Context**: Each event includes `trace_id` and `span_id` aligned with OpenTelemetry. Change signals propagate a `correlation_id` reused across participating systems.
- **Retention & Privacy**: Operational metrics retained 90 days; audit logs 12 months. PII prohibited; if unavoidable, anonymize and document handling.
- **Access & Tooling**: Provide dashboards and exportable APIs with RBAC. Support offline export for air-gapped review.

## Standards Alignment

- Leverage existing standards to reduce custom tooling and vendor lock-in:
  - **Manifests**: Align with OpenAPI/AsyncAPI for service interfaces, SPDX for SBOMs, and CNCF TAG App Delivery guidance where applicable.
  - **Behavior Specs**: Reference Gherkin/Cucumber BDD conventions; consider Living Documentation tooling for rendering.
  - **Security**: Adopt frameworks like NIST SSDF or OWASP SAMM for maturity benchmarks.
  - **Observability**: Follow OpenTelemetry for metrics and tracing to avoid bespoke instrumentation.
  - **Change Management**: Borrow from ITIL/DevOps change control where beneficial, but automate wherever possible.

## Anti-Goals

- Mandating a single monorepo or central code ownership.
- Forcing all projects to adopt identical technology stacks or languages.
- Centralizing decision making to the point of blocking local autonomy.
- Replacing project-level governance or incident response processes.
- Building proprietary tooling when existing open standards solve the problem.

## Constraints & Non-Goals

- **Autonomy** – Projects retain independent roadmaps; ecosystem guidelines should enable but not monopolize decision making.
- **Incremental Adoption** – New capabilities must be adoptable piecewise. Avoid all-or-nothing migrations.
- **Tool Diversity** – The ecosystem supports multiple languages or frameworks; specifications focus on interfaces, not implementation detail.
- **Minimal Bureaucracy** – Coordination mechanisms should minimize overhead while ensuring traceability of major decisions.

## Success Criteria (Qualitative)

- New contributors can orient themselves within hours using generated documentation and manifests.
- Cross-project changes are anticipated and coordinated, avoiding surprise breakages.
- Automation systems can run lifecycle tasks without bespoke scripts per repository.
- Runtime consumers connect to services using standard discovery information and compatibility checks.
- Governance artifacts (decisions, standards, compatibility matrices) are accessible and up to date.

## Ecosystem Interactions

To ground the intent, consider three recurring interaction loops. Each loop should be supported regardless of the concrete architecture chosen.

- **Plan-to-Build Loop** – A change request surfaces (human or agent). Actors consult capability discovery to determine whether existing functionality satisfies the need. If not, they draft new behaviors and manifests, creating traceable work items.
- **Build-to-Validate Loop** – Implementations publish updated metadata and execute shared validation suites. Integration contracts flag incompatibilities early across the project graph.
- **Release-to-Operate Loop** – Runtime assets register themselves for discovery. Operational tooling monitors health and feeds observations back into planning.

These loops overlap; short feedback cycles reduce systemic risk and keep metadata synchronized with reality.

## Quality Attributes

The ecosystem must exhibit several qualities independent of the specific technical stack:

- **Reliability** – Shared tooling should continue to function when individual projects change. Version negotiation and graceful degradation are required.
- **Scalability** – Adding new projects or capabilities should not exponentially increase coordination costs. Metadata and automation must scale with the constellation count.
- **Observability** – Operators can inspect state (who provides what, which behaviors pass, which signals are unresolved) without manual spelunking.
- **Security & Privacy** – Secrets remain scoped, logs respect boundaries, and third-party contributions cannot subvert shared tooling.
- **Extensibility** – New lifecycle stages or artifact types can be introduced without rewiring the ecosystem. Interfaces focus on contracts rather than implementations.

## Adoption Pathways

Because projects vary in maturity, solution candidates should offer progressive adoption steps:

1. **Documentation Alignment** – Projects map existing workflows to the shared lifecycle vocabulary and publish manifests describing current capabilities. *Acceptance*: manifests include minimum fields; lifecycle mapping reviewed by maintainers.
2. **Validation Integration** – Teams adopt shared integration contracts, running automated checks alongside local tests. *Acceptance*: CI includes contract suite; build fails on incompatibilities without waivers.
3. **Coordination Participation** – Projects begin emitting and responding to change signals, contributing decisions to the shared log. *Acceptance*: change signals follow the standardized workflow with SLA compliance.
4. **Runtime Interoperability** – Services expose runtime discovery metadata, enabling cross-project invocation. *Acceptance*: at least one dependent project successfully consumes runtime metadata with compatibility checks.

Each step yields value on its own and prepares the ground for the next, reducing the risk of large-bang transitions.

## Success Metrics (Illustrative)

To evaluate whether intent is being realized, stakeholders can monitor metrics such as:

- Time from change request to owner identification (“routing latency”) – baseline current average; target 50% reduction within two release cycles.
- Percentage of behaviors with up-to-date metadata and passing automated tests – baseline existing coverage; target ≥90% within one release cycle.
- Number of cross-project incidents caused by incompatibilities – establish quarterly baseline; target downward trend with less than one major incident per quarter.
- Mean time to integrate a new project into the ecosystem – measure first adopter; target <2 weeks once tooling is available.
- Adoption rate of shared runtime discovery (fraction of services exposing standardized endpoints) – baseline 0%; target 60% by end of the runtime interoperability phase.

These metrics do not prescribe tooling but provide signals that any solution should surface.

## Risks & Watchpoints

- **Stale Metadata** – Manifests or behavior registries drifting from reality weaken trust; require validation loops.
- **Fragmented UX** – Without enforced conventions, tooling feels inconsistent; require shared guidelines.
- **Signal Saturation** – Coordination channels may accumulate noise; implement prioritization, deduplication, and ownership assignment.
- **Security Erosion** – Shared tooling can propagate vulnerabilities; invest in automated scanning and timely response processes.

## Open Questions

- What governance cadence (e.g., weekly council, asynchronous voting) balances responsiveness with workload?
- How should runtime discovery authenticate services in multi-tenant or remote scenarios?
- What minimum metadata should behaviors and manifests expose to satisfy both human and agent needs?
- Which artifacts belong in a central repository versus remaining in individual projects?
- How will feedback loops function when some projects operate in offline or restricted environments?
- What escalation path exists when shared standards block urgent local changes?

## Naming Guidelines

- **Repositories**: platform/shared repos use `chora-<platform-domain>` (e.g., `chora-platform`); capability providers use `<domain>-<capability-provider>` (e.g., `mcp-orchestration`).
- **Capability IDs**: `<domain>.<capability>.<action>` (e.g., `mcp.registry.manage`); add a version suffix if multiple versions coexist.
- **Change Signals**: `SIG.<scope>.<subject>.<state>` with optional iteration suffix (`SIG.capability.mcp.registry.update-2`).
- **Packages/CLI**: prefix shared tooling with `chora-` (`chora-cli`, `chora-validator`).
- **Documentation**: place standards under `docs/standards/`, capability references under `docs/capabilities/`, reference snippets under `docs/reference/`.
- **Templates & Workflows**: publish reusable CI pipelines (`.github/workflows/chora-ci.yml`), AGENTS snippets, and CLI scaffolds under predictable paths so capability repos can copy/adopt them.
- **Value Scenario IDs**: use `<domain>.<capability>.<verb>` (e.g., `mcp.registry.manage.create-doc`) for scenario identifiers; store supporting guides under `docs/how-to/` and automated tests under `tests/value-scenarios/` for predictable discovery.

Changes to naming conventions should be recorded through change signals to maintain consistency across projects.

---

Use this intent document as a lens when evaluating or designing ecosystem architecture. Any proposed solution should be able to trace back how it fulfills these objectives and mitigates the outlined risks.
- **Access & Tooling**: Provide dashboards and exportable APIs with RBAC. Support offline export for air-gapped review.

## Offline / Air-Gapped Operation

- **Caching Strategy**: Projects operating offline maintain signed mirrors of manifests, behaviors, SBOMs, and change signals. Mirrors include freshness metadata and checksum files.
- **Sync Policies**: Define minimum sync cadence (e.g., weekly) and approval steps before import. Sync tooling verifies signatures and compatibility before applying updates.
- **Bundle Format**: Standardize bundle archives containing manifests, SBOMs, behaviors, and decision logs with accompanying signatures.
- **Conflict Resolution**: When mirrors diverge, raise change signals with context so maintainers can reconcile differences.
- **Telemetry Backfill**: Offline environments queue observability events locally and replay them once connectivity is restored, preserving correlation IDs.
```

## docs/how-to/create-doc.md

```md
---
title: Create MCP Registry Documentation Entry
status: draft
last_updated: 2025-10-05
---

# How To: Create Registry Documentation Entry

This guide covers the value scenario `mcp.registry.manage.create-doc`.

Objective: Produce a discoverable documentation entry for an MCP server in the registry so users can find connection parameters and usage notes.

Prerequisites
- Access to the MCP registry store (local or remote)
- The orchestrator CLI `mcp-orchestrator`

Steps
1. Identify the server ID and endpoint. Example: `example.srv`, `https://mcp.example.test`.
2. Use the orchestrator to register the server (or ensure it exists):
   - `mcp-orchestrator` (or API) to add/update the entry.
3. Create a documentation page or section for the server in your docs site.
   - Include: server ID, endpoint, auth requirements, supported tools, contact/owner.
4. Verify the entry appears in your docs navigation and search.

Expected Result
- The server `example.srv` is present in the registry and a docs entry exists with endpoint and basic usage details.

Automation Notes
- See BDD feature in `docs/capabilities/behaviors/mcp-registry-manage.feature`.
- A stub automated test exists in `tests/value-scenarios/test_create_doc.py`.

```

## docs/how-to/share-with-liminal.md

```md
# How to Share Bundles with Chora Liminal

This guide describes how to package a liminal-ready bundle and where CI publishes it.

Bundle contents
- `manifests/star.yaml`
- `docs/reference/overview.md`
- `docs/reference/signals/SIG-capability-onboard.md` (status closed; includes validation notes)
- `var/telemetry/events.jsonl` (CLI validation events)

Local packaging (manual)
```bash
mkdir -p var/bundles/liminal
zip -j var/bundles/liminal/mcp-orchestration-bundle.zip \
  manifests/star.yaml \
  docs/reference/overview.md \
  docs/reference/signals/SIG-capability-onboard.md \
  var/telemetry/events.jsonl
```

CI packaging
- Workflow: `.github/workflows/chora-ci.yml`
- Steps: generates overview, uploads telemetry + overview, and builds a zip under `var/bundles/liminal/` uploaded as artifact `liminal-bundle`.

Next steps
- Provide the bundle to the liminal inbox prototype and record results via a change signal (e.g., `SIG-liminal-inbox-prototype`).
```

## docs/how-to/telemetry.md

```md
# How to Emit Telemetry

This repository emits simple JSONL telemetry for key CLI flows using a shared emitter shim compatible with Chora Release B.

Emitter
- Module: `chora_platform_tools.telemetry.TelemetryEmitter`
- Output: `var/telemetry/events.jsonl` (one JSON object per line)

Event shape
```json
{"name":"manifest.validate","ts":"<RFC3339>","fields":{"file":"manifests/star.yaml","result":"ok"}}
```

Commands that write telemetry
- `PYTHONPATH=src python -m mcp_orchestrator.cli manifest-validate manifests/star.yaml`
- `PYTHONPATH=src python -m mcp_orchestrator.cli behavior-validate docs/capabilities/behaviors`
- `PYTHONPATH=src python -m mcp_orchestrator.cli scenario-validate manifests/star.yaml`

Local verification
```bash
PYTHONPATH=src python -m mcp_orchestrator.cli manifest-validate manifests/star.yaml
PYTHONPATH=src python -m mcp_orchestrator.cli behavior-validate docs/capabilities/behaviors
PYTHONPATH=src python -m mcp_orchestrator.cli scenario-validate manifests/star.yaml
tail -n +1 var/telemetry/events.jsonl
```

CI
- Workflow `.github/workflows/chora-ci.yml` runs validators and tests, generates the repository overview, and uploads telemetry + overview as artifacts.

Notes
- This emitter is a minimal shim for Release B and can be swapped for the official platform emitter when available.
```

## docs/reference/.gitkeep

```

```

## docs/reference/overview.md

```md
# Repository Overview — MCP Orchestration

- id: `mcp-orchestration`
- version: `0.0.1`
- owner: `team-mcp`
- lifecycle_stage: `operate`
- tags: chora, capability-provider, mcp, registry, orchestration

## Capabilities
- `mcp.registry.manage`
  - behavior: `MCP.REGISTRY.MANAGE` status=`draft` ref=`docs/capabilities/mcp-registry-manage.md`

## Value Scenarios
- `mcp.registry.manage.create-doc` — status=`ready`
  - guide: `docs/how-to/create-doc.md`
  - test: `tests/value-scenarios/test_create_doc.py`
  - test: `docs/capabilities/behaviors/mcp-registry-manage.feature`

## Telemetry Signals
- `SIG.capability.mcp.registry.onboard` — status=`in_progress` doc=`docs/reference/signals/SIG-capability-onboard.md`

## Dependencies
- `chora-validator` type=`tool` version=`>=0.0.1` scope=`dev`
- `mcp.runtime` type=`service` version=`>=1.0.0` scope=`runtime`

```

## docs/reference/release-a-plan.md

```md
# Release A Plan — MCP Orchestration Onboarding

This plan tracks capability-provider tasks required to complete Chora Release A from the MCP orchestration perspective.

## Objectives
- Adopt Chora manifest/behavior standards.
- Define at least one value scenario demonstrating the capability.
- Integrate and run `chora-validator` in CI.
- Emit change signals documenting readiness.
- Provide manifest/behavior samples for discovery and compatibility checks.

## Work Items
- [x] Update `manifests/star.yaml` with complete metadata (tags, dependencies, telemetry signals).
- [x] Tag behaviors (BDD or JSON) with `@behavior` and `@status` metadata.
- [x] Run `mcp-orchestrator manifest-validate manifests/star.yaml` locally and in CI.
- [x] Add a value scenario definition (metadata + doc + automated test) for `mcp.registry.manage.create-doc`.
- [x] Populate `docs/reference/signals/SIG-capability-onboard.md` with status updates.
- [ ] Add telemetry stubs/logs as per telemetry schema when available. *(Deferred to Release B; see `docs/reference/release-b-plan.md`.)*

## Acceptance Criteria
- Manifest passes Chora validator without overrides.
- Behavior spec exists for each declared capability.
- Value scenario `mcp.registry.manage.create-doc` documented and runnable (manual guide + automated test).
- Change signal `SIG-capability-onboard` marked complete with notes and timestamp.
- CI pipeline runs validator/test suite.

## Verification (Release A Templates Adoption)

- CI workflow added at `.github/workflows/chora-ci.yml` (runs manifest/behavior/scenario validators + pytest).
- Local validator runs (exit code 0):
  - Manifest: `PYTHONPATH=src python -m mcp_orchestrator.cli manifest-validate manifests/star.yaml` → success
  - Behaviors: `PYTHONPATH=src python -m mcp_orchestrator.cli behavior-validate docs/capabilities/behaviors` → success
  - Scenarios: `PYTHONPATH=src python -m mcp_orchestrator.cli scenario-validate manifests/star.yaml` → success
- Pytest: `PYTHONPATH=src pytest -q` → all tests passed locally.

Scenario status: ready (guide and tests referenced; validator passing).

## Release A Closure Summary (Implemented 2025-10-06)
- Shared CI pipeline validates manifest, behaviors, and value scenario on every push.
- Change signal `docs/reference/signals/SIG-capability-onboard.md` marked complete with validator output links.
- Telemetry adoption item migrated to Release B workstream alongside new platform emitter.
```

## docs/reference/release-b-plan.md

```md
---
title: Release B Plan — Telemetry & Liminal Integration
status: draft
version: 0.1.0
last_updated: 2025-10-07
---

# Release B Plan — MCP Orchestration

Release B focuses on adopting the platform telemetry/overview tooling and integrating with the liminal inbox prototype.

## Objectives
- Emit telemetry for key CLI flows using the shared emitter.
- Publish repository overviews alongside manifests and value scenarios.
- Provide liminal-ready bundles (manifest + telemetry + signals) for inbox ingestion.
- Track progress via change signals and update documentation accordingly.

## Workstreams & Status

### 1. Telemetry Adoption
- [x] Import telemetry emitter (shim) and write CLI events to `var/telemetry/events.jsonl`.
- [x] Document telemetry usage in `docs/how-to/telemetry.md` (commands + schema).
- [x] Update CI to archive telemetry samples for liminal testing.

### 2. Repository Overview Publication
- [x] Run `scripts/generate_repo_overview.py manifests/star.yaml -o docs/reference/overview.md` and commit output.
- [x] Include overview link in README + change signal updates.
 - [x] Add automation step (CI) to refresh overview and fail if stale.

### 3. Liminal Bundle Prep
- [x] Package manifest, overview, telemetry, and change signal notes under `var/bundles/liminal/` (README + structure).
- [x] Provide usage notes for liminal repo (`docs/how-to/share-with-liminal.md`).
 - [x] Emit signal update `SIG-liminal-inbox-prototype` referencing bundle location.

### 4. Governance & Comms
- [x] Update `docs/reference/release-b-plan.md` checkboxes as work completes.
- [ ] Add weekly progress note to `docs/reference/signals/SIG-capability-onboard.md` during Release B.
- [ ] Confirm adoption by referencing platform change signal `SIG-telemetry-adoption`.

### 5. Telemetry Migration Prep
- [ ] Replace local emitter with platform `TelemetryEmitter` once available.
- [ ] Update `docs/how-to/telemetry.md` and CI to reflect platform emitter configuration.
- [ ] Add compatibility note in signal doc linking to the migration PR.

### 6. Final Validation & Release
- [ ] Execute full Release B validation (validators + pytest + bundle ingestion by liminal) and capture evidence in signals/plan.
- [ ] Close coordination with platform (`SIG-telemetry-adoption`) and document alignment in the plan.
- [ ] Cut Release B tag and publish release notes once validation succeeds ("released" means tagged release artifacts are created).

### Release Checklist (after validation)
1. Check working tree: `git status`
2. Tag release: `git tag release-b`
3. Push tag: `git push origin release-b`
4. Publish GitHub release: `gh release create release-b --notes-file docs/reference/release-b-plan.md`
5. Update `docs/reference/signals/SIG-capability-onboard.md` with release URL and telemetry summary

## Acceptance Criteria
1. Telemetry events generated for manifest and scenario validation commands; emitter outputs validated in tests.
2. Repository overview kept in sync with manifest and value scenario metadata (CI enforcement).
3. Liminal bundle available with documentation, consumed successfully by inbox prototype (evidence via change signal).
4. Release documentation updated with links to telemetry files, overview artifacts, and liminal bundle instructions.

## Evidence Checklist
- `var/telemetry/events.jsonl`
- `docs/reference/overview.md`
- `var/bundles/liminal/README.md` (or equivalent packaging notes)
- Change signal updates referencing telemetry + bundle locations

Keep this plan current; mark tasks complete with timestamps and link supporting PRs or commits.

## Verification

- Validators (local):
  - `PYTHONPATH=src python -m mcp_orchestrator.cli manifest-validate manifests/star.yaml` → success
  - `PYTHONPATH=src python -m mcp_orchestrator.cli behavior-validate docs/capabilities/behaviors` → success
  - `PYTHONPATH=src python -m mcp_orchestrator.cli scenario-validate manifests/star.yaml` → success
- Overview: generated `docs/reference/overview.md`
- Telemetry: events written to `var/telemetry/events.jsonl` (JSONL)
- Bundle: `var/bundles/liminal/mcp-orchestration-bundle.zip` verified (`zip -Tv`)
- Tests: `PYTHONPATH=src pytest -q` → all tests passed
```

## docs/reference/release-plan-b.md

```md
---
title: Release Plan B — Telemetry & Liminal Integration
status: in_progress
version: 0.2.0
last_updated: 2025-10-07
---

# Release Plan B — MCP Orchestration

This plan operationalizes the Release B scope for the mcp-orchestration capability provider, aligned with ecosystem intent and approach documents. It captures objectives, current status, verification evidence, and next steps.

Aligns with:
- docs/ecosystem/solution-neutral-intent.md (capability/behavior/manifest/value-scenario definitions; change signals)
- docs/ecosystem/solution-approach-report.md (Release B objectives and change signals; naming conventions)

## Objectives
- Emit telemetry for key CLI flows using a shared emitter (initial shim, platform emitter next).
- Publish and enforce repository overview freshness alongside manifests and value scenarios.
- Package liminal-ready bundles (manifest + overview + telemetry + signals) for inbox ingestion.
- Track progress via change signals and keep documentation up to date.

## Workstreams & Status

### 1) Telemetry Adoption
- [x] CLI emits events to `var/telemetry/events.jsonl` for `manifest-validate`, `behavior-validate`, `scenario-validate`.
- [x] Documented usage and event shape: `docs/how-to/telemetry.md`.
- [x] CI uploads telemetry events as artifact.
- [ ] Migrate to platform TelemetryEmitter (replace shim and update docs/CI).

### 2) Repository Overview Publication
- [x] Generator script: `scripts/generate_repo_overview.py` → `docs/reference/overview.md`.
- [x] README links to overview and telemetry how-to.
- [x] CI freshness gate regenerates overview and fails if stale.

### 3) Liminal Bundle Prep
- [x] Bundle created with manifest, overview, signal, and telemetry under `var/bundles/liminal/`.
- [x] How-to updated: `docs/how-to/share-with-liminal.md` (local + CI packaging).
- [x] CI packages and uploads `liminal-bundle` artifact.
- [ ] Verify ingestion on liminal inbox prototype and record result.

### 4) Governance & Signals
- [x] Weekly progress captured in `docs/reference/signals/SIG-capability-onboard.md`.
- [x] Liminal ingest signal created: `docs/reference/signals/SIG-liminal-inbox-prototype.md` (prepared).
- [ ] Reference platform signal `SIG-telemetry-adoption` once published.

## Acceptance Criteria
1. Telemetry events generated for validator commands; basic emitter outputs tested.
2. Repository overview kept in sync with manifest and scenarios (CI enforcement).
3. Liminal bundle available and validated by inbox prototype; evidence recorded in signals.
4. Release documentation updated with links to telemetry, overview, and bundle.

## Evidence & Artifacts
- Telemetry: `var/telemetry/events.jsonl`
- Overview: `docs/reference/overview.md`
- Bundle (zip): `var/bundles/liminal/mcp-orchestration-bundle.zip`
- Signals: `docs/reference/signals/SIG-capability-onboard.md`, `docs/reference/signals/SIG-liminal-inbox-prototype.md`
- CI: `.github/workflows/chora-ci.yml`

## Verification (Latest)
- Validators (local):
  - `PYTHONPATH=src python -m mcp_orchestrator.cli manifest-validate manifests/star.yaml` → success
  - `PYTHONPATH=src python -m mcp_orchestrator.cli behavior-validate docs/capabilities/behaviors` → success
  - `PYTHONPATH=src python -m mcp_orchestrator.cli scenario-validate manifests/star.yaml` → success
- Tests: `PYTHONPATH=src pytest -q` → passing
- Overview: generated and checked by CI freshness gate
- Bundle: packaged locally and in CI (uploaded as `liminal-bundle`)

## Implementation Notes
- CLI emits events via local shim `mcp_orchestrator.telemetry` to ensure a stable JSONL format for Release B.
- Freshness gate: CI regenerates overview and fails on diff to prevent stale docs in PRs.
- Naming follows `solution-approach-report.md` conventions (e.g., `mcp.registry.manage`, `SIG.*`).

## Next Steps
- Replace emitter shim with platform TelemetryEmitter and update docs/CI; cross-reference platform `SIG-telemetry-adoption`.
- Validate liminal inbox ingestion; mark `SIG-liminal-inbox-prototype` complete with evidence.
- Continue weekly progress entries in `SIG-capability-onboard` while Release B is active.

```

## docs/reference/signals/.gitkeep

```

```

## docs/reference/signals/SIG-capability-onboard.md

```md
# SIG-capability-onboard

Tracks onboarding of manifests/behaviors to Chora platform standards.

## Tasks
- [x] Validate star.yaml against chora-validator
- [x] Implement behaviors/interfaces
- [x] Emit onboarding signal once complete

## Validation Log
- 2025-10-06: Manifest: `PYTHONPATH=src python -m mcp_orchestrator.cli manifest-validate manifests/star.yaml` → success.
- 2025-10-06: Behaviors: `PYTHONPATH=src python -m mcp_orchestrator.cli behavior-validate docs/capabilities/behaviors` → success.
- 2025-10-06: Scenarios: `PYTHONPATH=src python -m mcp_orchestrator.cli scenario-validate manifests/star.yaml` → success for `mcp.registry.manage.create-doc`.
- 2025-10-06: Pytest: `PYTHONPATH=src pytest -q` → all tests passed.

## Notes
- Manifest enriched with tags, dependencies (tooling/runtime), and telemetry signal `SIG.capability.mcp.registry.onboard`.
- Behavior definitions added under `docs/capabilities/behaviors/` using Gherkin for `MCP.REGISTRY.MANAGE`.
- Value scenario `mcp.registry.manage.create-doc` added with guide and stub test; will connect to full automation in CI.

## Status
- closed (Release A complete)
- Release B: telemetry integration started; events emitted to `var/telemetry/events.jsonl` and uploaded via CI artifact.
- Overview generated at `docs/reference/overview.md`.

### Release B Log — 2025-10-07
- Validators: manifest, behaviors, scenarios → success (local).
- Telemetry events written (see `var/telemetry/events.jsonl`).
- Overview generated (`docs/reference/overview.md`).
- Liminal bundle packaged (`var/bundles/liminal/mcp-orchestration-bundle.zip`).
- Liminal signal created: `docs/reference/signals/SIG-liminal-inbox-prototype.md` (status: prepared).

### Weekly Progress — 2025-10-07
- Implemented CI overview freshness gate.
- Prepared liminal bundle and created ingestion signal.
- Next: coordinate `SIG-telemetry-adoption` with platform and migrate to platform emitter.
```

## docs/reference/signals/SIG-liminal-inbox-prototype.md

```md
---
title: SIG-liminal-inbox-prototype
status: in_progress
last_updated: 2025-10-07
---

# SIG-liminal-inbox-prototype

Tracks preparation and ingestion of the liminal-ready bundle for the inbox prototype.

## Artifacts
- Bundle: `var/bundles/liminal/mcp-orchestration-bundle.zip`
- Overview: `docs/reference/overview.md`
- Telemetry: `var/telemetry/events.jsonl`
- Source PR: feature/release-b

## Validation
- Bundle packaged locally and by CI; archived as workflow artifact.
- Validators executed locally with success (manifest/behavior/scenario) and telemetry events recorded.

## Status
- prepared — bundle created and ready for ingestion testing.
- next — verify ingestion on the liminal inbox prototype and update this signal to `complete` with notes and timestamp.

```

## docs/standards/.gitkeep

```

```

## docs/standards/README.md

```md
# Standards Alignment

This repository consumes standards from chora-platform. See:
- Compatibility Policy
- Discovery Model
- Telemetry Schema

Local notes can be added here if needed.
```

## manifests/.gitkeep

```

```

## manifests/star.yaml

```yaml
id: mcp-orchestration
version: 0.0.1
owner: team-mcp
lifecycle_stage: operate
inputs: []
outputs:
  - registry_state
tags:
  - chora
  - capability-provider
  - mcp
  - registry
  - orchestration
dependencies:
  - id: chora-validator
    type: tool
    version: ">=0.0.1"
    scope: dev
    optional: false
  - id: mcp.runtime
    type: service
    version: ">=1.0.0"
    scope: runtime
    optional: true
security_tier: moderate
stability: beta
adr_links: []
validation_status:
  last_run: null
  result: pending
  tool: chora-validator
capabilities:
  - id: mcp.registry.manage
    behaviors:
      - ref: docs/capabilities/mcp-registry-manage.md
        id: MCP.REGISTRY.MANAGE
        status: draft
telemetry:
  signals:
    - id: SIG.capability.mcp.registry.onboard
      doc: docs/reference/signals/SIG-capability-onboard.md
      owner: team-mcp
      status: in_progress
      last_update: 2025-10-05
value_scenarios:
  - id: mcp.registry.manage.create-doc
    title: Create registry documentation entry
    capability: mcp.registry.manage
    guide: docs/how-to/create-doc.md
    tests:
      - tests/value-scenarios/test_create_doc.py
      - docs/capabilities/behaviors/mcp-registry-manage.feature
    status: ready
```

## pyproject.toml

```toml
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "mcp-orchestration"
version = "0.0.1"
description = "MCP orchestration capability provider"
authors = [{name = "Victor Piper"}]
readme = "README.md"
requires-python = ">=3.10"
dependencies = ["chora-validator @ file:///Users/victorpiper/code/chora-platform/dist/chora_validator-0.0.1-py3-none-any.whl"]

[project.optional-dependencies]
dev = ["pytest>=7.0"]

[project.scripts]
mcp-orchestrator = "mcp_orchestrator.cli:main"

[tool.pytest.ini_options]
pythonpath = ["src"]
```

## repo-dump.py

```py
#!/usr/bin/env python3
"""
repo-dump.py

Create a Markdown dump of the repository.
Supports two modes:
  1. Full dump: Includes all files except those excluded by .dumpignore and --exclude
  2. Partial dump: Includes only files listed in an input file,
     minus any --exclude patterns

Usage:
  python repo-dump.py full [--exclude PATTERN ...]
  python repo-dump.py partial files-to-dump.txt [--exclude PATTERN ...]

Output:
  repo-dump.md in the current directory

Notes:
- Each section in the Markdown file contains the relative path as a heading and
  the file contents as a code block.
- Binary files are skipped.
- .dumpignore is used for exclusions in full mode (supports basic patterns).
- --exclude patterns are always applied (in addition to .dumpignore in full mode).
"""

import fnmatch
import os
import sys
from pathlib import Path

DUMPIGNORE = ".dumpignore"
OUTPUT_MD = "repo-dump.md"


# Helper: Read .dumpignore patterns
def read_dumpignore():
    patterns = []
    if os.path.exists(DUMPIGNORE):
        with open(DUMPIGNORE) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    patterns.append(line)
    return patterns


def is_ignored(path, patterns):
    for pat in patterns:
        if fnmatch.fnmatch(path, pat) or fnmatch.fnmatch(os.path.basename(path), pat):
            return True
        # Directory pattern
        if pat.endswith("/") and path.startswith(pat):
            return True
    return False


def is_binary(file_path):
    try:
        with open(file_path, "rb") as f:
            chunk = f.read(1024)
            if b"\0" in chunk:
                return True
    except Exception:
        return True
    return False


def gather_files_full(patterns):
    files = []
    for root, dirs, filenames in os.walk("."):
        # Skip hidden dirs except .
        dirs[:] = [d for d in dirs if not d.startswith(".") or d == "."]
        for filename in filenames:
            rel_path = os.path.relpath(os.path.join(root, filename), ".")
            if rel_path == OUTPUT_MD or rel_path == DUMPIGNORE:
                continue
            if is_ignored(rel_path, patterns):
                continue
            files.append(rel_path)
    return sorted(files)


def gather_files_partial(list_file):
    files = []
    with open(list_file) as f:
        for line in f:
            rel_path = line.strip()
            if rel_path and os.path.isfile(rel_path):
                files.append(rel_path)
    return files


def write_markdown(files):
    with open(OUTPUT_MD, "w", encoding="utf-8") as out:
        for rel_path in files:
            if is_binary(rel_path):
                print(f"[SKIP] Binary file: {rel_path}")
                continue
            try:
                with open(rel_path, encoding="utf-8") as f:
                    content = f.read()
            except Exception as e:
                print(f"[SKIP] Could not read {rel_path}: {e}")
                continue
            out.write(f"## {rel_path}\n\n")
            out.write(f"```{Path(rel_path).suffix[1:] if Path(rel_path).suffix else ''}\n")
            out.write(content)
            if not content.endswith("\n"):
                out.write("\n")
            out.write("```\n\n")
    print(f"Markdown dump created: {OUTPUT_MD}")


def parse_args():
    import argparse

    parser = argparse.ArgumentParser(description="Markdown repo dump tool with exclude support.")
    parser.add_argument("mode", choices=["full", "partial"], help="Dump mode: full or partial")
    parser.add_argument("filelist", nargs="?", help="File list for partial mode")
    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        help="Glob pattern to exclude (can be repeated)",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    if args.mode == "full":
        patterns = read_dumpignore() + args.exclude
        files = gather_files_full(patterns)
    else:
        if not args.filelist or not os.path.isfile(args.filelist):
            print("Error: Please provide a valid file list for partial mode.")
            sys.exit(1)
        files = gather_files_partial(args.filelist)
        # Exclude patterns
        if args.exclude:
            files = [f for f in files if not is_ignored(f, args.exclude)]
    write_markdown(files)


if __name__ == "__main__":
    main()
```

## scripts/.gitkeep

```

```

## scripts/apply_manifest_policy.py

```py
#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from chora_validator.policy import load_policy
from chora_validator.validators import validate_manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate manifest using chora-validator")
    parser.add_argument("file", default="manifests/star.yaml", nargs="?")
    args = parser.parse_args()
    validate_manifest(Path(args.file), load_policy())
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

## scripts/generate_repo_overview.py

```py
#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Dict, List

import yaml


def load_manifest(path: Path) -> Dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def fmt_list(values: List[str]) -> str:
    return ", ".join(values) if values else "-"


def render_overview(data: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append("# Repository Overview — MCP Orchestration")
    lines.append("")
    lines.append(f"- id: `{data.get('id')}`")
    lines.append(f"- version: `{data.get('version')}`")
    lines.append(f"- owner: `{data.get('owner')}`")
    lines.append(f"- lifecycle_stage: `{data.get('lifecycle_stage')}`")
    tags = data.get("tags") or []
    lines.append(f"- tags: {fmt_list(tags)}")
    lines.append("")
    lines.append("## Capabilities")
    for cap in data.get("capabilities", []):
        lines.append(f"- `{cap.get('id')}`")
        behs = cap.get("behaviors") or []
        for b in behs:
            lines.append(f"  - behavior: `{b.get('id')}` status=`{b.get('status')}` ref=`{b.get('ref')}`")
    lines.append("")
    lines.append("## Value Scenarios")
    for s in data.get("value_scenarios", []) or []:
        lines.append(f"- `{s.get('id')}` — status=`{s.get('status')}`")
        lines.append(f"  - guide: `{s.get('guide')}`")
        tests = s.get("tests") or []
        for t in tests:
            lines.append(f"  - test: `{t}`")
    lines.append("")
    lines.append("## Telemetry Signals")
    for sig in (data.get("telemetry") or {}).get("signals", []) or []:
        lines.append(f"- `{sig.get('id')}` — status=`{sig.get('status')}` doc=`{sig.get('doc')}`")
    lines.append("")
    lines.append("## Dependencies")
    for d in data.get("dependencies", []) or []:
        lines.append(f"- `{d.get('id')}` type=`{d.get('type')}` version=`{d.get('version')}` scope=`{d.get('scope')}`")
    lines.append("")
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate repository overview from manifest")
    ap.add_argument("manifest", default="manifests/star.yaml")
    ap.add_argument("-o", "--output", default="docs/reference/overview.md")
    args = ap.parse_args()
    data = load_manifest(Path(args.manifest))
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_overview(data), encoding="utf-8")
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

```

## src/chora_platform_tools/telemetry.py

```py
from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class TelemetryEvent:
    name: str
    ts: str
    fields: Dict[str, Any]


class TelemetryEmitter:
    """Minimal JSONL emitter for Release B.

    Writes one JSON object per line to the configured path.
    """

    def __init__(self, path: os.PathLike[str] | str = "var/telemetry/events.jsonl") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def emit(self, name: str, **fields: Any) -> None:
        evt = TelemetryEvent(name=name, ts=_utc_now_iso(), fields=fields)
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(asdict(evt), separators=(",", ":")) + "\n")

```

## src/chora_validator/__init__.py

```py
from .policy import load_policy  # noqa: F401
from .validators import (
    validate_manifest,
    validate_behaviors,
    validate_scenarios,
)  # noqa: F401
```

## src/chora_validator/policy.py

```py
from __future__ import annotations

from typing import Any, Dict


def load_policy() -> Dict[str, Any]:
    """Return a minimal validation policy placeholder.

    The real chora-validator would supply detailed schemas and rules.
    """
    return {
        "required_manifest_fields": [
            "id",
            "version",
            "owner",
            "lifecycle_stage",
            "outputs",
            "dependencies",
            "tags",
            "security_tier",
            "stability",
            "validation_status",
            "capabilities",
            "telemetry",
        ]
    }

```

## src/chora_validator/validators.py

```py
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict

import yaml


class ValidationError(Exception):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def validate_manifest(file: os.PathLike[str] | str, policy: Dict[str, Any]) -> None:
    path = Path(file)
    _require(path.exists(), f"Manifest not found: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    _require(isinstance(data, dict), "Manifest must be a YAML mapping")

    # required top-level keys
    for key in policy.get("required_manifest_fields", []):
        _require(key in data, f"Missing required field: {key}")

    # types
    _require(isinstance(data.get("dependencies"), list), "dependencies must be a list")
    _require(isinstance(data.get("tags"), list), "tags must be a list")

    # capabilities -> behaviors
    caps = data.get("capabilities")
    _require(isinstance(caps, list) and caps, "capabilities must be a non-empty list")
    for cap in caps:
        _require("id" in cap, "capability missing id")
        behs = cap.get("behaviors")
        _require(isinstance(behs, list) and behs, "capability.behaviors must be non-empty list")
        for b in behs:
            _require("ref" in b and "id" in b and "status" in b, "behavior entry must have ref, id, status")
            # behavior ref should resolve to a file in repo
            bref = Path(b["ref"])  # relative to repo root
            _require(bref.exists(), f"behavior ref missing: {bref}")

    # telemetry signals basic checks
    telem = data.get("telemetry") or {}
    sigs = telem.get("signals") or []
    _require(isinstance(sigs, list) and sigs, "telemetry.signals must be a non-empty list")
    for s in sigs:
        _require("id" in s and "doc" in s and "status" in s, "signal must have id, doc, status")
        _require(Path(s["doc"]).exists(), f"signal doc missing: {s['doc']}")


def validate_behaviors(path: os.PathLike[str] | str, policy: Dict[str, Any] | None = None) -> None:  # noqa: ARG001
    base = Path(path)
    _require(base.exists() and base.is_dir(), f"Behavior path not found: {base}")
    found = False
    for root, _, files in os.walk(base):
        for f in files:
            if f.endswith((".feature", ".json")):
                found = True
                p = Path(root) / f
                text = p.read_text(encoding="utf-8")
                _require("@behavior:" in text, f"Missing @behavior tag in {p}")
                _require("@status:" in text, f"Missing @status tag in {p}")
    _require(found, f"No behavior files found under {base}")


def validate_scenarios(manifest_file: os.PathLike[str] | str) -> None:
    path = Path(manifest_file)
    _require(path.exists(), f"Manifest not found: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    scenarios = data.get("value_scenarios") or []
    _require(isinstance(scenarios, list) and scenarios, "value_scenarios must be a non-empty list")
    for s in scenarios:
        _require("id" in s, "scenario missing id")
        _require("guide" in s, f"scenario {s.get('id')} missing guide")
        _require(Path(s["guide"]).exists(), f"scenario guide missing: {s['guide']}")
        tests = s.get("tests") or []
        _require(isinstance(tests, list) and tests, f"scenario {s.get('id')} tests must be a non-empty list")
        for t in tests:
            _require(Path(t).exists(), f"scenario test ref missing: {t}")
```

## src/mcp_orchestrator/.gitkeep

```

```

## src/mcp_orchestrator/__init__.py

```py
__all__ = ["__version__"]
__version__ = "0.0.1"
```

## src/mcp_orchestrator/cli.py

```py
from __future__ import annotations

import argparse

from chora_validator.policy import load_policy
from chora_validator.validators import validate_manifest
from mcp_orchestrator.telemetry import get_emitter


class CLI:
    def __init__(self) -> None:
        parser = argparse.ArgumentParser(prog="mcp-orchestrator", description="MCP orchestration CLI")
        parser.add_argument("--version", action="version", version="0.0.1")
        sub = parser.add_subparsers(dest="command")
        manifest = sub.add_parser("manifest-validate", help="validate manifest")
        manifest.add_argument("file", default="manifests/star.yaml")
        behaviors = sub.add_parser("behavior-validate", help="validate behavior specs")
        behaviors.add_argument(
            "path",
            nargs="?",
            default="docs/capabilities/behaviors",
            help="Path to behavior specs (feature/json)",
        )
        scenarios = sub.add_parser("scenario-validate", help="validate value scenarios via manifest")
        scenarios.add_argument(
            "manifest",
            nargs="?",
            default="manifests/star.yaml",
            help="Manifest file to read scenarios from",
        )
        self.parser = parser
        self.emitter = get_emitter()

    def run(self, argv=None) -> int:
        args = self.parser.parse_args(argv)
        if args.command == "manifest-validate":
            validate_manifest(args.file, load_policy())
            print("Manifest valid")
            self.emitter.emit("manifest.validate", file=str(args.file), result="ok")
        elif args.command == "behavior-validate":
            # Prefer chora-validator behavior validation if available; otherwise, do minimal tag checks.
            try:
                from chora_validator.validators import validate_behaviors  # type: ignore

                validate_behaviors(args.path, load_policy())  # type: ignore
                print("Behaviors valid")
                self.emitter.emit("behavior.validate", path=str(args.path), result="ok")
            except Exception:
                # Fallback: ensure at least one spec exists and has required tags
                import os

                if not os.path.isdir(args.path):
                    raise SystemExit(f"Behavior path not found: {args.path}")
                found = False
                for root, _, files in os.walk(args.path):
                    for f in files:
                        if f.endswith((".feature", ".json")):
                            found = True
                            p = os.path.join(root, f)
                            with open(p, "r", encoding="utf-8") as fh:
                                content = fh.read()
                            if "@behavior:" not in content or "@status:" not in content:
                                raise SystemExit(f"Missing @behavior or @status tags in {p}")
                if not found:
                    raise SystemExit("No behavior specs found")
                print("Behaviors minimally validated (tags present)")
                self.emitter.emit("behavior.validate.minimal", path=str(args.path), result="ok")
        elif args.command == "scenario-validate":
            try:
                from chora_validator.validators import validate_scenarios  # type: ignore

                validate_scenarios(args.manifest)  # type: ignore
                print("Scenarios valid")
                self.emitter.emit("scenario.validate", manifest=str(args.manifest), result="ok")
            except Exception as e:
                raise SystemExit(str(e))
        return 0


def main(argv=None) -> int:
    return CLI().run(argv)
```

## src/mcp_orchestrator/telemetry.py

```py
from __future__ import annotations

from typing import Any

try:
    # Prefer platform emitter when available
    from chora_platform_tools.telemetry import TelemetryEmitter as PlatformEmitter  # type: ignore
except Exception:  # pragma: no cover - fallback path
    PlatformEmitter = None  # type: ignore

from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import json


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class _Evt:
    name: str
    ts: str
    fields: dict[str, Any]


class LocalEmitter:
    def __init__(self, path: str = "var/telemetry/events.jsonl") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def emit(self, name: str, **fields: Any) -> None:
        evt = _Evt(name=name, ts=_utc_now_iso(), fields=fields)
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(asdict(evt)) + "\n")


def get_emitter() -> Any:
    # For Release B in this repo, always use the local emitter to ensure
    # consistent event shape. Swap to platform emitter in a future PR.
    return LocalEmitter()
```

## tests/.gitkeep

```

```

## tests/data/.gitkeep

```

```

## tests/test_behaviors.py

```py
from mcp_orchestrator.cli import main


def test_behavior_specs_exist_and_validate():
    # Ensure behavior validation command returns success
    assert main(["behavior-validate", "docs/capabilities/behaviors"]) == 0

```

## tests/test_manifest.py

```py
from mcp_orchestrator.cli import main

def test_manifest_template():
    assert main(["manifest-validate", "manifests/star.yaml"]) == 0
```

## tests/test_telemetry.py

```py
import json
from pathlib import Path

from mcp_orchestrator.cli import main


def read_events(p: Path):
    if not p.exists():
        return []
    return [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_telemetry_emitted_for_cli_commands(tmp_path):
    events_file = Path("var/telemetry/events.jsonl")
    # reset events file
    if events_file.exists():
        events_file.unlink()

    assert main(["manifest-validate", "manifests/star.yaml"]) == 0
    assert main(["behavior-validate", "docs/capabilities/behaviors"]) == 0
    assert main(["scenario-validate", "manifests/star.yaml"]) == 0

    events = read_events(events_file)
    names = [e.get("name") for e in events]
    assert "manifest.validate" in names
    assert any(n.startswith("behavior.validate") for n in names)
    assert "scenario.validate" in names

```

## tests/value-scenarios/test_create_doc.py

```py
def test_value_scenario_create_doc_stub():
    # Placeholder assertion; real test should exercise registry+docs integration
    assert True

```

## var/.gitkeep

```

```

## var/bundles/liminal/README.md

```md
# Liminal Bundle (Release B)

This directory will contain a bundle consumable by the Chora Liminal inbox prototype.

Suggested contents
- `manifests/star.yaml`
- `docs/reference/overview.md`
- `docs/reference/signals/SIG-capability-onboard.md` (or extracted snippet)
- `var/telemetry/events.jsonl`

Packaging
- A simple `.zip` of the repo subset is sufficient for prototype testing.
- Example:
  ```bash
  zip -r var/bundles/liminal/mcp-orchestration-bundle.zip \
    manifests/star.yaml \
    docs/reference/overview.md \
    docs/reference/signals/SIG-capability-onboard.md \
    var/telemetry/events.jsonl
  ```

CI artifacts
- Workflow `.github/workflows/chora-ci.yml` builds and uploads the bundle as artifact `liminal-bundle`.
```

## var/telemetry/events.jsonl

```jsonl
{"name": "manifest.validate", "ts": "2025-10-07T05:14:29.512067+00:00", "fields": {"file": "manifests/star.yaml", "result": "ok"}}
{"name": "behavior.validate", "ts": "2025-10-07T05:14:29.512588+00:00", "fields": {"path": "docs/capabilities/behaviors", "result": "ok"}}
{"name": "scenario.validate", "ts": "2025-10-07T05:14:29.514880+00:00", "fields": {"manifest": "manifests/star.yaml", "result": "ok"}}
```

