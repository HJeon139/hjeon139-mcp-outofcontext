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
            config = Config(storage_path=tmpdir)
            server = MCPServer(config=config)
            assert server.config["storage_path"] == tmpdir

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
            # 5 CRUD tools + 1 test = 6
            assert len(tools) == 6
            tool_names = {tool.name for tool in tools}
            assert "test_tool" in tool_names
            assert "put_context" in tool_names
            assert "list_context" in tool_names
            assert "get_context" in tool_names
            assert "search_context" in tool_names
            assert "delete_context" in tool_names

    async def test_server_mcp_handlers_registered(self) -> None:
        """Test that MCP handlers are registered."""
        server = MCPServer()
        # MCP server should be initialized
        assert server.mcp_server is not None
        # Tool registry should have tools
        tools = server.tool_registry.list_tools()
        assert len(tools) == 5  # 5 CRUD tools

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
        assert len(registered_tools) == 5

        # Verify all expected tools are present
        tool_names = {tool.name for tool in registered_tools}
        expected_tools = {
            "put_context",
            "list_context",
            "get_context",
            "search_context",
            "delete_context",
        }
        assert expected_tools == tool_names

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

    async def test_mcp_batch_operations_json_strings(self) -> None:
        """Test batch operations with JSON string parameters (simulating MCP client behavior)."""
        import json
        import tempfile

        from hjeon139_mcp_outofcontext.config import Config

        # Create server with temp storage
        with tempfile.TemporaryDirectory() as tmpdir:
            config = Config(storage_path=tmpdir)
            server = MCPServer(config=config.to_dict())

            async with server.lifespan():
                # Test 1: Batch put_context with JSON string
                contexts_list = [
                    {"name": "batch-json-1", "text": "Content 1", "metadata": {"type": "test"}},
                    {"name": "batch-json-2", "text": "Content 2", "metadata": {"type": "test"}},
                ]
                contexts_json = json.dumps(contexts_list)

                result = await server.tool_registry.dispatch(
                    "put_context", {"contexts": contexts_json}, server.app_state
                )

                assert result["success"] is True
                assert result["operation"] == "bulk"
                assert result["count"] == 2
                assert all(r["success"] for r in result["results"])

                # Test 2: Batch get_context with list
                result = await server.tool_registry.dispatch(
                    "get_context",
                    {"names": ["batch-json-1", "batch-json-2", "nonexistent"]},
                    server.app_state,
                )

                assert result["success"] is True
                assert result["operation"] == "bulk"
                assert result["count"] == 3
                assert len(result["contexts"]) == 3
                assert result["contexts"][0]["success"] is True
                assert result["contexts"][1]["success"] is True
                assert result["contexts"][2]["success"] is False  # nonexistent

                # Test 3: Batch delete_context
                result = await server.tool_registry.dispatch(
                    "delete_context",
                    {"names": ["batch-json-1", "batch-json-2", "nonexistent"]},
                    server.app_state,
                )

                assert result["success"] is True
                assert result["operation"] == "bulk"
                assert result["count"] == 3
                assert result["results"][0]["success"] is True
                assert result["results"][1]["success"] is True
                assert result["results"][2]["success"] is False  # nonexistent

    async def test_mcp_batch_operations_python_repr_strings(self) -> None:
        """Test batch operations with Python repr() string parameters."""
        import tempfile

        from hjeon139_mcp_outofcontext.config import Config

        # Create server with temp storage
        with tempfile.TemporaryDirectory() as tmpdir:
            config = Config(storage_path=tmpdir)
            server = MCPServer(config=config.to_dict())

            async with server.lifespan():
                # Test batch put_context with Python repr string
                contexts_list = [
                    {"name": "batch-repr-1", "text": "Content 1", "metadata": {"type": "test"}},
                    {"name": "batch-repr-2", "text": "Content 2"},
                ]
                contexts_repr = repr(contexts_list)

                result = await server.tool_registry.dispatch(
                    "put_context", {"contexts": contexts_repr}, server.app_state
                )

                assert result["success"] is True
                assert result["operation"] == "bulk"
                assert result["count"] == 2
                assert all(r["success"] for r in result["results"])

                # Verify contexts were saved
                result = await server.tool_registry.dispatch(
                    "get_context",
                    {"names": ["batch-repr-1", "batch-repr-2"]},
                    server.app_state,
                )

                assert result["success"] is True
                assert result["contexts"][0]["success"] is True
                assert result["contexts"][1]["success"] is True

    async def test_mcp_batch_operations_regular_lists(self) -> None:
        """Test batch operations with regular list parameters (direct objects)."""
        import tempfile

        from hjeon139_mcp_outofcontext.config import Config

        # Create server with temp storage
        with tempfile.TemporaryDirectory() as tmpdir:
            config = Config(storage_path=tmpdir)
            server = MCPServer(config=config.to_dict())

            async with server.lifespan():
                # Test batch put_context with regular list
                result = await server.tool_registry.dispatch(
                    "put_context",
                    {
                        "contexts": [
                            {"name": "batch-list-1", "text": "Content 1"},
                            {"name": "batch-list-2", "text": "Content 2"},
                        ]
                    },
                    server.app_state,
                )

                assert result["success"] is True
                assert result["operation"] == "bulk"
                assert result["count"] == 2

                # Test batch get_context with regular list
                result = await server.tool_registry.dispatch(
                    "get_context",
                    {"names": ["batch-list-1", "batch-list-2"]},
                    server.app_state,
                )

                assert result["success"] is True
                assert result["operation"] == "bulk"
                assert len(result["contexts"]) == 2

    async def test_mcp_schema_generation_for_batch_operations(self) -> None:
        """Test that schemas are properly generated and simplified for batch operations."""
        server = MCPServer()

        # Get put_context tool schema
        tools = server.tool_registry.list_tools()
        put_context_tool = next((t for t in tools if t.name == "put_context"), None)
        assert put_context_tool is not None
        assert put_context_tool.params_model is not None

        # Generate schema
        schema = put_context_tool.params_model.model_json_schema()
        resolved = server._resolve_schema_refs(schema)
        simplified = server._simplify_schema(resolved)

        # Check that contexts property exists and is properly structured
        assert "properties" in simplified
        assert "contexts" in simplified["properties"]

        contexts_prop = simplified["properties"]["contexts"]
        # Should be an array type (possibly wrapped in anyOf for array/null)
        if "anyOf" in contexts_prop:
            # Find array option
            array_option = next(
                (opt for opt in contexts_prop["anyOf"] if opt.get("type") == "array"), None
            )
            assert array_option is not None
            assert "items" in array_option
            # Items should be inline object (not $ref)
            items = array_option["items"]
            assert "$ref" not in items
            assert "properties" in items
            assert "name" in items["properties"]
            assert "text" in items["properties"]
        else:
            # Direct array type
            assert contexts_prop["type"] == "array"
            assert "items" in contexts_prop
