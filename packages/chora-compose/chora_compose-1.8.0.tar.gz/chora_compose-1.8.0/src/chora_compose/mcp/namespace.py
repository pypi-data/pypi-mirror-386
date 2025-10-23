"""MCP namespace utilities for chora-compose.

Provides helper functions for consistent namespace usage following
Chora MCP Conventions v1.0.

Namespace: choracompose
See: docs/NAMESPACES.md
"""

import re
from typing import Optional

# Namespace configuration
MCP_NAMESPACE = "choracompose"
ENABLE_NAMESPACING = True

# Validation patterns (from Chora MCP Conventions v1.0)
NAMESPACE_PATTERN = re.compile(r"^[a-z][a-z0-9]{2,19}$")
TOOL_NAME_PATTERN = re.compile(r"^[a-z][a-z0-9_]+:[a-z][a-z0-9_]+$")
RESOURCE_URI_PATTERN = re.compile(r"^[a-z][a-z0-9]+://[a-z0-9_/\-\.]+(\?.*)?$")


def make_tool_name(tool: str) -> str:
    """Create namespaced tool name.

    Args:
        tool: Tool name (snake_case, no namespace)

    Returns:
        Namespaced tool name (e.g., "choracompose:generate_content")

    Example:
        >>> make_tool_name("generate_content")
        'choracompose:generate_content'
    """
    if not ENABLE_NAMESPACING:
        return tool
    return f"{MCP_NAMESPACE}:{tool}"


def make_resource_uri(
    resource_type: str, resource_id: str, query: Optional[str] = None
) -> str:
    """Create namespaced resource URI.

    Args:
        resource_type: Type of resource (e.g., "templates", "content")
        resource_id: Resource identifier
        query: Optional query string (without leading '?')

    Returns:
        Namespaced URI (e.g., "choracompose://templates/daily-report.md")

    Example:
        >>> make_resource_uri("templates", "daily-report.md")
        'choracompose://templates/daily-report.md'
        >>> make_resource_uri("content", "abc123", "version=2")
        'choracompose://content/abc123?version=2'
    """
    if not ENABLE_NAMESPACING:
        return f"{resource_type}/{resource_id}"

    uri = f"{MCP_NAMESPACE}://{resource_type}/{resource_id}"
    if query:
        uri += f"?{query}"
    return uri


def validate_tool_name(name: str) -> bool:
    """Validate tool name follows conventions.

    Args:
        name: Tool name to validate

    Returns:
        True if valid, False otherwise
    """
    if not ENABLE_NAMESPACING:
        return bool(re.match(r"^[a-z][a-z0-9_]+$", name))

    if not TOOL_NAME_PATTERN.match(name):
        return False

    namespace, _ = name.split(":", 1)
    return namespace == MCP_NAMESPACE


def validate_resource_uri(uri: str) -> bool:
    """Validate resource URI follows conventions.

    Args:
        uri: Resource URI to validate

    Returns:
        True if valid, False otherwise
    """
    if not ENABLE_NAMESPACING:
        return True  # No validation in non-namespaced mode

    if not RESOURCE_URI_PATTERN.match(uri):
        return False

    namespace = uri.split("://", 1)[0]
    return namespace == MCP_NAMESPACE


def get_namespace() -> str:
    """Get the current MCP namespace.

    Returns:
        Current namespace string
    """
    return MCP_NAMESPACE
