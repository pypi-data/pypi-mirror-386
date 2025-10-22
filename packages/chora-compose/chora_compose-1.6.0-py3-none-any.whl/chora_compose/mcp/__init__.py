"""MCP server for chora-compose.

This package provides a Model Context Protocol (MCP) server that exposes
chora-compose functionality to Claude Desktop and other MCP clients.

The server implements 17 tools including:
- Core tools: generate_content, assemble_artifact, list_generators, validate_content
- Config lifecycle tools (v1.1.0): draft_config, test_config, save_config, modify_config
- Workflow tools: regenerate_content, delete_content, preview_generation, batch_generate
- Management tools: trace_dependencies, list_artifacts, list_content, cleanup_ephemeral
"""

from .instance import _get_version, mcp
from .tools import (
    assemble_artifact,
    generate_content,
    list_generators,
    validate_content,
)

__all__ = [
    "mcp",
    "generate_content",
    "assemble_artifact",
    "list_generators",
    "validate_content",
]

# Version synced from pyproject.toml via importlib.metadata
__version__ = _get_version()
