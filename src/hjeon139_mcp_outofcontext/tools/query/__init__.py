"""Query tools for context management."""

__all__ = ["register_tools"]


def register_tools() -> None:
    """Register all query tools with FastMCP.

    Tools are registered via @mcp.tool() decorators when imported.
    This function ensures all tool modules are imported.
    """
    from . import (
        list_context,  # noqa: F401
        search_context,  # noqa: F401
    )
