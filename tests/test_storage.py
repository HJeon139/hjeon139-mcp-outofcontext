"""Tests for MDC storage layer."""

from pathlib import Path

import pytest

from hjeon139_mcp_outofcontext.storage import MDCStorage


@pytest.fixture
def temp_storage_path(tmp_path: Path) -> Path:
    """Create a temporary storage path for testing."""
    storage_dir = tmp_path / "storage"
    storage_dir.mkdir()
    return storage_dir


@pytest.fixture
def mdc_storage(temp_storage_path: Path) -> MDCStorage:
    """Create an MDCStorage instance for testing."""
    return MDCStorage(storage_path=str(temp_storage_path))


@pytest.mark.unit
class TestMDCStorage:
    """Test MDCStorage class."""

    def test_save_and_load_context(self, mdc_storage: MDCStorage) -> None:
        """Test saving and loading a context."""
        name = "test-context"
        text = "# Test Context\n\nThis is a test."
        metadata = {"type": "note", "tags": ["test"]}

        mdc_storage.save_context(name, text, metadata)

        result = mdc_storage.load_context(name)
        assert result is not None
        assert result["text"] == text
        assert result["metadata"]["name"] == name
        assert result["metadata"]["type"] == "note"
        assert result["metadata"]["tags"] == ["test"]
        assert "created_at" in result["metadata"]

    def test_load_nonexistent_context(self, mdc_storage: MDCStorage) -> None:
        """Test loading a non-existent context returns None."""
        result = mdc_storage.load_context("nonexistent")
        assert result is None

    def test_save_context_overwrites(self, mdc_storage: MDCStorage) -> None:
        """Test that saving to existing name overwrites."""
        name = "test-context"
        text1 = "First version"
        text2 = "Second version"

        mdc_storage.save_context(name, text1)
        mdc_storage.save_context(name, text2)

        result = mdc_storage.load_context(name)
        assert result is not None
        assert result["text"] == text2

    def test_save_contexts_bulk(self, mdc_storage: MDCStorage) -> None:
        """Test bulk save operation."""
        contexts = [
            {"name": "context-1", "text": "Content 1", "metadata": {"type": "note"}},
            {"name": "context-2", "text": "Content 2", "metadata": {"type": "code"}},
        ]

        results = mdc_storage.save_contexts(contexts)
        assert len(results) == 2
        assert all(r["success"] for r in results)

        # Verify both contexts were saved
        assert mdc_storage.load_context("context-1") is not None
        assert mdc_storage.load_context("context-2") is not None

    def test_load_contexts_bulk(self, mdc_storage: MDCStorage) -> None:
        """Test bulk load operation."""
        # Save some contexts
        mdc_storage.save_context("context-1", "Content 1")
        mdc_storage.save_context("context-2", "Content 2")

        results = mdc_storage.load_contexts(["context-1", "context-2", "nonexistent"])
        assert len(results) == 3
        assert results[0] is not None
        assert results[1] is not None
        assert results[2] is None  # nonexistent

    def test_list_contexts(self, mdc_storage: MDCStorage) -> None:
        """Test listing all contexts."""
        # Save multiple contexts
        mdc_storage.save_context("context-1", "Content 1")
        mdc_storage.save_context("context-2", "Content 2")
        mdc_storage.save_context("context-3", "Content 3")

        contexts = mdc_storage.list_contexts()
        assert len(contexts) == 3

        names = {ctx["name"] for ctx in contexts}
        assert "context-1" in names
        assert "context-2" in names
        assert "context-3" in names

        # Should have required fields
        for ctx in contexts:
            assert "name" in ctx
            assert "created_at" in ctx
            assert "preview" in ctx

    def test_list_contexts_sorted_newest_first(self, mdc_storage: MDCStorage) -> None:
        """Test that contexts are sorted newest first."""
        mdc_storage.save_context("old", "Old content")
        mdc_storage.save_context("new", "New content")

        contexts = mdc_storage.list_contexts()
        assert len(contexts) == 2
        # Newest should be first
        assert contexts[0]["name"] == "new"

    def test_list_contexts_with_datetime_created_at(self, mdc_storage: MDCStorage) -> None:
        """Test that list_contexts handles datetime objects in created_at (YAML parsing edge case)."""
        from datetime import datetime

        # Create a context file with datetime object in metadata (simulating YAML parsing)
        import yaml

        # Save a context normally
        mdc_storage.save_context("test-context", "Test content")

        # Manually modify the file to have a datetime object (simulating YAML parsing)
        file_path = mdc_storage.storage_path / "test-context.mdc"
        with open(file_path) as f:
            content = f.read()

        # Parse and modify the YAML to include a datetime object
        parts = content.split("---\n", 2)
        frontmatter_str = parts[1]
        metadata = yaml.safe_load(frontmatter_str)
        # Add a datetime object (simulating what YAML might do)
        metadata["created_at"] = datetime(2024, 12, 17, 10, 0, 0)

        # Write back with datetime object
        new_frontmatter = yaml.dump(metadata, default_flow_style=False, sort_keys=False)
        new_content = f"---\n{new_frontmatter}---\n\n{parts[2]}"

        with open(file_path, "w") as f:
            f.write(new_content)

        # Now read it back - YAML will parse it as datetime
        with open(file_path) as f:
            read_content = f.read()
        read_parts = read_content.split("---\n", 2)
        read_metadata = yaml.safe_load(read_parts[1])

        # Verify YAML parsed it as datetime
        assert isinstance(read_metadata.get("created_at"), datetime)

        # This should not raise an error
        contexts = mdc_storage.list_contexts()
        assert len(contexts) == 1
        assert contexts[0]["name"] == "test-context"
        # created_at should be normalized to string
        assert isinstance(contexts[0]["created_at"], str)

    def test_delete_context(self, mdc_storage: MDCStorage) -> None:
        """Test deleting a context."""
        name = "test-context"
        mdc_storage.save_context(name, "Content")

        mdc_storage.delete_context(name)

        assert mdc_storage.load_context(name) is None

    def test_delete_nonexistent_context_raises(self, mdc_storage: MDCStorage) -> None:
        """Test that deleting non-existent context raises ValueError."""
        with pytest.raises(ValueError, match="not found"):
            mdc_storage.delete_context("nonexistent")

    def test_delete_contexts_bulk(self, mdc_storage: MDCStorage) -> None:
        """Test bulk delete operation."""
        # Save some contexts
        mdc_storage.save_context("context-1", "Content 1")
        mdc_storage.save_context("context-2", "Content 2")
        mdc_storage.save_context("context-3", "Content 3")

        results = mdc_storage.delete_contexts(["context-1", "context-2", "nonexistent"])
        assert len(results) == 3
        assert results[0]["success"] is True
        assert results[1]["success"] is True
        assert results[2]["success"] is False  # nonexistent

        # Verify deleted
        assert mdc_storage.load_context("context-1") is None
        assert mdc_storage.load_context("context-2") is None
        assert mdc_storage.load_context("context-3") is not None  # Not deleted

    def test_search_contexts(self, mdc_storage: MDCStorage) -> None:
        """Test searching contexts."""
        mdc_storage.save_context("python-code", "Python code example", {"tags": ["python"]})
        mdc_storage.save_context("javascript-code", "JavaScript code example", {"tags": ["js"]})
        mdc_storage.save_context("note", "Just a note", {})

        # Search in text
        results = mdc_storage.search_contexts("Python")
        assert len(results) == 1
        assert results[0]["name"] == "python-code"

        # Search in metadata
        results = mdc_storage.search_contexts("python")
        assert len(results) == 1
        assert results[0]["name"] == "python-code"

        # Search that matches multiple
        results = mdc_storage.search_contexts("code")
        assert len(results) == 2

    def test_search_contexts_empty_query(self, mdc_storage: MDCStorage) -> None:
        """Test that empty query returns empty list."""
        mdc_storage.save_context("test", "Content")
        results = mdc_storage.search_contexts("")
        assert results == []

    def test_name_validation(self, mdc_storage: MDCStorage) -> None:
        """Test that invalid names raise ValueError."""
        # Empty name
        with pytest.raises(ValueError, match="cannot be empty"):
            mdc_storage.save_context("", "Content")

        # Invalid characters
        with pytest.raises(ValueError, match="must contain only"):
            mdc_storage.save_context("invalid name!", "Content")

        with pytest.raises(ValueError, match="must contain only"):
            mdc_storage.save_context("test@context", "Content")

    def test_markdown_format_preserved(self, mdc_storage: MDCStorage) -> None:
        """Test that markdown formatting is preserved."""
        name = "markdown-test"
        text = """# Heading

**Bold text** and *italic text*

- List item 1
- List item 2

```python
def hello():
    print("world")
```
"""

        mdc_storage.save_context(name, text)
        result = mdc_storage.load_context(name)
        assert result is not None
        assert result["text"] == text

    def test_yaml_frontmatter_parsing(self, mdc_storage: MDCStorage) -> None:
        """Test that YAML frontmatter is correctly parsed."""
        name = "metadata-test"
        text = "Content"
        metadata = {
            "type": "note",
            "tags": ["test", "example"],
            "custom_field": "custom_value",
        }

        mdc_storage.save_context(name, text, metadata)
        result = mdc_storage.load_context(name)

        assert result is not None
        assert result["metadata"]["type"] == "note"
        assert result["metadata"]["tags"] == ["test", "example"]
        assert result["metadata"]["custom_field"] == "custom_value"
        assert result["metadata"]["name"] == name
        assert "created_at" in result["metadata"]

    def test_save_context_with_json_string_metadata(self, mdc_storage: MDCStorage) -> None:
        """Test that metadata passed as JSON string is correctly parsed."""
        import json

        name = "json-metadata-test"
        text = "Content"
        metadata_dict = {"type": "test", "category": "fix-verification", "version": "0.14.0"}
        metadata_json = json.dumps(metadata_dict)

        # Test the bug fix: metadata might come as JSON string through MCP protocol
        # We test this by passing a string directly (bypassing type hints)
        # This simulates what might happen when metadata is serialized/deserialized
        mdc_storage.save_context(name, text, metadata_json)  # type: ignore[arg-type]

        result = mdc_storage.load_context(name)
        assert result is not None
        assert result["metadata"]["type"] == "test"
        assert result["metadata"]["category"] == "fix-verification"
        assert result["metadata"]["version"] == "0.14.0"

    def test_save_context_with_none_metadata(self, mdc_storage: MDCStorage) -> None:
        """Test that None metadata is handled correctly."""
        name = "none-metadata-test"
        text = "Content"

        mdc_storage.save_context(name, text, None)

        result = mdc_storage.load_context(name)
        assert result is not None
        # Should have default fields even when metadata is None
        assert result["metadata"]["name"] == name
        assert "created_at" in result["metadata"]

    def test_save_context_metadata_not_mutated(self, mdc_storage: MDCStorage) -> None:
        """Test that original metadata dict is not mutated."""
        name = "metadata-mutation-test"
        text = "Content"
        original_metadata = {"type": "test", "custom": "value"}

        mdc_storage.save_context(name, text, original_metadata)

        # Original dict should not have been modified (name and created_at added)
        assert "name" not in original_metadata
        assert "created_at" not in original_metadata
        assert original_metadata == {"type": "test", "custom": "value"}

        # But saved metadata should have defaults
        result = mdc_storage.load_context(name)
        assert result is not None
        assert result["metadata"]["name"] == name
        assert "created_at" in result["metadata"]
        assert result["metadata"]["type"] == "test"
        assert result["metadata"]["custom"] == "value"

    def test_storage_path_appends_contexts(self, tmp_path: Path) -> None:
        """Test that storage_path correctly appends /contexts subdirectory."""
        # Test the bug fix where storage_path from config needs /contexts appended
        base_path = tmp_path / "custom_storage"
        base_path.mkdir()

        storage = MDCStorage(storage_path=str(base_path))

        # Should create contexts subdirectory
        assert storage.storage_path == base_path / "contexts"
        assert storage.storage_path.exists()

        # Should be able to save files there
        storage.save_context("test", "content")
        assert (storage.storage_path / "test.mdc").exists()

    def test_storage_path_with_existing_contexts_dir(self, tmp_path: Path) -> None:
        """Test that storage_path already ending with contexts doesn't double-append."""
        contexts_path = tmp_path / "custom_storage" / "contexts"
        contexts_path.mkdir(parents=True)

        storage = MDCStorage(storage_path=str(contexts_path))

        # Should use the path as-is since it already ends with contexts
        assert storage.storage_path == contexts_path
        assert storage.storage_path.exists()

        # Should be able to save files there
        storage.save_context("test", "content")
        assert (storage.storage_path / "test.mdc").exists()
