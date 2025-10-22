"""FastMCP server instance - single source of truth.

This module creates the main FastMCP server instance in isolation to avoid
circular import issues between server.py and tools.py.

Import structure:
- instance.py: Creates mcp instance (no imports from mcp package)
- tools.py: Imports mcp from instance.py, decorates functions
- server.py: Imports mcp from instance.py, imports tools to register them
"""

from importlib.metadata import PackageNotFoundError, version

from fastmcp import FastMCP


def _get_version() -> str:
    """Get package version from installed metadata.

    Reads version from package metadata (synced with pyproject.toml).
    Falls back to development version if package not installed.

    Returns:
        Version string from pyproject.toml or "0.0.0-dev" for development
    """
    try:
        return version("chora-compose")
    except PackageNotFoundError:
        # Development mode: package not installed
        return "0.0.0-dev"


# Create MCP server instance - single source of truth
mcp = FastMCP(
    name="chora-compose",
    instructions=(
        "Configuration-driven content generation and artifact assembly. "
        "Generate content from templates, assemble artifacts from content pieces, "
        "and manage generators through a simple, declarative configuration format."
    ),
    version=_get_version(),
)
