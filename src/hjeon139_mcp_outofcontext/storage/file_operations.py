"""File I/O operations for storage layer."""

import json
import logging
from pathlib import Path

from ..models import ContextSegment

logger = logging.getLogger(__name__)


class FileOperations:
    """File I/O operations for storage layer."""

    def __init__(self, stashed_dir: Path, evicted_dir: Path) -> None:
        """Initialize file operations.

        Args:
            stashed_dir: Directory for stashed segments
            evicted_dir: Directory for evicted segments
        """
        self.stashed_dir = stashed_dir
        self.evicted_dir = evicted_dir

    def get_stashed_file_path(self, project_id: str) -> Path:
        """Get file path for project's stashed segments.

        Args:
            project_id: Project identifier

        Returns:
            Path to project's stashed file
        """
        return self.stashed_dir / f"{project_id}.json"

    def load_stashed_file(self, file_path: Path) -> list[dict]:
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

    def save_stashed_file(self, file_path: Path, segments: list[dict]) -> None:
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

    def load_stashed_segments(self, project_id: str) -> list[ContextSegment]:
        """Load all stashed segments for a project.

        Args:
            project_id: Project identifier

        Returns:
            List of ContextSegment objects
        """
        file_path = self.get_stashed_file_path(project_id)
        stashed = self.load_stashed_file(file_path)

        segments: list[ContextSegment] = []
        for seg_dict in stashed:
            try:
                segment = ContextSegment.model_validate(seg_dict)
                segments.append(segment)
            except Exception as e:
                logger.warning(f"Failed to deserialize segment {seg_dict.get('segment_id')}: {e}")

        return segments

    def load_stashed_segment(self, segment_id: str, project_id: str) -> ContextSegment | None:
        """Load a single stashed segment by ID.

        Args:
            segment_id: Segment identifier
            project_id: Project identifier

        Returns:
            ContextSegment if found, None otherwise
        """
        file_path = self.get_stashed_file_path(project_id)
        stashed = self.load_stashed_file(file_path)

        for seg_dict in stashed:
            if seg_dict.get("segment_id") == segment_id:
                try:
                    return ContextSegment.model_validate(seg_dict)
                except Exception as e:
                    logger.warning(f"Failed to deserialize segment {segment_id}: {e}")
                    return None

        return None

    def get_all_stashed_ids(self, project_id: str) -> set[str]:
        """Get all stashed segment IDs for a project.

        Args:
            project_id: Project identifier

        Returns:
            Set of segment IDs
        """
        file_path = self.get_stashed_file_path(project_id)
        stashed = self.load_stashed_file(file_path)
        return {seg_id for seg in stashed if (seg_id := seg.get("segment_id")) is not None}

    def save_evicted_segment(self, segment_id: str, segment: ContextSegment) -> None:
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

    def load_evicted_segment(self, segment_id: str) -> ContextSegment | None:
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
