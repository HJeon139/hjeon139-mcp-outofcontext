"""Interface for storage layer operations."""

from abc import ABC, abstractmethod

from .models import ContextSegment


class IStorageLayer(ABC):
    """Interface for storage layer operations."""

    @abstractmethod
    def store_segment(
        self,
        segment: ContextSegment,
        project_id: str,
    ) -> None:
        """Store segment in active storage."""

    @abstractmethod
    def load_segments(
        self,
        project_id: str,
    ) -> list[ContextSegment]:
        """Load all segments for a project."""

    @abstractmethod
    def stash_segment(
        self,
        segment: ContextSegment,
        project_id: str,
    ) -> None:
        """Move segment to stashed storage."""

    @abstractmethod
    def search_stashed(
        self,
        query: str,
        filters: dict,
        project_id: str,
    ) -> list[ContextSegment]:
        """Search stashed segments by keyword and metadata."""

    @abstractmethod
    def delete_segment(
        self,
        segment_id: str,
        project_id: str,
    ) -> None:
        """Delete segment from storage."""

    @abstractmethod
    def update_segment(
        self,
        segment: ContextSegment,
        project_id: str,
    ) -> None:
        """Update segment attributes in storage."""

    @abstractmethod
    def unstash_segment(
        self,
        segment: ContextSegment,
        project_id: str,
    ) -> None:
        """Move segment from stashed storage back to active storage."""
