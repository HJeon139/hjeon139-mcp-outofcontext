# Task 01: Project Foundation and Core Infrastructure

## Dependencies

None

## Scope

Set up the foundational project structure and core infrastructure for the Context Management MCP Server. This includes:

- Set up project structure following Hatch standards
- Configure dependencies: `mcp`, `pydantic`, `tiktoken`
- Create core package structure: `src/out_of_context/`
- Implement base data models (`ContextSegment`, `ContextDescriptors`, etc.) from [09_interfaces.md](../design/09_interfaces.md)
- Set up MCP server skeleton with tool registry pattern
- Configure development environment (pytest, ruff, mypy)

## Acceptance Criteria

- Project builds and installs with `hatch build`
- All dependencies resolve correctly
- Basic MCP server starts and responds to protocol handshake
- Data models validate with Pydantic
- Test infrastructure runs successfully

## Implementation Details

### Project Structure

Create the following directory structure:

```
src/
  out_of_context/
    __init__.py
    models.py
    server.py
    tool_registry.py
tests/
  test_models.py
  test_server.py
```

### Dependencies

Update `pyproject.toml` to include:

```toml
[project]
dependencies = [
    "mcp>=1.0.0",
    "pydantic>=2.0.0",
    "tiktoken>=0.5.0",
]
```

### Data Models (`src/out_of_context/models.py`)

Implement the core data models from [09_interfaces.md](../design/09_interfaces.md):

- `ContextSegment` - Core segment model with all metadata fields
- `ContextDescriptors` - Input descriptor for platform context
- `TokenUsage` - Token count information
- `FileInfo` - File metadata
- `Message` - Message structure
- `SegmentSummary` - High-level segment information
- `TaskInfo` - Task metadata
- `PruningRecommendation` - Pruning action recommendation
- `AnalysisResult` - Context analysis results
- `WorkingSet` - Working set abstraction
- `StashResult` - Stashing operation result

All models should use Pydantic `BaseModel` for validation.

### MCP Server Skeleton (`src/out_of_context/server.py`)

Create a basic MCP server that:

- Initializes with MCP SDK
- Responds to protocol handshake
- Has placeholder for tool registration
- Handles basic protocol messages

### Tool Registry (`src/out_of_context/tool_registry.py`)

Implement a tool registry pattern that:

- Maintains a registry of tool name -> handler mappings
- Provides registration function
- Provides dispatch function
- Validates tool parameters using Pydantic schemas
- Returns structured tool results

### Development Environment

Ensure the following work:

- `hatch run test` - Runs pytest
- `hatch run lint-fix` - Runs ruff check and fix
- `hatch run fmt-fix` - Runs ruff format
- `hatch run typecheck` - Runs mypy

## Testing Approach

### Unit Tests

- Test data model validation (valid and invalid inputs)
- Test Pydantic serialization/deserialization
- Test tool registry registration and dispatch
- Test MCP server initialization

### Integration Tests

- Test MCP protocol handshake
- Test basic tool discovery (empty tool list initially)
- Test server startup and shutdown

### Test Files

- `tests/test_models.py` - Data model tests
- `tests/test_server.py` - Server skeleton tests
- `tests/test_tool_registry.py` - Tool registry tests

## References

- [Interfaces and Data Models](../design/09_interfaces.md) - Data model specifications
- [Core Architecture](../design/01_core_architecture.md) - Overall architecture
- [Constraints and Requirements](../design/07_constraints_requirements.md) - Dependency requirements
- [Hatch Documentation](https://hatch.pypa.io/) - Project management
- [MCP SDK Documentation](https://modelcontextprotocol.io/) - MCP protocol implementation

