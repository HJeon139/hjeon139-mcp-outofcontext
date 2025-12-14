"""Tests for CRUD tool handlers."""

import pytest

from hjeon139_mcp_outofcontext.app_state import AppState
from hjeon139_mcp_outofcontext.tools.crud.delete_context import handle_delete_context
from hjeon139_mcp_outofcontext.tools.crud.get_context import handle_get_context
from hjeon139_mcp_outofcontext.tools.crud.list_context import handle_list_context
from hjeon139_mcp_outofcontext.tools.crud.put_context import handle_put_context
from hjeon139_mcp_outofcontext.tools.crud.search_context import handle_search_context


@pytest.mark.unit
class TestPutContext:
    """Test put_context tool handler."""

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
            metadata={"type": "note", "tags": ["test"]},
        )

        assert result["success"] is True

        loaded = app_state.storage.load_context("test-context")
        assert loaded is not None
        assert loaded["metadata"]["type"] == "note"
        assert loaded["metadata"]["tags"] == ["test"]

    @pytest.mark.asyncio
    async def test_put_context_bulk(self, app_state: AppState) -> None:
        """Test bulk context put operation."""
        contexts = [
            {"name": "context-1", "text": "Content 1"},
            {"name": "context-2", "text": "Content 2", "metadata": {"type": "note"}},
        ]

        result = await handle_put_context(app_state, contexts=contexts)

        assert result["success"] is True
        assert result["operation"] == "bulk"
        assert result["count"] == 2
        assert len(result["results"]) == 2
        assert all(r["success"] for r in result["results"])

    @pytest.mark.asyncio
    async def test_put_context_missing_name(self, app_state: AppState) -> None:
        """Test put context with missing name."""
        result = await handle_put_context(app_state, text="Content")

        assert "error" in result
        assert result["error"]["code"] == "INVALID_PARAMETER"

    @pytest.mark.asyncio
    async def test_put_context_invalid_name(self, app_state: AppState) -> None:
        """Test put context with invalid name."""
        result = await handle_put_context(app_state, name="invalid name!", text="Content")

        assert "error" in result
        assert result["error"]["code"] == "INVALID_PARAMETER"


@pytest.mark.unit
class TestGetContext:
    """Test get_context tool handler."""

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

    @pytest.mark.asyncio
    async def test_get_context_bulk(self, app_state: AppState) -> None:
        """Test bulk context get operation."""
        # Save some contexts
        app_state.storage.save_context("context-1", "Content 1")
        app_state.storage.save_context("context-2", "Content 2")

        result = await handle_get_context(
            app_state, names=["context-1", "context-2", "nonexistent"]
        )

        assert result["success"] is True
        assert result["operation"] == "bulk"
        assert result["count"] == 3
        assert len(result["contexts"]) == 3

        # Check results
        assert result["contexts"][0]["success"] is True
        assert result["contexts"][1]["success"] is True
        assert result["contexts"][2]["success"] is False  # nonexistent


@pytest.mark.unit
class TestListContext:
    """Test list_context tool handler."""

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

        result = await handle_list_context(app_state)

        assert result["success"] is True
        assert result["count"] == 2
        assert len(result["contexts"]) == 2

        names = {ctx["name"] for ctx in result["contexts"]}
        assert "context-1" in names
        assert "context-2" in names

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


@pytest.mark.unit
class TestSearchContext:
    """Test search_context tool handler."""

    @pytest.mark.asyncio
    async def test_search_context(self, app_state: AppState) -> None:
        """Test searching contexts."""
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
        result = await handle_search_context(app_state, query="")

        assert "error" in result
        assert result["error"]["code"] == "INVALID_PARAMETER"


@pytest.mark.unit
class TestDeleteContext:
    """Test delete_context tool handler."""

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
