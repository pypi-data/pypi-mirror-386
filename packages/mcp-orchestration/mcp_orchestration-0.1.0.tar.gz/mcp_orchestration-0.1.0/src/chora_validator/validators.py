from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict

import yaml


class ValidationError(Exception):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def validate_manifest(file: os.PathLike[str] | str, policy: Dict[str, Any]) -> None:
    path = Path(file)
    _require(path.exists(), f"Manifest not found: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    _require(isinstance(data, dict), "Manifest must be a YAML mapping")

    # required top-level keys
    for key in policy.get("required_manifest_fields", []):
        _require(key in data, f"Missing required field: {key}")

    # types
    _require(isinstance(data.get("dependencies"), list), "dependencies must be a list")
    _require(isinstance(data.get("tags"), list), "tags must be a list")

    # capabilities -> behaviors
    caps = data.get("capabilities")
    _require(isinstance(caps, list) and caps, "capabilities must be a non-empty list")
    for cap in caps:
        _require("id" in cap, "capability missing id")
        behs = cap.get("behaviors")
        _require(isinstance(behs, list) and behs, "capability.behaviors must be non-empty list")
        for b in behs:
            _require("ref" in b and "id" in b and "status" in b, "behavior entry must have ref, id, status")
            # behavior ref should resolve to a file in repo
            bref = Path(b["ref"])  # relative to repo root
            _require(bref.exists(), f"behavior ref missing: {bref}")

    # telemetry signals basic checks
    telem = data.get("telemetry") or {}
    sigs = telem.get("signals") or []
    _require(isinstance(sigs, list) and sigs, "telemetry.signals must be a non-empty list")
    for s in sigs:
        _require("id" in s and "doc" in s and "status" in s, "signal must have id, doc, status")
        _require(Path(s["doc"]).exists(), f"signal doc missing: {s['doc']}")


def validate_behaviors(path: os.PathLike[str] | str, policy: Dict[str, Any] | None = None) -> None:  # noqa: ARG001
    base = Path(path)
    _require(base.exists() and base.is_dir(), f"Behavior path not found: {base}")
    found = False
    for root, _, files in os.walk(base):
        for f in files:
            if f.endswith((".feature", ".json")):
                found = True
                p = Path(root) / f
                text = p.read_text(encoding="utf-8")
                _require("@behavior:" in text, f"Missing @behavior tag in {p}")
                _require("@status:" in text, f"Missing @status tag in {p}")
    _require(found, f"No behavior files found under {base}")


def validate_scenarios(manifest_file: os.PathLike[str] | str) -> None:
    path = Path(manifest_file)
    _require(path.exists(), f"Manifest not found: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    scenarios = data.get("value_scenarios") or []
    _require(isinstance(scenarios, list) and scenarios, "value_scenarios must be a non-empty list")
    for s in scenarios:
        _require("id" in s, "scenario missing id")
        _require("guide" in s, f"scenario {s.get('id')} missing guide")
        _require(Path(s["guide"]).exists(), f"scenario guide missing: {s['guide']}")
        tests = s.get("tests") or []
        _require(isinstance(tests, list) and tests, f"scenario {s.get('id')} tests must be a non-empty list")
        for t in tests:
            _require(Path(t).exists(), f"scenario test ref missing: {t}")
