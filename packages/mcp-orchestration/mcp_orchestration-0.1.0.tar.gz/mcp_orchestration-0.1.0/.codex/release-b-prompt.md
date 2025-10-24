# Codex Instructions — Release B (MCP Orchestration)

Telemetry, overview, CI validators, and liminal bundle packaging are live. Focus on remaining Release B gates, execute end-to-end validation, and prepare to tag the release. You may run `git` and `gh` commands for coordination and publishing.

## Context
- Release docs: `docs/reference/release-b-plan.md` (freshness gate done; liminal signal created), `docs/reference/release-a-plan.md` (closure notes).
- Automation: `.github/workflows/chora-ci.yml` runs validators/tests, generates `docs/reference/overview.md`, uploads telemetry (`var/telemetry/events.jsonl`) and bundle (`var/bundles/liminal/mcp-orchestration-bundle.zip`).
- Documentation: `docs/how-to/telemetry.md`, `docs/how-to/share-with-liminal.md`, README links to overview/telemetry.
- Change signals: `docs/reference/signals/SIG-capability-onboard.md` captures Release B run; `docs/reference/signals/SIG-liminal-inbox-prototype.md` tracks bundle ingestion.

## Next Objectives
1. **Overview Freshness Gate** — Keep the CI check green; adjust scripts if metadata changes and record outcomes in the plan/signals.
2. **Final Validation Run** — Execute validators, pytest, and liminal bundle ingestion; capture telemetry and append evidence to `docs/reference/release-b-plan.md` and signals.
3. **Release Prep** — After validation passes: `git status` → `git tag release-b` → `git push origin release-b` → `gh release create release-b --notes-file docs/reference/release-b-plan.md`. Record the release URL in `docs/reference/signals/SIG-capability-onboard.md`.
4. **Telemetry Migration Prep** — Plan the transition from local shim to platform `TelemetryEmitter`; document remaining actions while keeping evidence logs current.

## Workflow Expectations
- Review outstanding checklist items before editing.
- Run validators/tests (manifest, behavior, scenario, pytest) whenever telemetry, manifest, or overview code changes.
- After CI or local packaging, update docs/signals with bundle paths and telemetry summaries.

## Guardrails
- Preserve stdout JSON-RPC purity for CLI tools; log diagnostics to stderr.
- Keep telemetry/bundle outputs under `var/`; documentation updates under `docs/`.
- Coordinate schema changes with platform signals prior to merging.
 - Align with ecosystem docs: ensure value scenarios, change signals, and naming follow `docs/ecosystem/solution-neutral-intent.md` and `docs/ecosystem/solution-approach-report.md` (e.g., capability IDs like `mcp.registry.manage`, signals under `docs/reference/signals/`).
