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
- **[Phase 4: HTTP Transport](phase-4-http-transport.md)** - Add HTTP transport support and auto-reload
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

**Next**: Proceed to [Phase 2: Remove Tool Registry](phase-2-remove-registry.md)

## Important Notes

⚠️ **Feature Parity is MANDATORY** - The migration must maintain 100% feature parity. See [Overview - Critical Requirements](overview.md#critical-requirements) for details.

✅ **Pre-Migration Testing is REQUIRED** - All integration tests must be created and pass before starting migration. See [Phase 0](phase-0-pre-migration.md).

🔍 **Validation is CRITICAL** - Extensive validation is required after migration. See [Phase 5](phase-5-validation.md).
