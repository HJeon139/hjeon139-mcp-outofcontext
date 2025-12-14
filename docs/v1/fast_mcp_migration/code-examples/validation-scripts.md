# Validation Scripts

Reference implementations for validation scripts used in Phase 0 and Phase 5.

## test_mcp_server.py

Manual validation script using MCP client library:

```python
"""Manual validation script for MCP server.

Tests the MCP server directly using the MCP client library.
Validates all tools work correctly and produce expected outputs.
"""
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_server():
    """Test MCP server functionality."""
    # Configure server parameters
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "hjeon139_mcp_outofcontext.main"],
        env=None,
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize session
            await session.initialize()
            
            # Test 1: List tools
            print("Testing tools/list...")
            tools_result = await session.list_tools()
            tools = tools_result.tools
            print(f"Found {len(tools)} tools")
            tool_names = [tool.name for tool in tools]
            expected_tools = ["put_context", "get_context", "list_context", "search_context", "delete_context"]
            assert set(tool_names) == set(expected_tools), f"Expected {expected_tools}, got {tool_names}"
            
            # Test 2: put_context (single)
            print("Testing put_context (single)...")
            put_result = await session.call_tool(
                "put_context",
                {"name": "test-validation", "text": "Test content", "metadata": {"tag": "test"}},
            )
            print(f"put_context result: {put_result.content}")
            assert put_result.isError == False
            
            # Test 3: get_context
            print("Testing get_context...")
            get_result = await session.call_tool("get_context", {"name": "test-validation"})
            print(f"get_context result: {get_result.content}")
            assert get_result.isError == False
            
            # Test 4: list_context
            print("Testing list_context...")
            list_result = await session.call_tool("list_context", {})
            print(f"list_context result: {list_result.content}")
            assert list_result.isError == False
            
            # Test 5: search_context
            print("Testing search_context...")
            search_result = await session.call_tool("search_context", {"query": "test"})
            print(f"search_context result: {search_result.content}")
            assert search_result.isError == False
            
            # Test 6: delete_context
            print("Testing delete_context...")
            delete_result = await session.call_tool("delete_context", {"name": "test-validation"})
            print(f"delete_context result: {delete_result.content}")
            assert delete_result.isError == False
            
            # Test 7: Bulk operations
            print("Testing bulk operations...")
            bulk_put = await session.call_tool(
                "put_context",
                {
                    "contexts": [
                        {"name": "bulk-1", "text": "Content 1"},
                        {"name": "bulk-2", "text": "Content 2"},
                    ]
                },
            )
            assert bulk_put.isError == False
            
            bulk_get = await session.call_tool("get_context", {"names": ["bulk-1", "bulk-2"]})
            assert bulk_get.isError == False
            
            bulk_delete = await session.call_tool("delete_context", {"names": ["bulk-1", "bulk-2"]})
            assert bulk_delete.isError == False
            
            # Test 8: Error cases
            print("Testing error cases...")
            error_result = await session.call_tool("get_context", {"name": "nonexistent"})
            # Should return error or empty result (depending on implementation)
            print(f"Error case result: {error_result.content}")
            
            print("\n✅ All tests passed!")

if __name__ == "__main__":
    asyncio.run(test_server())
```

## test_all_tools.sh

Shell script for automated validation:

```bash
#!/bin/bash
# Validation script for MCP server
# Starts server in background and tests each tool

set -e

echo "Starting MCP server validation..."

# Start server in background
python -m hjeon139_mcp_outofcontext.main &
SERVER_PID=$!

# Wait for server to start
sleep 2

# Run validation script
python scripts/test_mcp_server.py

# Cleanup
kill $SERVER_PID 2>/dev/null || true

echo "Validation complete!"
```

## compare_baseline.py

Compare migrated server outputs with baseline (optional):

```python
"""Compare migrated server outputs with baseline.

Runs same operations on old and new server implementations
and compares outputs to verify feature parity.
"""
import asyncio
import json
from pathlib import Path

# Implementation to run same operations on both servers
# and compare JSON outputs byte-for-byte
```
