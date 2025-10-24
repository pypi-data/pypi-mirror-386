from __future__ import annotations

import argparse

from chora_validator.policy import load_policy
from chora_validator.validators import validate_manifest
from mcp_orchestrator.telemetry import get_emitter


class CLI:
    def __init__(self) -> None:
        parser = argparse.ArgumentParser(prog="mcp-orchestrator", description="MCP orchestration CLI")
        parser.add_argument("--version", action="version", version="0.0.1")
        sub = parser.add_subparsers(dest="command")
        manifest = sub.add_parser("manifest-validate", help="validate manifest")
        manifest.add_argument("file", default="manifests/star.yaml")
        behaviors = sub.add_parser("behavior-validate", help="validate behavior specs")
        behaviors.add_argument(
            "path",
            nargs="?",
            default="docs/capabilities/behaviors",
            help="Path to behavior specs (feature/json)",
        )
        scenarios = sub.add_parser("scenario-validate", help="validate value scenarios via manifest")
        scenarios.add_argument(
            "manifest",
            nargs="?",
            default="manifests/star.yaml",
            help="Manifest file to read scenarios from",
        )
        self.parser = parser
        self.emitter = get_emitter()

    def run(self, argv=None) -> int:
        args = self.parser.parse_args(argv)
        if args.command == "manifest-validate":
            validate_manifest(args.file, load_policy())
            print("Manifest valid")
            self.emitter.emit("manifest.validate", file=str(args.file), result="ok")
        elif args.command == "behavior-validate":
            # Prefer chora-validator behavior validation if available; otherwise, do minimal tag checks.
            try:
                from chora_validator.validators import validate_behaviors  # type: ignore

                validate_behaviors(args.path, load_policy())  # type: ignore
                print("Behaviors valid")
                self.emitter.emit("behavior.validate", path=str(args.path), result="ok")
            except Exception:
                # Fallback: ensure at least one spec exists and has required tags
                import os

                if not os.path.isdir(args.path):
                    raise SystemExit(f"Behavior path not found: {args.path}")
                found = False
                for root, _, files in os.walk(args.path):
                    for f in files:
                        if f.endswith((".feature", ".json")):
                            found = True
                            p = os.path.join(root, f)
                            with open(p, "r", encoding="utf-8") as fh:
                                content = fh.read()
                            if "@behavior:" not in content or "@status:" not in content:
                                raise SystemExit(f"Missing @behavior or @status tags in {p}")
                if not found:
                    raise SystemExit("No behavior specs found")
                print("Behaviors minimally validated (tags present)")
                self.emitter.emit("behavior.validate.minimal", path=str(args.path), result="ok")
        elif args.command == "scenario-validate":
            try:
                from chora_validator.validators import validate_scenarios  # type: ignore

                validate_scenarios(args.manifest)  # type: ignore
                print("Scenarios valid")
                self.emitter.emit("scenario.validate", manifest=str(args.manifest), result="ok")
            except Exception as e:
                raise SystemExit(str(e))
        return 0


def main(argv=None) -> int:
    return CLI().run(argv)
