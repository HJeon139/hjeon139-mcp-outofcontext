"""MCP server skeleton with dependency injection and lifecycle management."""

import asyncio
from contextlib import asynccontextmanager
from typing import Any

from hjeon139_mcp_outofcontext.app_state import AppState
from hjeon139_mcp_outofcontext.tool_registry import ToolRegistry
from hjeon139_mcp_outofcontext.tools import (
    register_monitoring_tools,
    register_pruning_tools,
)


class MCPServer:
    """
    MCP server with dependency injection and lifecycle management.

    Follows best practices:
    - NO global variables - all state is instance-scoped
    - AppState holds all components (initialized in __init__)
    - Lifecycle management via async context manager
    - Tool registry with dependency injection
    """

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """
        Initialize MCP server.

        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        # Create AppState instance (not global)
        self.app_state = AppState(config=self.config)
        # Create tool registry
        self.tool_registry = ToolRegistry()
        # Register all tools
        self._register_tools()
        self._running = False

    @asynccontextmanager
    async def lifespan(self) -> Any:
        """
        Lifespan context manager for startup/shutdown.

        Usage:
            async with server.lifespan():
                # Server running
                pass
        """
        self._running = True
        try:
            async with self.app_state.lifespan():
                yield
        finally:
            self._running = False

    async def run(self) -> None:
        """
        Run the MCP server.

        This is a placeholder - actual MCP SDK integration will be
        implemented based on MCP SDK documentation.
        """
        async with self.lifespan():
            # MCP server will use stdio or other transport
            # This is a placeholder structure
            while self._running:
                await asyncio.sleep(0.1)

    def get_app_state(self) -> AppState:
        """
        Get application state instance.

        Returns:
            AppState instance
        """
        return self.app_state

    def get_tool_registry(self) -> ToolRegistry:
        """
        Get tool registry instance.

        Returns:
            ToolRegistry instance
        """
        return self.tool_registry

    def _register_tools(self) -> None:
        """
        Register all tools with the tool registry.

        Called during initialization to register all available tools.
        """
        # Register monitoring tools
        register_monitoring_tools(self.tool_registry, self.app_state)
        # Register pruning tools
        register_pruning_tools(self.tool_registry, self.app_state)


async def create_server(config: dict[str, Any] | None = None) -> MCPServer:
    """
    Create MCP server instance.

    Args:
        config: Optional configuration dictionary

    Returns:
        MCPServer instance (components initialized in __init__)
    """
    return MCPServer(config=config)
