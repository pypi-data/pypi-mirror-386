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
