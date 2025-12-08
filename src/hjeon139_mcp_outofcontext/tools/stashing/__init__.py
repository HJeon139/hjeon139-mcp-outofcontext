"""Stashing tools package."""

from ...app_state import AppState
from ...tool_registry import ToolRegistry
from .context_list_projects import handle_list_projects
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
            "PUT CONTEXT: Move segments from active context to stashed storage by filtering. "
            "This is the primary tool for freeing up active context space. "
            "\n\n"
            "**When to use:**\n"
            "- When context usage is high (>80%) and you need to free space\n"
            "- When you want to archive old or unused segments\n"
            "- When you want to stash segments matching specific criteria\n"
            "\n"
            "**How to use:**\n"
            "- Required: project_id (scopes operation to a project, prevents context bleed)\n"
            "- Optional: query (keyword to match segment text, e.g., 'old documentation')\n"
            "- Optional: filters (metadata filters: file_path, task_id, tags, type, created_after, created_before)\n"
            "- If both query and filters are omitted, all working segments will be stashed\n"
            "\n"
            "**Examples:**\n"
            "- Stash all segments: project_id='my-project'\n"
            "- Stash by content: project_id='my-project', query='old bugs'\n"
            "- Stash by metadata: project_id='my-project', filters={'type': 'file', 'task_id': 'task-123'}\n"
            "- Stash old segments: project_id='my-project', filters={'created_before': '2024-01-01T00:00:00Z'}\n"
            "\n"
            "**Returns:** stashed_segments (IDs), tokens_stashed, segments_matched"
        ),
    )

    # Register context_list_projects tool
    registry.register(
        name="context_list_projects",
        handler=handle_list_projects,
        description=(
            "List all available project IDs from stashed storage. "
            "Use this tool to discover available projects when you don't know the project_id "
            "or need to search across multiple projects. "
            "Example: Call without parameters to get a list of all projects with stashed context. "
            "No parameters required."
        ),
    )

    # Register context_search_stashed tool
    registry.register(
        name="context_search_stashed",
        handler=handle_search_stashed,
        description=(
            "SEARCH STASHED: Search stashed segments by keyword and metadata filters (read-only). "
            "Use this tool to discover what's in stashed storage before retrieving. "
            "This is a read-only search - it doesn't move or retrieve segments. "
            "\n\n"
            "**When to use:**\n"
            "- When you want to explore what's in stashed storage\n"
            "- When you need to find segments before retrieving them\n"
            "- When you want to search across multiple projects (omit project_id)\n"
            "\n"
            "**How to use:**\n"
            "- Optional: project_id (omit to search across all projects)\n"
            "- Optional: query (keyword search in segment text)\n"
            "- Optional: filters (metadata filters: file_path, task_id, tags, type, created_after, created_before)\n"
            "- Optional: limit (max results, default: 50)\n"
            "\n"
            "**Examples:**\n"
            "- Search all projects: query='function'\n"
            "- Search in project: project_id='my-project', query='function'\n"
            "- Search with filters: project_id='my-project', filters={'file_path': 'src/main.py'}\n"
            "\n"
            "**Returns:** segments (matching segments), total_matches, query, filters_applied"
        ),
    )

    # Register context_retrieve_stashed tool
    registry.register(
        name="context_retrieve_stashed",
        handler=handle_retrieve_stashed,
        description=(
            "FETCH CONTEXT: Retrieve stashed segments by searching with query and filters. "
            "This is the primary tool for accessing previously stashed context. "
            "\n\n"
            "**When to use:**\n"
            "- When you need to access previously stashed context\n"
            "- When you want to find context by content (query) or metadata (filters)\n"
            "- When you want to restore stashed segments back to active context\n"
            "\n"
            "**How to use:**\n"
            "- Required: project_id (scopes search to a project, prevents context bleed)\n"
            "- Optional: query (keyword to match segment text, e.g., 'launch bugs')\n"
            "- Optional: filters (metadata filters: file_path, task_id, tags, type, created_after, created_before)\n"
            "- Optional: move_to_active (default: False) - if True, restores segments to active context\n"
            "- If both query and filters are omitted, all stashed segments will be retrieved\n"
            "\n"
            "**Examples:**\n"
            "- Retrieve all stashed: project_id='my-project'\n"
            "- Retrieve by content: project_id='my-project', query='launch bugs'\n"
            "- Retrieve by metadata: project_id='my-project', filters={'type': 'file', 'task_id': 'task-123'}\n"
            "- Retrieve and restore: project_id='my-project', query='important', move_to_active=True\n"
            "\n"
            "**Returns:** retrieved_segments (full details), moved_to_active (IDs if moved), segments_found"
        ),
    )
