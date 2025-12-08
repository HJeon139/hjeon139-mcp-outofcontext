"""Unit tests for MCP server."""

import tempfile

import pytest

from hjeon139_mcp_outofcontext.app_state import AppState
from hjeon139_mcp_outofcontext.config import Config
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

    def test_server_with_config_dict(self) -> None:
        """Test server initialization with config dict."""
        config = {"test_key": "test_value"}
        server = MCPServer(config=config)
        assert server.config == config
        assert server.app_state.config == config

    def test_server_with_config_object(self) -> None:
        """Test server initialization with Config object."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = Config(storage_path=tmpdir, model="gpt-3.5-turbo")
            server = MCPServer(config=config)
            assert server.config["storage_path"] == tmpdir
            assert server.config["model"] == "gpt-3.5-turbo"

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
            # 2 monitoring + 4 pruning + 3 stashing + 3 task + 1 test = 13
            assert len(tools) == 13
            tool_names = {tool.name for tool in tools}
            assert "test_tool" in tool_names
            assert "context_analyze_usage" in tool_names
            assert "context_get_working_set" in tool_names
            assert "context_gc_analyze" in tool_names
            assert "context_set_current_task" in tool_names
            assert "context_get_task_context" in tool_names
            assert "context_create_task_snapshot" in tool_names
            assert "context_gc_prune" in tool_names
            assert "context_gc_pin" in tool_names
            assert "context_gc_unpin" in tool_names

    async def test_server_mcp_handlers_registered(self) -> None:
        """Test that MCP handlers are registered."""
        server = MCPServer()
        # MCP server should be initialized
        assert server.mcp_server is not None
        # Tool registry should have tools
        tools = server.tool_registry.list_tools()
        assert len(tools) >= 12  # At least all registered tools

    async def test_server_error_handling(self) -> None:
        """Test server error handling."""
        server = MCPServer()

        # Test error formatting
        error = ValueError("Test error")
        error_msg = server._format_error(error)
        assert "error" in error_msg
        assert "Test error" in error_msg
        assert "ValueError" in error_msg

    async def test_mcp_list_tools_handler(self) -> None:
        """Test MCP list_tools handler returns all registered tools."""
        server = MCPServer()

        # Get tools via MCP handler (simulating MCP protocol call)
        # We need to access the registered handler
        # The handler is registered via decorator, so we'll test it indirectly
        # by checking that tools are discoverable through the MCP server

        # Verify MCP server has tools registered
        # This tests that list_tools handler would return correct tools
        registered_tools = server.tool_registry.list_tools()
        assert len(registered_tools) >= 12

        # Verify all expected tools are present
        tool_names = {tool.name for tool in registered_tools}
        expected_tools = {
            "context_analyze_usage",
            "context_get_working_set",
            "context_gc_analyze",
            "context_gc_prune",
            "context_gc_pin",
            "context_gc_unpin",
            "context_stash",
            "context_retrieve_stashed",
            "context_search_stashed",
            "context_set_current_task",
            "context_get_task_context",
            "context_create_task_snapshot",
        }
        assert expected_tools.issubset(tool_names)

    async def test_mcp_call_tool_handler(self) -> None:
        """Test MCP call_tool handler dispatches tool calls correctly."""
        server = MCPServer()

        # Register a test tool
        async def test_handler(app_state: AppState, **kwargs: dict) -> dict:
            return {"status": "ok", "message": "test successful"}

        server.tool_registry.register("test_tool", test_handler, "Test tool")

        # Simulate MCP tool call by directly calling the dispatch mechanism
        # that the MCP handler uses
        result = await server.tool_registry.dispatch("test_tool", {}, server.app_state)

        assert result["status"] == "ok"
        assert result["message"] == "test successful"

    async def test_mcp_call_tool_handler_invalid_tool(self) -> None:
        """Test MCP call_tool handler handles invalid tool names."""
        server = MCPServer()

        # Try to dispatch a non-existent tool
        # This should raise ValueError which the handler would catch
        with pytest.raises(ValueError, match="Tool 'nonexistent_tool' is not registered"):
            await server.tool_registry.dispatch("nonexistent_tool", {}, server.app_state)

    async def test_mcp_server_initialization_options(self) -> None:
        """Test MCP server creates valid initialization options."""
        server = MCPServer()

        # Verify initialization options can be created
        init_options = server.mcp_server.create_initialization_options()
        assert init_options is not None
        # Initialization options should be valid
        assert init_options is not None or hasattr(init_options, "capabilities")
