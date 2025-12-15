"""Unit tests for query tool parameter models."""

import pytest
from pydantic import ValidationError

from hjeon139_mcp_outofcontext.tools.query.models import ListContextParams, SearchContextParams


@pytest.mark.unit
class TestListContextParams:
    """Test ListContextParams model."""

    def test_list_context_params_no_limit(self) -> None:
        """Test ListContextParams without limit."""
        params = ListContextParams()
        assert params.limit is None

    def test_list_context_params_with_limit(self) -> None:
        """Test ListContextParams with valid limit."""
        params = ListContextParams(limit=10)
        assert params.limit == 10

    def test_list_context_params_limit_minimum(self) -> None:
        """Test ListContextParams limit must be >= 1."""
        params = ListContextParams(limit=1)
        assert params.limit == 1

    def test_list_context_params_limit_validation_fails_zero(self) -> None:
        """Test ListContextParams limit validation fails for 0."""
        with pytest.raises(ValidationError) as exc_info:
            ListContextParams(limit=0)
        assert "limit" in str(exc_info.value)

    def test_list_context_params_limit_validation_fails_negative(self) -> None:
        """Test ListContextParams limit validation fails for negative values."""
        with pytest.raises(ValidationError) as exc_info:
            ListContextParams(limit=-1)
        assert "limit" in str(exc_info.value)

    def test_list_context_params_limit_type_string_coerced(self) -> None:
        """Test ListContextParams coerces valid integer strings to int."""
        # Pydantic v2 automatically coerces "10" to 10
        params = ListContextParams(limit="10")  # type: ignore[arg-type]
        assert params.limit == 10
        assert isinstance(params.limit, int)

    def test_list_context_params_limit_type_invalid_string_fails(self) -> None:
        """Test ListContextParams limit validation fails for invalid string."""
        with pytest.raises(ValidationError):
            ListContextParams(limit="not-a-number")  # type: ignore[arg-type]

    def test_list_context_params_limit_type_float_fails(self) -> None:
        """Test ListContextParams limit must be int, not float."""
        with pytest.raises(ValidationError):
            ListContextParams(limit=10.5)  # type: ignore[arg-type]


@pytest.mark.unit
class TestSearchContextParams:
    """Test SearchContextParams model."""

    def test_search_context_params_required_query(self) -> None:
        """Test SearchContextParams requires query field."""
        params = SearchContextParams(query="test query")
        assert params.query == "test query"
        assert params.limit is None

    def test_search_context_params_with_limit(self) -> None:
        """Test SearchContextParams with query and limit."""
        params = SearchContextParams(query="test", limit=5)
        assert params.query == "test"
        assert params.limit == 5

    def test_search_context_params_missing_query(self) -> None:
        """Test SearchContextParams requires query field."""
        with pytest.raises(ValidationError) as exc_info:
            SearchContextParams()
        assert "query" in str(exc_info.value)

    def test_search_context_params_empty_query_allowed(self) -> None:
        """Test SearchContextParams allows empty string query."""
        params = SearchContextParams(query="")
        assert params.query == ""

    def test_search_context_params_limit_minimum(self) -> None:
        """Test SearchContextParams limit must be >= 1."""
        params = SearchContextParams(query="test", limit=1)
        assert params.limit == 1

    def test_search_context_params_limit_validation_fails_zero(self) -> None:
        """Test SearchContextParams limit validation fails for 0."""
        with pytest.raises(ValidationError) as exc_info:
            SearchContextParams(query="test", limit=0)
        assert "limit" in str(exc_info.value)

    def test_search_context_params_limit_validation_fails_negative(self) -> None:
        """Test SearchContextParams limit validation fails for negative values."""
        with pytest.raises(ValidationError) as exc_info:
            SearchContextParams(query="test", limit=-1)
        assert "limit" in str(exc_info.value)

    def test_search_context_params_query_type_string(self) -> None:
        """Test SearchContextParams query must be string."""
        params = SearchContextParams(query="test string")
        assert isinstance(params.query, str)

    def test_search_context_params_query_type_int_fails(self) -> None:
        """Test SearchContextParams query must be string, not int."""
        with pytest.raises(ValidationError):
            SearchContextParams(query=123)  # type: ignore[arg-type]

    def test_search_context_params_limit_type_string_coerced(self) -> None:
        """Test SearchContextParams coerces valid integer strings to int."""
        # Pydantic v2 automatically coerces "10" to 10
        params = SearchContextParams(query="test", limit="10")  # type: ignore[arg-type]
        assert params.limit == 10
        assert isinstance(params.limit, int)

    def test_search_context_params_limit_type_invalid_string_fails(self) -> None:
        """Test SearchContextParams limit validation fails for invalid string."""
        with pytest.raises(ValidationError):
            SearchContextParams(query="test", limit="not-a-number")  # type: ignore[arg-type]
