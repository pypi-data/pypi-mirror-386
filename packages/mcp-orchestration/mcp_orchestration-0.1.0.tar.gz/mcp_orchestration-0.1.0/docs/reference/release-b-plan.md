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
