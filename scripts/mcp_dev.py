"""Development entry point for mcp-hmr."""

from hjeon139_mcp_outofcontext.config import load_config
from hjeon139_mcp_outofcontext.fastmcp_server import (
    initialize_app_state,
    mcp,
    register_all_tools,
)

# Initialize before mcp-hmr takes over
config = load_config()
initialize_app_state(config)
register_all_tools()

# Export the mcp instance for mcp-hmr
__all__ = ["mcp"]
