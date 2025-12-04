"""MCP server skeleton with dependency injection and lifecycle management."""

import asyncio
from contextlib import asynccontextmanager
from typing import Any

from hjeon139_mcp_outofcontext.app_state import AppState
from hjeon139_mcp_outofcontext.tool_registry import ToolRegistry


class MCPServer:
    """
    MCP server with dependency injection and lifecycle management.

    Follows best practices:
    - NO global variables - all state is instance-scoped
    - AppState holds all components
    - Lifecycle management - explicit initialize/cleanup
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
        self._running = False

    async def initialize(self) -> None:
        """
        Initialize server and application state.

        Sets up lifecycle and initializes all components.
        """
        # Initialize application state (loads storage, initializes components)
        await self.app_state.initialize()
        # Tools will be registered here in later tasks
        # For now, registry is empty

    async def cleanup(self) -> None:
        """
        Cleanup server resources.

        Ensures proper resource cleanup and persistence.
        """
        # Cleanup application state
        await self.app_state.cleanup()
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
        await self.initialize()
        self._running = True
        try:
            yield
        finally:
            await self.cleanup()

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


async def create_server(config: dict[str, Any] | None = None) -> MCPServer:
    """
    Create and initialize MCP server instance.

    Args:
        config: Optional configuration dictionary

    Returns:
        Initialized MCPServer instance
    """
    server = MCPServer(config=config)
    await server.initialize()
    return server
