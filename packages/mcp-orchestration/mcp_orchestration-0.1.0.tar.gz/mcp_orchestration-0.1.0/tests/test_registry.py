"""Tests for client registry module."""

import pytest

from mcp_orchestrator.registry import (
    ClientDefinition,
    ClientRegistry,
    ProfileDefinition,
    get_default_registry,
)


class TestClientRegistry:
    """Test client registry functionality."""

    @pytest.fixture
    def registry(self) -> ClientRegistry:
        """Create empty registry for testing."""
        return ClientRegistry()

    @pytest.fixture
    def sample_client(self) -> ClientDefinition:
        """Create sample client definition."""
        return ClientDefinition(
            client_id="test-client",
            display_name="Test Client",
            platform="macos",
            config_location="~/test/config.json",
            default_profiles=[
                ProfileDefinition(
                    profile_id="default",
                    display_name="Default",
                    description="Default profile",
                ),
                ProfileDefinition(
                    profile_id="dev",
                    display_name="Development",
                    description="Dev profile",
                ),
            ],
        )

    def test_register_client(
        self, registry: ClientRegistry, sample_client: ClientDefinition
    ) -> None:
        """Test registering a client."""
        registry.register(sample_client)

        assert registry.has_client("test-client")
        assert not registry.has_client("unknown-client")

    def test_get_client(
        self, registry: ClientRegistry, sample_client: ClientDefinition
    ) -> None:
        """Test retrieving a client."""
        registry.register(sample_client)

        client = registry.get_client("test-client")
        assert client is not None
        assert client.client_id == "test-client"
        assert client.display_name == "Test Client"

        # Unknown client returns None
        unknown = registry.get_client("unknown")
        assert unknown is None

    def test_list_clients(
        self, registry: ClientRegistry, sample_client: ClientDefinition
    ) -> None:
        """Test listing all clients."""
        assert len(registry.list_clients()) == 0

        registry.register(sample_client)
        clients = registry.list_clients()

        assert len(clients) == 1
        assert clients[0].client_id == "test-client"

    def test_get_profiles(
        self, registry: ClientRegistry, sample_client: ClientDefinition
    ) -> None:
        """Test getting profiles for a client."""
        registry.register(sample_client)

        profiles = registry.get_profiles("test-client")
        assert len(profiles) == 2

        profile_ids = [p.profile_id for p in profiles]
        assert "default" in profile_ids
        assert "dev" in profile_ids

        # Unknown client returns empty list
        unknown_profiles = registry.get_profiles("unknown")
        assert len(unknown_profiles) == 0

    def test_get_profile(
        self, registry: ClientRegistry, sample_client: ClientDefinition
    ) -> None:
        """Test getting specific profile."""
        registry.register(sample_client)

        profile = registry.get_profile("test-client", "default")
        assert profile is not None
        assert profile.profile_id == "default"
        assert profile.display_name == "Default"

        # Unknown profile returns None
        unknown = registry.get_profile("test-client", "unknown")
        assert unknown is None

    def test_client_ids(
        self, registry: ClientRegistry, sample_client: ClientDefinition
    ) -> None:
        """Test getting list of client IDs."""
        assert registry.client_ids() == []

        registry.register(sample_client)
        ids = registry.client_ids()

        assert len(ids) == 1
        assert "test-client" in ids


class TestDefaultRegistry:
    """Test the default registry configuration."""

    def test_default_registry_has_clients(self) -> None:
        """Test that default registry has expected clients."""
        registry = get_default_registry()

        clients = registry.list_clients()
        assert len(clients) >= 2  # At least claude-desktop and cursor

        client_ids = [c.client_id for c in clients]
        assert "claude-desktop" in client_ids
        assert "cursor" in client_ids

    def test_claude_desktop_configuration(self) -> None:
        """Test claude-desktop client configuration."""
        registry = get_default_registry()

        client = registry.get_client("claude-desktop")
        assert client is not None
        assert client.display_name == "Claude Desktop"
        assert client.platform == "macos"
        assert client.capabilities.environment_variables is True
        assert client.capabilities.working_directory is True

        # Check profiles
        profiles = registry.get_profiles("claude-desktop")
        profile_ids = [p.profile_id for p in profiles]
        assert "default" in profile_ids
        assert "dev" in profile_ids

    def test_cursor_configuration(self) -> None:
        """Test cursor client configuration."""
        registry = get_default_registry()

        client = registry.get_client("cursor")
        assert client is not None
        assert client.display_name == "Cursor IDE"
        assert client.platform == "cross-platform"
        assert client.capabilities.environment_variables is True
        assert client.capabilities.working_directory is False  # Cursor limitation

        # Check limitations
        assert client.limitations.max_servers == 20
        assert client.limitations.max_env_vars_per_server == 50

        # Check profiles
        profiles = registry.get_profiles("cursor")
        assert len(profiles) >= 1
        assert profiles[0].profile_id == "default"
