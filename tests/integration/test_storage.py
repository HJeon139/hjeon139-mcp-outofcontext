"""Integration tests for storage layer.

Tests file format preservation, metadata handling, search functionality, and edge cases.
"""

import json
from pathlib import Path

import pytest

from hjeon139_mcp_outofcontext.storage import MDCStorage


@pytest.mark.integration
class TestStorageFileFormat:
    """Integration tests for file format preservation."""

    def test_yaml_frontmatter_preservation(self, tmp_path: Path) -> None:
        """Test that YAML frontmatter is correctly preserved."""
        storage = MDCStorage(storage_path=str(tmp_path))

        metadata = {
            "type": "note",
            "tags": ["test", "integration"],
            "custom_field": "custom_value",
            "nested": {"key": "value"},
        }
        text = "# Test Content\n\nThis is test content."

        storage.save_context("format-test", text, metadata)
        result = storage.load_context("format-test")

        assert result is not None
        assert result["text"] == text
        assert result["metadata"]["type"] == "note"
        assert result["metadata"]["tags"] == ["test", "integration"]
        assert result["metadata"]["custom_field"] == "custom_value"
        assert result["metadata"]["nested"]["key"] == "value"

    def test_markdown_body_preservation(self, tmp_path: Path) -> None:
        """Test that markdown body is correctly preserved."""
        storage = MDCStorage(storage_path=str(tmp_path))

        text = """# Heading

**Bold text** and *italic text*

- List item 1
- List item 2

```python
def hello():
    print("world")
```

More content here.
"""

        storage.save_context("markdown-test", text)
        result = storage.load_context("markdown-test")

        assert result is not None
        assert result["text"] == text

    def test_empty_text_handling(self, tmp_path: Path) -> None:
        """Test handling of empty text."""
        storage = MDCStorage(storage_path=str(tmp_path))

        storage.save_context("empty-text", "")
        result = storage.load_context("empty-text")

        assert result is not None
        assert result["text"] == ""

    def test_special_characters_in_text(self, tmp_path: Path) -> None:
        """Test special characters in markdown text."""
        storage = MDCStorage(storage_path=str(tmp_path))

        text = "Special chars: <>&\"'`\nNewline\ttab"
        storage.save_context("special-chars", text)
        result = storage.load_context("special-chars")

        assert result is not None
        assert result["text"] == text

    def test_unicode_characters(self, tmp_path: Path) -> None:
        """Test unicode characters in text."""
        storage = MDCStorage(storage_path=str(tmp_path))

        text = "Unicode: 你好 🌟 émojis 🚀"
        storage.save_context("unicode-test", text)
        result = storage.load_context("unicode-test")

        assert result is not None
        assert result["text"] == text

    def test_metadata_serialization_deserialization(self, tmp_path: Path) -> None:
        """Test that metadata is correctly serialized and deserialized."""
        storage = MDCStorage(storage_path=str(tmp_path))

        metadata = {
            "string": "value",
            "number": 42,
            "boolean": True,
            "list": [1, 2, 3],
            "dict": {"nested": "value"},
        }

        storage.save_context("serialization-test", "Content", metadata)
        result = storage.load_context("serialization-test")

        assert result is not None
        assert result["metadata"]["string"] == "value"
        assert result["metadata"]["number"] == 42
        assert result["metadata"]["boolean"] is True
        assert result["metadata"]["list"] == [1, 2, 3]
        assert result["metadata"]["dict"]["nested"] == "value"


@pytest.mark.integration
class TestStorageMetadataHandling:
    """Integration tests for metadata handling."""

    def test_default_metadata_fields(self, tmp_path: Path) -> None:
        """Test that default metadata fields are added."""
        storage = MDCStorage(storage_path=str(tmp_path))

        storage.save_context("defaults-test", "Content")
        result = storage.load_context("defaults-test")

        assert result is not None
        assert result["metadata"]["name"] == "defaults-test"
        assert "created_at" in result["metadata"]

    def test_custom_metadata_fields(self, tmp_path: Path) -> None:
        """Test custom metadata fields are preserved."""
        storage = MDCStorage(storage_path=str(tmp_path))

        metadata = {
            "type": "note",
            "category": "test",
            "priority": "high",
            "tags": ["integration", "test"],
        }

        storage.save_context("custom-metadata", "Content", metadata)
        result = storage.load_context("custom-metadata")

        assert result is not None
        assert result["metadata"]["type"] == "note"
        assert result["metadata"]["category"] == "test"
        assert result["metadata"]["priority"] == "high"
        assert result["metadata"]["tags"] == ["integration", "test"]
        # Default fields should also be present
        assert result["metadata"]["name"] == "custom-metadata"
        assert "created_at" in result["metadata"]

    def test_metadata_not_mutated(self, tmp_path: Path) -> None:
        """Test that original metadata dict is not mutated."""
        storage = MDCStorage(storage_path=str(tmp_path))

        original_metadata = {"type": "test", "custom": "value"}

        storage.save_context("mutation-test", "Content", original_metadata)

        # Original dict should not have been modified
        assert "name" not in original_metadata
        assert "created_at" not in original_metadata
        assert original_metadata == {"type": "test", "custom": "value"}

        # But saved metadata should have defaults
        result = storage.load_context("mutation-test")
        assert result is not None
        assert result["metadata"]["name"] == "mutation-test"
        assert "created_at" in result["metadata"]
        assert result["metadata"]["type"] == "test"
        assert result["metadata"]["custom"] == "value"

    def test_json_string_metadata_parsing(self, tmp_path: Path) -> None:
        """Test that JSON string metadata is correctly parsed."""
        storage = MDCStorage(storage_path=str(tmp_path))

        metadata_dict = {"type": "test", "category": "integration", "version": "0.1.0"}
        metadata_json = json.dumps(metadata_dict)

        # Pass as string (simulating MCP protocol behavior)
        storage.save_context("json-metadata", "Content", metadata_json)  # type: ignore[arg-type]

        result = storage.load_context("json-metadata")
        assert result is not None
        assert result["metadata"]["type"] == "test"
        assert result["metadata"]["category"] == "integration"
        assert result["metadata"]["version"] == "0.1.0"

    def test_none_metadata_handling(self, tmp_path: Path) -> None:
        """Test that None metadata is handled correctly."""
        storage = MDCStorage(storage_path=str(tmp_path))

        storage.save_context("none-metadata", "Content", None)

        result = storage.load_context("none-metadata")
        assert result is not None
        # Should have default fields even when metadata is None
        assert result["metadata"]["name"] == "none-metadata"
        assert "created_at" in result["metadata"]


@pytest.mark.integration
class TestStorageSearchFunctionality:
    """Integration tests for search functionality."""

    def test_search_in_text_content(self, tmp_path: Path) -> None:
        """Test searching in text content."""
        storage = MDCStorage(storage_path=str(tmp_path))

        storage.save_context("python-code", "Python code example")
        storage.save_context("javascript-code", "JavaScript code example")
        storage.save_context("note", "Just a note")

        results = storage.search_contexts("Python")
        assert len(results) == 1
        assert results[0]["name"] == "python-code"

    def test_search_in_metadata(self, tmp_path: Path) -> None:
        """Test searching in metadata."""
        storage = MDCStorage(storage_path=str(tmp_path))

        storage.save_context("note-1", "Some content", {"tags": ["python", "test"]})
        storage.save_context("note-2", "Other content", {"tags": ["js"]})

        results = storage.search_contexts("python")
        assert len(results) == 1
        assert results[0]["name"] == "note-1"

    def test_search_case_insensitive(self, tmp_path: Path) -> None:
        """Test that search is case-insensitive."""
        storage = MDCStorage(storage_path=str(tmp_path))

        storage.save_context("test", "Python Code Example")

        results = storage.search_contexts("python")
        assert len(results) == 1
        assert results[0]["name"] == "test"

        results = storage.search_contexts("PYTHON")
        assert len(results) == 1

    def test_search_multiple_matches(self, tmp_path: Path) -> None:
        """Test searching with multiple matches."""
        storage = MDCStorage(storage_path=str(tmp_path))

        storage.save_context("code-1", "Python code")
        storage.save_context("code-2", "Python code")
        storage.save_context("code-3", "JavaScript code")

        results = storage.search_contexts("code")
        assert len(results) == 3

        results = storage.search_contexts("Python")
        assert len(results) == 2

    def test_search_match_locations(self, tmp_path: Path) -> None:
        """Test that match locations are correctly identified."""
        storage = MDCStorage(storage_path=str(tmp_path))

        storage.save_context("test", "Python content", {"tags": ["python"]})

        results = storage.search_contexts("python")
        assert len(results) == 1
        assert "matches" in results[0]
        # Should match in both text and metadata
        assert "text" in results[0]["matches"] or "metadata" in results[0]["matches"]

    def test_search_empty_query(self, tmp_path: Path) -> None:
        """Test that empty query returns empty list."""
        storage = MDCStorage(storage_path=str(tmp_path))

        storage.save_context("test", "Content")
        results = storage.search_contexts("")
        assert results == []


@pytest.mark.integration
class TestStorageEdgeCases:
    """Integration tests for edge cases."""

    def test_invalid_filename_raises_error(self, tmp_path: Path) -> None:
        """Test that invalid filenames raise ValueError."""
        storage = MDCStorage(storage_path=str(tmp_path))

        # Empty name
        with pytest.raises(ValueError, match="cannot be empty"):
            storage.save_context("", "Content")

        # Invalid characters
        with pytest.raises(ValueError, match="must contain only"):
            storage.save_context("invalid name!", "Content")

        with pytest.raises(ValueError, match="must contain only"):
            storage.save_context("test@context", "Content")

    def test_missing_file_returns_none(self, tmp_path: Path) -> None:
        """Test that loading non-existent file returns None."""
        storage = MDCStorage(storage_path=str(tmp_path))

        result = storage.load_context("nonexistent")
        assert result is None

    def test_storage_path_handling(self, tmp_path: Path) -> None:
        """Test that storage path is correctly handled."""
        # Test with path that doesn't end with "contexts"
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
        """Test that storage path already ending with contexts doesn't double-append."""
        contexts_path = tmp_path / "custom_storage" / "contexts"
        contexts_path.mkdir(parents=True)

        storage = MDCStorage(storage_path=str(contexts_path))

        # Should use the path as-is since it already ends with contexts
        assert storage.storage_path == contexts_path
        assert storage.storage_path.exists()

        # Should be able to save files there
        storage.save_context("test", "content")
        assert (storage.storage_path / "test.mdc").exists()

    def test_overwrite_existing_context(self, tmp_path: Path) -> None:
        """Test that overwriting existing context works correctly."""
        storage = MDCStorage(storage_path=str(tmp_path))

        # Save initial context
        storage.save_context("overwrite", "Original content", {"version": 1})

        # Overwrite it
        storage.save_context("overwrite", "Updated content", {"version": 2})

        result = storage.load_context("overwrite")
        assert result is not None
        assert result["text"] == "Updated content"
        assert result["metadata"]["version"] == 2

    def test_bulk_operations_with_mixed_results(self, tmp_path: Path) -> None:
        """Test bulk operations with some successes and some failures."""
        storage = MDCStorage(storage_path=str(tmp_path))

        # Save one context
        storage.save_context("existing", "Content")

        # Try to load existing and non-existent
        results = storage.load_contexts(["existing", "nonexistent"])
        assert len(results) == 2
        assert results[0] is not None
        assert results[1] is None

        # Try to delete existing and non-existent
        delete_results = storage.delete_contexts(["existing", "nonexistent"])
        assert len(delete_results) == 2
        assert delete_results[0]["success"] is True
        assert delete_results[1]["success"] is False

    def test_large_text_content(self, tmp_path: Path) -> None:
        """Test handling of large text content."""
        storage = MDCStorage(storage_path=str(tmp_path))

        # Create large text (10KB)
        large_text = "A" * 10000

        storage.save_context("large-content", large_text)
        result = storage.load_context("large-content")

        assert result is not None
        assert len(result["text"]) == 10000
        assert result["text"] == large_text

    def test_complex_metadata_structure(self, tmp_path: Path) -> None:
        """Test handling of complex nested metadata structures."""
        storage = MDCStorage(storage_path=str(tmp_path))

        complex_metadata = {
            "level1": {
                "level2": {
                    "level3": "deep value",
                    "array": [1, 2, {"nested": "object"}],
                },
                "list": ["a", "b", "c"],
            },
            "tags": ["complex", "nested", "structure"],
        }

        storage.save_context("complex-metadata", "Content", complex_metadata)
        result = storage.load_context("complex-metadata")

        assert result is not None
        assert result["metadata"]["level1"]["level2"]["level3"] == "deep value"
        assert result["metadata"]["level1"]["level2"]["array"][2]["nested"] == "object"
        assert result["metadata"]["level1"]["list"] == ["a", "b", "c"]
        assert result["metadata"]["tags"] == ["complex", "nested", "structure"]
