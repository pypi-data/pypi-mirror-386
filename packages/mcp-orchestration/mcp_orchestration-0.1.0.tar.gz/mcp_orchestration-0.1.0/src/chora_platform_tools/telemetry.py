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

