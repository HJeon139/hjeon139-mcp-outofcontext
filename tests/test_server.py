"""Unit tests for MCP server."""

import pytest

from out_of_context.app_state import AppState
from out_of_context.server import MCPServer, create_server
from out_of_context.tool_registry import ToolRegistry


@pytest.mark.unit
class TestMCPServer:
    """Test MCPServer class."""

    def test_server_initialization(self) -> None:
        """Test server initialization."""
        server = MCPServer()
        assert server.app_state is not None
        assert server.tool_registry is not None
        assert isinstance(server.app_state, AppState)
        assert isinstance(server.tool_registry, ToolRegistry)

    def test_server_with_config(self) -> None:
        """Test server initialization with config."""
        config = {"test_key": "test_value"}
        server = MCPServer(config=config)
        assert server.config == config
        assert server.app_state.config == config

    def test_server_no_global_state(self) -> None:
        """Test that server instances don't share state."""
        server1 = MCPServer(config={"app": "1"})
        server2 = MCPServer(config={"app": "2"})
        assert server1.app_state.config != server2.app_state.config

    def test_get_app_state(self) -> None:
        """Test getting app state."""
        server = MCPServer()
        app_state = server.get_app_state()
        assert app_state is server.app_state

    def test_get_tool_registry(self) -> None:
        """Test getting tool registry."""
        server = MCPServer()
        registry = server.get_tool_registry()
        assert registry is server.tool_registry

    async def test_server_lifespan(self) -> None:
        """Test server lifespan context manager."""
        server = MCPServer()

        async with server.lifespan():
            assert server._running is True
            assert server.app_state._initialized is True

        assert server._running is False
        assert server.app_state._initialized is False

    async def test_server_initialize_cleanup(self) -> None:
        """Test server initialize and cleanup methods."""
        server = MCPServer()
        assert server.app_state._initialized is False
        assert server._running is False

        await server.initialize()
        assert server.app_state._initialized is True
        # _running is only set to True in lifespan context, not in initialize()
        assert server._running is False

        await server.cleanup()
        assert server.app_state._initialized is False
        assert server._running is False

    async def test_create_server(self) -> None:
        """Test create_server factory function."""
        server = await create_server()
        assert isinstance(server, MCPServer)
        assert server.app_state._initialized is True

        # Cleanup
        await server.cleanup()

    async def test_create_server_with_config(self) -> None:
        """Test create_server with config."""
        config = {"test": "value"}
        server = await create_server(config=config)
        assert server.config == config

        # Cleanup
        await server.cleanup()

    async def test_double_initialize(self) -> None:
        """Test that double initialization is safe."""
        server = MCPServer()
        await server.initialize()
        assert server.app_state._initialized is True

        # Second initialize should be safe
        await server.initialize()
        assert server.app_state._initialized is True

        await server.cleanup()

    async def test_cleanup_before_initialize(self) -> None:
        """Test that cleanup before initialize is safe."""
        server = MCPServer()
        # Should not raise
        await server.cleanup()
        assert server.app_state._initialized is False


@pytest.mark.integration
class TestMCPServerIntegration:
    """Integration tests for MCP server."""

    async def test_server_with_tool_registry(self) -> None:
        """Test server with tool registry integration."""
        server = MCPServer()

        async def test_handler(app_state: AppState, **kwargs: dict) -> dict:
            return {"status": "ok"}

        server.tool_registry.register("test_tool", test_handler, "Test tool")

        async with server.lifespan():
            tools = server.tool_registry.list_tools()
            assert len(tools) == 1
            assert tools[0].name == "test_tool"
