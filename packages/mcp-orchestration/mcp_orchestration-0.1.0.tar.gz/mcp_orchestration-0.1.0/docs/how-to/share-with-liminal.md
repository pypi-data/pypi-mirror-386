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
