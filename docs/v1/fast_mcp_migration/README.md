# FastMCP Migration Documentation

This directory contains documentation for migrating from the standard MCP SDK to FastMCP.

## Document Structure

- **[Overview](overview.md)** - Introduction, critical requirements, why migrate, key concepts, current architecture, and recommended approaches
- **[Migration Checklist](migration-checklist.md)** - Complete checklist for tracking migration progress
- **[Risks and Considerations](risks-and-considerations.md)** - Key risks and mitigation strategies

## Phase Documentation

- **[Phase 0: Pre-Migration Testing](phase-0-pre-migration.md)** - Create comprehensive integration tests before migration
- **[Phase 1: Basic Migration](phase-1-basic-migration.md)** - Update dependencies and create FastMCP server structure
- **[Phase 2: Remove Tool Registry](phase-2-remove-registry.md)** - Remove custom ToolRegistry, simplify tool structure
- **[Phase 3: FastMCP Features](phase-3-fastmcp-features.md)** - Add optional FastMCP features (resources, prompts, storage backends)
- **[Phase 4: Development Auto-Reload](phase-4-auto-reload.md)** - Enable auto-reload for development using hot module replacement (mcp-hmr)
- **[Phase 5: Validation](phase-5-validation.md)** - Comprehensive testing and validation
- **[Phase 6: Cleanup](phase-6-cleanup.md)** - Documentation updates and code cleanup

## Code Examples

- **[Code Examples Directory](code-examples/)** - Reference implementations for FastMCP patterns

## Quick Start

1. Read the [Overview](overview.md) to understand the migration goals and approach
2. Follow [Phase 0](phase-0-pre-migration.md) to create pre-migration tests
3. Use the [Migration Checklist](migration-checklist.md) to track progress
4. Follow phases 1-6 sequentially
5. Refer to [Code Examples](code-examples/) for implementation reference

## Migration Progress

### ✅ Phase 0: Pre-Migration Testing (COMPLETE)

- ✅ Created comprehensive integration test suite (`tests/integration/test_all_features.py`)
- ✅ Created MCP protocol integration tests (`tests/integration/test_mcp_protocol.py`)
- ✅ Created storage layer integration tests (`tests/integration/test_storage.py`)
- ✅ All 73 integration tests passing
- ✅ Baseline behavior documented in [phase-0-baseline.md](phase-0-baseline.md)
- ✅ Tests can be run with `hatch test -m integration`

### ✅ Phase 1: Basic Migration (COMPLETE)

- ✅ Updated dependencies: replaced `mcp>=1.0.0` with `fastmcp>=2.11.0`
- ✅ Created `fastmcp_server.py` with FastMCP instance and `AppStateMiddleware` for dependency injection
- ✅ Created `fastmcp_tools.py` with all 5 CRUD tool wrappers using `@mcp.tool()` decorators
- ✅ Updated `main.py` with synchronous initialization (mcp.run() is synchronous)
- ✅ Added `register_tools()` function to `tools/crud/__init__.py`
- ✅ All 91 unit tests passing with 80% code coverage
- ✅ All 84 integration tests passing (verified feature parity)
- ✅ Tools verified working via direct MCP tool invocation
- ✅ Release pipeline passes (linting, formatting, type checking, tests, build)

**Implementation Details:**
- Tools use context state injection via `ctx.get_state("app_state")` (no global variables)
- Middleware pattern follows FastMCP best practices for dependency injection
- All existing handler functions preserved for feature parity
- Old `server.py` and `tool_registry.py` kept for Phase 2 removal

### ✅ Phase 2: Remove Tool Registry (COMPLETE)

- ✅ Removed `tool_registry.py` file (ToolRegistry no longer needed)
- ✅ Refactored package structure: separated CRUD operations from query operations
- ✅ Created `tools/query/` package for `list_context` and `search_context`
- ✅ Tools now use `@mcp.tool()` decorator directly in their implementation files
- ✅ Eliminated wrapper layer: each tool file contains implementation + decorator
- ✅ Removed `fastmcp_tools.py` wrapper file
- ✅ Split models: CRUD models in `tools/crud/models.py`, query models in `tools/query/models.py`
- ✅ Updated `fastmcp_server.py` to register tools from both `tools/crud/` and `tools/query/`
- ✅ Removed ToolRegistry tests

**New Package Structure:**
```
tools/
  crud/
    __init__.py          (register_tools - imports CRUD modules)
    models.py            (PutContextParams, GetContextParams, DeleteContextParams, ContextItem)
    put_context.py       (put_context with @mcp.tool() decorator)
    get_context.py       (get_context with @mcp.tool() decorator)
    delete_context.py    (delete_context with @mcp.tool() decorator)
  query/
    __init__.py          (register_tools - imports query modules)
    models.py            (ListContextParams, SearchContextParams)
    list_context.py      (list_context with @mcp.tool() decorator)
    search_context.py    (search_context with @mcp.tool() decorator)
```

**Architectural Improvement:**
- Each tool file is self-contained with `@mcp.tool()` decorator and implementation together
- Tools get `app_state` from FastMCP context (via middleware), not as function parameter
- Simpler, more maintainable structure following FastMCP best practices

**Next**: Proceed to [Phase 3: FastMCP Features](phase-3-fastmcp-features.md) (optional) or [Phase 5: Validation](phase-5-validation.md)

### ✅ Phase 4: Development Auto-Reload (COMPLETE)

Phase 4 enables auto-reload for development workflows using hot module replacement with stdio transport.

**Development Auto-Reload:**
- **Stdio transport**: Hot module replacement using `mcp-hmr` (external tool)
  - Maintains connection to Cursor during reloads
  - Only reloads changed modules (faster than full restart)
  - Requires development wrapper script for initialization

**Key Design Decisions:**
- Focus on improving development workflow without changing production setup
- Use `mcp-hmr` for stdio transport auto-reload
- Keep production configuration unchanged (continue using standard `python` command)
- Development mode uses `mcp-hmr` wrapper for auto-reload

**Implementation Details:**
- ✅ `mcp-hmr>=0.1.0` added to dev dependencies in `pyproject.toml`
- ✅ Development wrapper script created at `scripts/mcp_dev.py`
- ✅ Wrapper initializes config, AppState, and registers all tools before exporting `mcp` instance
- ✅ Configuration documented in [phase-4-auto-reload.md](phase-4-auto-reload.md)

**Usage:**
- **Development mode**: Update Cursor config to use `mcp-hmr` with `scripts.mcp_dev:mcp`
- **Production mode**: Use `hjeon139_mcp_outofcontext` command (installed via pip)

**Next**: Proceed to [Phase 6: Cleanup](phase-6-cleanup.md)

## Important Notes

⚠️ **Feature Parity is MANDATORY** - The migration must maintain 100% feature parity. See [Overview - Critical Requirements](overview.md#critical-requirements) for details.

✅ **Pre-Migration Testing is REQUIRED** - All integration tests must be created and pass before starting migration. See [Phase 0](phase-0-pre-migration.md).

🔍 **Validation is CRITICAL** - Extensive validation is required after migration. See [Phase 5](phase-5-validation.md).
