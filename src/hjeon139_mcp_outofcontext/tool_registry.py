"""Tool registry for MCP tool registration and dispatch with dependency injection."""

from collections.abc import Awaitable, Callable
from typing import Any

from hjeon139_mcp_outofcontext.app_state import AppState


class ToolHandler:
    """
    Tool handler with dependency injection support.

    Handlers receive AppState as a dependency, not global state.
    """

    def __init__(
        self,
        name: str,
        handler: Callable[..., Awaitable[Any]],
        description: str,
    ) -> None:
        """
        Initialize tool handler.

        Args:
            name: Tool name
            handler: Async handler function that receives app_state as first arg
            description: Tool description
        """
        self.name = name
        self.handler = handler
        self.description = description


class ToolRegistry:
    """
    Registry for MCP tools with dependency injection.

    Maintains a registry of tool name -> handler mappings.
    Provides registration and dispatch functions.
    """

    def __init__(self) -> None:
        """Initialize empty tool registry."""
        self._tools: dict[str, ToolHandler] = {}

    def register(
        self,
        name: str,
        handler: Callable[..., Awaitable[Any]],
        description: str,
    ) -> None:
        """
        Register a tool with the registry.

        Args:
            name: Tool name (must be unique)
            handler: Async handler function that receives app_state as first arg
            description: Tool description

        Raises:
            ValueError: If tool name is already registered
        """
        if name in self._tools:
            raise ValueError(f"Tool '{name}' is already registered")

        self._tools[name] = ToolHandler(name, handler, description)

    async def dispatch(self, name: str, arguments: dict[str, Any], app_state: AppState) -> Any:
        """
        Dispatch tool call to registered handler.

        Args:
            name: Tool name
            arguments: Tool arguments
            app_state: Application state for dependency injection

        Returns:
            Tool result

        Raises:
            ValueError: If tool is not registered
        """
        if name not in self._tools:
            raise ValueError(f"Tool '{name}' is not registered")

        tool = self._tools[name]

        # Call handler with app_state as first argument (dependency injection)
        result = await tool.handler(app_state, **arguments)
        return result

    def list_tools(self) -> list[ToolHandler]:
        """
        List all registered tools.

        Returns:
            List of tool handlers
        """
        return list(self._tools.values())

    def get_tool(self, name: str) -> ToolHandler | None:
        """
        Get tool handler by name.

        Args:
            name: Tool name

        Returns:
            Tool handler or None if not found
        """
        return self._tools.get(name)
