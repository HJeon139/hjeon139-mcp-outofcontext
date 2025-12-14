# Phase 1: Basic Migration

This phase covers updating dependencies and creating the FastMCP server structure following best practices.

## Overview

Phase 1 involves:
1. Updating dependencies in `pyproject.toml`
2. Creating new FastMCP server structure with middleware
3. Converting tool handlers to use FastMCP decorators
4. Updating entry point with proper lifespan management

## Steps

### 1.1 Update Dependencies

**Update `pyproject.toml`:**

- Replace `mcp>=1.0.0` with `fastmcp>=2.11.0`
- Keep `pydantic>=2.0.0` (FastMCP uses it)
- Keep `pyyaml>=6.0.0` (still needed for storage)
- Consider adding `uvicorn` for HTTP/auto-reload support (optional, dev dependency)

**Note**: We may keep `mcp` package temporarily for client testing, but `fastmcp` replaces the server implementation.

### 1.2 Create New FastMCP Server Structure

**RECOMMENDED APPROACH: Use Middleware for Dependency Injection (Best Practice)**

Based on FastMCP documentation and best practices, we use middleware to inject AppState into the request context, avoiding global variables. This follows FastMCP's dependency injection patterns.

**Implementation**: See [Code Examples - fastmcp-server.py](code-examples/fastmcp-server.py) for the full implementation.

**Key points:**
- ✅ No global state access in tools - Uses context state via middleware
- ✅ Proper dependency injection - AppState injected via middleware pattern
- ✅ Testable - Can mock/inject different AppState instances
- ✅ Follows FastMCP patterns - Uses middleware for request-scoped dependencies
- ✅ Lifecycle management - AppState initialized before server starts, can add cleanup later

### 1.3 Migrate Tools to FastMCP Decorators

**RECOMMENDED APPROACH: Use Context State (via Middleware Injection)**

Convert tool handlers to use Context state for AppState access.

**Implementation Pattern:**

All tools will follow this pattern (see [Code Examples - tool-example.py](code-examples/tool-example.py)):

```python
@mcp.tool()
async def tool_name(
    param1: str,
    param2: int | None = None,
    ctx: Context = CurrentContext(),
) -> dict[str, Any]:
    """Tool description."""
    # Get AppState from context (injected by middleware)
    app_state: AppState = ctx.get_state("app_state")
    
    # Call existing handler function (maintains separation of concerns)
    return await handle_tool_name(app_state, param1=param1, param2=param2)
```

**Why this approach:**
1. ✅ Well-documented pattern - Context state is a standard FastMCP feature
2. ✅ No global variables - AppState accessed via request context
3. ✅ Request-scoped - Each request gets fresh access
4. ✅ Testable - Can set state in tests easily
5. ✅ Simple to implement - Uses built-in context.get_state()

### 1.4 Create Tool Registration Module

Update `src/hjeon139_mcp_outofcontext/tools/crud/__init__.py` to register tools:

```python
"""CRUD tools registration for FastMCP."""

def register_tools() -> None:
    """Register all CRUD tools with FastMCP.
    
    Tools are registered via @mcp.tool() decorators when imported.
    This function ensures all tool modules are imported.
    """
    # Import all tool modules (decorators register tools on import)
    from . import fastmcp_tools  # noqa: F401
```

### 1.5 Update Entry Point

**RECOMMENDED: Proper Lifespan Management**

**New `main.py`**: See [Code Examples - main-stdio.py](code-examples/main-stdio.py) for stdio transport.

**For HTTP Transport (Development Mode)**: See [Code Examples - main-http.py](code-examples/main-http.py) for HTTP transport with auto-reload.

**Why this approach:**
1. ✅ Proper lifespan management - Uses async context manager pattern
2. ✅ Clear initialization order - AppState initialized before server starts
3. ✅ Shutdown handling - Placeholder for cleanup logic
4. ✅ Follows Python best practices - No global state, proper resource management
5. ✅ Supports both transports - Separate entry points for stdio and HTTP

## Deliverables

- [ ] `pyproject.toml` updated with fastmcp dependency
- [ ] `src/hjeon139_mcp_outofcontext/fastmcp_server.py` created
- [ ] All tool handlers converted to use `@mcp.tool()` decorator
- [ ] `src/hjeon139_mcp_outofcontext/main.py` updated with lifespan management
- [ ] Tools accessible via FastMCP (basic functionality working)

## Next Steps

After Phase 1 is complete, proceed to [Phase 2: Remove Tool Registry](phase-2-remove-registry.md).

## Related Documentation

- [Overview - Recommended Approaches](overview.md#recommended-approaches-based-on-fastmcp-best-practices)
- [Code Examples](code-examples/)
- [Migration Checklist](migration-checklist.md#phase-1-basic-migration)
