"""Application state container for dependency injection."""

from contextlib import asynccontextmanager
from typing import Any

from .analysis_engine import AnalysisEngine
from .context_manager import ContextManager
from .gc_engine import GCEngine
from .storage import StorageLayer
from .tokenizer import Tokenizer


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

        # 1. Initialize Storage Layer (no dependencies)
        storage_path = self.config.get("storage_path")
        max_active_segments = self.config.get("max_active_segments", 10000)
        self.storage = StorageLayer(
            storage_path=storage_path,
            max_active_segments=max_active_segments,
        )

        # 2. Initialize Tokenizer (no dependencies)
        model = self.config.get("model", "gpt-4")
        tokenizer = Tokenizer(model=model)

        # 3. Initialize Analysis Engine (depends on tokenizer)
        self.analysis_engine = AnalysisEngine(tokenizer=tokenizer, model=model)

        # 4. Initialize GC Engine (no dependencies)
        recent_messages_count = self.config.get("recent_messages_count", 10)
        recent_decision_hours = self.config.get("recent_decision_hours", 1)
        self.gc_engine = GCEngine(
            recent_messages_count=recent_messages_count,
            recent_decision_hours=recent_decision_hours,
        )

        # 5. Initialize Context Manager (depends on all above)
        self.context_manager = ContextManager(
            storage=self.storage,
            gc_engine=self.gc_engine,
            analysis_engine=self.analysis_engine,
            tokenizer=tokenizer,
        )

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
