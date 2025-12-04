"""Storage layer for context segments."""

import json
import logging
import os
from abc import ABC, abstractmethod
from pathlib import Path

from .models import ContextSegment

logger = logging.getLogger(__name__)


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


class StorageLayer(IStorageLayer):
    """Storage layer implementation with in-memory and JSON persistence."""

    def __init__(self, storage_path: str | None = None) -> None:
        """Initialize storage layer.

        Args:
            storage_path: Path to storage JSON file. Defaults to ~/.out_of_context/storage.json
        """
        if storage_path is None:
            storage_path = os.getenv(
                "OUT_OF_CONTEXT_STORAGE_PATH",
                str(Path.home() / ".out_of_context" / "storage.json"),
            )

        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

        # In-memory storage: project_id -> segment_id -> segment
        self.active_segments: dict[str, dict[str, ContextSegment]] = {}

        # Load persisted data on startup
        self._load_persisted_data()

    def store_segment(
        self,
        segment: ContextSegment,
        project_id: str,
    ) -> None:
        """Store segment in active storage."""
        if project_id not in self.active_segments:
            self.active_segments[project_id] = {}

        self.active_segments[project_id][segment.segment_id] = segment

    def load_segments(
        self,
        project_id: str,
    ) -> list[ContextSegment]:
        """Load all segments for a project."""
        active = list(self.active_segments.get(project_id, {}).values())
        stashed = self._load_stashed_segments(project_id)
        return active + stashed

    def stash_segment(
        self,
        segment: ContextSegment,
        project_id: str,
    ) -> None:
        """Move segment to stashed storage."""
        # Remove from active storage if present
        if project_id in self.active_segments:
            self.active_segments[project_id].pop(segment.segment_id, None)

        # Update segment tier
        segment.tier = "stashed"

        # Load existing stashed data
        stashed_data = self._load_stashed_data()

        # Initialize project if needed
        if "projects" not in stashed_data:
            stashed_data["projects"] = {}
        if project_id not in stashed_data["projects"]:
            stashed_data["projects"][project_id] = {"segments": [], "indexes": {}}

        project_data = stashed_data["projects"][project_id]

        # Remove segment if it already exists (update case)
        project_data["segments"] = [
            s for s in project_data["segments"] if s.get("segment_id") != segment.segment_id
        ]

        # Add segment
        segment_dict = segment.model_dump(mode="json")
        project_data["segments"].append(segment_dict)

        # Update indexes
        self._update_indexes(project_data, segment, add=True)

        # Persist to file
        self._save_stashed_data(stashed_data)

    def search_stashed(
        self,
        query: str,
        filters: dict,
        project_id: str,
    ) -> list[ContextSegment]:
        """Search stashed segments by keyword and metadata."""
        stashed_data = self._load_stashed_data()
        segments: list[ContextSegment] = []

        if "projects" not in stashed_data:
            return segments

        project_data = stashed_data["projects"].get(project_id, {})
        project_segments = project_data.get("segments", [])

        # Filter by metadata if provided
        if filters:
            project_segments = self._filter_segments(project_segments, filters)

        # Search by keyword if provided
        if query:
            query_lower = query.lower()
            project_segments = [
                s
                for s in project_segments
                if query_lower in s.get("text", "").lower()
                or query_lower in s.get("segment_id", "").lower()
            ]

        # Convert to ContextSegment objects
        for seg_dict in project_segments:
            try:
                segment = ContextSegment.model_validate(seg_dict)
                segments.append(segment)
            except Exception as e:
                logger.warning(f"Failed to deserialize segment {seg_dict.get('segment_id')}: {e}")

        return segments

    def delete_segment(
        self,
        segment_id: str,
        project_id: str,
    ) -> None:
        """Delete segment from storage."""
        # Remove from active storage
        if project_id in self.active_segments:
            self.active_segments[project_id].pop(segment_id, None)

        # Remove from stashed storage
        stashed_data = self._load_stashed_data()
        if "projects" in stashed_data and project_id in stashed_data["projects"]:
            project_data = stashed_data["projects"][project_id]
            segments = project_data.get("segments", [])

            # Find and remove segment
            removed_segment = None
            for seg_dict in segments:
                if seg_dict.get("segment_id") == segment_id:
                    removed_segment = seg_dict
                    break

            if removed_segment:
                project_data["segments"] = [
                    s for s in segments if s.get("segment_id") != segment_id
                ]

                # Update indexes (remove)
                try:
                    segment = ContextSegment.model_validate(removed_segment)
                    self._update_indexes(project_data, segment, add=False)
                except Exception as e:
                    logger.warning(f"Failed to deserialize segment for index update: {e}")

                # Persist changes
                self._save_stashed_data(stashed_data)

    def _load_persisted_data(self) -> None:
        """Load persisted data on startup."""
        # Load stashed segments into memory (optional, for faster access)
        # For now, we'll load on-demand via load_segments
        # Just verify the file is readable
        self._load_stashed_data()

    def _load_stashed_data(self) -> dict:
        """Load stashed data from JSON file."""
        # Check for temp file (incomplete write)
        temp_path = self.storage_path.with_suffix(".json.tmp")
        if temp_path.exists():
            logger.warning(f"Found incomplete write at {temp_path}, removing it")
            try:
                temp_path.unlink()
            except Exception as e:
                logger.error(f"Failed to remove temp file: {e}")

        # Load main file
        if not self.storage_path.exists():
            return {"version": "1.0", "projects": {}}

        try:
            with open(self.storage_path, encoding="utf-8") as f:
                data = json.load(f)
                # Ensure structure
                if "version" not in data:
                    data["version"] = "1.0"
                if "projects" not in data:
                    data["projects"] = {}
                return data
        except json.JSONDecodeError as e:
            logger.error(f"Corrupt JSON file at {self.storage_path}: {e}")
            # Backup corrupt file
            backup_path = self.storage_path.with_suffix(".json.corrupt")
            try:
                self.storage_path.rename(backup_path)
                logger.info(f"Backed up corrupt file to {backup_path}")
            except Exception as backup_error:
                logger.error(f"Failed to backup corrupt file: {backup_error}")
            return {"version": "1.0", "projects": {}}
        except PermissionError as e:
            logger.error(f"Permission error reading {self.storage_path}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error loading {self.storage_path}: {e}")
            raise

    def _save_stashed_data(self, data: dict) -> None:
        """Save stashed data to JSON file atomically."""
        temp_path = self.storage_path.with_suffix(".json.tmp")

        try:
            # Write to temp file
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, default=str)

            # Atomic rename
            temp_path.replace(self.storage_path)
        except PermissionError as e:
            logger.error(f"Permission error writing to {self.storage_path}: {e}")
            raise
        except OSError as e:
            if e.errno == 28:  # No space left on device
                logger.error(f"Disk full when writing to {self.storage_path}: {e}")
                raise
            raise
        except Exception as e:
            logger.error(f"Unexpected error saving to {self.storage_path}: {e}")
            # Clean up temp file on error
            try:
                if temp_path.exists():
                    temp_path.unlink()
            except Exception:
                pass
            raise

    def _load_stashed_segments(self, project_id: str) -> list[ContextSegment]:
        """Load stashed segments for a project."""
        stashed_data = self._load_stashed_data()
        segments: list[ContextSegment] = []

        if "projects" not in stashed_data:
            return segments

        project_data = stashed_data["projects"].get(project_id, {})
        project_segments = project_data.get("segments", [])

        for seg_dict in project_segments:
            try:
                segment = ContextSegment.model_validate(seg_dict)
                segments.append(segment)
            except Exception as e:
                logger.warning(f"Failed to deserialize segment {seg_dict.get('segment_id')}: {e}")

        return segments

    def _update_indexes(
        self,
        project_data: dict,
        segment: ContextSegment,
        add: bool,
    ) -> None:
        """Update metadata indexes for a segment."""
        if "indexes" not in project_data:
            project_data["indexes"] = {}

        indexes = project_data["indexes"]

        # Initialize index structures
        if "by_task" not in indexes:
            indexes["by_task"] = {}
        if "by_file" not in indexes:
            indexes["by_file"] = {}
        if "by_tag" not in indexes:
            indexes["by_tag"] = {}

        segment_id = segment.segment_id

        # Update task index
        if segment.task_id:
            if add:
                if segment.task_id not in indexes["by_task"]:
                    indexes["by_task"][segment.task_id] = []
                if segment_id not in indexes["by_task"][segment.task_id]:
                    indexes["by_task"][segment.task_id].append(segment_id)
            else:
                if segment.task_id in indexes["by_task"]:
                    indexes["by_task"][segment.task_id] = [
                        sid for sid in indexes["by_task"][segment.task_id] if sid != segment_id
                    ]
                    if not indexes["by_task"][segment.task_id]:
                        del indexes["by_task"][segment.task_id]

        # Update file index
        if segment.file_path:
            if add:
                if segment.file_path not in indexes["by_file"]:
                    indexes["by_file"][segment.file_path] = []
                if segment_id not in indexes["by_file"][segment.file_path]:
                    indexes["by_file"][segment.file_path].append(segment_id)
            else:
                if segment.file_path in indexes["by_file"]:
                    indexes["by_file"][segment.file_path] = [
                        sid for sid in indexes["by_file"][segment.file_path] if sid != segment_id
                    ]
                    if not indexes["by_file"][segment.file_path]:
                        del indexes["by_file"][segment.file_path]

        # Update tag index
        for tag in segment.tags:
            if add:
                if tag not in indexes["by_tag"]:
                    indexes["by_tag"][tag] = []
                if segment_id not in indexes["by_tag"][tag]:
                    indexes["by_tag"][tag].append(segment_id)
            else:
                if tag in indexes["by_tag"]:
                    indexes["by_tag"][tag] = [
                        sid for sid in indexes["by_tag"][tag] if sid != segment_id
                    ]
                    if not indexes["by_tag"][tag]:
                        del indexes["by_tag"][tag]

    def _filter_segments(
        self,
        segments: list[dict],
        filters: dict,
    ) -> list[dict]:
        """Filter segments by metadata."""
        filtered = segments

        if "task_id" in filters:
            task_id = filters["task_id"]
            filtered = [s for s in filtered if s.get("task_id") == task_id]

        if "file_path" in filters:
            file_path = filters["file_path"]
            filtered = [s for s in filtered if s.get("file_path") == file_path]

        if "tag" in filters:
            tag = filters["tag"]
            filtered = [s for s in filtered if tag in s.get("tags", [])]

        if "type" in filters:
            seg_type = filters["type"]
            filtered = [s for s in filtered if s.get("type") == seg_type]

        return filtered
