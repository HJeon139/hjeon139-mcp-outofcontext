# FastMCP Migration Overview

This document provides an overview of the migration from the standard MCP SDK to FastMCP for the `hjeon139-mcp-outofcontext` package.

## ⚠️ Critical Requirements

### Feature Parity (MANDATORY)

**The migration MUST maintain 100% feature parity with the existing implementation.**

- All existing tools must work identically
- Response formats must match exactly
- Error handling must produce identical error messages
- Storage format must remain unchanged
- Client compatibility must be preserved

See [Migration Requirements](#migration-requirements) for detailed requirements.

### Pre-Migration Testing (REQUIRED)

**Before starting migration**:

1. Create comprehensive integration tests for all features
2. Document baseline behavior and outputs
3. Validate all tests pass with existing implementation
4. Use these tests to validate post-migration parity

See [Phase 0: Pre-Migration Testing](phase-0-pre-migration.md) for details.

### Validation Strategy (MANDATORY)

**After migration**:

1. Run all pre-migration integration tests - must pass identically
2. Test MCP server directly using MCP client library
3. Compare outputs byte-for-byte with baseline
4. Test with real MCP clients (Cursor, Claude Desktop)
5. Verify backward compatibility with existing context files

**No migration code should be merged until all validation passes.**

See [Phase 5: Validation](phase-5-validation.md) for detailed validation steps.

## Why Migrate to FastMCP?

FastMCP 2.0 extends beyond basic MCP protocol implementation, providing:

1. **Additional MCP Features**:
   - **Prompts**: Reusable templates for LLM interactions
   - **Resources**: Structured data sources (similar to GET endpoints)
   - **Context Management**: Built-in context handling with request isolation
   - **Storage Backends**: Flexible storage options (disk, Redis, in-memory)

2. **Production-Ready Features**:
   - Advanced MCP patterns (server composition, proxying, OpenAPI/FastAPI generation)
   - Enterprise authentication (Google, GitHub, Azure, Auth0, WorkOS)
   - Deployment tools and testing frameworks
   - Comprehensive client libraries

3. **Development Experience**:
   - **Auto-reload with Uvicorn**: Use `uvicorn` with `--reload` for hot-reloading during development
   - HTTP transport mode: Can serve via HTTP/SSE in addition to stdio
   - Pythonic decorator-based API: Cleaner, less boilerplate
   - Better dependency injection support

## FastMCP Key Concepts

### Core Architecture

FastMCP uses a simple decorator-based approach:

```python
from fastmcp import FastMCP

mcp = FastMCP("Demo 🚀")

@mcp.tool
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b

if __name__ == "__main__":
    mcp.run()
```

### Tools

Tools in FastMCP are decorated functions that provide functionality (like POST endpoints):

```python
@mcp.tool()
def my_tool(param1: str, param2: int) -> str:
    """Tool description"""
    return "result"
```

- FastMCP automatically generates schema from type hints and docstrings
- Pydantic models are supported for complex parameter validation
- Tools are automatically registered when decorated

### Resources

Resources provide structured data sources (like GET endpoints):

```python
@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a personalized greeting"""
    return f"Hello, {name}!"
```

### Prompts

Prompts are reusable templates for LLM interactions:

```python
@mcp.prompt("greeting")
def greeting_prompt(name: str) -> str:
    return f"Hello, {name}!"
```

### Context and Dependency Injection

FastMCP provides a `Context` object for each MCP request with isolated state:

```python
from fastmcp.dependencies import CurrentContext
from fastmcp.server.context import Context

@mcp.tool
async def process_file(file_uri: str, ctx: Context = CurrentContext()) -> str:
    """Processes a file, using context for logging and resource access."""
    await ctx.info(f"Processing {file_uri}")
    return "Processed file"
```

- Context is injected via `CurrentContext()` dependency
- Each request gets its own isolated context
- Context provides logging, progress reporting, resource access, etc.
- State management: `ctx.set_state(key, value)` and `ctx.get_state(key)`

### Storage Backends

FastMCP supports multiple storage backends for caching and state. See [Phase 3: FastMCP Features](phase-3-fastmcp-features.md) for details.

### Transport Modes

FastMCP supports two transport modes:

1. **STDIO (default)**: For local development and desktop apps
2. **HTTP**: For network deployment with multiple concurrent clients

See [Phase 4: HTTP Transport](phase-4-http-transport.md) for details.

### Auto-Reload with Uvicorn

For development, FastMCP can run as an ASGI app with auto-reload. See [Phase 4: HTTP Transport](phase-4-http-transport.md) for details.

## Current Architecture Analysis

### Current MCP Server Structure

Our current implementation uses:

1. **MCPServer Class** (`server.py`):
   - Manages MCP server lifecycle
   - Registers tools via `ToolRegistry`
   - Handles MCP protocol handlers (`tools/list`, `tools/call`)
   - Uses `AppState` for dependency injection

2. **ToolRegistry** (`tool_registry.py`):
   - Custom registry for tool registration and dispatch
   - Supports Pydantic models for parameter validation
   - Provides dependency injection via `AppState`

3. **AppState** (`app_state.py`):
   - Container for application state (storage, config)
   - Lifecycle management via async context manager
   - Dependency injection for tools

4. **Tools** (`tools/crud/`):
   - Individual tool handlers (put_context, get_context, list_context, search_context, delete_context)
   - Each handler receives `app_state` as first parameter
   - Pydantic models for parameter validation

5. **Storage** (`storage/mdc_storage.py`):
   - MDCStorage for markdown files with YAML frontmatter
   - File-based storage in `.out_of_context/contexts/`

### Current Entry Point

```python
# main.py
async def main() -> None:
    config = load_config()
    server = MCPServer(config=config)
    await server.run()
```

Uses stdio transport exclusively.

## Migration Requirements

### Feature Parity Requirement

**CRITICAL**: The migration MUST maintain 100% feature parity with the existing MCP SDK implementation. All existing features must work identically after migration:

1. **All Tools Must Work Identically**:
   - `put_context` (single and bulk operations)
   - `get_context` (single and bulk operations)
   - `list_context` (with optional limit)
   - `search_context` (with query and optional limit)
   - `delete_context` (single and bulk operations)

2. **Parameter Validation**:
   - Pydantic model validation must work identically
   - Error messages must be the same format
   - Bulk operation support must be maintained

3. **Storage Layer**:
   - MDC file format must remain unchanged
   - Storage path configuration must work identically
   - File operations must have same behavior

4. **MCP Protocol Compliance**:
   - Tools must be discoverable via `tools/list`
   - Tool calls via `tools/call` must work identically
   - Response format must match existing implementation
   - Error handling must produce same error format

5. **Client Compatibility**:
   - Must work with existing MCP clients (Cursor, Claude Desktop, etc.)
   - Must work with stdio transport (default)
   - Configuration format must remain compatible

### Pre-Migration Integration Tests

**BEFORE starting migration**, we MUST have comprehensive integration tests that validate all features work correctly. See [Phase 0: Pre-Migration Testing](phase-0-pre-migration.md) for details.

### Validation Strategy

After migration, validate changes using multiple approaches. See [Phase 5: Validation](phase-5-validation.md) for detailed validation steps.

## Recommended Approaches (Based on FastMCP Best Practices)

After researching FastMCP documentation and best practices, we've selected the following approaches:

### 1. Dependency Injection: **Middleware Pattern** ✅

**Selected**: Use `Middleware` to inject `AppState` into request context state.

**Why**: 
- ✅ No global variables in tools (follows FastMCP best practices)
- ✅ Request-scoped access via `ctx.get_state("app_state")`
- ✅ Well-documented pattern in FastMCP
- ✅ Testable (can inject mock AppState)
- ✅ Proper separation of concerns

**Implementation**: See [Phase 1: Basic Migration](phase-1-basic-migration.md) for `AppStateMiddleware` implementation.

### 2. State Management: **Lifespan Context Manager** ✅

**Selected**: Use `@asynccontextmanager` for proper lifecycle management.

**Why**:
- ✅ Follows Python best practices for resource management
- ✅ Clear initialization and cleanup phases
- ✅ Compatible with both stdio and HTTP transports
- ✅ No global state access during normal operation

**Implementation**: See [Phase 1: Basic Migration](phase-1-basic-migration.md) for lifespan implementation.

### 3. Tool Implementation: **Context State Access** ✅

**Selected**: Tools access AppState via `ctx.get_state("app_state")` (injected by middleware).

**Why**:
- ✅ Uses FastMCP's built-in context state feature
- ✅ No direct global access
- ✅ Request-scoped (each request gets fresh access)
- ✅ Maintains existing handler functions (separation of concerns)

**Implementation**: All tools follow pattern:
```python
@mcp.tool()
async def tool_name(..., ctx: Context = CurrentContext()) -> dict[str, Any]:
    app_state = ctx.get_state("app_state")
    return await handle_tool_name(app_state, ...)
```

See [Code Examples](code-examples/) for full implementation examples.

### 4. Entry Point: **Lifespan-Managed Initialization** ✅

**Selected**: Initialize AppState in lifespan context manager before server starts.

**Why**:
- ✅ Proper resource lifecycle management
- ✅ Works with both stdio and HTTP transports
- ✅ Clear initialization order
- ✅ Follows FastAPI/FastMCP patterns

**Implementation**: See [Phase 1: Basic Migration](phase-1-basic-migration.md) for entry point implementation.

## Migration Phases

The migration is organized into phases:

1. **[Phase 0: Pre-Migration Testing](phase-0-pre-migration.md)** - Create comprehensive integration tests
2. **[Phase 1: Basic Migration](phase-1-basic-migration.md)** - Update dependencies and create FastMCP server
3. **[Phase 2: Remove Tool Registry](phase-2-remove-registry.md)** - Remove custom ToolRegistry
4. **[Phase 3: FastMCP Features](phase-3-fastmcp-features.md)** - Add optional FastMCP features
5. **[Phase 4: HTTP Transport](phase-4-http-transport.md)** - Add HTTP transport and auto-reload
6. **[Phase 5: Validation](phase-5-validation.md)** - Comprehensive testing and validation
7. **[Phase 6: Cleanup](phase-6-cleanup.md)** - Documentation and code cleanup

See [Migration Checklist](migration-checklist.md) for tracking progress.

## Benefits After Migration

1. **Simpler Code**: Less boilerplate, decorator-based tool registration
2. **Additional Features**: Access to prompts, resources, storage backends
3. **Better DX**: Auto-reload with uvicorn for faster development
4. **HTTP Transport**: Option to serve via HTTP for multi-client scenarios
5. **Production Features**: Access to authentication, deployment tools, etc.
6. **Active Maintenance**: FastMCP is actively maintained and extended

## References

- FastMCP Documentation: https://gofastmcp.com/getting-started/welcome
- FastMCP Installation: https://gofastmcp.com/getting-started/installation
- FastMCP Servers: https://gofastmcp.com/servers/overview
- FastMCP Context: https://gofastmcp.com/servers/context
- FastMCP Deployment: https://gofastmcp.com/servers/deployment
- Uvicorn Auto-Reload: https://www.uvicorn.org/settings/
