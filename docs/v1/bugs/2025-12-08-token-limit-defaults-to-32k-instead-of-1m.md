# Issue: Token limit defaults to 32k instead of 1 million tokens

**Date**: 2025-12-08  
**Severity**: High (Launch Blocker)  
**Component**: Configuration / Token Limits / Analysis Engine  
**Status**: Open

## Description
The system configuration (`config.py`) defines `token_limit: int = 1000000` (1 million tokens) as the default, but the MCP tools and analysis engine use hardcoded defaults of 32,000 tokens throughout the codebase. The config's token limit is never actually used - it's defined but not connected to the tools. This means the system effectively stores only 32k tokens before eviction, which is far below the required 1 million tokens needed to match Cursor's native chat context size.

## Reproduction
1. Check `config.py`: `token_limit: int = 1000000` (1 million tokens)
2. Call `context_analyze_usage` without providing `token_limit` parameter
3. Observe the response shows `estimated_remaining_tokens: 32000` (not 1 million)
4. Check tool behavior - all tools default to 32k when `token_limit` is not provided

## Expected Behavior
- System should use the config's `token_limit` (1 million tokens) as the default
- Tools should read from config when `token_limit` parameter is not provided
- Analysis engine should use config value instead of hardcoded 32k defaults
- System should be able to store at least 1 million tokens before eviction

## Actual Behavior
- Config defines 1 million tokens but it's never used
- `models/params.py`: `token_limit: int | None = Field(32000, ...)` - hardcoded 32k default
- `analysis_engine.py`: Multiple functions default to `token_limit: int = 32000`
- `tools/monitoring.py`: Uses `32000` as default when token_limit is not provided
- `AppState` doesn't store or expose config's `token_limit` value
- System effectively limits to 32k tokens, not 1 million

## Impact
- **Launch Blocker**: System cannot meet requirement to match Cursor's native context size (1 million tokens)
- Users will hit eviction limits at 32k tokens instead of 1 million
- System claims to support 1 million tokens but actually only supports 32k
- Significant gap between advertised capability and actual behavior
- Poor user experience - context will be evicted much earlier than expected

## Root Cause
- Config's `token_limit` is defined but never connected to the application
- `AppState` doesn't extract or store `token_limit` from config
- All tools and analysis functions use hardcoded 32k defaults
- No mechanism to pass config values to tools

## Code Locations
- `src/hjeon139_mcp_outofcontext/config.py:16` - Defines `token_limit: int = 1000000`
- `src/hjeon139_mcp_outofcontext/models/params.py:18` - Hardcoded `Field(32000, ...)`
- `src/hjeon139_mcp_outofcontext/analysis_engine.py:26,42,84,170` - Multiple `token_limit: int = 32000` defaults
- `src/hjeon139_mcp_outofcontext/tools/monitoring.py:40,90` - Uses `32000` as default
- `src/hjeon139_mcp_outofcontext/app_state.py` - Doesn't extract `token_limit` from config

## Proposed Solution
1. **Extract token_limit from config in AppState**:
   ```python
   token_limit = self.config.get("token_limit", 1000000)
   self.token_limit = token_limit
   ```

2. **Pass config token_limit to tools**:
   - Update `AppState` to expose `token_limit`
   - Modify tools to use `app_state.token_limit` as default instead of hardcoded 32k
   - Update `AnalyzeUsageParams` to use config value as default

3. **Update analysis engine defaults**:
   - Change all `token_limit: int = 32000` to use config value
   - Or make them optional and pass config value from callers

4. **Update tool parameter defaults**:
   - Change `Field(32000, ...)` to use config value or make it truly optional

## Implementation Notes
- Need to thread config's `token_limit` through `AppState` → tools → analysis engine
- Consider making `token_limit` a required parameter in `AppState.__init__` or extract from config dict
- Update all hardcoded 32k values to use config default
- Ensure backward compatibility if tools are called with explicit `token_limit` parameter

## Related Issues
- Related to monitoring and analysis tools - they all need to use consistent token limits
- Related to eviction/pruning logic - needs to respect the correct token limit

