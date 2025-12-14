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

## Important Notes

⚠️ **Feature Parity is MANDATORY** - The migration must maintain 100% feature parity. See [Overview - Critical Requirements](overview.md#critical-requirements) for details.

✅ **Pre-Migration Testing is REQUIRED** - All integration tests must be created and pass before starting migration. See [Phase 0](phase-0-pre-migration.md).

🔍 **Validation is CRITICAL** - Extensive validation is required after migration. See [Phase 5](phase-5-validation.md).
