"""Segment CRUD operations for storage layer."""

import logging
from typing import TYPE_CHECKING

from ..models import ContextSegment

if TYPE_CHECKING:
    from ..lru_segment_cache import LRUSegmentCache
    from .file_operations import FileOperations
    from .indexing import IndexingOperations

logger = logging.getLogger(__name__)


class SegmentOperations:
    """Segment CRUD operations for storage layer."""

    def __init__(
        self,
        active_segments: "LRUSegmentCache",
        active_segment_ids: dict[str, set[str]],
        file_ops: "FileOperations",
        indexing_ops: "IndexingOperations",
    ) -> None:
        """Initialize segment operations.

        Args:
            active_segments: LRU cache for active segments
            active_segment_ids: Dictionary tracking active segment IDs by project
            file_ops: FileOperations instance
            indexing_ops: IndexingOperations instance
        """
        self.active_segments = active_segments
        self.active_segment_ids = active_segment_ids
        self.file_ops = file_ops
        self.indexing_ops = indexing_ops

    def store_segment(self, segment: ContextSegment, project_id: str) -> None:
        """Store segment in active storage."""
        # Use LRU cache for active segments
        self.active_segments.put(segment.segment_id, segment)

        # Track active segment IDs by project
        if project_id not in self.active_segment_ids:
            self.active_segment_ids[project_id] = set()
        self.active_segment_ids[project_id].add(segment.segment_id)

    def load_segments(self, project_id: str) -> list[ContextSegment]:
        """Load all segments for a project."""
        segments: list[ContextSegment] = []

        # Load active segments from LRU cache
        active_ids = self.active_segment_ids.get(project_id, set())
        for segment_id in active_ids:
            segment = self.active_segments.get(segment_id)
            if segment:
                segments.append(segment)

        # Load stashed segments
        stashed = self.file_ops.load_stashed_segments(project_id)
        segments.extend(stashed)

        return segments

    def stash_segment(self, segment: ContextSegment, project_id: str) -> None:
        """Move segment to stashed storage."""
        # Remove from active storage if present
        self.active_segments.remove(segment.segment_id)

        # Remove from active tracking
        if project_id in self.active_segment_ids:
            self.active_segment_ids[project_id].discard(segment.segment_id)

        # Update segment tier
        segment.tier = "stashed"

        # Get project-specific file path
        file_path = self.file_ops.get_stashed_file_path(project_id)

        # Load existing stashed segments
        stashed = self.file_ops.load_stashed_file(file_path)

        # Remove segment if it already exists (update case)
        stashed = [s for s in stashed if s.get("segment_id") != segment.segment_id]

        # Add segment
        segment_dict = segment.model_dump(mode="json")
        stashed.append(segment_dict)

        # Save to sharded file
        self.file_ops.save_stashed_file(file_path, stashed)

        # Update indexes
        self.indexing_ops.update_metadata_indexes(segment, project_id, add=True)

        # Update keyword index
        keyword_index = self.indexing_ops.keyword_index
        from ..inverted_index import InvertedIndex

        if project_id not in keyword_index:
            keyword_index[project_id] = InvertedIndex()
        keyword_index[project_id].add_segment(segment.segment_id, segment.text)

    def search_stashed(
        self,
        query: str,
        filters: dict,
        project_id: str,
    ) -> list[ContextSegment]:
        """Search stashed segments by keyword and metadata using indexes."""
        # Start with all stashed segment IDs for this project
        candidate_ids: set[str] | None = None

        # Use keyword index for query
        keyword_index = self.indexing_ops.keyword_index
        if query and project_id in keyword_index:
            candidate_ids = keyword_index[project_id].search(query)
        else:
            # No query or no index: get all stashed segment IDs
            candidate_ids = self.file_ops.get_all_stashed_ids(project_id)

        # Apply metadata filters using hash maps
        if filters:
            candidate_ids = self.indexing_ops.apply_metadata_filters(
                candidate_ids, filters, project_id
            )

        # Load only matching segments
        segments: list[ContextSegment] = []
        for seg_id in candidate_ids:
            segment = self.file_ops.load_stashed_segment(seg_id, project_id)
            if segment:
                segments.append(segment)

        return segments

    def delete_segment(self, segment_id: str, project_id: str) -> None:
        """Delete segment from storage."""
        # Remove from active storage
        self.active_segments.remove(segment_id)

        # Remove from active tracking
        if project_id in self.active_segment_ids:
            self.active_segment_ids[project_id].discard(segment_id)

        # Load stashed file
        file_path = self.file_ops.get_stashed_file_path(project_id)
        stashed = self.file_ops.load_stashed_file(file_path)

        # Find and remove segment
        removed_segment = None
        for seg_dict in stashed:
            if seg_dict.get("segment_id") == segment_id:
                removed_segment = seg_dict
                break

        if removed_segment:
            # Remove from list
            stashed = [s for s in stashed if s.get("segment_id") != segment_id]

            # Save updated file
            self.file_ops.save_stashed_file(file_path, stashed)

            # Update indexes (remove)
            try:
                segment = ContextSegment.model_validate(removed_segment)
                self.indexing_ops.update_metadata_indexes(segment, project_id, add=False)

                # Remove from keyword index
                keyword_index = self.indexing_ops.keyword_index
                if project_id in keyword_index:
                    keyword_index[project_id].remove_segment(segment_id)
            except Exception as e:
                logger.warning(f"Failed to deserialize segment for index update: {e}")

    def update_segment(self, segment: ContextSegment, project_id: str) -> None:
        """Update segment attributes in storage."""
        segment_id = segment.segment_id

        # Check if segment is in active storage
        existing_active = self.active_segments.get(segment_id)
        if existing_active:
            # Update in active storage
            self.active_segments.put(segment_id, segment)
            return

        # Check if segment is in stashed storage
        file_path = self.file_ops.get_stashed_file_path(project_id)
        stashed = self.file_ops.load_stashed_file(file_path)

        # Find and update segment in stashed storage
        old_segment_dict = None
        updated = False
        for i, seg_dict in enumerate(stashed):
            if seg_dict.get("segment_id") == segment_id:
                # Save old segment for index update
                old_segment_dict = seg_dict
                # Update the segment
                stashed[i] = segment.model_dump(mode="json")
                updated = True
                break

        if updated:
            # Save updated file
            self.file_ops.save_stashed_file(file_path, stashed)

            # Rebuild indexes for this segment
            # Remove old indexes
            if old_segment_dict:
                try:
                    old_segment = ContextSegment.model_validate(old_segment_dict)
                    self.indexing_ops.update_metadata_indexes(old_segment, project_id, add=False)
                except Exception as e:
                    logger.warning(f"Failed to deserialize old segment for index update: {e}")

            # Add new indexes
            self.indexing_ops.update_metadata_indexes(segment, project_id, add=True)
        else:
            logger.warning(f"Segment {segment_id} not found for update in project {project_id}")
