"""Application state container for dependency injection."""

from contextlib import asynccontextmanager
from typing import Any

from .storage import MDCStorage


class AppState:
    """
    Application state container that manages component lifecycle.

    Follows FastAPI/MCP best practices:
    - NO global variables - all state is instance-scoped
    - Dependency injection - components receive dependencies via constructor
    - Components initialized in __init__ (no lazy loading)
    - Async context manager for lifecycle management
    - Testable - can create multiple AppState instances for testing
    """

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """
        Initialize application state and all components.

        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}

        # Initialize Storage Layer (MDCStorage for markdown files)
        storage_path = self.config.get("storage_path")
        self.storage = MDCStorage(storage_path=storage_path)

    @asynccontextmanager
    async def lifespan(self) -> Any:
        """
        Async context manager for lifecycle management.

        Usage:
            async with app_state.lifespan():
                # Use app_state components
                pass
        """
        try:
            yield
        finally:
            # Components don't have cleanup methods currently
            # If cleanup is needed in the future, add cleanup methods here
            pass
