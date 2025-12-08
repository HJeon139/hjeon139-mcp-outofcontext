"""Interface for Context Manager operations."""

from abc import ABC, abstractmethod

from ..models import (
    AnalysisResult,
    ContextDescriptors,
    ContextSegment,
    StashResult,
    WorkingSet,
)


class IContextManager(ABC):
    """Interface for Context Manager operations.

    Note: This is not a Python context manager (does not implement
    __enter__/__exit__). It manages conversation/working context for the
    MCP server, not Python context protocol.
    """

    @abstractmethod
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

    @abstractmethod
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

    @abstractmethod
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

    @abstractmethod
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
