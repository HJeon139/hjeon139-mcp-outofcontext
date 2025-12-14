# Phase 2: Remove Custom Tool Registry

This phase involves removing the custom ToolRegistry since FastMCP handles tool registration automatically.

## Overview

Phase 2 involves:
1. Removing the ToolRegistry class
2. Simplifying tool structure
3. Cleaning up unused code

## Steps

### 2.1 Remove ToolRegistry

- FastMCP handles tool registration automatically via decorators
- Remove `tool_registry.py`
- Remove `register_crud_tools` function (now handled by decorators)
- Tools are registered via `@mcp.tool()` decorator automatically

### 2.2 Simplify Tool Structure

- Each tool handler is already a standalone function with `@mcp.tool()` decorator
- Keep Pydantic models for validation (FastMCP uses function signatures, but we can still use Pydantic internally if needed)
- Tool registration happens automatically when modules are imported (due to decorators)

### 2.3 Update Imports

- Remove all imports of `ToolRegistry`
- Remove all imports of `register_crud_tools`
- Update any code that referenced the old registry

## Deliverables

- [ ] `tool_registry.py` file removed
- [ ] `register_crud_tools` function removed
- [ ] All imports updated
- [ ] Tests updated (remove ToolRegistry tests if any)
- [ ] Tools still work correctly via FastMCP

## Next Steps

After Phase 2 is complete, proceed to [Phase 3: FastMCP Features](phase-3-fastmcp-features.md) (optional) or [Phase 5: Validation](phase-5-validation.md) if skipping optional features.

## Related Documentation

- [Overview - Current Architecture](overview.md#current-architecture-analysis)
- [Migration Checklist](migration-checklist.md)
