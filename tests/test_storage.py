"""Tests for storage layer."""

import json
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from hjeon139_mcp_outofcontext.models import ContextSegment
from hjeon139_mcp_outofcontext.storage import IStorageLayer, StorageLayer


@pytest.fixture
def temp_storage_path(tmp_path: Path) -> Path:
    """Create a temporary storage path for testing."""
    storage_dir = tmp_path / "storage"
    storage_dir.mkdir()
    return storage_dir / "storage.json"


@pytest.fixture
def storage_layer(temp_storage_path: Path) -> StorageLayer:
    """Create a storage layer instance for testing."""
    return StorageLayer(storage_path=str(temp_storage_path))


@pytest.fixture
def sample_segment() -> ContextSegment:
    """Create a sample context segment for testing."""
    return ContextSegment(
        segment_id="seg-1",
        text="Sample text content",
        type="message",
        project_id="proj-1",
        task_id="task-1",
        created_at=datetime.now(),
        last_touched_at=datetime.now(),
        tokens=100,
        file_path="test.py",
        tags=["test", "sample"],
    )


@pytest.fixture
def sample_segment_2() -> ContextSegment:
    """Create another sample context segment for testing."""
    return ContextSegment(
        segment_id="seg-2",
        text="Another text content",
        type="code",
        project_id="proj-1",
        task_id="task-1",
        created_at=datetime.now(),
        last_touched_at=datetime.now(),
        tokens=200,
        file_path="test2.py",
        tags=["code"],
    )


class TestStorageInterface:
    """Test that StorageLayer implements IStorageLayer interface."""

    @pytest.mark.unit
    def test_implements_interface(self, storage_layer: StorageLayer) -> None:
        """Test that StorageLayer implements IStorageLayer."""
        assert isinstance(storage_layer, IStorageLayer)


class TestInMemoryStorage:
    """Test in-memory storage operations."""

    @pytest.mark.unit
    def test_store_segment(
        self,
        storage_layer: StorageLayer,
        sample_segment: ContextSegment,
    ) -> None:
        """Test storing a segment in memory."""
        storage_layer.store_segment(sample_segment, "proj-1")
        assert "proj-1" in storage_layer.active_segments
        assert "seg-1" in storage_layer.active_segments["proj-1"]
        assert storage_layer.active_segments["proj-1"]["seg-1"] == sample_segment

    @pytest.mark.unit
    def test_store_multiple_segments(
        self,
        storage_layer: StorageLayer,
        sample_segment: ContextSegment,
        sample_segment_2: ContextSegment,
    ) -> None:
        """Test storing multiple segments."""
        storage_layer.store_segment(sample_segment, "proj-1")
        storage_layer.store_segment(sample_segment_2, "proj-1")

        assert len(storage_layer.active_segments["proj-1"]) == 2
        assert "seg-1" in storage_layer.active_segments["proj-1"]
        assert "seg-2" in storage_layer.active_segments["proj-1"]

    @pytest.mark.unit
    def test_store_different_projects(
        self,
        storage_layer: StorageLayer,
        sample_segment: ContextSegment,
    ) -> None:
        """Test project isolation."""
        segment_proj2 = ContextSegment(
            segment_id="seg-1",
            text="Different project",
            type="message",
            project_id="proj-2",
            created_at=datetime.now(),
            last_touched_at=datetime.now(),
            tokens=50,
        )

        storage_layer.store_segment(sample_segment, "proj-1")
        storage_layer.store_segment(segment_proj2, "proj-2")

        assert len(storage_layer.active_segments) == 2
        assert "proj-1" in storage_layer.active_segments
        assert "proj-2" in storage_layer.active_segments
        assert storage_layer.active_segments["proj-1"]["seg-1"].project_id == "proj-1"
        assert storage_layer.active_segments["proj-2"]["seg-1"].project_id == "proj-2"

    @pytest.mark.unit
    def test_load_segments_active_only(
        self,
        storage_layer: StorageLayer,
        sample_segment: ContextSegment,
    ) -> None:
        """Test loading active segments."""
        storage_layer.store_segment(sample_segment, "proj-1")
        segments = storage_layer.load_segments("proj-1")
        assert len(segments) == 1
        assert segments[0].segment_id == "seg-1"


class TestJSONPersistence:
    """Test JSON file persistence."""

    @pytest.mark.unit
    def test_stash_segment_persists(
        self,
        storage_layer: StorageLayer,
        temp_storage_path: Path,
        sample_segment: ContextSegment,
    ) -> None:
        """Test that stashing a segment persists to JSON."""
        storage_layer.stash_segment(sample_segment, "proj-1")

        # Verify file exists
        assert temp_storage_path.exists()

        # Load and verify
        with open(temp_storage_path) as f:
            data = json.load(f)

        assert "projects" in data
        assert "proj-1" in data["projects"]
        assert len(data["projects"]["proj-1"]["segments"]) == 1
        assert data["projects"]["proj-1"]["segments"][0]["segment_id"] == "seg-1"

    @pytest.mark.unit
    def test_stash_segment_updates_tier(
        self,
        storage_layer: StorageLayer,
        sample_segment: ContextSegment,
    ) -> None:
        """Test that stashing updates segment tier."""
        assert sample_segment.tier == "working"
        storage_layer.stash_segment(sample_segment, "proj-1")
        assert sample_segment.tier == "stashed"

    @pytest.mark.unit
    def test_load_segments_includes_stashed(
        self,
        storage_layer: StorageLayer,
        sample_segment: ContextSegment,
    ) -> None:
        """Test that load_segments includes stashed segments."""
        storage_layer.stash_segment(sample_segment, "proj-1")
        segments = storage_layer.load_segments("proj-1")
        assert len(segments) == 1
        assert segments[0].segment_id == "seg-1"
        assert segments[0].tier == "stashed"

    @pytest.mark.unit
    def test_stash_removes_from_active(
        self,
        storage_layer: StorageLayer,
        sample_segment: ContextSegment,
    ) -> None:
        """Test that stashing removes segment from active storage."""
        storage_layer.store_segment(sample_segment, "proj-1")
        assert "seg-1" in storage_layer.active_segments["proj-1"]

        storage_layer.stash_segment(sample_segment, "proj-1")
        assert "seg-1" not in storage_layer.active_segments.get("proj-1", {})

    @pytest.mark.unit
    def test_persistence_survives_restart(
        self,
        temp_storage_path: Path,
        sample_segment: ContextSegment,
    ) -> None:
        """Test that storage survives server restart."""
        # Create and stash
        storage1 = StorageLayer(storage_path=str(temp_storage_path))
        storage1.stash_segment(sample_segment, "proj-1")

        # Create new instance (simulating restart)
        storage2 = StorageLayer(storage_path=str(temp_storage_path))
        segments = storage2.load_segments("proj-1")

        assert len(segments) == 1
        assert segments[0].segment_id == "seg-1"
        assert segments[0].text == "Sample text content"


class TestAtomicOperations:
    """Test atomic write operations."""

    @pytest.mark.unit
    def test_atomic_write_creates_temp_file(
        self,
        storage_layer: StorageLayer,
        temp_storage_path: Path,
        sample_segment: ContextSegment,
    ) -> None:
        """Test that atomic write uses temp file pattern."""
        storage_layer.stash_segment(sample_segment, "proj-1")

        # Temp file should not exist after successful write
        temp_path = temp_storage_path.with_suffix(".json.tmp")
        assert not temp_path.exists()
        assert temp_storage_path.exists()

    @pytest.mark.unit
    def test_handles_incomplete_write(
        self,
        temp_storage_path: Path,
        sample_segment: ContextSegment,
    ) -> None:
        """Test handling of incomplete write (temp file exists)."""
        # Create a temp file (simulating crash during write)
        temp_path = temp_storage_path.with_suffix(".json.tmp")
        temp_path.write_text('{"incomplete": true}')

        # Create storage layer (should clean up temp file)
        storage = StorageLayer(storage_path=str(temp_storage_path))
        storage.stash_segment(sample_segment, "proj-1")

        # Temp file should be gone
        assert not temp_path.exists()
        # Main file should exist with correct data
        assert temp_storage_path.exists()


class TestErrorHandling:
    """Test error handling scenarios."""

    @pytest.mark.unit
    def test_handles_missing_json_file(
        self,
        temp_storage_path: Path,
        sample_segment: ContextSegment,
    ) -> None:
        """Test handling of missing JSON file."""
        # File doesn't exist yet
        assert not temp_storage_path.exists()

        storage = StorageLayer(storage_path=str(temp_storage_path))
        storage.stash_segment(sample_segment, "proj-1")

        # Should create file successfully
        assert temp_storage_path.exists()

    @pytest.mark.unit
    def test_handles_corrupt_json_file(
        self,
        temp_storage_path: Path,
        sample_segment: ContextSegment,
    ) -> None:
        """Test handling of corrupt JSON file."""
        # Create corrupt JSON file
        temp_storage_path.write_text("not valid json {")

        storage = StorageLayer(storage_path=str(temp_storage_path))
        storage.stash_segment(sample_segment, "proj-1")

        # Should create backup and start fresh
        backup_path = temp_storage_path.with_suffix(".json.corrupt")
        assert backup_path.exists()
        # Should have valid data now
        assert temp_storage_path.exists()
        with open(temp_storage_path) as f:
            data = json.load(f)
            assert "projects" in data

    @pytest.mark.unit
    @patch("hjeon139_mcp_outofcontext.storage.open")
    def test_handles_permission_error_on_read(
        self,
        mock_open: MagicMock,
        temp_storage_path: Path,
    ) -> None:
        """Test handling of permission errors on read."""
        # Create storage layer first (file doesn't exist yet, so init succeeds)
        storage = StorageLayer(storage_path=str(temp_storage_path))

        # Create file so exists() returns True when load_segments is called
        temp_storage_path.touch()

        # Mock open to raise PermissionError when load_segments calls
        # _load_stashed_data
        mock_open.side_effect = PermissionError("Permission denied")

        # Should raise PermissionError
        with pytest.raises(PermissionError, match="Permission denied"):
            storage.load_segments("proj-1")

        # Verify open was called
        mock_open.assert_called()


class TestProjectIsolation:
    """Test project isolation."""

    @pytest.mark.unit
    def test_segments_isolated_by_project(
        self,
        storage_layer: StorageLayer,
        sample_segment: ContextSegment,
    ) -> None:
        """Test that segments are isolated by project."""
        segment_proj2 = ContextSegment(
            segment_id="seg-1",
            text="Different project",
            type="message",
            project_id="proj-2",
            created_at=datetime.now(),
            last_touched_at=datetime.now(),
            tokens=50,
        )

        storage_layer.stash_segment(sample_segment, "proj-1")
        storage_layer.stash_segment(segment_proj2, "proj-2")

        segments_proj1 = storage_layer.load_segments("proj-1")
        segments_proj2 = storage_layer.load_segments("proj-2")

        assert len(segments_proj1) == 1
        assert len(segments_proj2) == 1
        assert segments_proj1[0].project_id == "proj-1"
        assert segments_proj2[0].project_id == "proj-2"

    @pytest.mark.unit
    def test_search_stashed_project_isolation(
        self,
        storage_layer: StorageLayer,
        sample_segment: ContextSegment,
    ) -> None:
        """Test that search respects project isolation."""
        segment_proj2 = ContextSegment(
            segment_id="seg-2",
            text="Different project",
            type="message",
            project_id="proj-2",
            created_at=datetime.now(),
            last_touched_at=datetime.now(),
            tokens=50,
        )

        storage_layer.stash_segment(sample_segment, "proj-1")
        storage_layer.stash_segment(segment_proj2, "proj-2")

        results = storage_layer.search_stashed("Sample", {}, "proj-1")
        assert len(results) == 1
        assert results[0].segment_id == "seg-1"

        results = storage_layer.search_stashed("Different", {}, "proj-2")
        assert len(results) == 1
        assert results[0].segment_id == "seg-2"


class TestMetadataIndexing:
    """Test metadata indexing."""

    @pytest.mark.unit
    def test_indexes_created_on_stash(
        self,
        storage_layer: StorageLayer,
        temp_storage_path: Path,
        sample_segment: ContextSegment,
    ) -> None:
        """Test that indexes are created when stashing."""
        storage_layer.stash_segment(sample_segment, "proj-1")

        with open(temp_storage_path) as f:
            data = json.load(f)

        indexes = data["projects"]["proj-1"]["indexes"]
        assert "by_task" in indexes
        assert "by_file" in indexes
        assert "by_tag" in indexes

        assert "task-1" in indexes["by_task"]
        assert "test.py" in indexes["by_file"]
        assert "test" in indexes["by_tag"]
        assert "sample" in indexes["by_tag"]

    @pytest.mark.unit
    def test_indexes_updated_on_delete(
        self,
        storage_layer: StorageLayer,
        temp_storage_path: Path,
        sample_segment: ContextSegment,
    ) -> None:
        """Test that indexes are updated when deleting."""
        storage_layer.stash_segment(sample_segment, "proj-1")
        storage_layer.delete_segment("seg-1", "proj-1")

        with open(temp_storage_path) as f:
            data = json.load(f)

        indexes = data["projects"]["proj-1"]["indexes"]
        # Indexes should be cleaned up
        assert "task-1" not in indexes["by_task"]
        assert "test.py" not in indexes["by_file"]
        assert "test" not in indexes["by_tag"]


class TestSearchFunctionality:
    """Test search functionality."""

    @pytest.mark.unit
    def test_search_by_keyword(
        self,
        storage_layer: StorageLayer,
        sample_segment: ContextSegment,
        sample_segment_2: ContextSegment,
    ) -> None:
        """Test searching by keyword."""
        storage_layer.stash_segment(sample_segment, "proj-1")
        storage_layer.stash_segment(sample_segment_2, "proj-1")

        results = storage_layer.search_stashed("Sample", {}, "proj-1")
        assert len(results) == 1
        assert results[0].segment_id == "seg-1"

        results = storage_layer.search_stashed("Another", {}, "proj-1")
        assert len(results) == 1
        assert results[0].segment_id == "seg-2"

    @pytest.mark.unit
    def test_search_by_task_id(
        self,
        storage_layer: StorageLayer,
        sample_segment: ContextSegment,
        sample_segment_2: ContextSegment,
    ) -> None:
        """Test searching by task_id filter."""
        storage_layer.stash_segment(sample_segment, "proj-1")
        storage_layer.stash_segment(sample_segment_2, "proj-1")

        results = storage_layer.search_stashed("", {"task_id": "task-1"}, "proj-1")
        assert len(results) == 2

        results = storage_layer.search_stashed("", {"task_id": "task-2"}, "proj-1")
        assert len(results) == 0

    @pytest.mark.unit
    def test_search_by_file_path(
        self,
        storage_layer: StorageLayer,
        sample_segment: ContextSegment,
        sample_segment_2: ContextSegment,
    ) -> None:
        """Test searching by file_path filter."""
        storage_layer.stash_segment(sample_segment, "proj-1")
        storage_layer.stash_segment(sample_segment_2, "proj-1")

        results = storage_layer.search_stashed("", {"file_path": "test.py"}, "proj-1")
        assert len(results) == 1
        assert results[0].segment_id == "seg-1"

    @pytest.mark.unit
    def test_search_by_tag(
        self,
        storage_layer: StorageLayer,
        sample_segment: ContextSegment,
        sample_segment_2: ContextSegment,
    ) -> None:
        """Test searching by tag filter."""
        storage_layer.stash_segment(sample_segment, "proj-1")
        storage_layer.stash_segment(sample_segment_2, "proj-1")

        results = storage_layer.search_stashed("", {"tag": "test"}, "proj-1")
        assert len(results) == 1
        assert results[0].segment_id == "seg-1"

        results = storage_layer.search_stashed("", {"tag": "code"}, "proj-1")
        assert len(results) == 1
        assert results[0].segment_id == "seg-2"

    @pytest.mark.unit
    def test_search_by_type(
        self,
        storage_layer: StorageLayer,
        sample_segment: ContextSegment,
        sample_segment_2: ContextSegment,
    ) -> None:
        """Test searching by type filter."""
        storage_layer.stash_segment(sample_segment, "proj-1")
        storage_layer.stash_segment(sample_segment_2, "proj-1")

        results = storage_layer.search_stashed("", {"type": "message"}, "proj-1")
        assert len(results) == 1
        assert results[0].segment_id == "seg-1"

        results = storage_layer.search_stashed("", {"type": "code"}, "proj-1")
        assert len(results) == 1
        assert results[0].segment_id == "seg-2"

    @pytest.mark.unit
    def test_search_combines_filters(
        self,
        storage_layer: StorageLayer,
        sample_segment: ContextSegment,
        sample_segment_2: ContextSegment,
    ) -> None:
        """Test that multiple filters are combined."""
        storage_layer.stash_segment(sample_segment, "proj-1")
        storage_layer.stash_segment(sample_segment_2, "proj-1")

        results = storage_layer.search_stashed(
            "", {"task_id": "task-1", "type": "message"}, "proj-1"
        )
        assert len(results) == 1
        assert results[0].segment_id == "seg-1"


class TestDeleteOperations:
    """Test delete operations."""

    @pytest.mark.unit
    def test_delete_from_active(
        self,
        storage_layer: StorageLayer,
        sample_segment: ContextSegment,
    ) -> None:
        """Test deleting from active storage."""
        storage_layer.store_segment(sample_segment, "proj-1")
        assert "seg-1" in storage_layer.active_segments["proj-1"]

        storage_layer.delete_segment("seg-1", "proj-1")
        assert "seg-1" not in storage_layer.active_segments.get("proj-1", {})

    @pytest.mark.unit
    def test_delete_from_stashed(
        self,
        storage_layer: StorageLayer,
        temp_storage_path: Path,
        sample_segment: ContextSegment,
    ) -> None:
        """Test deleting from stashed storage."""
        storage_layer.stash_segment(sample_segment, "proj-1")
        storage_layer.delete_segment("seg-1", "proj-1")

        with open(temp_storage_path) as f:
            data = json.load(f)

        assert len(data["projects"]["proj-1"]["segments"]) == 0

    @pytest.mark.unit
    def test_delete_nonexistent_segment(
        self,
        storage_layer: StorageLayer,
    ) -> None:
        """Test deleting a segment that doesn't exist."""
        # Should not raise an error
        storage_layer.delete_segment("nonexistent", "proj-1")
