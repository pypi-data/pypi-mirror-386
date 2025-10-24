from mcp_orchestrator.cli import main


def test_behavior_specs_exist_and_validate():
    # Ensure behavior validation command returns success
    assert main(["behavior-validate", "docs/capabilities/behaviors"]) == 0

