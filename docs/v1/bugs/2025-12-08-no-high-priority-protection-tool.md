# Issue: No tool to mark/protect high-priority context segments

**Date**: 2025-12-08  
**Severity**: Medium  
**Component**: pruning / task tools  
**Status**: Open

## Description
Requirements (docs/v0/requirements.md, item 3 and 8) call for the ability to mark essential segments and protect them from pruning/removal. The current MCP tool set (monitoring, pruning, stashing, task) does not expose a way to flag segments as high priority or protected. Although the model schema has `pinned` fields, there is no MCP tool to set/clear this state, and pruning logic does not enforce protection.

## Reproduction
1. Inspect available tools via `list_tools`: no tool exists to mark/pin segments.
2. Attempt pruning/stashing flows: no protection API or enforcement is present.

## Expected Behavior
- Tool(s) to mark/unmark segments as protected/high-priority/pinned.
- Pruning routines respect these flags and exclude protected segments by default.

## Actual Behavior
- No tool to set protection flags; pruning/stashing can act on any working segment.

## Environment
- Python: (per project)
- Platform: darwin

## Impact
- Risk of pruning/removing critical context; agents cannot safeguard essential items.

## Proposed Solution (if known)
- Small-scope fix: add MCP tools to set/unset protection (reuse `pinned`) on segment IDs; no new dependencies.
- Update pruning/stashing logic to honor `pinned` by default (skip unless explicitly overridden).
- Surface protected segments in monitoring outputs for visibility, and add quick-start prompts in tool descriptions (e.g., “Pin critical segments before pruning/stashing”).

## Notes
- Keep the API consistent with existing segment/tier semantics; reuse `pinned` where possible.

