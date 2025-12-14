# Phase 5: Testing and Validation

This phase covers comprehensive testing and validation to ensure feature parity after migration.

## Overview

Phase 5 is **CRITICAL** - it validates that the migration maintains 100% feature parity. All validation steps must pass before proceeding.

## Steps

### 5.1 Run Pre-Migration Integration Tests

**CRITICAL**: Run the integration tests created in [Phase 0](phase-0-pre-migration.md):

1. **Run All Integration Tests**:
   ```bash
   pytest tests/integration/ -v
   ```
   - All tests must pass
   - Compare outputs to baseline (should be identical)

2. **Run MCP Protocol Tests**:
   ```bash
   pytest tests/integration/test_mcp_protocol.py -v
   ```
   - Verify tool discovery works correctly
   - Verify tool execution matches baseline behavior

3. **Run Storage Tests**:
   ```bash
   pytest tests/integration/test_storage.py -v
   ```
   - Verify file format is preserved
   - Verify metadata handling works correctly

### 5.2 Direct MCP Server Validation

**Validate the migrated server directly**:

1. **Start Server Manually**:
   ```bash
   python -m hjeon139_mcp_outofcontext.main
   ```

2. **Test with MCP Client**:
   Use the validation scripts created in Phase 0. See [Code Examples - Validation Scripts](code-examples/validation-scripts.md).
   ```bash
   python scripts/test_mcp_server.py
   ```
   - Verify all tools are discoverable
   - Test each tool execution
   - Verify response formats match baseline

3. **Test Tool-by-Tool**:
   - Test `put_context` (single and bulk)
   - Test `get_context` (single and bulk)
   - Test `list_context` (with and without limit)
   - Test `search_context` (various queries)
   - Test `delete_context` (single and bulk)
   - Test error cases (invalid parameters, missing contexts, etc.)

4. **Compare with Baseline**:
   - Run same operations against old and new server
   - Compare outputs byte-for-byte
   - Verify identical error messages
   - Document any differences (should be zero)

### 5.3 Update Tests for FastMCP

- Update tests to work with FastMCP's API (if needed)
- Test tool registration and execution
- Test with both stdio and HTTP transports (if Phase 4 was implemented)
- Verify Pydantic validation still works
- **Ensure all tests still pass after updates**

### 5.4 Real-World Client Testing

**Test with actual MCP clients**:

1. **Test with Cursor**:
   - Configure Cursor to use migrated server
   - Test each tool through Cursor interface
   - Verify no regressions

2. **Test with Claude Desktop**:
   - Configure Claude Desktop to use migrated server
   - Test tool execution
   - Verify compatibility

3. **Test with Existing Context Files**:
   - Use existing `.out_of_context/contexts/` directory
   - Verify all existing contexts are readable
   - Verify search works with existing data
   - Test backward compatibility

### 5.5 Validation Checklist

- [ ] All pre-migration integration tests pass
- [ ] Outputs match baseline (byte-for-byte comparison)
- [ ] All tools discoverable via `tools/list`
- [ ] All tools execute correctly via `tools/call`
- [ ] Error responses match expected format
- [ ] Storage operations work identically
- [ ] File format is preserved
- [ ] Works with MCP client library
- [ ] Works with Cursor
- [ ] Works with Claude Desktop
- [ ] Backward compatible with existing context files
- [ ] No regressions in functionality

## Deliverables

- [ ] All validation tests passing
- [ ] Validation results documented
- [ ] Baseline comparison shows no differences
- [ ] Real-world client testing completed
- [ ] All issues resolved (if any found)

## Next Steps

After Phase 5 validation passes:
- If optional features are desired, proceed to [Phase 3: FastMCP Features](phase-3-fastmcp-features.md) or [Phase 4: HTTP Transport](phase-4-http-transport.md)
- Otherwise, proceed to [Phase 6: Cleanup](phase-6-cleanup.md)

## Related Documentation

- [Phase 0: Pre-Migration Testing](phase-0-pre-migration.md) - Pre-migration test creation
- [Code Examples - Validation Scripts](code-examples/validation-scripts.md) - Validation script examples
- [Overview - Validation Strategy](overview.md#validation-strategy)
- [Migration Checklist](migration-checklist.md#phase-2-validation-critical)
- [Risks and Considerations](risks-and-considerations.md)
