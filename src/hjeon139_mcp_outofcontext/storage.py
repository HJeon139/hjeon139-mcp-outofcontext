"""Storage layer for context segments."""

import json
import logging
import os
from pathlib import Path

from .i_storage_layer import IStorageLayer
from .inverted_index import InvertedIndex
from .lru_segment_cache import LRUSegmentCache
from .models import ContextSegment

# Re-export for backward compatibility
__all__ = ["IStorageLayer", "InvertedIndex", "LRUSegmentCache", "StorageLayer"]

logger = logging.getLogger(__name__)


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

        # Load persisted data on startup
        self._load_persisted_data()

    def store_segment(
        self,
        segment: ContextSegment,
        project_id: str,
    ) -> None:
        """Store segment in active storage."""
        # Use LRU cache for active segments
        self.active_segments.put(segment.segment_id, segment)

        # Track active segment IDs by project
        if project_id not in self.active_segment_ids:
            self.active_segment_ids[project_id] = set()
        self.active_segment_ids[project_id].add(segment.segment_id)

    def load_segments(
        self,
        project_id: str,
    ) -> list[ContextSegment]:
        """Load all segments for a project."""
        segments: list[ContextSegment] = []

        # Load active segments from LRU cache
        active_ids = self.active_segment_ids.get(project_id, set())
        for segment_id in active_ids:
            segment = self.active_segments.get(segment_id)
            if segment:
                segments.append(segment)

        # Load stashed segments
        stashed = self._load_stashed_segments(project_id)
        segments.extend(stashed)

        return segments

    def stash_segment(
        self,
        segment: ContextSegment,
        project_id: str,
    ) -> None:
        """Move segment to stashed storage."""
        # Remove from active storage if present
        self.active_segments.remove(segment.segment_id)

        # Remove from active tracking
        if project_id in self.active_segment_ids:
            self.active_segment_ids[project_id].discard(segment.segment_id)

        # Update segment tier
        segment.tier = "stashed"

        # Get project-specific file path
        file_path = self._get_stashed_file_path(project_id)

        # Load existing stashed segments
        stashed = self._load_stashed_file(file_path)

        # Remove segment if it already exists (update case)
        stashed = [s for s in stashed if s.get("segment_id") != segment.segment_id]

        # Add segment
        segment_dict = segment.model_dump(mode="json")
        stashed.append(segment_dict)

        # Save to sharded file
        self._save_stashed_file(file_path, stashed)

        # Update indexes
        self._update_metadata_indexes(segment, project_id, add=True)

        # Update keyword index
        if project_id not in self.keyword_index:
            self.keyword_index[project_id] = InvertedIndex()
        self.keyword_index[project_id].add_segment(segment.segment_id, segment.text)

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
        if query and project_id in self.keyword_index:
            candidate_ids = self.keyword_index[project_id].search(query)
        else:
            # No query or no index: get all stashed segment IDs
            candidate_ids = self._get_all_stashed_ids(project_id)

        # Apply metadata filters using hash maps
        if filters:
            candidate_ids = self._apply_metadata_filters(candidate_ids, filters, project_id)

        # Load only matching segments
        segments: list[ContextSegment] = []
        for seg_id in candidate_ids:
            segment = self._load_stashed_segment(seg_id, project_id)
            if segment:
                segments.append(segment)

        return segments

    def delete_segment(
        self,
        segment_id: str,
        project_id: str,
    ) -> None:
        """Delete segment from storage."""
        # Remove from active storage
        self.active_segments.remove(segment_id)

        # Remove from active tracking
        if project_id in self.active_segment_ids:
            self.active_segment_ids[project_id].discard(segment_id)

        # Load stashed file
        file_path = self._get_stashed_file_path(project_id)
        stashed = self._load_stashed_file(file_path)

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
            self._save_stashed_file(file_path, stashed)

            # Update indexes (remove)
            try:
                segment = ContextSegment.model_validate(removed_segment)
                self._update_metadata_indexes(segment, project_id, add=False)

                # Remove from keyword index
                if project_id in self.keyword_index:
                    self.keyword_index[project_id].remove_segment(segment_id)
            except Exception as e:
                logger.warning(f"Failed to deserialize segment for index update: {e}")

    def _load_persisted_data(self) -> None:
        """Load persisted data on startup."""
        # Rebuild indexes from stashed files
        self._rebuild_indexes()

    def _get_stashed_file_path(self, project_id: str) -> Path:
        """Get file path for project's stashed segments.

        Args:
            project_id: Project identifier

        Returns:
            Path to project's stashed file
        """
        return self.stashed_dir / f"{project_id}.json"

    def _load_stashed_file(self, file_path: Path) -> list[dict]:
        """Load stashed segments from file.

        Args:
            file_path: Path to stashed file

        Returns:
            List of segment dictionaries
        """
        if not file_path.exists():
            return []

        # Check for temp file (incomplete write)
        temp_path = file_path.with_suffix(".json.tmp")
        if temp_path.exists():
            logger.warning(f"Found incomplete write at {temp_path}, removing it")
            try:
                temp_path.unlink()
            except Exception as e:
                logger.error(f"Failed to remove temp file: {e}")

        try:
            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)
                return data.get("segments", [])
        except json.JSONDecodeError as e:
            logger.error(f"Corrupt JSON file at {file_path}: {e}")
            # Backup corrupt file
            backup_path = file_path.with_suffix(".json.corrupt")
            try:
                file_path.rename(backup_path)
                logger.info(f"Backed up corrupt file to {backup_path}")
            except Exception as backup_error:
                logger.error(f"Failed to backup corrupt file: {backup_error}")
            return []
        except PermissionError as e:
            logger.error(f"Permission error reading {file_path}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error loading {file_path}: {e}")
            raise

    def _save_stashed_file(self, file_path: Path, segments: list[dict]) -> None:
        """Save stashed segments to file atomically.

        Args:
            file_path: Path to stashed file
            segments: List of segment dictionaries
        """
        temp_path = file_path.with_suffix(".json.tmp")

        try:
            # Write to temp file
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump({"segments": segments}, f, indent=2, default=str)

            # Atomic rename
            temp_path.replace(file_path)
        except PermissionError as e:
            logger.error(f"Permission error writing to {file_path}: {e}")
            raise
        except OSError as e:
            if e.errno == 28:  # No space left on device
                logger.error(f"Disk full when writing to {file_path}: {e}")
                raise
            raise
        except Exception as e:
            logger.error(f"Unexpected error saving to {file_path}: {e}")
            # Clean up temp file on error
            try:
                if temp_path.exists():
                    temp_path.unlink()
            except Exception:
                pass
            raise

    def _load_stashed_segments(self, project_id: str) -> list[ContextSegment]:
        """Load all stashed segments for a project.

        Args:
            project_id: Project identifier

        Returns:
            List of ContextSegment objects
        """
        file_path = self._get_stashed_file_path(project_id)
        stashed = self._load_stashed_file(file_path)

        segments: list[ContextSegment] = []
        for seg_dict in stashed:
            try:
                segment = ContextSegment.model_validate(seg_dict)
                segments.append(segment)
            except Exception as e:
                logger.warning(f"Failed to deserialize segment {seg_dict.get('segment_id')}: {e}")

        return segments

    def _load_stashed_segment(self, segment_id: str, project_id: str) -> ContextSegment | None:
        """Load a single stashed segment by ID.

        Args:
            segment_id: Segment identifier
            project_id: Project identifier

        Returns:
            ContextSegment if found, None otherwise
        """
        file_path = self._get_stashed_file_path(project_id)
        stashed = self._load_stashed_file(file_path)

        for seg_dict in stashed:
            if seg_dict.get("segment_id") == segment_id:
                try:
                    return ContextSegment.model_validate(seg_dict)
                except Exception as e:
                    logger.warning(f"Failed to deserialize segment {segment_id}: {e}")
                    return None

        return None

    def _get_all_stashed_ids(self, project_id: str) -> set[str]:
        """Get all stashed segment IDs for a project.

        Args:
            project_id: Project identifier

        Returns:
            Set of segment IDs
        """
        file_path = self._get_stashed_file_path(project_id)
        stashed = self._load_stashed_file(file_path)
        return {seg_id for seg in stashed if (seg_id := seg.get("segment_id")) is not None}

    def _update_metadata_indexes(
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

    def _apply_metadata_filters(
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

    def _rebuild_indexes(self) -> None:
        """Rebuild all indexes from stashed files."""
        # Rebuild keyword indexes and metadata indexes from all stashed files
        for file_path in self.stashed_dir.glob("*.json"):
            if file_path.suffix == ".json" and not file_path.name.endswith(".tmp"):
                # Extract project_id from filename
                project_id = file_path.stem
                stashed = self._load_stashed_file(file_path)

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
                        self._update_metadata_indexes(segment, project_id, add=True)
                    except Exception as e:
                        logger.warning(
                            f"Failed to rebuild index for segment {seg_dict.get('segment_id')}: {e}"
                        )

    def _save_evicted_segment(self, segment_id: str, segment: ContextSegment) -> None:
        """Save evicted segment to disk.

        Args:
            segment_id: Segment identifier
            segment: Segment to save
        """
        evicted_file = self.evicted_dir / f"{segment_id}.json"
        try:
            with open(evicted_file, "w", encoding="utf-8") as f:
                json.dump(segment.model_dump(mode="json"), f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save evicted segment {segment_id}: {e}")

    def _load_evicted_segment(self, segment_id: str) -> ContextSegment | None:
        """Load evicted segment from disk.

        Args:
            segment_id: Segment identifier

        Returns:
            ContextSegment if found, None otherwise
        """
        evicted_file = self.evicted_dir / f"{segment_id}.json"
        if not evicted_file.exists():
            return None

        try:
            with open(evicted_file, encoding="utf-8") as f:
                data = json.load(f)
                return ContextSegment.model_validate(data)
        except Exception as e:
            logger.error(f"Failed to load evicted segment {segment_id}: {e}")
            return None
