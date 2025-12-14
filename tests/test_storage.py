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
