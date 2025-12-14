"""Main entry point for MCP server with stdio transport.

Reference implementation for Phase 1 migration.
"""

import asyncio
import logging
import sys
from contextlib import asynccontextmanager

from hjeon139_mcp_outofcontext.config import load_config
from hjeon139_mcp_outofcontext.fastmcp_server import mcp, initialize_app_state

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def app_lifespan():
    """Manage application lifespan (startup and shutdown)."""
    # Startup: Initialize AppState
    config = load_config()
    initialize_app_state(config)

    logger.info("Starting FastMCP server...")
    logger.info(f"Storage path: {config.storage_path}")
    logger.info(f"Log level: {config.log_level}")

    try:
        yield
    finally:
        # Shutdown: Cleanup resources if needed
        # Currently AppState doesn't require cleanup, but this is where it would go
        logger.info("Shutting down FastMCP server...")


async def main() -> None:
    """Main entry point for MCP server."""
    try:
        # For stdio transport (default), use lifespan context
        async with app_lifespan():
            # Run stdio server (blocking)
            await mcp.run()

    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.exception(f"Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
