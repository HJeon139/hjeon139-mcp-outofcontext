"""Comprehensive integration tests for all CRUD tools.

Tests all CRUD operations (put, get, list, search, delete) with single and bulk operations,
parameter validation, error cases, and edge cases.
"""

import json

import pytest

from hjeon139_mcp_outofcontext.app_state import AppState
from hjeon139_mcp_outofcontext.tools.crud.delete_context import handle_delete_context
from hjeon139_mcp_outofcontext.tools.crud.get_context import handle_get_context
from hjeon139_mcp_outofcontext.tools.crud.list_context import handle_list_context
from hjeon139_mcp_outofcontext.tools.crud.put_context import handle_put_context
from hjeon139_mcp_outofcontext.tools.crud.search_context import handle_search_context


@pytest.mark.integration
class TestPutContextIntegration:
    """Integration tests for put_context tool."""

    @pytest.mark.asyncio
    async def test_put_context_single(self, app_state: AppState) -> None:
        """Test single context put operation."""
        result = await handle_put_context(
            app_state, name="test-context", text="# Test\n\nContent here"
        )

        assert result["success"] is True
        assert result["operation"] == "single"
        assert result["name"] == "test-context"

        # Verify it was saved
        loaded = app_state.storage.load_context("test-context")
        assert loaded is not None
        assert loaded["text"] == "# Test\n\nContent here"

    @pytest.mark.asyncio
    async def test_put_context_with_metadata(self, app_state: AppState) -> None:
        """Test put context with metadata."""
        result = await handle_put_context(
            app_state,
            name="test-context",
            text="Content",
            metadata={"type": "note", "tags": ["test", "integration"]},
        )

        assert result["success"] is True

        loaded = app_state.storage.load_context("test-context")
        assert loaded is not None
        assert loaded["metadata"]["type"] == "note"
        assert loaded["metadata"]["tags"] == ["test", "integration"]

    @pytest.mark.asyncio
    async def test_put_context_bulk(self, app_state: AppState) -> None:
        """Test bulk context put operation."""
        contexts = [
            {"name": "context-1", "text": "Content 1"},
            {"name": "context-2", "text": "Content 2", "metadata": {"type": "note"}},
            {"name": "context-3", "text": "Content 3", "metadata": {"tags": ["bulk"]}},
        ]

        result = await handle_put_context(app_state, contexts=contexts)

        assert result["success"] is True
        assert result["operation"] == "bulk"
        assert result["count"] == 3
        assert len(result["results"]) == 3
        assert all(r["success"] for r in result["results"])

        # Verify all contexts were saved
        for ctx in contexts:
            loaded = app_state.storage.load_context(ctx["name"])
            assert loaded is not None
            assert loaded["text"] == ctx["text"]

    @pytest.mark.asyncio
    async def test_put_context_overwrites(self, app_state: AppState) -> None:
        """Test that put_context overwrites existing context."""
        # Create initial context
        await handle_put_context(app_state, name="overwrite-test", text="Original")

        # Overwrite it
        result = await handle_put_context(
            app_state, name="overwrite-test", text="Updated", metadata={"version": 2}
        )

        assert result["success"] is True

        # Verify it was overwritten
        loaded = app_state.storage.load_context("overwrite-test")
        assert loaded is not None
        assert loaded["text"] == "Updated"
        assert loaded["metadata"]["version"] == 2

    @pytest.mark.asyncio
    async def test_put_context_missing_name(self, app_state: AppState) -> None:
        """Test put context with missing name."""
        result = await handle_put_context(app_state, text="Content")

        assert "error" in result
        assert result["error"]["code"] == "INVALID_PARAMETER"

    @pytest.mark.asyncio
    async def test_put_context_missing_text(self, app_state: AppState) -> None:
        """Test put context with missing text."""
        result = await handle_put_context(app_state, name="test")

        assert "error" in result
        assert result["error"]["code"] == "INVALID_PARAMETER"

    @pytest.mark.asyncio
    async def test_put_context_invalid_name(self, app_state: AppState) -> None:
        """Test put context with invalid name."""
        result = await handle_put_context(app_state, name="invalid name!", text="Content")

        assert "error" in result
        assert result["error"]["code"] == "INVALID_PARAMETER"

    @pytest.mark.asyncio
    async def test_put_context_with_none_metadata(self, app_state: AppState) -> None:
        """Test put context with None metadata."""
        result = await handle_put_context(
            app_state, name="none-metadata", text="Content", metadata=None
        )

        assert result["success"] is True

        loaded = app_state.storage.load_context("none-metadata")
        assert loaded is not None
        # Should have default metadata fields
        assert "name" in loaded["metadata"]
        assert "created_at" in loaded["metadata"]

    @pytest.mark.asyncio
    async def test_put_context_with_json_string_metadata(self, app_state: AppState) -> None:
        """Test put context with JSON string metadata."""
        metadata_dict = {"type": "test", "category": "integration"}
        metadata_json = json.dumps(metadata_dict)

        result = await handle_put_context(
            app_state, name="json-metadata", text="Content", metadata=metadata_json
        )

        assert result["success"] is True

        loaded = app_state.storage.load_context("json-metadata")
        assert loaded is not None
        # Note: The storage layer handles JSON string parsing
        assert loaded["metadata"]["name"] == "json-metadata"


@pytest.mark.integration
class TestGetContextIntegration:
    """Integration tests for get_context tool."""

    @pytest.mark.asyncio
    async def test_get_context_single(self, app_state: AppState) -> None:
        """Test single context get operation."""
        # Save a context first
        app_state.storage.save_context("test-context", "# Test\n\nContent")

        result = await handle_get_context(app_state, name="test-context")

        assert result["success"] is True
        assert result["operation"] == "single"
        assert result["name"] == "test-context"
        assert result["text"] == "# Test\n\nContent"
        assert "metadata" in result

    @pytest.mark.asyncio
    async def test_get_context_not_found(self, app_state: AppState) -> None:
        """Test get context that doesn't exist."""
        result = await handle_get_context(app_state, name="nonexistent")

        assert "error" in result
        assert result["error"]["code"] == "NOT_FOUND"
        assert "nonexistent" in result["error"]["message"]

    @pytest.mark.asyncio
    async def test_get_context_bulk(self, app_state: AppState) -> None:
        """Test bulk context get operation."""
        # Save some contexts
        app_state.storage.save_context("context-1", "Content 1")
        app_state.storage.save_context("context-2", "Content 2")
        app_state.storage.save_context("context-3", "Content 3")

        result = await handle_get_context(
            app_state, names=["context-1", "context-2", "nonexistent"]
        )

        assert result["success"] is True
        assert result["operation"] == "bulk"
        assert result["count"] == 3
        assert len(result["contexts"]) == 3

        # Check results
        assert result["contexts"][0]["success"] is True
        assert result["contexts"][0]["name"] == "context-1"
        assert result["contexts"][1]["success"] is True
        assert result["contexts"][1]["name"] == "context-2"
        assert result["contexts"][2]["success"] is False  # nonexistent

    @pytest.mark.asyncio
    async def test_get_context_bulk_via_name_list(self, app_state: AppState) -> None:
        """Test bulk operation via name parameter as list."""
        app_state.storage.save_context("bulk-1", "Content 1")
        app_state.storage.save_context("bulk-2", "Content 2")

        result = await handle_get_context(app_state, name=["bulk-1", "bulk-2"])

        assert result["success"] is True
        assert result["operation"] == "bulk"
        assert result["count"] == 2
        assert len(result["contexts"]) == 2
        assert all(ctx["success"] for ctx in result["contexts"])

    @pytest.mark.asyncio
    async def test_get_context_missing_parameter(self, app_state: AppState) -> None:
        """Test get context with missing name/names parameter."""
        result = await handle_get_context(app_state)

        assert "error" in result
        assert result["error"]["code"] == "INVALID_PARAMETER"


@pytest.mark.integration
class TestListContextIntegration:
    """Integration tests for list_context tool."""

    @pytest.mark.asyncio
    async def test_list_context_empty(self, app_state: AppState) -> None:
        """Test listing contexts when none exist."""
        result = await handle_list_context(app_state)

        assert result["success"] is True
        assert result["count"] == 0
        assert result["contexts"] == []

    @pytest.mark.asyncio
    async def test_list_context_with_contexts(self, app_state: AppState) -> None:
        """Test listing contexts."""
        app_state.storage.save_context("context-1", "Content 1")
        app_state.storage.save_context("context-2", "Content 2")
        app_state.storage.save_context("context-3", "Content 3")

        result = await handle_list_context(app_state)

        assert result["success"] is True
        assert result["count"] == 3
        assert len(result["contexts"]) == 3

        names = {ctx["name"] for ctx in result["contexts"]}
        assert "context-1" in names
        assert "context-2" in names
        assert "context-3" in names

        # Verify each context has required fields
        for ctx in result["contexts"]:
            assert "name" in ctx
            assert "created_at" in ctx
            assert "preview" in ctx

    @pytest.mark.asyncio
    async def test_list_context_with_limit(self, app_state: AppState) -> None:
        """Test listing contexts with limit."""
        app_state.storage.save_context("context-1", "Content 1")
        app_state.storage.save_context("context-2", "Content 2")
        app_state.storage.save_context("context-3", "Content 3")

        result = await handle_list_context(app_state, limit=2)

        assert result["success"] is True
        assert result["count"] == 2
        assert len(result["contexts"]) == 2

    @pytest.mark.asyncio
    async def test_list_context_sorted_newest_first(self, app_state: AppState) -> None:
        """Test that contexts are sorted newest first."""
        import time

        app_state.storage.save_context("old", "Old content")
        time.sleep(0.1)  # Small delay to ensure different timestamps
        app_state.storage.save_context("new", "New content")

        result = await handle_list_context(app_state)

        assert result["success"] is True
        assert len(result["contexts"]) == 2
        # Newest should be first
        assert result["contexts"][0]["name"] == "new"
        assert result["contexts"][1]["name"] == "old"


@pytest.mark.integration
class TestSearchContextIntegration:
    """Integration tests for search_context tool."""

    @pytest.mark.asyncio
    async def test_search_context_in_text(self, app_state: AppState) -> None:
        """Test searching contexts by text content."""
        app_state.storage.save_context("python-code", "Python code example", {"tags": ["python"]})
        app_state.storage.save_context(
            "javascript-code", "JavaScript code example", {"tags": ["js"]}
        )

        result = await handle_search_context(app_state, query="Python")

        assert result["success"] is True
        assert result["query"] == "Python"
        assert result["count"] == 1
        assert len(result["matches"]) == 1
        assert result["matches"][0]["name"] == "python-code"

    @pytest.mark.asyncio
    async def test_search_context_in_metadata(self, app_state: AppState) -> None:
        """Test searching contexts by metadata."""
        app_state.storage.save_context("note-1", "Some content", {"tags": ["python", "test"]})
        app_state.storage.save_context("note-2", "Other content", {"tags": ["js"]})

        result = await handle_search_context(app_state, query="python")

        assert result["success"] is True
        assert result["count"] == 1
        assert result["matches"][0]["name"] == "note-1"

    @pytest.mark.asyncio
    async def test_search_context_multiple_matches(self, app_state: AppState) -> None:
        """Test searching with multiple matches."""
        app_state.storage.save_context("code-1", "Python code")
        app_state.storage.save_context("code-2", "Python code")
        app_state.storage.save_context("code-3", "JavaScript code")

        result = await handle_search_context(app_state, query="Python")

        assert result["success"] is True
        assert result["count"] == 2
        assert len(result["matches"]) == 2

        names = {match["name"] for match in result["matches"]}
        assert "code-1" in names
        assert "code-2" in names

    @pytest.mark.asyncio
    async def test_search_context_with_limit(self, app_state: AppState) -> None:
        """Test searching contexts with limit."""
        app_state.storage.save_context("code-1", "Python code")
        app_state.storage.save_context("code-2", "Python code")
        app_state.storage.save_context("code-3", "Python code")

        result = await handle_search_context(app_state, query="Python", limit=2)

        assert result["success"] is True
        assert result["count"] == 2
        assert len(result["matches"]) == 2

    @pytest.mark.asyncio
    async def test_search_context_empty_query(self, app_state: AppState) -> None:
        """Test searching with empty query."""
        app_state.storage.save_context("test", "Content")

        result = await handle_search_context(app_state, query="")

        assert "error" in result
        assert result["error"]["code"] == "INVALID_PARAMETER"

    @pytest.mark.asyncio
    async def test_search_context_case_insensitive(self, app_state: AppState) -> None:
        """Test that search is case-insensitive."""
        app_state.storage.save_context("test", "Python Code Example")

        result = await handle_search_context(app_state, query="python")

        assert result["success"] is True
        assert result["count"] == 1
        assert result["matches"][0]["name"] == "test"


@pytest.mark.integration
class TestDeleteContextIntegration:
    """Integration tests for delete_context tool."""

    @pytest.mark.asyncio
    async def test_delete_context_single(self, app_state: AppState) -> None:
        """Test single context delete operation."""
        # Save a context first
        app_state.storage.save_context("test-context", "Content")

        result = await handle_delete_context(app_state, name="test-context")

        assert result["success"] is True
        assert result["operation"] == "single"
        assert result["name"] == "test-context"

        # Verify it was deleted
        assert app_state.storage.load_context("test-context") is None

    @pytest.mark.asyncio
    async def test_delete_context_not_found(self, app_state: AppState) -> None:
        """Test deleting non-existent context."""
        result = await handle_delete_context(app_state, name="nonexistent")

        assert "error" in result
        assert result["error"]["code"] == "INVALID_PARAMETER"

    @pytest.mark.asyncio
    async def test_delete_context_bulk(self, app_state: AppState) -> None:
        """Test bulk context delete operation."""
        # Save some contexts
        app_state.storage.save_context("context-1", "Content 1")
        app_state.storage.save_context("context-2", "Content 2")
        app_state.storage.save_context("context-3", "Content 3")

        result = await handle_delete_context(
            app_state, names=["context-1", "context-2", "nonexistent"]
        )

        assert result["success"] is True
        assert result["operation"] == "bulk"
        assert result["count"] == 3
        assert len(result["results"]) == 3

        # Check results
        assert result["results"][0]["success"] is True
        assert result["results"][1]["success"] is True
        assert result["results"][2]["success"] is False  # nonexistent

        # Verify deleted
        assert app_state.storage.load_context("context-1") is None
        assert app_state.storage.load_context("context-2") is None
        assert app_state.storage.load_context("context-3") is not None  # Not deleted

    @pytest.mark.asyncio
    async def test_delete_context_bulk_via_name_list(self, app_state: AppState) -> None:
        """Test bulk delete via name parameter as list."""
        app_state.storage.save_context("bulk-1", "Content 1")
        app_state.storage.save_context("bulk-2", "Content 2")

        result = await handle_delete_context(app_state, name=["bulk-1", "bulk-2"])

        assert result["success"] is True
        assert result["operation"] == "bulk"
        assert result["count"] == 2

        # Verify deleted
        assert app_state.storage.load_context("bulk-1") is None
        assert app_state.storage.load_context("bulk-2") is None

    @pytest.mark.asyncio
    async def test_delete_context_missing_parameter(self, app_state: AppState) -> None:
        """Test delete context with missing name/names parameter."""
        result = await handle_delete_context(app_state)

        assert "error" in result
        assert result["error"]["code"] == "INVALID_PARAMETER"


@pytest.mark.integration
class TestEndToEndWorkflows:
    """Integration tests for end-to-end workflows."""

    @pytest.mark.asyncio
    async def test_put_get_list_search_delete_workflow(self, app_state: AppState) -> None:
        """Test complete workflow: put → get → list → search → delete."""
        # Put
        put_result = await handle_put_context(
            app_state,
            name="workflow-test",
            text="Test content for workflow",
            metadata={"type": "test", "workflow": True},
        )
        assert put_result["success"] is True

        # Get
        get_result = await handle_get_context(app_state, name="workflow-test")
        assert get_result["success"] is True
        assert get_result["text"] == "Test content for workflow"

        # List
        list_result = await handle_list_context(app_state)
        assert list_result["success"] is True
        assert list_result["count"] >= 1
        names = {ctx["name"] for ctx in list_result["contexts"]}
        assert "workflow-test" in names

        # Search
        search_result = await handle_search_context(app_state, query="workflow")
        assert search_result["success"] is True
        assert search_result["count"] >= 1
        match_names = {match["name"] for match in search_result["matches"]}
        assert "workflow-test" in match_names

        # Delete
        delete_result = await handle_delete_context(app_state, name="workflow-test")
        assert delete_result["success"] is True

        # Verify deleted
        get_result_after = await handle_get_context(app_state, name="workflow-test")
        assert "error" in get_result_after
        assert get_result_after["error"]["code"] == "NOT_FOUND"

    @pytest.mark.asyncio
    async def test_bulk_operations_workflow(self, app_state: AppState) -> None:
        """Test bulk operations workflow."""
        # Bulk put
        contexts = [
            {"name": "bulk-1", "text": "Content 1"},
            {"name": "bulk-2", "text": "Content 2"},
            {"name": "bulk-3", "text": "Content 3"},
        ]
        put_result = await handle_put_context(app_state, contexts=contexts)
        assert put_result["success"] is True
        assert put_result["count"] == 3

        # Bulk get
        get_result = await handle_get_context(app_state, names=["bulk-1", "bulk-2", "bulk-3"])
        assert get_result["success"] is True
        assert get_result["count"] == 3
        assert all(ctx["success"] for ctx in get_result["contexts"])

        # Bulk delete
        delete_result = await handle_delete_context(app_state, names=["bulk-1", "bulk-2", "bulk-3"])
        assert delete_result["success"] is True
        assert delete_result["count"] == 3
        assert all(r["success"] for r in delete_result["results"])

        # Verify all deleted
        for name in ["bulk-1", "bulk-2", "bulk-3"]:
            assert app_state.storage.load_context(name) is None
