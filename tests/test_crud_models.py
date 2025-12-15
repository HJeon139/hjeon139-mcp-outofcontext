"""Unit tests for CRUD tool parameter models."""

import pytest
from pydantic import ValidationError

from hjeon139_mcp_outofcontext.tools.crud.models import (
    ContextItem,
    DeleteContextParams,
    GetContextParams,
    PutContextParams,
)


@pytest.mark.unit
class TestContextItem:
    """Test ContextItem model."""

    def test_context_item_required_fields(self) -> None:
        """Test ContextItem requires name and text fields."""
        item = ContextItem(name="test-context", text="Content here")
        assert item.name == "test-context"
        assert item.text == "Content here"
        assert item.metadata is None

    def test_context_item_with_metadata(self) -> None:
        """Test ContextItem with optional metadata."""
        metadata = {"type": "note", "tags": ["test"]}
        item = ContextItem(name="test-context", text="Content", metadata=metadata)
        assert item.name == "test-context"
        assert item.text == "Content"
        assert item.metadata == metadata

    def test_context_item_missing_name(self) -> None:
        """Test ContextItem requires name field."""
        with pytest.raises(ValidationError) as exc_info:
            ContextItem(text="Content")
        assert "name" in str(exc_info.value)

    def test_context_item_missing_text(self) -> None:
        """Test ContextItem requires text field."""
        with pytest.raises(ValidationError) as exc_info:
            ContextItem(name="test")
        assert "text" in str(exc_info.value)

    def test_context_item_name_type(self) -> None:
        """Test ContextItem name must be string."""
        with pytest.raises(ValidationError):
            ContextItem(name=123, text="Content")  # type: ignore[arg-type]

    def test_context_item_text_type(self) -> None:
        """Test ContextItem text must be string."""
        with pytest.raises(ValidationError):
            ContextItem(name="test", text=123)  # type: ignore[arg-type]


@pytest.mark.unit
class TestPutContextParams:
    """Test PutContextParams model."""

    def test_put_context_params_single_operation(self) -> None:
        """Test PutContextParams for single operation."""
        params = PutContextParams(name="test", text="Content")
        assert params.name == "test"
        assert params.text == "Content"
        assert params.metadata is None
        assert params.contexts is None

    def test_put_context_params_single_with_metadata(self) -> None:
        """Test PutContextParams single operation with metadata."""
        metadata = {"type": "note"}
        params = PutContextParams(name="test", text="Content", metadata=metadata)
        assert params.name == "test"
        assert params.text == "Content"
        assert params.metadata == metadata
        assert params.contexts is None

    def test_put_context_params_bulk_operation(self) -> None:
        """Test PutContextParams for bulk operation."""
        contexts = [
            ContextItem(name="context-1", text="Content 1"),
            ContextItem(name="context-2", text="Content 2"),
        ]
        params = PutContextParams(contexts=contexts)
        assert params.name is None
        assert params.text is None
        assert params.metadata is None
        assert params.contexts == contexts

    def test_put_context_params_bulk_with_dicts(self) -> None:
        """Test PutContextParams bulk operation with dict items."""
        contexts = [
            {"name": "context-1", "text": "Content 1"},
            {"name": "context-2", "text": "Content 2", "metadata": {"type": "note"}},
        ]
        params = PutContextParams(contexts=contexts)  # type: ignore[arg-type]
        assert params.contexts is not None
        assert len(params.contexts) == 2
        assert params.contexts[0].name == "context-1"
        assert params.contexts[1].metadata == {"type": "note"}

    def test_put_context_params_all_optional(self) -> None:
        """Test PutContextParams allows all fields to be None."""
        params = PutContextParams()
        assert params.name is None
        assert params.text is None
        assert params.metadata is None
        assert params.contexts is None

    def test_put_context_params_metadata_type(self) -> None:
        """Test PutContextParams metadata must be dict or None."""
        params = PutContextParams(name="test", text="Content", metadata={"key": "value"})
        assert params.metadata == {"key": "value"}

        params_none = PutContextParams(name="test", text="Content", metadata=None)
        assert params_none.metadata is None


@pytest.mark.unit
class TestGetContextParams:
    """Test GetContextParams model."""

    def test_get_context_params_single_name(self) -> None:
        """Test GetContextParams with single name string."""
        params = GetContextParams(name="test-context")
        assert params.name == "test-context"
        assert params.names is None

    def test_get_context_params_name_as_list(self) -> None:
        """Test GetContextParams with name as list (bulk operation)."""
        params = GetContextParams(name=["context-1", "context-2"])
        assert params.name == ["context-1", "context-2"]
        assert params.names is None

    def test_get_context_params_names_list(self) -> None:
        """Test GetContextParams with names list."""
        params = GetContextParams(names=["context-1", "context-2"])
        assert params.names == ["context-1", "context-2"]
        assert params.name is None

    def test_get_context_params_all_optional(self) -> None:
        """Test GetContextParams allows all fields to be None."""
        params = GetContextParams()
        assert params.name is None
        assert params.names is None

    def test_get_context_params_name_type_string(self) -> None:
        """Test GetContextParams name accepts string."""
        params = GetContextParams(name="test")
        assert isinstance(params.name, str)

    def test_get_context_params_name_type_list(self) -> None:
        """Test GetContextParams name accepts list of strings."""
        params = GetContextParams(name=["test1", "test2"])
        assert isinstance(params.name, list)
        assert all(isinstance(n, str) for n in params.name)


@pytest.mark.unit
class TestDeleteContextParams:
    """Test DeleteContextParams model."""

    def test_delete_context_params_single_name(self) -> None:
        """Test DeleteContextParams with single name string."""
        params = DeleteContextParams(name="test-context")
        assert params.name == "test-context"
        assert params.names is None

    def test_delete_context_params_name_as_list(self) -> None:
        """Test DeleteContextParams with name as list (bulk operation)."""
        params = DeleteContextParams(name=["context-1", "context-2"])
        assert params.name == ["context-1", "context-2"]
        assert params.names is None

    def test_delete_context_params_names_list(self) -> None:
        """Test DeleteContextParams with names list."""
        params = DeleteContextParams(names=["context-1", "context-2"])
        assert params.names == ["context-1", "context-2"]
        assert params.name is None

    def test_delete_context_params_all_optional(self) -> None:
        """Test DeleteContextParams allows all fields to be None."""
        params = DeleteContextParams()
        assert params.name is None
        assert params.names is None

    def test_delete_context_params_name_type_string(self) -> None:
        """Test DeleteContextParams name accepts string."""
        params = DeleteContextParams(name="test")
        assert isinstance(params.name, str)

    def test_delete_context_params_name_type_list(self) -> None:
        """Test DeleteContextParams name accepts list of strings."""
        params = DeleteContextParams(name=["test1", "test2"])
        assert isinstance(params.name, list)
        assert all(isinstance(n, str) for n in params.name)
