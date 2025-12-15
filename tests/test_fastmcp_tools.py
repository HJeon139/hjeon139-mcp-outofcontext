"""Tests for FastMCP tool wrappers.

Note: FastMCP tools are wrapped by @mcp.tool() decorator, making direct unit testing
of the wrapper functions difficult. The underlying handler functions are tested
separately. These tests verify that tools are properly registered and the module
can be imported.
"""

import pytest


@pytest.mark.unit
class TestFastMCPToolsRegistration:
    """Test that FastMCP tools are properly registered."""

    def test_fastmcp_tools_module_imports(self) -> None:
        """Test that fastmcp_tools module can be imported."""
        # This verifies the module structure and that decorators execute
        from hjeon139_mcp_outofcontext.tools.crud import fastmcp_tools

        # Verify tools are defined in the module
        assert hasattr(fastmcp_tools, "put_context")
        assert hasattr(fastmcp_tools, "get_context")
        assert hasattr(fastmcp_tools, "list_context")
        assert hasattr(fastmcp_tools, "search_context")
        assert hasattr(fastmcp_tools, "delete_context")

    def test_register_tools_function(self) -> None:
        """Test that register_tools function works."""
        from hjeon139_mcp_outofcontext.tools.crud import register_tools

        # Should not raise
        register_tools()
