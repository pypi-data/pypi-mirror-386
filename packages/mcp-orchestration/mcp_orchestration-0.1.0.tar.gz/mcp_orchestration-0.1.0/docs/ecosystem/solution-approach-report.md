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
