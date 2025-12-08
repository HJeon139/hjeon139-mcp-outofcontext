# Issue: Tool responses lack impact/next-step guidance per requirements

**Date**: 2025-12-08  
**Severity**: Low  
**Component**: monitoring / MCP responses  
**Status**: Partially Fixed (2025-12-08)

## Description
Requirement 15 (docs/v0/requirements.md) expects tool calls to provide clear feedback on what context was affected, estimated impact on usage, and recommended next steps. Current MCP handlers (e.g., `context_stash`, `context_search_stashed`, `context_retrieve_stashed`, `context_analyze_usage`) return raw results without explicit guidance or impact summaries. Users must infer usage effects and follow-on actions.

## Reproduction
1. Call `context_stash` or `context_retrieve_stashed`: responses contain IDs and tokens but no guidance on next actions.
2. Call `context_search_stashed`: returns matches without impact/next-step suggestions.
3. Call `context_analyze_usage`: returns metrics, but not contextual recommendations tied to actions.

## Expected Behavior
- Each tool response should include brief guidance (e.g., recommended prune/stash/restore actions, estimated usage change).
- Monitoring should surface clear next steps when thresholds are approached.

## Actual Behavior
- Responses are data-only; no guidance or impact narrative is included.

## Environment
- Python: (per project)
- Platform: darwin

## Impact
- Higher agent effort to decide next actions; risk of missed pruning/stashing opportunities.

## Proposed Solution (if known)
- Small-scope fix to reduce agent ramp-up:
  - Add concise “what changed” + “suggested next step” strings to MCP tool responses (`context_stash`, `context_retrieve_stashed`, `context_search_stashed`, `context_analyze_usage`), including estimated token impact where available.
  - Add quick-start prompts/examples in each tool description (e.g., “To stash the current working set: call context_get_working_set → context_stash with returned IDs”) so agents can use tools without prior ramp-up.
- Align messages with future threshold policies (once proactive warnings exist) to make responses actionable.
- Keep payloads lightweight; short text fields only, no new dependencies or schema-heavy changes.

## Partial Resolution (2025-12-08)
**Fixed:**
- Added comprehensive tool descriptions with "When to use" and "How to use" sections
- Added examples in tool descriptions showing common usage patterns
- Added "Returns" section in descriptions explaining response structure
- `context_analyze_usage` now includes `warnings`, `suggested_actions`, and `impact_summary` fields
- Tool descriptions now include clear guidance on when and how to use each tool

**Still Open:**
- Response payloads for `context_stash` and `context_retrieve_stashed` don't yet include explicit "what changed" or "suggested next step" text fields
- Impact summaries could be more detailed with estimated token impact per action

**Implementation:**
- `src/hjeon139_mcp_outofcontext/tools/stashing/__init__.py` - Enhanced tool descriptions with usage guidance
- `src/hjeon139_mcp_outofcontext/tools/monitoring.py` - Added impact summaries to `context_analyze_usage`

## Notes
- Start with response text + description updates; defer schema changes and new dependencies.

