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

