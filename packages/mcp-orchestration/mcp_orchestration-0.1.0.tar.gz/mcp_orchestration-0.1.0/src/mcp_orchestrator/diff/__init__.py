"""Configuration diff module for MCP orchestration.

This module provides diff functionality to compare local and remote MCP configurations.
"""

__all__ = ["compare_configs", "DiffResult", "ConfigChangeType"]

from .config_diff import ConfigChangeType, DiffResult, compare_configs
