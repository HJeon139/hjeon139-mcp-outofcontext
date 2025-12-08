"""Indexing operations for storage layer."""

import logging
from pathlib import Path

from ..inverted_index import InvertedIndex
from ..models import ContextSegment

logger = logging.getLogger(__name__)


class IndexingOperations:
    """Indexing operations for storage layer."""

    def __init__(
        self,
        keyword_index: dict[str, InvertedIndex],
        metadata_indexes: dict[str, dict[str, dict[str, set[str]]]],
    ) -> None:
        """Initialize indexing operations.

        Args:
            keyword_index: Keyword index dictionary
            metadata_indexes: Metadata indexes dictionary
        """
        self.keyword_index = keyword_index
        self.metadata_indexes = metadata_indexes

    def update_metadata_indexes(
        self,
        segment: ContextSegment,
        project_id: str,
        add: bool,
    ) -> None:
        """Update metadata indexes for a segment using sets.

        Args:
            segment: Context segment
            project_id: Project identifier
            add: True to add, False to remove
        """
        if project_id not in self.metadata_indexes:
            self.metadata_indexes[project_id] = {
                "by_file": {},
                "by_task": {},
                "by_tag": {},
                "by_type": {},
            }

        indexes = self.metadata_indexes[project_id]
        segment_id = segment.segment_id

        # Update file_path index
        if segment.file_path:
            if add:
                indexes["by_file"].setdefault(segment.file_path, set()).add(segment_id)
            else:
                if segment.file_path in indexes["by_file"]:
                    indexes["by_file"][segment.file_path].discard(segment_id)
                    if not indexes["by_file"][segment.file_path]:
                        del indexes["by_file"][segment.file_path]

        # Update task_id index
        if segment.task_id:
            if add:
                indexes["by_task"].setdefault(segment.task_id, set()).add(segment_id)
            else:
                if segment.task_id in indexes["by_task"]:
                    indexes["by_task"][segment.task_id].discard(segment_id)
                    if not indexes["by_task"][segment.task_id]:
                        del indexes["by_task"][segment.task_id]

        # Update tags index
        for tag in segment.tags:
            if add:
                indexes["by_tag"].setdefault(tag, set()).add(segment_id)
            else:
                if tag in indexes["by_tag"]:
                    indexes["by_tag"][tag].discard(segment_id)
                    if not indexes["by_tag"][tag]:
                        del indexes["by_tag"][tag]

        # Update type index
        if add:
            indexes["by_type"].setdefault(segment.type, set()).add(segment_id)
        else:
            if segment.type in indexes["by_type"]:
                indexes["by_type"][segment.type].discard(segment_id)
                if not indexes["by_type"][segment.type]:
                    del indexes["by_type"][segment.type]

    def apply_metadata_filters(
        self, candidate_ids: set[str], filters: dict, project_id: str
    ) -> set[str]:
        """Apply metadata filters using hash-based indexes.

        Args:
            candidate_ids: Set of candidate segment IDs
            filters: Filter dictionary
            project_id: Project identifier

        Returns:
            Filtered set of segment IDs
        """
        if project_id not in self.metadata_indexes:
            return candidate_ids

        indexes = self.metadata_indexes[project_id]

        # Apply file_path filter
        if "file_path" in filters:
            file_path = filters["file_path"]
            file_ids = indexes["by_file"].get(file_path, set())
            candidate_ids &= file_ids

        # Apply task_id filter
        if "task_id" in filters:
            task_id = filters["task_id"]
            task_ids = indexes["by_task"].get(task_id, set())
            candidate_ids &= task_ids

        # Apply tag filter
        if "tag" in filters:
            tag = filters["tag"]
            tag_ids = indexes["by_tag"].get(tag, set())
            candidate_ids &= tag_ids

        # Apply type filter
        if "type" in filters:
            seg_type = filters["type"]
            type_ids = indexes["by_type"].get(seg_type, set())
            candidate_ids &= type_ids

        return candidate_ids

    def rebuild_indexes(self, stashed_dir: Path, file_ops) -> None:
        """Rebuild all indexes from stashed files.

        Args:
            stashed_dir: Directory containing stashed files
            file_ops: FileOperations instance
        """
        # Rebuild keyword indexes and metadata indexes from all stashed files
        for file_path in stashed_dir.glob("*.json"):
            if file_path.suffix == ".json" and not file_path.name.endswith(".tmp"):
                # Extract project_id from filename
                project_id = file_path.stem
                stashed = file_ops.load_stashed_file(file_path)

                # Initialize indexes for this project
                if project_id not in self.keyword_index:
                    self.keyword_index[project_id] = InvertedIndex()

                # Rebuild indexes from segments
                for seg_dict in stashed:
                    try:
                        segment = ContextSegment.model_validate(seg_dict)
                        # Add to keyword index
                        self.keyword_index[project_id].add_segment(segment.segment_id, segment.text)
                        # Add to metadata indexes
                        self.update_metadata_indexes(segment, project_id, add=True)
                    except Exception as e:
                        logger.warning(
                            f"Failed to rebuild index for segment {seg_dict.get('segment_id')}: {e}"
                        )
