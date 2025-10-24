# Codex Instructions — Cleanup Tasks (MCP Orchestration)

Goal: tidy up Release B collateral so the repo reflects the latest work accurately.

## Clean-up Focus
1. **Signal Accuracy** — Ensure change signals live under `docs/reference/signals/` for this repo (e.g., `SIG-capability-onboard.md`). Remove or correct any stray references to liminal signals that belong elsewhere.
2. **Prompt Alignment** — Update `.codex/release-b-prompt.md` and related documentation so instructions reference the proper files (`SIG-capability-onboard`, overview freshness gate steps, telemetry migration notes).
3. **Documentation Hygiene** — Review `docs/reference/release-b-plan.md`, README, and how-to guides for stale wording or duplicate guidance. Consolidate Release B status and link to evidence (overview artifact, telemetry JSONL, liminal bundle).
4. **Artifacts & CI** — Verify CI artifacts (liminal bundle zip, overview) match documented paths; delete obsolete files if any, and update `var/bundles/liminal/README.md` with current bundle info.

## Workflow Expectations
- Before editing, scan for mismatched paths or duplicate notes.
- After changes, run validators/tests (`python -m mcp_orchestrator.cli ...`, `pytest -q`) if functional code is touched.
- Summarize updates in `docs/reference/release-b-plan.md` and, if needed, append a note to `docs/reference/signals/SIG-capability-onboard.md`.

## Guardrails
- Maintain stdout purity for CLI scripts; use stderr for diagnostics.
- Keep telemetry and bundle outputs under `var/`; documentation under `docs/`.
- Coordinate with platform repo before altering shared schema references.
