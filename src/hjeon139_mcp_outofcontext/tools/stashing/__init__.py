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
            "**Prerequisites:**\n"
            "- Segments must exist in active/working context first\n"
            "- Use context_analyze_usage with context_descriptors to create segments, or\n"
            "- Retrieve from stashed storage using context_retrieve_stashed with move_to_active=True\n"
            "- Use context_get_working_set to see what's available to stash\n"
            "\n"
            "**When to use:**\n"
            "- When context usage is high (>80%) and you need to free space\n"
            "- When you want to archive old or unused segments\n"
            "- When you want to stash segments matching specific criteria\n"
            "\n"
            "**How to use:**\n"
            "- **Avoid project_id when possible** - the server uses the project directory by default\n"
            "- Optional: project_id (defaults to 'default' if omitted)\n"
            "- Optional: query (keyword to match segment text, e.g., 'old documentation')\n"
            "- Optional: filters (metadata filters: file_path, task_id, tags, type, created_after, created_before)\n"
            "- If both query and filters are omitted, all working segments will be stashed\n"
            "- **Note:** Only stashes segments from active/working tier (not already stashed segments)\n"
            "\n"
            "**Typical workflow:**\n"
            "1. Create context: context_analyze_usage(context_descriptors={...})\n"
            "2. Check what's available: context_get_working_set()\n"
            "3. Stash segments: context_stash(query='...')\n"
            "4. Verify: context_search_stashed(query='...')\n"
            "\n"
            "**Examples:**\n"
            "- Stash all segments: (no parameters needed - uses default project)\n"
            "- Stash by content: query='old bugs'\n"
            "- Stash by metadata: filters={'type': 'file', 'task_id': 'task-123'}\n"
            "- Stash old segments: filters={'created_before': '2024-01-01T00:00:00Z'}\n"
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
            "- Before retrieving: use this to verify segments exist before calling context_retrieve_stashed\n"
            "\n"
            "**How to use:**\n"
            "- **Avoid project_id when possible** - the server uses the project directory by default\n"
            "- Optional: project_id (omit to search across all projects, or defaults to 'default')\n"
            "- Optional: query (keyword search in segment text)\n"
            "- Optional: filters (metadata filters: file_path, task_id, tags, type, created_after, created_before)\n"
            "- Optional: limit (max results, default: 50)\n"
            "\n"
            "**Typical workflow:**\n"
            "1. Search for segments: context_search_stashed(query='...')\n"
            "2. Review results to find what you need\n"
            "3. Retrieve segments: context_retrieve_stashed(query='...', move_to_active=True)\n"
            "\n"
            "**Examples:**\n"
            "- Search all projects: query='function' (omit project_id)\n"
            "- Search default project: query='function' (project_id defaults to 'default')\n"
            "- Search with filters: filters={'file_path': 'src/main.py'}\n"
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
            "- After searching: use context_search_stashed first to find what's available\n"
            "\n"
            "**How to use:**\n"
            "- **Avoid project_id when possible** - the server uses the project directory by default\n"
            "- Optional: project_id (defaults to 'default' if omitted)\n"
            "- Optional: query (keyword to match segment text, e.g., 'launch bugs')\n"
            "- Optional: filters (metadata filters: file_path, task_id, tags, type, created_after, created_before)\n"
            "- Optional: move_to_active (default: False) - if True, restores segments to active context\n"
            "- If both query and filters are omitted, all stashed segments will be retrieved\n"
            "- **Note:** With move_to_active=True, segments are moved from stashed to active tier\n"
            "\n"
            "**Typical workflow:**\n"
            "1. Search for segments: context_search_stashed(query='...')\n"
            "2. Retrieve segments: context_retrieve_stashed(query='...')\n"
            "3. Restore to active: context_retrieve_stashed(query='...', move_to_active=True)\n"
            "4. Verify: context_get_working_set() to see restored segments\n"
            "\n"
            "**Examples:**\n"
            "- Retrieve all stashed: (no parameters needed - uses default project)\n"
            "- Retrieve by content: query='launch bugs'\n"
            "- Retrieve by metadata: filters={'type': 'file', 'task_id': 'task-123'}\n"
            "- Retrieve and restore: query='important', move_to_active=True\n"
            "\n"
            "**Returns:** retrieved_segments (full details), moved_to_active (IDs if moved), segments_found"
        ),
    )
