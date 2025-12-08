# Issue: No proactive limit warnings or automated stashing triggers

**Date**: 2025-12-08  
**Severity**: Medium  
**Component**: monitoring / MCP tools  
**Status**: Open

## Description
The MCP server lacks proactive notifications or threshold-triggered actions when context approaches limits. Requirements (docs/v0/requirements.md, items 5, 16, 18) call for warnings and proactive suggestions or automated actions when nearing capacity. Current flow is entirely agent-initiated, so stashing/pruning only happens if the agent manually checks usage.

## Reproduction
1. Call `context_analyze_usage` and `context_get_working_set` as context grows.
2. Observe that no warnings or suggestions are emitted as usage increases.
3. No automatic threshold-based stashing/pruning is triggered.

## Expected Behavior
- Server should emit warnings/recommendations when usage crosses configurable thresholds (e.g., 60/80/90%).
- Optionally trigger suggested actions (prune/stash candidates) or provide a follow-up tool call payload.

## Actual Behavior
- No proactive signals or automated triggers; only manual, agent-initiated checks.

## Environment
- Python: (per project)
- Platform: darwin

## Impact
- Higher risk of hitting context limits before the agent intervenes.
- Additional user overhead to remember to poll usage.

## Proposed Solution (if known)
- Small-scope fix: add threshold configuration (e.g., 60/80/90%) and include warnings + suggested next actions in monitoring tool responses (`context_analyze_usage`), without adding new dependencies.
- Return recommended follow-up tool calls (e.g., `context_stash` with candidate IDs) in the same response so agents don’t have to craft requests.
- Add concise prompt text in tool descriptions to remind agents to run analyze/get_working_set periodically; defer any background watcher to a later phase.

## Notes
- Keep minimal dependencies; prefer existing metrics and GC heuristics.

