"""Context Manager implementation that orchestrates all context operations."""

import logging
from datetime import UTC, datetime
from typing import Any

from ..analysis_engine import IAnalysisEngine
from ..gc_engine import IGCEngine
from ..models import (
    AnalysisResult,
    ContextDescriptors,
    ContextSegment,
    StashResult,
    WorkingSet,
)
from ..storage import IStorageLayer
from ..tokenizer import Tokenizer
from .interface import IContextManager

logger = logging.getLogger(__name__)


class ContextManager(IContextManager):
    """Context Manager implementation that orchestrates all context operations.

    Note: This class manages conversation/working context (segments,
    working sets) for the MCP server, not Python context managers. It
    does not implement the context manager protocol (__enter__/__exit__).
    """

    def __init__(
        self,
        storage: IStorageLayer,
        gc_engine: IGCEngine,
        analysis_engine: IAnalysisEngine,
        tokenizer: Tokenizer | None = None,
    ) -> None:
        """Initialize Context Manager.

        Args:
            storage: Storage layer instance
            gc_engine: GC engine instance
            analysis_engine: Analysis engine instance
            tokenizer: Tokenizer instance (creates new one if None)
        """
        self.storage = storage
        self.gc_engine = gc_engine
        self.analysis_engine = analysis_engine
        self.tokenizer = tokenizer if tokenizer is not None else Tokenizer()

        # Project/task scoping state
        self.current_tasks: dict[str, str | None] = {}  # project_id -> task_id
        self.working_sets: dict[
            str, dict[str | None, WorkingSet]
        ] = {}  # project_id -> task_id -> working_set

    def analyze_context(
        self,
        descriptors: ContextDescriptors,
        project_id: str,
    ) -> AnalysisResult:
        """Analyze context and return usage metrics.

        Args:
            descriptors: Context descriptors from platform
            project_id: Project identifier

        Returns:
            Analysis result with metrics and recommendations
        """
        # Validate project_id
        if not project_id:
            raise ValueError("project_id cannot be empty")

        # Convert descriptors to segments
        new_segments = self._convert_descriptors_to_segments(descriptors, project_id)

        # Store new segments
        for segment in new_segments:
            self.storage.store_segment(segment, project_id)

        # Load all segments for the project (including newly stored ones)
        all_segments = self.storage.load_segments(project_id)

        # Filter to only working tier segments for analysis
        working_segments = [s for s in all_segments if s.tier == "working"]

        # Get token limit from descriptors
        token_limit = descriptors.token_usage.limit

        # Compute metrics using analysis engine
        metrics = self.analysis_engine.analyze_context_usage(working_segments, token_limit)

        # Compute health score
        health_score = self.analysis_engine.compute_health_score(working_segments, token_limit)

        # Generate recommendations
        recommendations_list = self.analysis_engine.generate_recommendations(metrics)
        recommendation_messages = [rec.message for rec in recommendations_list]

        # Update current task if provided
        if descriptors.task_info:
            self.current_tasks[project_id] = descriptors.task_info.task_id

        # Update working set
        self._update_working_set(
            project_id, descriptors.task_info.task_id if descriptors.task_info else None
        )

        return AnalysisResult(
            total_tokens=metrics.total_tokens,
            segment_count=metrics.total_segments,
            usage_percent=metrics.usage_percent,
            health_score=health_score,
            recommendations=recommendation_messages,
        )

    def get_working_set(
        self,
        project_id: str,
        task_id: str | None = None,
    ) -> WorkingSet:
        """Get current working set segments.

        Args:
            project_id: Project identifier
            task_id: Optional task identifier

        Returns:
            Working set with active segments
        """
        # Validate project_id
        if not project_id:
            raise ValueError("project_id cannot be empty")

        # Use provided task_id or current task for project
        effective_task_id = task_id if task_id is not None else self.current_tasks.get(project_id)

        # Check if we have a cached working set
        if project_id in self.working_sets and effective_task_id in self.working_sets[project_id]:
            return self.working_sets[project_id][effective_task_id]

        # Build working set from storage
        all_segments = self.storage.load_segments(project_id)

        # Filter to working tier segments
        working_segments = [s for s in all_segments if s.tier == "working"]

        # Filter by task if specified
        if effective_task_id:
            working_segments = [s for s in working_segments if s.task_id == effective_task_id]

        # Sort by last_touched_at (most recent first)
        working_segments.sort(key=lambda s: s.last_touched_at, reverse=True)

        # Calculate total tokens (handle None values)
        total_tokens = sum(
            segment.tokens if segment.tokens is not None else 0 for segment in working_segments
        )

        # Create working set
        working_set = WorkingSet(
            segments=working_segments,
            total_tokens=total_tokens,
            project_id=project_id,
            task_id=effective_task_id,
            last_updated=datetime.now(UTC).replace(tzinfo=None),
        )

        # Cache working set
        if project_id not in self.working_sets:
            self.working_sets[project_id] = {}
        self.working_sets[project_id][effective_task_id] = working_set

        return working_set

    def stash_segments(
        self,
        segment_ids: list[str],
        project_id: str,
    ) -> StashResult:
        """Move segments to stashed storage.

        Args:
            segment_ids: List of segment IDs to stash
            project_id: Project identifier

        Returns:
            Stash result with stashed segment IDs and tokens freed
        """
        # Validate inputs
        if not project_id:
            raise ValueError("project_id cannot be empty")
        if not segment_ids:
            return StashResult(stashed_segments=[], tokens_freed=0, stash_location=None)

        # Load all segments to find the ones to stash
        all_segments = self.storage.load_segments(project_id)

        # Find segments to stash (only from working tier)
        segments_to_stash: list[ContextSegment] = []
        for segment in all_segments:
            if segment.segment_id in segment_ids and segment.tier == "working":
                segments_to_stash.append(segment)

        # Validate all segments were found
        found_ids = {s.segment_id for s in segments_to_stash}
        missing_ids = set(segment_ids) - found_ids
        if missing_ids:
            logger.warning(f"Some segments not found or not in working tier: {missing_ids}")

        # Atomic operation: stash all or none
        # For now, we'll stash all found segments (partial success is acceptable)
        stashed_ids: list[str] = []
        total_tokens_freed = 0

        try:
            for segment in segments_to_stash:
                # Stash the segment
                self.storage.stash_segment(segment, project_id)
                stashed_ids.append(segment.segment_id)
                # Handle None tokens (use 0 as default)
                tokens = segment.tokens if segment.tokens is not None else 0
                total_tokens_freed += tokens
        except Exception as e:
            logger.error(f"Error during stash operation: {e}")
            # In a real implementation, we might want to rollback
            # For now, we'll return what we successfully stashed
            raise

        # Invalidate working set cache for this project
        if project_id in self.working_sets:
            self.working_sets[project_id].clear()

        return StashResult(
            stashed_segments=stashed_ids,
            tokens_freed=total_tokens_freed,
            stash_location=None,  # Storage layer handles location internally
        )

    def retrieve_stashed(
        self,
        query: str,
        filters: dict,
        project_id: str,
    ) -> list[ContextSegment]:
        """Retrieve stashed segments by keyword/metadata search.

        Args:
            query: Search query string
            filters: Metadata filters (task_id, file_path, tag, type)
            project_id: Project identifier

        Returns:
            List of matching stashed segments
        """
        # Validate project_id
        if not project_id:
            raise ValueError("project_id cannot be empty")

        # Use storage layer to search stashed segments
        segments = self.storage.search_stashed(query, filters, project_id)

        return segments

    def _convert_descriptors_to_segments(
        self,
        descriptors: ContextDescriptors,
        project_id: str,
    ) -> list[ContextSegment]:
        """Convert context descriptors to context segments.

        Args:
            descriptors: Context descriptors from platform
            project_id: Project identifier

        Returns:
            List of context segments
        """
        segments: list[ContextSegment] = []

        now = datetime.now(UTC).replace(tzinfo=None)  # Use UTC, then make naive

        # Convert recent messages to segments
        for i, message in enumerate(descriptors.recent_messages):
            segment_id = f"msg-{project_id}-{now.timestamp()}-{i}"
            text = f"{message.role}: {message.content}"
            tokens = self.tokenizer.count_tokens(text)

            segment = ContextSegment(
                segment_id=segment_id,
                text=text,
                type="message",
                project_id=project_id,
                task_id=descriptors.task_info.task_id if descriptors.task_info else None,
                created_at=message.timestamp if message.timestamp else now,
                last_touched_at=message.timestamp if message.timestamp else now,
                pinned=False,
                generation="young",
                gc_survival_count=0,
                refcount=0,
                file_path=None,
                line_range=None,
                tags=[],
                topic_id=None,
                tokens=tokens,
                tokens_computed_at=None,
                text_hash=None,
                tier="working",
            )
            segments.append(segment)

        # Convert current file to segment if provided
        if descriptors.current_file:
            file_path = descriptors.current_file.path
            segment_id = f"file-{project_id}-{now.timestamp()}"
            # For file segments, we'd typically load the file content
            # For now, we'll create a placeholder segment
            text = f"File: {file_path}"
            if descriptors.current_file.current_line:
                text += f" (line {descriptors.current_file.current_line})"
            tokens = self.tokenizer.count_tokens(text)

            segment = ContextSegment(
                segment_id=segment_id,
                text=text,
                type="code",
                project_id=project_id,
                task_id=descriptors.task_info.task_id if descriptors.task_info else None,
                created_at=now,
                last_touched_at=now,
                pinned=False,
                generation="young",
                gc_survival_count=0,
                refcount=0,
                file_path=file_path,
                line_range=(
                    (descriptors.current_file.current_line, descriptors.current_file.current_line)
                    if descriptors.current_file.current_line
                    else None
                ),
                tags=[],
                topic_id=None,
                tokens=tokens,
                tokens_computed_at=None,
                text_hash=None,
                tier="working",
            )
            segments.append(segment)

        # Convert segment summaries to segments (if they don't already exist)
        # Note: In a real implementation, we might check if these segments already exist
        # For now, we'll create placeholder segments from summaries
        for summary in descriptors.segment_summaries:
            # Check if segment already exists (by ID)
            # For now, we'll skip if it's a summary (might already exist)
            # In practice, summaries might represent existing segments
            if summary.type == "summary":
                continue

            # Create segment from summary
            # Normalize datetime to timezone-naive for consistency
            created_at = summary.created_at
            if created_at.tzinfo is not None:
                created_at = created_at.replace(tzinfo=None)

            segment = ContextSegment(
                segment_id=summary.segment_id,
                text=summary.preview,
                type=summary.type,
                project_id=project_id,
                task_id=descriptors.task_info.task_id if descriptors.task_info else None,
                created_at=created_at,
                last_touched_at=created_at,
                pinned=False,
                generation="young",
                gc_survival_count=0,
                refcount=0,
                file_path=None,
                line_range=None,
                tags=[],
                topic_id=None,
                tokens=summary.tokens,
                tokens_computed_at=None,
                text_hash=None,
                tier="working",
            )
            segments.append(segment)

        return segments

    def _update_working_set(
        self,
        project_id: str,
        task_id: str | None,
    ) -> None:
        """Update working set cache for a project/task.

        Args:
            project_id: Project identifier
            task_id: Optional task identifier
        """
        # Invalidate cache - will be rebuilt on next get_working_set call
        if project_id in self.working_sets:
            # Clear all task caches for this project
            # In a more sophisticated implementation, we might only clear the specific task
            self.working_sets[project_id].clear()

    def set_current_task(
        self,
        project_id: str,
        task_id: str | None,
    ) -> dict[str, Any]:
        """Set the active task ID for a project, updating the working set.

        Args:
            project_id: Project identifier
            task_id: Optional task identifier (None to clear current task)

        Returns:
            Dictionary with:
            - previous_task_id: Optional[str]
            - current_task_id: Optional[str]
            - working_set_updated: bool
        """
        # Validate project_id
        if not project_id:
            raise ValueError("project_id cannot be empty")

        # Get previous task ID
        previous_task_id = self.current_tasks.get(project_id)

        # Update current task
        if task_id is None:
            # Clear current task
            if project_id in self.current_tasks:
                del self.current_tasks[project_id]
        else:
            self.current_tasks[project_id] = task_id

        # Recompute working set for new task
        self._update_working_set(project_id, task_id)

        # Get the new working set to verify it was updated
        try:
            self.get_working_set(project_id, task_id)
            working_set_updated = True
        except Exception:
            working_set_updated = False

        return {
            "previous_task_id": previous_task_id,
            "current_task_id": task_id,
            "working_set_updated": working_set_updated,
        }

    def get_task_context(
        self,
        project_id: str,
        task_id: str | None = None,
    ) -> dict[str, Any]:
        """Get all context segments for a specific task.

        Args:
            project_id: Project identifier
            task_id: Optional task identifier (None uses current task)

        Returns:
            Dictionary with:
            - task_id: str
            - segments: List[ContextSegment]
            - total_tokens: int
            - segment_count: int
            - active: bool (Is this the current task?)
        """
        # Validate project_id
        if not project_id:
            raise ValueError("project_id cannot be empty")

        # Get effective task_id (from param or current task)
        effective_task_id = task_id if task_id is not None else self.current_tasks.get(project_id)

        if effective_task_id is None:
            # No task specified and no current task
            return {
                "task_id": None,
                "segments": [],
                "total_tokens": 0,
                "segment_count": 0,
                "active": False,
            }

        # Load all segments for the project
        all_segments = self.storage.load_segments(project_id)

        # Filter to segments with this task_id (from any tier)
        task_segments = [s for s in all_segments if s.task_id == effective_task_id]

        # Calculate total tokens
        total_tokens = sum(
            segment.tokens if segment.tokens is not None else 0 for segment in task_segments
        )

        # Check if this is the current task
        is_active = self.current_tasks.get(project_id) == effective_task_id

        return {
            "task_id": effective_task_id,
            "segments": task_segments,
            "total_tokens": total_tokens,
            "segment_count": len(task_segments),
            "active": is_active,
        }

    def create_task_snapshot(
        self,
        project_id: str,
        task_id: str | None = None,
        name: str | None = None,
    ) -> dict[str, Any]:
        """Create a snapshot of current task state for later retrieval.

        Args:
            project_id: Project identifier
            task_id: Optional task identifier (None uses current task)
            name: Optional snapshot name

        Returns:
            Dictionary with:
            - snapshot_id: str
            - task_id: str
            - segments_captured: int
            - tokens_captured: int
            - created_at: str (ISO datetime)
        """
        # Validate project_id
        if not project_id:
            raise ValueError("project_id cannot be empty")

        # Get effective task_id (from param or current task)
        effective_task_id = task_id if task_id is not None else self.current_tasks.get(project_id)

        if effective_task_id is None:
            raise ValueError("No task specified and no current task set")

        # Get current task segments
        task_context = self.get_task_context(project_id, effective_task_id)
        task_segments = task_context["segments"]

        # Create snapshot ID
        now = datetime.now(UTC).replace(tzinfo=None)  # Use UTC, then make naive
        snapshot_id = f"snapshot-{project_id}-{effective_task_id}-{now.timestamp()}"

        # Create snapshot segments by copying task segments and adding snapshot tag
        snapshot_segments: list[ContextSegment] = []
        for segment in task_segments:
            # Create a copy of the segment with snapshot tag
            snapshot_segment = ContextSegment(
                segment_id=f"{segment.segment_id}-{snapshot_id}",
                text=segment.text,
                type=segment.type,
                project_id=segment.project_id,
                task_id=segment.task_id,
                created_at=segment.created_at,
                last_touched_at=now,
                pinned=segment.pinned,
                generation=segment.generation,
                gc_survival_count=segment.gc_survival_count,
                refcount=segment.refcount,
                file_path=segment.file_path,
                line_range=segment.line_range,
                tags=segment.tags + ["snapshot", snapshot_id] + ([name] if name else []),
                topic_id=segment.topic_id,
                tokens=segment.tokens,
                tokens_computed_at=segment.tokens_computed_at,
                text_hash=segment.text_hash,
                tier="stashed",  # Snapshots are stored in stashed tier
            )
            snapshot_segments.append(snapshot_segment)

        # Store snapshot segments (as stashed with snapshot tag)
        for segment in snapshot_segments:
            self.storage.stash_segment(segment, project_id)

        # Calculate captured metrics
        segments_captured = len(snapshot_segments)
        tokens_captured = sum(
            segment.tokens if segment.tokens is not None else 0 for segment in snapshot_segments
        )

        return {
            "snapshot_id": snapshot_id,
            "task_id": effective_task_id,
            "segments_captured": segments_captured,
            "tokens_captured": tokens_captured,
            "created_at": now.isoformat(),
        }
