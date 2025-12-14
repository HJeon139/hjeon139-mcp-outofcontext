# Phase 0: Baseline Test Results

This document captures the baseline behavior and test results for the current MCP SDK implementation. These results will be used to validate feature parity after migration to FastMCP.

## Test Execution

**Date**: 2024-12-XX  
**Test Command**: `hatch run pytest -m integration tests/integration/`  
**Total Tests**: 73  
**Status**: ✅ All tests passing

## Test Coverage

### Integration Test Files

1. **`tests/integration/test_all_features.py`** (36 tests)
   - Comprehensive CRUD tool tests
   - Single and bulk operations
   - Parameter validation
   - Error cases
   - End-to-end workflows

2. **`tests/integration/test_mcp_protocol.py`** (18 tests)
   - MCP client library integration tests
   - Tools/list endpoint validation
   - Tools/call endpoint validation
   - Schema generation and validation
   - End-to-end protocol workflows

3. **`tests/integration/test_storage.py`** (19 tests)
   - File format preservation
   - Metadata handling
   - Search functionality
   - Edge cases

## Expected Tool Behaviors

### put_context

**Single Operation:**
- Parameters: `name` (str), `text` (str), `metadata` (dict, optional)
- Response: `{"success": true, "operation": "single", "name": "..."}`
- Overwrites existing contexts with same name

**Bulk Operation:**
- Parameters: `contexts` (list[dict])
- Response: `{"success": true, "operation": "bulk", "count": N, "results": [...]}`
- Each result has `{"name": "...", "success": true/false}`

**Error Cases:**
- Missing `name`: `{"error": {"code": "INVALID_PARAMETER", "message": "'name' is required..."}}`
- Missing `text`: `{"error": {"code": "INVALID_PARAMETER", "message": "'text' is required..."}}`
- Invalid name (special characters): `{"error": {"code": "INVALID_PARAMETER", ...}}`

### get_context

**Single Operation:**
- Parameters: `name` (str)
- Response: `{"success": true, "operation": "single", "name": "...", "text": "...", "metadata": {...}}`
- Not found: `{"error": {"code": "NOT_FOUND", "message": "Context '...' not found"}}`

**Bulk Operation:**
- Parameters: `names` (list[str]) or `name` (list[str])
- Response: `{"success": true, "operation": "bulk", "count": N, "contexts": [...]}`
- Each context has `{"name": "...", "success": true/false, "text": "...", "metadata": {...}}` or `{"name": "...", "success": false, "error": "..."}`

### list_context

**Parameters:**
- `limit` (int, optional): Maximum number of results

**Response:**
- `{"success": true, "count": N, "contexts": [...]}`
- Contexts sorted by `created_at` (newest first)
- Each context has: `{"name": "...", "created_at": "...", "preview": "..."}`

### search_context

**Parameters:**
- `query` (str, required): Search query
- `limit` (int, optional): Maximum number of results

**Response:**
- `{"success": true, "query": "...", "count": N, "matches": [...]}`
- Each match has: `{"name": "...", "text": "...", "metadata": {...}, "matches": ["text"|"metadata"]}`
- Search is case-insensitive
- Searches in both text content and metadata

**Error Cases:**
- Empty query: `{"error": {"code": "INVALID_PARAMETER", "message": "'query' is required"}}`

### delete_context

**Single Operation:**
- Parameters: `name` (str)
- Response: `{"success": true, "operation": "single", "name": "..."}`
- Not found: `{"error": {"code": "INVALID_PARAMETER", ...}}`

**Bulk Operation:**
- Parameters: `names` (list[str]) or `name` (list[str])
- Response: `{"success": true, "operation": "bulk", "count": N, "results": [...]}`
- Each result has: `{"name": "...", "success": true/false}`

## MCP Protocol Behaviors

### tools/list

- Returns all 5 tools: `put_context`, `get_context`, `list_context`, `search_context`, `delete_context`
- Tool schemas are generated from Pydantic models
- Schemas have `$ref` references resolved (inlined)
- Schemas are simplified (nullable types handled, no `$defs` in final schema)
- Required fields are properly set

### tools/call

- Response format: `TextContent` with JSON string in `text` field
- Error responses: JSON with `{"error": {"code": "...", "message": "..."}}`
- Invalid tool name: Returns error in response (not MCP-level error)
- All tools work correctly via MCP protocol

## Storage Layer Behaviors

### File Format

- Files stored as `.mdc` (markdown with YAML frontmatter)
- Format: `---\n{frontmatter}\n---\n\n{body}`
- YAML frontmatter contains metadata
- Markdown body contains text content
- Special characters and unicode preserved

### Metadata

- Default fields: `name`, `created_at` (ISO format)
- Custom metadata fields preserved
- Original metadata dict not mutated
- JSON string metadata parsed correctly
- `None` metadata handled (defaults added)

### Search

- Case-insensitive search
- Searches in both text and metadata
- Returns match locations (`["text"]`, `["metadata"]`, or both)
- Empty query returns empty list

## Error Response Format

All errors follow this format:
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Error message"
  }
}
```

**Error Codes:**
- `INVALID_PARAMETER`: Invalid or missing parameters
- `NOT_FOUND`: Resource not found
- `INTERNAL_ERROR`: Unexpected server error

## Test Fixtures

All integration tests use:
- Temporary storage paths (isolated per test)
- `AppState` instances with temporary storage
- MCP client library for protocol tests
- Clean state between tests

## Notes

- All tests are deterministic (no random data)
- Tests are isolated (use temporary storage)
- MCP protocol tests use actual MCP client library
- Storage tests verify file format preservation
- Error messages match exactly (validated in tests)

## Next Steps

After migration to FastMCP:
1. Run all integration tests: `hatch run pytest -m integration tests/integration/`
2. Verify all 73 tests pass
3. Compare outputs byte-for-byte if needed
4. Test with real MCP clients (Cursor, Claude Desktop)
