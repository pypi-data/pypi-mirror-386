"""Client family registry for MCP orchestration.

This module provides the registry of supported MCP client families and their
configurations, capabilities, and profiles.
"""

__all__ = [
    "ClientRegistry",
    "ClientDefinition",
    "ProfileDefinition",
    "ClientCapabilities",
    "ClientLimitations",
    "get_default_registry",
]

from .clients import (
    ClientCapabilities,
    ClientDefinition,
    ClientLimitations,
    ClientRegistry,
    ProfileDefinition,
    get_default_registry,
)
