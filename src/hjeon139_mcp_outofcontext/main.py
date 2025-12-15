"""Main entry point for MCP server."""

import logging
import sys

from hjeon139_mcp_outofcontext import prompts as _prompts  # noqa: F401
from hjeon139_mcp_outofcontext.config import load_config
from hjeon139_mcp_outofcontext.fastmcp_server import initialize_app_state, mcp, register_all_tools

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)

logger = logging.getLogger(__name__)


def main() -> None:
    """Main entry point for MCP server."""
    try:
        # Startup: Initialize AppState
        config = load_config()

        # Set log level from config
        log_level = getattr(logging, config.log_level.upper(), logging.INFO)
        logging.getLogger().setLevel(log_level)

        initialize_app_state(config)

        logger.info("Starting FastMCP server...")
        logger.info(f"Storage path: {config.storage_path}")
        logger.info(f"Log level: {config.log_level}")

        # Register all tools
        register_all_tools()

        # Run stdio server (blocking)
        mcp.run()

    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.exception(f"Server error: {e}")
        sys.exit(1)
    finally:
        # Shutdown: Cleanup resources if needed
        # Currently AppState doesn't require cleanup, but this is where it would go
        logger.info("Shutting down FastMCP server...")


if __name__ == "__main__":
    main()
