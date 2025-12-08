"""Unit tests for MCP server."""

import pytest

from hjeon139_mcp_outofcontext.app_state import AppState
from hjeon139_mcp_outofcontext.server import MCPServer, create_server
from hjeon139_mcp_outofcontext.tool_registry import ToolRegistry


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

    def test_app_state_components_initialized(self) -> None:
        """Test that AppState components are initialized in __init__."""
        server = MCPServer()
        # Components should be available immediately
        assert server.app_state.storage is not None
        assert server.app_state.analysis_engine is not None
        assert server.app_state.gc_engine is not None
        assert server.app_state.context_manager is not None

    async def test_server_lifespan(self) -> None:
        """Test server lifespan context manager."""
        server = MCPServer()

        async with server.lifespan():
            assert server._running is True
            # Components should be available
            assert server.app_state.storage is not None

        assert server._running is False

    async def test_create_server(self) -> None:
        """Test create_server factory function."""
        server = await create_server()
        assert isinstance(server, MCPServer)
        # Components should be initialized
        assert server.app_state.storage is not None

    async def test_create_server_with_config(self) -> None:
        """Test create_server with config."""
        config = {"test": "value"}
        server = await create_server(config=config)
        assert server.config == config
        # Components should be initialized
        assert server.app_state.storage is not None


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
            # Should have 2 monitoring tools + 1 test tool = 3 total
            assert len(tools) == 3
            tool_names = {tool.name for tool in tools}
            assert "test_tool" in tool_names
            assert "context_analyze_usage" in tool_names
            assert "context_get_working_set" in tool_names
