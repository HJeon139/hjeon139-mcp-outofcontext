"""Main entry point for MCP server."""

import asyncio
import logging
import sys

from hjeon139_mcp_outofcontext.config import load_config
from hjeon139_mcp_outofcontext.server import MCPServer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)

logger = logging.getLogger(__name__)


async def main() -> None:
    """Main entry point for MCP server."""
    try:
        # Load configuration
        config = load_config()

        # Set log level from config
        log_level = getattr(logging, config.log_level.upper(), logging.INFO)
        logging.getLogger().setLevel(log_level)

        logger.info("Starting MCP server...")
        logger.info(f"Storage path: {config.storage_path}")
        logger.info(f"Model: {config.model}")
        logger.info(f"Log level: {config.log_level}")

        # Create and run server
        server = MCPServer(config=config)
        await server.run()

    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.exception(f"Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
