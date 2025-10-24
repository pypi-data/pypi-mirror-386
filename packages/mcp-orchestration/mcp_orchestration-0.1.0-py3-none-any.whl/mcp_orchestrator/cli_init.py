"""CLI command to initialize sample configurations.

This module provides a command to generate and store initial MCP configurations
for supported client families.
"""

from datetime import datetime, timezone
from pathlib import Path

import click

from mcp_orchestrator.crypto import ArtifactSigner
from mcp_orchestrator.registry import get_default_registry
from mcp_orchestrator.storage import ArtifactStore, ConfigArtifact


def generate_sample_payload(client_id: str, profile_id: str) -> dict:
    """Generate sample MCP configuration payload.

    Args:
        client_id: Client family identifier
        profile_id: Profile identifier

    Returns:
        Sample mcpServers configuration
    """
    # Sample configurations for different client/profile combinations
    if client_id == "claude-desktop" and profile_id == "default":
        return {
            "mcpServers": {
                "filesystem": {
                    "command": "npx",
                    "args": [
                        "-y",
                        "@modelcontextprotocol/server-filesystem",
                        str(Path.home() / "Documents"),
                    ],
                },
                "brave-search": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-brave-search"],
                    "env": {"BRAVE_API_KEY": "${BRAVE_API_KEY}"},
                },
            }
        }
    elif client_id == "claude-desktop" and profile_id == "dev":
        return {
            "mcpServers": {
                "filesystem": {
                    "command": "npx",
                    "args": [
                        "-y",
                        "@modelcontextprotocol/server-filesystem",
                        str(Path.home() / "projects"),
                    ],
                },
                "brave-search": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-brave-search"],
                    "env": {"BRAVE_API_KEY": "${BRAVE_API_KEY}"},
                },
                "github": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-github"],
                    "env": {"GITHUB_TOKEN": "${GITHUB_TOKEN}"},
                },
            }
        }
    elif client_id == "cursor" and profile_id == "default":
        return {
            "mcpServers": {
                "filesystem": {
                    "command": "npx",
                    "args": [
                        "-y",
                        "@modelcontextprotocol/server-filesystem",
                        str(Path.home() / "code"),
                    ],
                },
            }
        }
    else:
        # Generic fallback
        return {
            "mcpServers": {
                "filesystem": {
                    "command": "npx",
                    "args": [
                        "-y",
                        "@modelcontextprotocol/server-filesystem",
                        str(Path.home()),
                    ],
                },
            }
        }


@click.command()
@click.option(
    "--key-path",
    type=click.Path(exists=False, dir_okay=False, path_type=Path),
    help="Path to signing key (default: ~/.mcp-orchestration/keys/signing_key.pem)",
)
@click.option(
    "--storage-path",
    type=click.Path(exists=False, file_okay=False, path_type=Path),
    help="Path to storage directory (default: ~/.mcp-orchestration)",
)
@click.option(
    "--regenerate",
    is_flag=True,
    help="Regenerate configs even if they already exist",
)
def init_configs(
    key_path: Path | None, storage_path: Path | None, regenerate: bool
) -> None:
    """Initialize sample MCP configurations for supported clients.

    This command generates signed configuration artifacts for each
    supported client family and profile, stores them in the artifact
    store, and sets up the necessary signing keys.

    Examples:
        # Initialize with defaults
        $ mcp-orchestration init-configs

        # Use custom paths
        $ mcp-orchestration init-configs --key-path ./my-key.pem --storage-path ./my-storage

        # Regenerate existing configs
        $ mcp-orchestration init-configs --regenerate
    """
    click.echo("🚀 Initializing MCP orchestration configurations...")

    # Set up paths
    if storage_path is None:
        storage_path = Path.home() / ".mcp-orchestration"
    if key_path is None:
        key_path = storage_path / "keys" / "signing_key.pem"

    # Initialize storage
    store = ArtifactStore(base_path=storage_path)
    click.echo(f"📁 Storage initialized at: {storage_path}")

    # Initialize or load signing key
    if key_path.exists() and not regenerate:
        click.echo(f"🔑 Loading existing signing key from: {key_path}")
        signer = ArtifactSigner.from_file(key_path, key_id="orchestration-init")
    else:
        click.echo(f"🔑 Generating new signing key at: {key_path}")
        signer = ArtifactSigner.generate(key_id="orchestration-init")
        signer.save_private_key(key_path)

        # Also save public verification key
        public_key_path = key_path.parent / "verification_key.pem"
        signer.save_public_key(public_key_path)
        click.echo(f"🔐 Public verification key saved to: {public_key_path}")

    # Get registry
    registry = get_default_registry()

    # Generate and store configs for each client/profile
    total_created = 0
    total_skipped = 0

    for client_def in registry.list_clients():
        client_id = client_def.client_id

        for profile_def in client_def.default_profiles:
            profile_id = profile_def.profile_id

            # Check if artifact already exists
            if not regenerate:
                try:
                    existing = store.get(client_id, profile_id)
                    click.echo(
                        f"⏭️  Skipping {client_id}/{profile_id} "
                        f"(already exists: {existing.artifact_id[:16]}...)"
                    )
                    total_skipped += 1
                    continue
                except Exception:
                    # Doesn't exist, create it
                    pass

            # Generate payload
            payload = generate_sample_payload(client_id, profile_id)

            # Compute artifact ID
            artifact_id = store.compute_artifact_id(payload)

            # Sign payload
            signature = signer.sign(payload)

            # Create artifact
            artifact = ConfigArtifact(
                artifact_id=artifact_id,
                client_id=client_id,
                profile_id=profile_id,
                created_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                payload=payload,
                signature=signature,
                signing_key_id=signer.key_id,
                metadata={
                    "generator": "init-configs",
                    "generator_version": "0.1.0",
                    "profile_description": profile_def.description,
                },
            )

            # Store artifact
            store.store(artifact)

            click.echo(
                f"✅ Created {client_id}/{profile_id}: {artifact_id[:16]}..."
            )
            total_created += 1

    # Summary
    click.echo("\n" + "=" * 60)
    click.echo(f"📊 Summary:")
    click.echo(f"   • Created: {total_created} configurations")
    click.echo(f"   • Skipped: {total_skipped} (already existed)")
    click.echo(f"   • Storage: {storage_path}")
    click.echo(f"   • Signing key: {key_path}")
    click.echo("=" * 60)

    if total_created > 0:
        click.echo(
            "\n✨ Configurations initialized! "
            "You can now use the MCP orchestration server."
        )
    else:
        click.echo(
            "\n💡 All configurations already exist. "
            "Use --regenerate to recreate them."
        )


if __name__ == "__main__":
    init_configs()
