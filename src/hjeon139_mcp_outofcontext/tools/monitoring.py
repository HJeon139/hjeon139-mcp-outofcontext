"""Monitoring tools for context analysis and working set inspection."""

import logging
from typing import Any

from ..app_state import AppState
from ..models import (
    AnalyzeUsageParams,
    ContextDescriptors,
    GetWorkingSetParams,
    Recommendation,
    TokenUsage,
)
from ..tool_registry import ToolRegistry

logger = logging.getLogger(__name__)


async def handle_analyze_usage(  # noqa: C901
    app_state: AppState,
    context_descriptors: dict[str, Any] | None = None,
    project_id: str | None = None,
    task_id: str | None = None,
    token_limit: int | None = None,
) -> dict[str, Any]:
    """
    Analyze context usage and return metrics, health score, and recommendations.

    This tool analyzes the current context usage for a project and returns:
    - Usage metrics (token counts, segment counts, distribution)
    - Health score (0-100, higher = healthier)
    - Recommendations for context management
    - Count of pruning candidates

    Args:
        app_state: Application state with all components
        context_descriptors: Optional context descriptors from platform
        project_id: Project identifier (required)
        task_id: Optional task identifier
        token_limit: Optional token limit (default: from config, typically 1 million)

    Returns:
        Dictionary with:
        - usage_metrics: UsageMetrics
        - health_score: HealthScore
        - recommendations: List[Recommendation]
        - pruning_candidates_count: int

    Raises:
        ValueError: If project_id is missing or invalid
    """
    # Validate and parse parameters
    try:
        params = AnalyzeUsageParams(
            context_descriptors=(
                ContextDescriptors(**context_descriptors) if context_descriptors else None
            ),
            project_id=project_id or "",
            task_id=task_id,
            token_limit=token_limit,
        )
    except Exception as e:
        logger.error(f"Invalid parameters for analyze_usage: {e}")
        return {
            "error": {
                "code": "INVALID_PARAMETER",
                "message": f"Invalid parameters: {e!s}",
                "details": {"exception": str(e)},
            }
        }

    if not params.project_id:
        return {
            "error": {
                "code": "INVALID_PARAMETER",
                "message": "project_id is required",
                "details": {},
            }
        }

    try:
        # Prepare context descriptors
        # If not provided, create minimal descriptors with token_limit
        if params.context_descriptors is None:
            descriptors = ContextDescriptors(
                recent_messages=[],
                current_file=None,
                token_usage=TokenUsage(
                    current=0,
                    limit=params.token_limit or 32000,
                    usage_percent=0.0,
                ),
                segment_summaries=[],
                task_info=None,
            )
        else:
            descriptors = params.context_descriptors
            # Override token_limit if provided
            if params.token_limit is not None:
                descriptors.token_usage.limit = params.token_limit

        # Call context manager to analyze context
        analysis_result = app_state.context_manager.analyze_context(
            descriptors=descriptors,
            project_id=params.project_id,
        )

        # Get usage metrics by analyzing segments directly
        # We need to load segments to compute metrics
        all_segments = app_state.storage.load_segments(params.project_id)
        working_segments = [s for s in all_segments if s.tier == "working"]

        # Compute usage metrics
        metrics = app_state.analysis_engine.analyze_context_usage(
            working_segments, descriptors.token_usage.limit
        )

        # Get pruning candidates count using GC engine
        # Build root set from recent messages and current file
        roots: set[str] = set()
        if descriptors.recent_messages:
            # Get segment IDs from recent messages (they should be in working set)
            # For now, we'll use all segments as potential roots
            # In a real implementation, we'd track which segments correspond to messages
            pass

        # Analyze pruning candidates
        pruning_candidates = app_state.gc_engine.analyze_pruning_candidates(working_segments, roots)
        pruning_candidates_count = len(pruning_candidates)

        # Convert recommendations from strings to Recommendation objects
        recommendations: list[Recommendation] = []
        # The analysis_result.recommendations are strings, but we need Recommendation objects
        # We'll regenerate them from metrics to get full Recommendation objects
        recommendation_objects = app_state.analysis_engine.generate_recommendations(metrics)
        recommendations = recommendation_objects

        # Generate threshold-based warnings and suggested actions
        warnings: list[str] = []
        suggested_actions: list[dict[str, Any]] = []
        impact_summary: dict[str, Any] = {}

        usage_percent = metrics.usage_percent
        if usage_percent >= 90.0:
            warnings.append(
                "URGENT: Context usage at 90%+ - prune immediately to avoid hitting limits"
            )
            suggested_actions.append(
                {
                    "tool": "context_gc_prune",
                    "description": "Prune old segments immediately",
                    "estimated_tokens_freed": metrics.total_tokens * 0.3,  # Rough estimate
                }
            )
        elif usage_percent >= 80.0:
            warnings.append("HIGH: Context usage at 80%+ - consider pruning to free space")
            suggested_actions.append(
                {
                    "tool": "context_gc_analyze",
                    "description": "Analyze pruning candidates",
                    "estimated_tokens_freed": metrics.total_tokens * 0.2,  # Rough estimate
                }
            )
            suggested_actions.append(
                {
                    "tool": "context_stash",
                    "description": "Stash old segments to free space",
                    "estimated_tokens_freed": metrics.total_tokens * 0.15,  # Rough estimate
                }
            )
        elif usage_percent >= 60.0:
            warnings.append(
                "WARNING: Context usage at 60%+ - monitor closely and consider stashing old segments"
            )
            suggested_actions.append(
                {
                    "tool": "context_stash",
                    "description": "Stash old segments to free space",
                    "estimated_tokens_freed": metrics.total_tokens * 0.1,  # Rough estimate
                }
            )

        # Calculate impact summary if pruning candidates exist
        if pruning_candidates_count > 0:
            # Estimate tokens that could be freed (rough calculation)
            avg_tokens_per_segment = (
                metrics.total_tokens / metrics.total_segments if metrics.total_segments > 0 else 0
            )
            estimated_tokens_freed = pruning_candidates_count * avg_tokens_per_segment
            estimated_usage_after = max(
                0.0,
                usage_percent - (estimated_tokens_freed / descriptors.token_usage.limit * 100.0),
            )
            impact_summary = {
                "pruning_candidates_count": pruning_candidates_count,
                "estimated_tokens_freed": int(estimated_tokens_freed),
                "estimated_usage_after_pruning": round(estimated_usage_after, 1),
            }

        # Format response
        return {
            "usage_metrics": metrics.model_dump(),
            "health_score": analysis_result.health_score.model_dump(),
            "recommendations": [rec.model_dump() for rec in recommendations],
            "warnings": warnings,
            "suggested_actions": suggested_actions,
            "impact_summary": impact_summary,
            "pruning_candidates_count": pruning_candidates_count,
        }
    except ValueError as e:
        logger.error(f"Value error in analyze_usage: {e}")
        return {
            "error": {
                "code": "INVALID_PARAMETER",
                "message": str(e),
                "details": {},
            }
        }
    except Exception as e:
        logger.error(f"Unexpected error in analyze_usage: {e}", exc_info=True)
        return {
            "error": {
                "code": "INTERNAL_ERROR",
                "message": f"Internal error: {e!s}",
                "details": {"exception": str(e)},
            }
        }


async def handle_get_working_set(
    app_state: AppState,
    project_id: str | None = None,
    task_id: str | None = None,
) -> dict[str, Any]:
    """
    Get current working set segments for the active task.

    This tool returns the current working set of context segments for a project
    and optionally a specific task. The working set contains all active segments
    that are currently in use.

    Args:
        app_state: Application state with all components
        project_id: Project identifier (required)
        task_id: Optional task identifier (uses current task if not provided)

    Returns:
        Dictionary with:
        - working_set: WorkingSet
        - segments: List[ContextSegment]
        - total_tokens: int
        - segment_count: int

    Raises:
        ValueError: If project_id is missing or invalid
    """
    # Validate and parse parameters
    try:
        params = GetWorkingSetParams(
            project_id=project_id or "",
            task_id=task_id,
        )
    except Exception as e:
        logger.error(f"Invalid parameters for get_working_set: {e}")
        return {
            "error": {
                "code": "INVALID_PARAMETER",
                "message": f"Invalid parameters: {e!s}",
                "details": {"exception": str(e)},
            }
        }

    if not params.project_id:
        return {
            "error": {
                "code": "INVALID_PARAMETER",
                "message": "project_id is required",
                "details": {},
            }
        }

    try:
        # Call context manager to get working set
        working_set = app_state.context_manager.get_working_set(
            project_id=params.project_id,
            task_id=params.task_id,
        )

        # Format response
        return {
            "working_set": {
                "project_id": working_set.project_id,
                "task_id": working_set.task_id,
                "total_tokens": working_set.total_tokens,
                "last_updated": working_set.last_updated.isoformat(),
            },
            "segments": [segment.model_dump() for segment in working_set.segments],
            "total_tokens": working_set.total_tokens,
            "segment_count": len(working_set.segments),
        }
    except ValueError as e:
        logger.error(f"Value error in get_working_set: {e}")
        return {
            "error": {
                "code": "INVALID_PARAMETER",
                "message": str(e),
                "details": {},
            }
        }
    except Exception as e:
        logger.error(f"Unexpected error in get_working_set: {e}", exc_info=True)
        return {
            "error": {
                "code": "INTERNAL_ERROR",
                "message": f"Internal error: {e!s}",
                "details": {"exception": str(e)},
            }
        }


def register_monitoring_tools(
    registry: ToolRegistry,
    app_state: AppState,
) -> None:
    """
    Register monitoring tools with the tool registry.

    Args:
        registry: Tool registry instance
        app_state: Application state (for dependency injection)
    """
    # Register context_analyze_usage tool
    registry.register(
        name="context_analyze_usage",
        handler=handle_analyze_usage,
        description=(
            "Analyze current context usage and return metrics, health score, and recommendations. "
            "Use this tool to understand how much context is being used, the health of the context, "
            "and get recommendations for context management. "
            "Warnings are provided when usage crosses thresholds: 60% (warning), 80% (high), 90% (urgent). "
            "Check usage periodically, especially when context grows. "
            "Example: Call with project_id='my-project' to analyze context usage. "
            "If usage > 60%, consider stashing/pruning. "
            "Optional parameters: context_descriptors (from platform), task_id, token_limit."
        ),
    )

    # Register context_get_working_set tool
    registry.register(
        name="context_get_working_set",
        handler=handle_get_working_set,
        description=(
            "Get current working set segments for the active task. "
            "Use this tool to see what segments are currently active in the working set. "
            "Example: Call with project_id='my-project' to get working set for current task. "
            "Optional parameter: task_id (to get working set for specific task)."
        ),
    )
