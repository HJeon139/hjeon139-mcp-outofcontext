# Issue: Slow MCP workflow due to multi-step calls and drafting latency

**Date**: 2025-12-08  
**Severity**: Medium  
**Component**: MCP UX / performance  
**Status**: Partially Addressed (2025-12-08)

## Description
Using the current workflow (`context_analyze_usage` → `context_get_working_set` → `context_stash`) is slow end-to-end. Latency comes from:
- LLM drafting long tool payloads (documented in 2025-12-08-llm-drafting-latency.md)
- Multiple sequential tool calls per update (3 calls to ingest + stash)
- Server-side execution adds to the total wall-clock

This makes routine context updates feel sluggish and discourages frequent use.

## Reproduction
1. Ingest context via `context_analyze_usage`, then `context_get_working_set`, then `context_stash`.
2. Observe noticeable total latency (LLM drafting + multiple MCP calls + server processing).

## Expected Behavior
- Faster end-to-end context capture with fewer tool calls and reduced drafting overhead.
- A streamlined or bundled call path that minimizes round-trips.

## Actual Behavior
- Three calls are needed and drafting is heavy; total time feels slow even when each tool is individually acceptable.

## Impact
- Users may avoid frequent updates; context freshness suffers.
- Perception that the MCP flow is slow, reducing adoption.

## Proposed Solution (if known)
- Prompt engineering: shorter, templated payloads; concise descriptors.
- Reduce tool steps: combine analysis+stash (or expose a single “ingest_and_stash” helper) to cut round-trips.
- Performance tuning: ensure server-side handlers are as fast as possible; consider optional batching of recent_messages/file pointers.
- Keep dependencies minimal; prefer protocol/tooling changes over new libraries.

## Partial Resolution (2025-12-08)
**Improved:**
- Reduced workflow from 3 calls to 2 calls: `context_analyze_usage` → `context_stash` (eliminated `context_get_working_set` step)
- Simplified interface: No need to extract segment IDs from working set - can stash directly with query/filters
- More intuitive: Agents can stash by content (`query="old docs"`) or metadata (`filters={"type": "file"}`) without managing IDs
- Reduced cognitive overhead: Agents think in terms of content/metadata, not low-level segment IDs

**Still Open:**
- Still requires 2 separate calls (not a single combined call)
- LLM drafting latency for large payloads remains (see 2025-12-08-llm-drafting-latency.md)

**Implementation:**
- `src/hjeon139_mcp_outofcontext/tools/stashing/context_stash.py` - Refactored to use query/filters instead of segment_ids
- `src/hjeon139_mcp_outofcontext/tools/stashing/context_retrieve_stashed.py` - Refactored to use query/filters instead of segment_ids

## Notes
- Related to 2025-12-08-llm-drafting-latency.md, but focuses on multi-call overhead and workflow optimization, not just drafting. 

