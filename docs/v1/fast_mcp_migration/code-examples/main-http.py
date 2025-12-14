"""Development entry point with HTTP transport and auto-reload.

Reference implementation for Phase 4 migration.
"""

import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI

from hjeon139_mcp_outofcontext.config import load_config
from hjeon139_mcp_outofcontext.fastmcp_server import mcp, initialize_app_state

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def app_lifespan(app: FastAPI):
    """Manage application lifespan with FastAPI."""
    # Startup: Initialize AppState
    config = load_config()
    initialize_app_state(config)

    logger.info("Starting FastMCP server (HTTP mode)...")
    logger.info(f"Storage path: {config.storage_path}")

    try:
        yield
    finally:
        # Shutdown: Cleanup resources if needed
        logger.info("Shutting down FastMCP server...")


# Create FastAPI app with lifespan
app = FastAPI(lifespan=app_lifespan)

# Create FastMCP HTTP app
mcp_app = mcp.http_app()

# Mount the MCP app
app.mount("/mcp", mcp_app)

if __name__ == "__main__":
    import uvicorn
    # Run with auto-reload for development
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)
