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

