from __future__ import annotations

from typing import Any, Dict


def load_policy() -> Dict[str, Any]:
    """Return a minimal validation policy placeholder.

    The real chora-validator would supply detailed schemas and rules.
    """
    return {
        "required_manifest_fields": [
            "id",
            "version",
            "owner",
            "lifecycle_stage",
            "outputs",
            "dependencies",
            "tags",
            "security_tier",
            "stability",
            "validation_status",
            "capabilities",
            "telemetry",
        ]
    }

