"""Client family registry and metadata.

This module defines the registry of supported MCP client families, their
capabilities, and default profiles.
"""

from typing import Any

from pydantic import BaseModel, Field


class ClientCapabilities(BaseModel):
    """Capabilities supported by a client family."""

    environment_variables: bool = Field(
        default=True, description="Supports environment variables in server configs"
    )
    command_args: bool = Field(
        default=True, description="Supports command-line arguments"
    )
    working_directory: bool = Field(
        default=False, description="Supports setting working directory"
    )
    multiple_servers: bool = Field(
        default=True, description="Supports multiple MCP servers"
    )


class ClientLimitations(BaseModel):
    """Limitations/constraints for a client family."""

    max_servers: int | None = Field(
        default=None, description="Maximum number of servers (None = unlimited)"
    )
    max_env_vars_per_server: int | None = Field(
        default=None,
        description="Maximum environment variables per server (None = unlimited)",
    )


class ProfileDefinition(BaseModel):
    """Profile definition for a client family."""

    profile_id: str = Field(..., description="Profile identifier")
    display_name: str = Field(..., description="Human-readable profile name")
    description: str = Field(..., description="Profile purpose/usage")


class ClientDefinition(BaseModel):
    """Definition of a supported MCP client family."""

    client_id: str = Field(..., description="Unique client identifier")
    display_name: str = Field(..., description="Human-readable client name")
    platform: str = Field(
        ..., description="Primary platform (macos, windows, linux, cross-platform)"
    )
    config_location: str = Field(
        ..., description="Default config file path pattern"
    )
    config_format: str = Field(
        default="json", description="Configuration file format"
    )
    version_min: str | None = Field(
        default=None, description="Minimum supported client version"
    )
    version_max: str | None = Field(
        default=None, description="Maximum supported client version"
    )
    capabilities: ClientCapabilities = Field(
        default_factory=ClientCapabilities, description="Client capabilities"
    )
    limitations: ClientLimitations = Field(
        default_factory=ClientLimitations, description="Client limitations"
    )
    default_profiles: list[ProfileDefinition] = Field(
        default_factory=list, description="Default profiles for this client"
    )


class ClientRegistry:
    """Registry of supported MCP client families.

    This class maintains the definitive list of client families that the
    orchestration system supports, along with their metadata, capabilities,
    and default profile definitions.

    Example:
        >>> registry = get_default_registry()
        >>> client = registry.get_client("claude-desktop")
        >>> print(client.display_name)  # "Claude Desktop"
        >>> profiles = registry.get_profiles("claude-desktop")
        >>> print(len(profiles))  # 2 (default, dev)
    """

    def __init__(self) -> None:
        """Initialize empty registry."""
        self._clients: dict[str, ClientDefinition] = {}

    def register(self, client: ClientDefinition) -> None:
        """Register a client family.

        Args:
            client: Client definition to register
        """
        self._clients[client.client_id] = client

    def get_client(self, client_id: str) -> ClientDefinition | None:
        """Get client definition by ID.

        Args:
            client_id: Client family identifier

        Returns:
            ClientDefinition if found, None otherwise
        """
        return self._clients.get(client_id)

    def list_clients(self) -> list[ClientDefinition]:
        """List all registered clients.

        Returns:
            List of all client definitions
        """
        return list(self._clients.values())

    def get_profiles(self, client_id: str) -> list[ProfileDefinition]:
        """Get default profiles for a client.

        Args:
            client_id: Client family identifier

        Returns:
            List of profile definitions, empty if client not found
        """
        client = self.get_client(client_id)
        return client.default_profiles if client else []

    def get_profile(
        self, client_id: str, profile_id: str
    ) -> ProfileDefinition | None:
        """Get specific profile definition.

        Args:
            client_id: Client family identifier
            profile_id: Profile identifier

        Returns:
            ProfileDefinition if found, None otherwise
        """
        profiles = self.get_profiles(client_id)
        for profile in profiles:
            if profile.profile_id == profile_id:
                return profile
        return None

    def has_client(self, client_id: str) -> bool:
        """Check if client is registered.

        Args:
            client_id: Client family identifier

        Returns:
            True if client is registered, False otherwise
        """
        return client_id in self._clients

    def client_ids(self) -> list[str]:
        """Get list of all client IDs.

        Returns:
            List of client_id strings
        """
        return list(self._clients.keys())


def get_default_registry() -> ClientRegistry:
    """Get the default client registry with Wave 1 clients.

    Returns:
        ClientRegistry populated with claude-desktop and cursor
    """
    registry = ClientRegistry()

    # Register Claude Desktop
    registry.register(
        ClientDefinition(
            client_id="claude-desktop",
            display_name="Claude Desktop",
            platform="macos",
            config_location="~/Library/Application Support/Claude/claude_desktop_config.json",
            config_format="json",
            version_min="0.5.0",
            capabilities=ClientCapabilities(
                environment_variables=True,
                command_args=True,
                working_directory=True,
                multiple_servers=True,
            ),
            limitations=ClientLimitations(
                max_servers=None, max_env_vars_per_server=None
            ),
            default_profiles=[
                ProfileDefinition(
                    profile_id="default",
                    display_name="Default",
                    description="Standard configuration for most users",
                ),
                ProfileDefinition(
                    profile_id="dev",
                    display_name="Development",
                    description="Development tools and debug servers",
                ),
            ],
        )
    )

    # Register Cursor
    registry.register(
        ClientDefinition(
            client_id="cursor",
            display_name="Cursor IDE",
            platform="cross-platform",
            config_location="~/.cursor/mcp_config.json",
            config_format="json",
            version_min="0.1.0",
            capabilities=ClientCapabilities(
                environment_variables=True,
                command_args=True,
                working_directory=False,  # Cursor doesn't support this
                multiple_servers=True,
            ),
            limitations=ClientLimitations(
                max_servers=20, max_env_vars_per_server=50
            ),
            default_profiles=[
                ProfileDefinition(
                    profile_id="default",
                    display_name="Default",
                    description="Standard configuration for Cursor users",
                ),
            ],
        )
    )

    return registry
