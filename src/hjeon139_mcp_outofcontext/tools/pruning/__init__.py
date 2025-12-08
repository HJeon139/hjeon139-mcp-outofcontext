"""Pruning tools package."""

from ...app_state import AppState
from ...tool_registry import ToolRegistry
from .gc_analyze import handle_gc_analyze
from .gc_pin import handle_gc_pin
from .gc_prune import handle_gc_prune
from .gc_unpin import handle_gc_unpin

__all__ = ["register_pruning_tools"]


def register_pruning_tools(
    registry: ToolRegistry,
    app_state: AppState,
) -> None:
    """
    Register pruning tools with the tool registry.

    Args:
        registry: Tool registry instance
        app_state: Application state (for dependency injection)
    """
    # Register context_gc_analyze tool
    registry.register(
        name="context_gc_analyze",
        handler=handle_gc_analyze,
        description=(
            "Analyze context and identify pruning candidates using GC heuristics. "
            "Use this tool to see which segments are candidates for pruning based on "
            "age, reachability, type, and other factors. "
            "Optionally provide target_tokens to generate a pruning plan. "
            "Example: Call with project_id='my-project' to analyze pruning candidates. "
            "Optional parameters: context_descriptors, task_id, target_tokens."
        ),
    )

    # Register context_gc_prune tool
    registry.register(
        name="context_gc_prune",
        handler=handle_gc_prune,
        description=(
            "Execute pruning plan to free context space. "
            "Use this tool to stash or delete segments identified as pruning candidates. "
            "Pinned segments cannot be pruned. Delete actions require confirm=True. "
            "Example: Call with project_id='my-project', segment_ids=['seg1', 'seg2'], "
            "action='stash' to stash segments. "
            "Required parameters: project_id, segment_ids, action ('stash' or 'delete'). "
            "Optional parameter: confirm (must be True for delete actions)."
        ),
    )

    # Register context_gc_pin tool
    registry.register(
        name="context_gc_pin",
        handler=handle_gc_pin,
        description=(
            "Pin segments to protect them from pruning. "
            "Pinned segments will not be pruned by the GC engine. "
            "Use this tool to protect important segments from being removed. "
            "Example: Call with project_id='my-project', segment_ids=['seg1', 'seg2'] "
            "to pin segments. "
            "Required parameters: project_id, segment_ids."
        ),
    )

    # Register context_gc_unpin tool
    registry.register(
        name="context_gc_unpin",
        handler=handle_gc_unpin,
        description=(
            "Unpin segments to allow pruning. "
            "Unpinned segments can be pruned by the GC engine. "
            "Use this tool to allow previously pinned segments to be removed. "
            "Example: Call with project_id='my-project', segment_ids=['seg1', 'seg2'] "
            "to unpin segments. "
            "Required parameters: project_id, segment_ids."
        ),
    )
