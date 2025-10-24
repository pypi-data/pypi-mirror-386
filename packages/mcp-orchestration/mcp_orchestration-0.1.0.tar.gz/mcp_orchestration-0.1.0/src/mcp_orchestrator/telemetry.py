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
