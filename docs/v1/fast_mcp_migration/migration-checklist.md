# Migration Checklist

Complete checklist for tracking FastMCP migration progress.

## Phase 0: Pre-Migration (REQUIRED) ✅ COMPLETE

- [x] Create comprehensive integration test suite (`tests/integration/test_all_features.py`)
- [x] Create MCP protocol integration tests (`tests/integration/test_mcp_protocol.py`)
- [x] Create storage layer integration tests (`tests/integration/test_storage.py`)
- [x] Run all pre-migration tests and document baseline results
- [x] All pre-migration tests pass (73 tests)
- [x] Document expected outputs and behavior for comparison ([phase-0-baseline.md](phase-0-baseline.md))
- [x] Configure test environment (`hatch test -m integration` works)

See [Phase 0: Pre-Migration Testing](phase-0-pre-migration.md) for details.

## Phase 1: Basic Migration

- [ ] Update `pyproject.toml` dependencies (add fastmcp, keep mcp for client testing)
- [ ] Install FastMCP and test basic functionality
- [ ] Create new `fastmcp_server.py` with FastMCP instance
- [ ] Convert all tool handlers to use `@mcp.tool()` decorator
- [ ] Implement AppState injection pattern (middleware-based)
- [ ] Update `main.py` to use FastMCP with lifespan management
- [ ] Tools accessible via FastMCP (basic functionality working)

See [Phase 1: Basic Migration](phase-1-basic-migration.md) for details.

## Phase 2: Remove Tool Registry

- [ ] Remove `tool_registry.py` file
- [ ] Remove `register_crud_tools` function
- [ ] Update all imports (remove ToolRegistry references)
- [ ] Update tests (remove ToolRegistry tests if any)
- [ ] Verify tools still work correctly via FastMCP

See [Phase 2: Remove Tool Registry](phase-2-remove-registry.md) for details.

## Phase 2: Validation (CRITICAL)

- [ ] **Run all pre-migration integration tests** - all must pass
- [ ] **Compare outputs with baseline** - must be identical
- [ ] **Test MCP protocol directly** - tools/list and tools/call must work
- [ ] **Validate each tool individually** - put, get, list, search, delete (single and bulk)
- [ ] **Test error handling** - error responses must match baseline format
- [ ] **Test storage operations** - file format must be preserved
- [ ] **Test with MCP client library** - validate end-to-end functionality
- [ ] **Test with real clients** - Cursor and Claude Desktop must work
- [ ] **Test backward compatibility** - existing context files must work

See [Phase 5: Validation](phase-5-validation.md) for details.

## Phase 3: Additional Features (Optional - After Migration Validated)

- [ ] Add resources (optional - can expose contexts as MCP resources)
- [ ] Add prompts (optional - reusable prompt templates)
- [ ] Add storage backend support (optional - for caching with FastMCP middleware)
- [ ] Update tests to work with FastMCP's API (if needed)

See [Phase 3: FastMCP Features](phase-3-fastmcp-features.md) for details.

## Phase 4: Development Auto-Reload (Optional) ✅ COMPLETE

- [x] Install `mcp-hmr` as dev dependency
- [x] Create development wrapper script (`scripts/mcp_dev.py`)
- [x] Configure wrapper to initialize config, AppState, and register tools
- [x] Export FastMCP instance for `mcp-hmr` to use
- [x] Document development workflow and Cursor configuration

See [Phase 4: Development Auto-Reload](phase-4-auto-reload.md) for details.

## Phase 4: Finalization

- [ ] Update documentation (README, etc.)
- [ ] Remove deprecated code (MCPServer, ToolRegistry)
- [ ] Run full test suite (unit + integration)
- [ ] Final validation with real-world clients
- [ ] Update version and commit

See [Phase 6: Cleanup](phase-6-cleanup.md) for details.

## Notes

- Phase 0 is **REQUIRED** before starting migration
- Phase 2 (Validation) is **CRITICAL** and must pass before proceeding
- Phases 3 and 4 are optional
- All validation must pass before removing old code
