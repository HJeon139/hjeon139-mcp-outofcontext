"""Stashing tools package."""

from ...app_state import AppState
from ...tool_registry import ToolRegistry
from .context_retrieve_stashed import handle_retrieve_stashed
from .context_search_stashed import handle_search_stashed
from .context_stash import handle_stash

__all__ = ["register_stashing_tools"]


def register_stashing_tools(
    registry: ToolRegistry,
    app_state: AppState,
) -> None:
    """
    Register stashing tools with the tool registry.

    Args:
        registry: Tool registry instance
        app_state: Application state (for dependency injection)
    """
    # Register context_stash tool
    registry.register(
        name="context_stash",
        handler=handle_stash,
        description=(
            "Move segments from active context to stashed storage. "
            "Use this tool to stash segments that are no longer needed in active context. "
            "Stashed segments can be searched and retrieved later. "
            "Example: Call with project_id='my-project', segment_ids=['seg1', 'seg2'] "
            "to stash segments. "
            "Required parameters: project_id, segment_ids."
        ),
    )

    # Register context_search_stashed tool
    registry.register(
        name="context_search_stashed",
        handler=handle_search_stashed,
        description=(
            "Search stashed segments by keyword and metadata filters. "
            "Use this tool to find stashed segments using keyword search and/or metadata filters. "
            "Supports filtering by file_path, task_id, tags, type, and time range. "
            "Example: Call with project_id='my-project', query='function', "
            "filters={'file_path': 'src/main.py'} to search for segments. "
            "Required parameters: project_id. "
            "Optional parameters: query (keyword search), filters (metadata filters), limit (max results)."
        ),
    )

    # Register context_retrieve_stashed tool
    registry.register(
        name="context_retrieve_stashed",
        handler=handle_retrieve_stashed,
        description=(
            "Retrieve specific stashed segments by ID and optionally move back to active. "
            "Use this tool to retrieve stashed segments by their IDs. "
            "Optionally move them back to active storage with move_to_active=True. "
            "Example: Call with project_id='my-project', segment_ids=['seg1', 'seg2'], "
            "move_to_active=True to retrieve and move segments back to active. "
            "Required parameters: project_id, segment_ids. "
            "Optional parameter: move_to_active (default: False)."
        ),
    )
