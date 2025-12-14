"""Integration tests for MCP protocol endpoints.

Tests MCP protocol communication using the MCP client library to validate
tool discovery, tool execution, and response formats.
"""

import json
import os
import sys
from pathlib import Path

import pytest

try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
except ImportError:
    pytest.skip("MCP client library not available", allow_module_level=True)


@pytest.fixture
def temp_storage_env(tmp_path: Path) -> dict[str, str]:
    """Create environment variables for temporary storage."""
    env = os.environ.copy()
    env["OUT_OF_CONTEXT_STORAGE_PATH"] = str(tmp_path)
    return env


@pytest.fixture
def server_params(temp_storage_env: dict[str, str]) -> StdioServerParameters:
    """Create server parameters for MCP server."""
    return StdioServerParameters(
        command=sys.executable,
        args=["-m", "hjeon139_mcp_outofcontext.main"],
        env=temp_storage_env,
    )


@pytest.mark.integration
class TestMCPToolsList:
    """Integration tests for tools/list endpoint."""

    @pytest.mark.asyncio
    async def test_list_tools_returns_all_tools(self, server_params: StdioServerParameters) -> None:
        """Test that tools/list returns all 5 CRUD tools."""
        async with (
            stdio_client(server_params) as (read, write),
            ClientSession(read, write) as session,
        ):
            await session.initialize()

            tools_result = await session.list_tools()
            tools = tools_result.tools

            assert len(tools) == 5
            tool_names = {tool.name for tool in tools}
            expected_tools = {
                "put_context",
                "get_context",
                "list_context",
                "search_context",
                "delete_context",
            }
            assert tool_names == expected_tools

    @pytest.mark.asyncio
    async def test_tool_schemas_are_correct(self, server_params: StdioServerParameters) -> None:
        """Test that tool schemas are correctly generated."""
        async with (
            stdio_client(server_params) as (read, write),
            ClientSession(read, write) as session,
        ):
            await session.initialize()

            tools_result = await session.list_tools()
            tools = {tool.name: tool for tool in tools_result.tools}

            # Test put_context schema
            put_tool = tools["put_context"]
            assert put_tool.description is not None
            assert put_tool.inputSchema is not None
            assert "properties" in put_tool.inputSchema

            # Test get_context schema
            get_tool = tools["get_context"]
            assert get_tool.description is not None
            assert get_tool.inputSchema is not None

    @pytest.mark.asyncio
    async def test_tool_schemas_no_refs(self, server_params: StdioServerParameters) -> None:
        """Test that tool schemas don't contain $ref references (should be inlined)."""
        async with (
            stdio_client(server_params) as (read, write),
            ClientSession(read, write) as session,
        ):
            await session.initialize()

            tools_result = await session.list_tools()
            tools = {tool.name: tool for tool in tools_result.tools}

            # Check put_context schema (has complex structure with contexts array)
            put_tool = tools["put_context"]
            schema = put_tool.inputSchema

            # Recursively check for $ref
            def has_ref(obj: dict) -> bool:
                if isinstance(obj, dict):
                    if "$ref" in obj:
                        return True
                    return any(has_ref(v) for v in obj.values())
                elif isinstance(obj, list):
                    return any(has_ref(item) for item in obj)
                return False

            assert not has_ref(schema), "Schema should not contain $ref references"

    @pytest.mark.asyncio
    async def test_tool_schemas_required_fields(self, server_params: StdioServerParameters) -> None:
        """Test that required fields are properly set in schemas."""
        async with (
            stdio_client(server_params) as (read, write),
            ClientSession(read, write) as session,
        ):
            await session.initialize()

            tools_result = await session.list_tools()
            tools = {tool.name: tool for tool in tools_result.tools}

            # search_context should have required query field
            search_tool = tools["search_context"]
            schema = search_tool.inputSchema
            if "required" in schema:
                assert "query" in schema["required"]


@pytest.mark.integration
class TestMCPToolsCall:
    """Integration tests for tools/call endpoint."""

    @pytest.mark.asyncio
    async def test_call_put_context_single(self, server_params: StdioServerParameters) -> None:
        """Test calling put_context tool (single operation)."""
        async with (
            stdio_client(server_params) as (read, write),
            ClientSession(read, write) as session,
        ):
            await session.initialize()

            result = await session.call_tool(
                "put_context",
                {"name": "test-single", "text": "Test content", "metadata": {"tag": "test"}},
            )

            assert not result.isError
            assert len(result.content) > 0

            # Parse response
            response_text = result.content[0].text
            response_data = json.loads(response_text)

            assert response_data["success"] is True
            assert response_data["operation"] == "single"
            assert response_data["name"] == "test-single"

    @pytest.mark.asyncio
    async def test_call_put_context_bulk(self, server_params: StdioServerParameters) -> None:
        """Test calling put_context tool (bulk operation)."""
        async with (
            stdio_client(server_params) as (read, write),
            ClientSession(read, write) as session,
        ):
            await session.initialize()

            result = await session.call_tool(
                "put_context",
                {
                    "contexts": [
                        {"name": "bulk-1", "text": "Content 1"},
                        {"name": "bulk-2", "text": "Content 2"},
                    ]
                },
            )

            assert not result.isError
            response_text = result.content[0].text
            response_data = json.loads(response_text)

            assert response_data["success"] is True
            assert response_data["operation"] == "bulk"
            assert response_data["count"] == 2

    @pytest.mark.asyncio
    async def test_call_get_context_single(self, server_params: StdioServerParameters) -> None:
        """Test calling get_context tool (single operation)."""
        async with (
            stdio_client(server_params) as (read, write),
            ClientSession(read, write) as session,
        ):
            await session.initialize()

            # First put a context
            await session.call_tool("put_context", {"name": "get-test", "text": "Get test content"})

            # Then get it
            result = await session.call_tool("get_context", {"name": "get-test"})

            assert not result.isError
            response_text = result.content[0].text
            response_data = json.loads(response_text)

            assert response_data["success"] is True
            assert response_data["operation"] == "single"
            assert response_data["name"] == "get-test"
            assert response_data["text"] == "Get test content"

    @pytest.mark.asyncio
    async def test_call_get_context_not_found(self, server_params: StdioServerParameters) -> None:
        """Test calling get_context with non-existent context."""
        async with (
            stdio_client(server_params) as (read, write),
            ClientSession(read, write) as session,
        ):
            await session.initialize()

            result = await session.call_tool("get_context", {"name": "nonexistent"})

            assert not result.isError  # MCP doesn't treat this as an error
            response_text = result.content[0].text
            response_data = json.loads(response_text)

            assert "error" in response_data
            assert response_data["error"]["code"] == "NOT_FOUND"

    @pytest.mark.asyncio
    async def test_call_list_context(self, server_params: StdioServerParameters) -> None:
        """Test calling list_context tool."""
        async with (
            stdio_client(server_params) as (read, write),
            ClientSession(read, write) as session,
        ):
            await session.initialize()

            # Create some contexts
            await session.call_tool("put_context", {"name": "list-1", "text": "Content 1"})
            await session.call_tool("put_context", {"name": "list-2", "text": "Content 2"})

            # List them
            result = await session.call_tool("list_context", {})

            assert not result.isError
            response_text = result.content[0].text
            response_data = json.loads(response_text)

            assert response_data["success"] is True
            assert response_data["count"] >= 2
            names = {ctx["name"] for ctx in response_data["contexts"]}
            assert "list-1" in names
            assert "list-2" in names

    @pytest.mark.asyncio
    async def test_call_list_context_with_limit(self, server_params: StdioServerParameters) -> None:
        """Test calling list_context with limit parameter."""
        async with (
            stdio_client(server_params) as (read, write),
            ClientSession(read, write) as session,
        ):
            await session.initialize()

            # Create multiple contexts
            for i in range(5):
                await session.call_tool(
                    "put_context", {"name": f"limit-{i}", "text": f"Content {i}"}
                )

            # List with limit
            result = await session.call_tool("list_context", {"limit": 2})

            assert not result.isError
            response_text = result.content[0].text
            response_data = json.loads(response_text)

            assert response_data["success"] is True
            assert response_data["count"] == 2
            assert len(response_data["contexts"]) == 2

    @pytest.mark.asyncio
    async def test_call_search_context(self, server_params: StdioServerParameters) -> None:
        """Test calling search_context tool."""
        async with (
            stdio_client(server_params) as (read, write),
            ClientSession(read, write) as session,
        ):
            await session.initialize()

            # Create contexts
            await session.call_tool(
                "put_context",
                {
                    "name": "python-code",
                    "text": "Python code example",
                    "metadata": {"tags": ["python"]},
                },
            )
            await session.call_tool(
                "put_context",
                {
                    "name": "js-code",
                    "text": "JavaScript code example",
                    "metadata": {"tags": ["js"]},
                },
            )

            # Search
            result = await session.call_tool("search_context", {"query": "Python"})

            assert not result.isError
            response_text = result.content[0].text
            response_data = json.loads(response_text)

            assert response_data["success"] is True
            assert response_data["query"] == "Python"
            assert response_data["count"] >= 1
            match_names = {match["name"] for match in response_data["matches"]}
            assert "python-code" in match_names

    @pytest.mark.asyncio
    async def test_call_delete_context_single(self, server_params: StdioServerParameters) -> None:
        """Test calling delete_context tool (single operation)."""
        async with (
            stdio_client(server_params) as (read, write),
            ClientSession(read, write) as session,
        ):
            await session.initialize()

            # Create a context
            await session.call_tool("put_context", {"name": "delete-test", "text": "Content"})

            # Delete it
            result = await session.call_tool("delete_context", {"name": "delete-test"})

            assert not result.isError
            response_text = result.content[0].text
            response_data = json.loads(response_text)

            assert response_data["success"] is True
            assert response_data["operation"] == "single"
            assert response_data["name"] == "delete-test"

            # Verify deleted
            get_result = await session.call_tool("get_context", {"name": "delete-test"})
            get_response = json.loads(get_result.content[0].text)
            assert "error" in get_response
            assert get_response["error"]["code"] == "NOT_FOUND"

    @pytest.mark.asyncio
    async def test_call_delete_context_bulk(self, server_params: StdioServerParameters) -> None:
        """Test calling delete_context tool (bulk operation)."""
        async with (
            stdio_client(server_params) as (read, write),
            ClientSession(read, write) as session,
        ):
            await session.initialize()

            # Create contexts
            await session.call_tool("put_context", {"name": "bulk-del-1", "text": "Content 1"})
            await session.call_tool("put_context", {"name": "bulk-del-2", "text": "Content 2"})

            # Delete them
            result = await session.call_tool(
                "delete_context", {"names": ["bulk-del-1", "bulk-del-2"]}
            )

            assert not result.isError
            response_text = result.content[0].text
            response_data = json.loads(response_text)

            assert response_data["success"] is True
            assert response_data["operation"] == "bulk"
            assert response_data["count"] == 2

    @pytest.mark.asyncio
    async def test_call_invalid_tool_name(self, server_params: StdioServerParameters) -> None:
        """Test calling non-existent tool returns error."""
        async with (
            stdio_client(server_params) as (read, write),
            ClientSession(read, write) as session,
        ):
            await session.initialize()

            result = await session.call_tool("nonexistent_tool", {})

            assert not result.isError  # MCP doesn't treat this as an error
            response_text = result.content[0].text
            response_data = json.loads(response_text)

            assert "error" in response_data
            assert "not registered" in response_data["error"]["message"].lower()

    @pytest.mark.asyncio
    async def test_error_response_format(self, server_params: StdioServerParameters) -> None:
        """Test that error responses have correct format."""
        async with (
            stdio_client(server_params) as (read, write),
            ClientSession(read, write) as session,
        ):
            await session.initialize()

            # Test with invalid parameter (missing required field)
            result = await session.call_tool("put_context", {"text": "Content"})  # Missing name

            assert not result.isError
            response_text = result.content[0].text
            response_data = json.loads(response_text)

            assert "error" in response_data
            assert "code" in response_data["error"]
            assert "message" in response_data["error"]
            assert response_data["error"]["code"] == "INVALID_PARAMETER"


@pytest.mark.integration
class TestMCPEndToEndWorkflows:
    """Integration tests for end-to-end workflows via MCP protocol."""

    @pytest.mark.asyncio
    async def test_put_get_list_search_delete_workflow(
        self, server_params: StdioServerParameters
    ) -> None:
        """Test complete workflow via MCP protocol."""
        async with (
            stdio_client(server_params) as (read, write),
            ClientSession(read, write) as session,
        ):
            await session.initialize()

            # Put
            put_result = await session.call_tool(
                "put_context",
                {
                    "name": "workflow-test",
                    "text": "Test content for workflow",
                    "metadata": {"type": "test"},
                },
            )
            put_data = json.loads(put_result.content[0].text)
            assert put_data["success"] is True

            # Get
            get_result = await session.call_tool("get_context", {"name": "workflow-test"})
            get_data = json.loads(get_result.content[0].text)
            assert get_data["success"] is True
            assert get_data["text"] == "Test content for workflow"

            # List
            list_result = await session.call_tool("list_context", {})
            list_data = json.loads(list_result.content[0].text)
            assert list_data["success"] is True
            names = {ctx["name"] for ctx in list_data["contexts"]}
            assert "workflow-test" in names

            # Search
            search_result = await session.call_tool("search_context", {"query": "workflow"})
            search_data = json.loads(search_result.content[0].text)
            assert search_data["success"] is True
            match_names = {match["name"] for match in search_data["matches"]}
            assert "workflow-test" in match_names

            # Delete
            delete_result = await session.call_tool("delete_context", {"name": "workflow-test"})
            delete_data = json.loads(delete_result.content[0].text)
            assert delete_data["success"] is True

            # Verify deleted
            get_result_after = await session.call_tool("get_context", {"name": "workflow-test"})
            get_data_after = json.loads(get_result_after.content[0].text)
            assert "error" in get_data_after
            assert get_data_after["error"]["code"] == "NOT_FOUND"

    @pytest.mark.asyncio
    async def test_bulk_operations_workflow(self, server_params: StdioServerParameters) -> None:
        """Test bulk operations workflow via MCP protocol."""
        async with (
            stdio_client(server_params) as (read, write),
            ClientSession(read, write) as session,
        ):
            await session.initialize()

            # Bulk put
            put_result = await session.call_tool(
                "put_context",
                {
                    "contexts": [
                        {"name": "bulk-1", "text": "Content 1"},
                        {"name": "bulk-2", "text": "Content 2"},
                        {"name": "bulk-3", "text": "Content 3"},
                    ]
                },
            )
            put_data = json.loads(put_result.content[0].text)
            assert put_data["success"] is True
            assert put_data["count"] == 3

            # Bulk get
            get_result = await session.call_tool(
                "get_context", {"names": ["bulk-1", "bulk-2", "bulk-3"]}
            )
            get_data = json.loads(get_result.content[0].text)
            assert get_data["success"] is True
            assert get_data["count"] == 3
            assert all(ctx["success"] for ctx in get_data["contexts"])

            # Bulk delete
            delete_result = await session.call_tool(
                "delete_context", {"names": ["bulk-1", "bulk-2", "bulk-3"]}
            )
            delete_data = json.loads(delete_result.content[0].text)
            assert delete_data["success"] is True
            assert delete_data["count"] == 3
            assert all(r["success"] for r in delete_data["results"])
