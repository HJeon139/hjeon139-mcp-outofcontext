"""Task management tools package."""

from ...app_state import AppState
from ...tool_registry import ToolRegistry
from .context_create_task_snapshot import handle_create_task_snapshot
from .context_get_task_context import handle_get_task_context
from .context_set_current_task import handle_set_current_task

__all__ = ["register_task_management_tools"]


def register_task_management_tools(
    registry: ToolRegistry,
    app_state: AppState,
) -> None:
    """
    Register task management tools with the tool registry.

    Args:
        registry: Tool registry instance
        app_state: Application state (for dependency injection)
    """
    # Register context_set_current_task tool
    registry.register(
        name="context_set_current_task",
        handler=handle_set_current_task,
        description=(
            "Set the active task ID for a project, updating the working set. "
            "Use this tool to switch between tasks or clear the current task. "
            "The working set will automatically update to include only segments "
            "for the new task. "
            "Example: Call with project_id='my-project', task_id='task-123' "
            "to set the current task. "
            "To clear the current task, set task_id=None. "
            "Required parameters: project_id. "
            "Optional parameter: task_id (None to clear current task)."
        ),
    )

    # Register context_get_task_context tool
    registry.register(
        name="context_get_task_context",
        handler=handle_get_task_context,
        description=(
            "Get all context segments for a specific task. "
            "Use this tool to see all segments (from all tiers) that belong "
            "to a specific task. "
            "Example: Call with project_id='my-project', task_id='task-123' "
            "to get all segments for that task. "
            "If task_id is not provided, uses the current task. "
            "Required parameters: project_id. "
            "Optional parameter: task_id (None uses current task)."
        ),
    )

    # Register context_create_task_snapshot tool
    registry.register(
        name="context_create_task_snapshot",
        handler=handle_create_task_snapshot,
        description=(
            "Create a snapshot of current task state for later retrieval. "
            "Use this tool to capture the state of a task before switching "
            "to another task or performing major context cleanup. "
            "Snapshots are stored in stashed storage with special tags. "
            "Example: Call with project_id='my-project', task_id='task-123', "
            "name='before-refactor' to create a named snapshot. "
            "Required parameters: project_id. "
            "Optional parameters: task_id (None uses current task), name (snapshot name)."
        ),
    )
