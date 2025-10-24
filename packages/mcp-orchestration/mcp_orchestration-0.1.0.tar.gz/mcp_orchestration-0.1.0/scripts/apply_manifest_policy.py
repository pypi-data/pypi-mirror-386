#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from chora_validator.policy import load_policy
from chora_validator.validators import validate_manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate manifest using chora-validator")
    parser.add_argument("file", default="manifests/star.yaml", nargs="?")
    args = parser.parse_args()
    validate_manifest(Path(args.file), load_policy())
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
