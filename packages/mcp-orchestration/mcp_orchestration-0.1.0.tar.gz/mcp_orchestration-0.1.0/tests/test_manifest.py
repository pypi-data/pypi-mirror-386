from mcp_orchestrator.cli import main

def test_manifest_template():
    assert main(["manifest-validate", "manifests/star.yaml"]) == 0
