"""Helper functions for stashing tools."""

import ast
import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


def create_error_response(
    code: str, message: str, details: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Create a standardized error response dictionary.

    Args:
        code: Error code (e.g., "INVALID_PARAMETER", "INTERNAL_ERROR")
        message: Error message
        details: Optional additional error details

    Returns:
        Dictionary with error structure
    """
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details or {},
        }
    }


def parse_json_or_literal(value: str, param_name: str) -> Any:
    """Parse a JSON string or Python literal string into a Python object.

    Args:
        value: String value to parse (JSON or Python literal)
        param_name: Name of the parameter (for error messages)

    Returns:
        Parsed Python object (dict, list, etc.)

    Raises:
        ValueError: If parsing fails
    """
    try:
        # Try JSON first
        return json.loads(value)
    except json.JSONDecodeError:
        try:
            # Fall back to Python literal evaluation
            return ast.literal_eval(value)
        except (ValueError, SyntaxError) as e:
            logger.error(f"Failed to parse {param_name}: {e}")
            raise ValueError(
                f"Invalid format in {param_name} (expected JSON or Python literal): {e!s}"
            ) from e


def parse_filters_param(filters: dict[str, Any] | str | None) -> dict[str, Any] | None:
    """Parse filters parameter from string or dict.

    Args:
        filters: Filters as dict, JSON string, Python literal string, or None

    Returns:
        Parsed filters dict or None

    Raises:
        ValueError: If parsing fails or filters is not a dict when provided as string
    """
    if filters is None:
        return None

    if isinstance(filters, dict):
        return filters

    if isinstance(filters, str):
        parsed_value = parse_json_or_literal(filters, "filters")
        if not isinstance(parsed_value, dict):
            raise ValueError("filters must be a dictionary")
        return parsed_value

    raise ValueError(f"filters must be a dict, string, or None, got {type(filters).__name__}")
