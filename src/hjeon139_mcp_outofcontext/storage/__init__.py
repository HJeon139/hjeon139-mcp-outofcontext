"""Storage layer for context segments."""

import os
from pathlib import Path

from ..i_storage_layer import IStorageLayer
from ..inverted_index import InvertedIndex
from ..lru_segment_cache import LRUSegmentCache
from .file_operations import FileOperations
from .indexing import IndexingOperations
from .segment_operations import SegmentOperations

# Re-export for backward compatibility
__all__ = [
    "IStorageLayer",
    "InvertedIndex",
    "LRUSegmentCache",
    "StorageLayer",
]


class StorageLayer(IStorageLayer):
    """Storage layer implementation with in-memory and JSON persistence."""

    def __init__(self, storage_path: str | None = None, max_active_segments: int = 10000) -> None:
        """Initialize storage layer.

        Args:
            storage_path: Path to storage directory. Defaults to ~/.out_of_context/
            max_active_segments: Maximum number of active segments in memory
        """
        if storage_path is None:
            storage_path = os.getenv(
                "OUT_OF_CONTEXT_STORAGE_PATH",
                str(Path.home() / ".out_of_context"),
            )

        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Sharded storage: one file per project
        # Format: storage_path / "stashed" / f"{project_id}.json"
        self.stashed_dir = self.storage_path / "stashed"
        self.stashed_dir.mkdir(exist_ok=True)

        # Legacy single file support (for backward compatibility)
        self.legacy_storage_path = self.storage_path / "storage.json"

        # In-memory storage: Use LRU cache for active segments
        self.active_segments: LRUSegmentCache = LRUSegmentCache(
            maxsize=max_active_segments, storage=self
        )

        # Track active segments by project (for load_segments)
        self.active_segment_ids: dict[str, set[str]] = {}

        # Keyword indexes: project_id -> InvertedIndex
        self.keyword_index: dict[str, InvertedIndex] = {}

        # Metadata indexes: project_id -> {by_file, by_task, by_tag, by_type} -> {value: set(segment_ids)}
        self.metadata_indexes: dict[str, dict[str, dict[str, set[str]]]] = {}

        # Evicted segments storage: segment_id -> segment (for LRU eviction)
        self.evicted_dir = self.storage_path / "evicted"
        self.evicted_dir.mkdir(exist_ok=True)

        # Initialize component classes
        self.file_ops = FileOperations(self.stashed_dir, self.evicted_dir)
        self.indexing_ops = IndexingOperations(self.keyword_index, self.metadata_indexes)
        self.segment_ops = SegmentOperations(
            self.active_segments,
            self.active_segment_ids,
            self.file_ops,
            self.indexing_ops,
        )

        # Load persisted data on startup
        self._load_persisted_data()

    def store_segment(self, segment, project_id: str) -> None:
        """Store segment in active storage."""
        return self.segment_ops.store_segment(segment, project_id)

    def load_segments(self, project_id: str) -> list:
        """Load all segments for a project."""
        return self.segment_ops.load_segments(project_id)

    def stash_segment(self, segment, project_id: str) -> None:
        """Move segment to stashed storage."""
        return self.segment_ops.stash_segment(segment, project_id)

    def search_stashed(self, query: str, filters: dict, project_id: str) -> list:
        """Search stashed segments by keyword and metadata."""
        return self.segment_ops.search_stashed(query, filters, project_id)

    def delete_segment(self, segment_id: str, project_id: str) -> None:
        """Delete segment from storage."""
        return self.segment_ops.delete_segment(segment_id, project_id)

    def update_segment(self, segment, project_id: str) -> None:
        """Update segment attributes in storage."""
        return self.segment_ops.update_segment(segment, project_id)

    def unstash_segment(self, segment, project_id: str) -> None:
        """Move segment from stashed storage back to active storage."""
        return self.segment_ops.unstash_segment(segment, project_id)

    def _load_persisted_data(self) -> None:
        """Load persisted data on startup."""
        # Rebuild indexes from stashed files
        self.indexing_ops.rebuild_indexes(self.stashed_dir, self.file_ops)

    # Methods for LRU cache compatibility
    def _save_evicted_segment(self, segment_id: str, segment) -> None:
        """Save evicted segment to disk (called by LRU cache)."""
        return self.file_ops.save_evicted_segment(segment_id, segment)

    def _load_evicted_segment(self, segment_id: str):
        """Load evicted segment from disk (called by LRU cache)."""
        return self.file_ops.load_evicted_segment(segment_id)
