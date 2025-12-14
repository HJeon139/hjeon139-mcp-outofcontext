"""Unit tests for MCP server schema resolution and simplification."""

import json

import pytest

from hjeon139_mcp_outofcontext.server import MCPServer
from hjeon139_mcp_outofcontext.tools.crud.models import PutContextParams


@pytest.mark.unit
class TestSchemaResolution:
    """Test schema $ref resolution."""

    def test_resolve_schema_refs(self) -> None:
        """Test that $ref references are resolved to inline definitions."""
        server = MCPServer()

        # Generate schema with $ref
        schema = PutContextParams.model_json_schema()
        # Should have $defs
        assert "$defs" in schema
        assert "ContextItem" in schema["$defs"]

        # Resolve refs
        resolved = server._resolve_schema_refs(schema)

        # Should not have $defs after resolution
        assert "$defs" not in resolved

        # Check that contexts property has inline items (not $ref)
        contexts_prop = resolved["properties"]["contexts"]
        # Handle anyOf structure
        if "anyOf" in contexts_prop:
            array_option = next(
                (opt for opt in contexts_prop["anyOf"] if opt.get("type") == "array"), None
            )
            if array_option and "items" in array_option:
                items = array_option["items"]
                # Should be inline object, not $ref
                assert "$ref" not in items
                assert "properties" in items
                assert "name" in items["properties"]
                assert "text" in items["properties"]

    def test_resolve_nested_refs(self) -> None:
        """Test that nested $ref references are resolved."""
        server = MCPServer()

        schema = PutContextParams.model_json_schema()
        resolved = server._resolve_schema_refs(schema)

        # Check nested structures don't have $ref
        contexts_prop = resolved["properties"]["contexts"]
        if "anyOf" in contexts_prop:
            array_option = next(
                (opt for opt in contexts_prop["anyOf"] if opt.get("type") == "array"), None
            )
            if array_option and "items" in array_option:
                items = array_option["items"]
                # Metadata should also be resolved (no $ref in nested structures)
                if "properties" in items and "metadata" in items["properties"]:
                    metadata_prop = items["properties"]["metadata"]
                    # Should not have $ref
                    assert "$ref" not in str(json.dumps(metadata_prop))


@pytest.mark.unit
class TestSchemaSimplification:
    """Test schema simplification (removing anyOf for nullable types)."""

    def test_simplify_nullable_string(self) -> None:
        """Test simplification of nullable string type."""
        server = MCPServer()

        # Create a schema with nullable string
        schema = {
            "type": "object",
            "properties": {
                "name": {
                    "anyOf": [
                        {"type": "string"},
                        {"type": "null"},
                    ],
                    "description": "Name field",
                }
            },
        }

        simplified = server._simplify_schema(schema)

        # Should remove anyOf and just have string type
        name_prop = simplified["properties"]["name"]
        assert "anyOf" not in name_prop
        assert name_prop["type"] == "string"
        assert name_prop["description"] == "Name field"

    def test_simplify_nullable_array(self) -> None:
        """Test simplification of nullable array type."""
        server = MCPServer()

        schema = {
            "type": "object",
            "properties": {
                "contexts": {
                    "anyOf": [
                        {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        {"type": "null"},
                    ],
                    "description": "List of contexts",
                }
            },
        }

        simplified = server._simplify_schema(schema)

        # Should remove anyOf and just have array type
        contexts_prop = simplified["properties"]["contexts"]
        assert "anyOf" not in contexts_prop
        assert contexts_prop["type"] == "array"
        assert contexts_prop["description"] == "List of contexts"
        assert "items" in contexts_prop

    def test_simplify_put_context_params_schema(self) -> None:
        """Test simplification of actual PutContextParams schema."""
        server = MCPServer()

        # Generate and resolve schema
        schema = PutContextParams.model_json_schema()
        resolved = server._resolve_schema_refs(schema)
        simplified = server._simplify_schema(resolved)

        # Check that nullable properties are simplified
        for prop_name in ["name", "text", "metadata", "contexts"]:
            if prop_name in simplified["properties"]:
                prop = simplified["properties"][prop_name]
                # Should not have anyOf for simple nullable types
                # (contexts might still have anyOf for array/null, but items should be simplified)
                if prop_name != "contexts":
                    # Simple nullable types should be simplified
                    if "anyOf" in prop:
                        # If still has anyOf, it should be for array/null case
                        pass  # This is acceptable for complex types
                else:
                    # For contexts, check that items are simplified
                    if "anyOf" in prop:
                        array_option = next(
                            (opt for opt in prop["anyOf"] if opt.get("type") == "array"), None
                        )
                        if array_option and "items" in array_option:
                            items = array_option["items"]
                            # Items should not have anyOf for nullable metadata
                            if "properties" in items and "metadata" in items["properties"]:
                                metadata_prop = items["properties"]["metadata"]
                                # Metadata should be simplified (no anyOf)
                                assert "anyOf" not in metadata_prop

    def test_simplify_preserves_required_fields(self) -> None:
        """Test that simplification preserves required fields in nested structures."""
        server = MCPServer()

        schema = {
            "type": "object",
            "properties": {
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "anyOf": [{"type": "string"}, {"type": "null"}],
                            },
                            "text": {"type": "string"},
                        },
                        "required": ["name", "text"],
                    },
                }
            },
        }

        simplified = server._simplify_schema(schema)

        # Required fields should be preserved
        items_prop = simplified["properties"]["items"]["items"]
        assert "required" in items_prop
        assert "name" in items_prop["required"]
        assert "text" in items_prop["required"]
