# Issue: Large MCP payloads cause slow tool calls due to LLM drafting

**Date**: 2025-12-08  
**Severity**: Low  
**Component**: MCP UX / agent usage  
**Status**: Open

## Description
When the LLM must draft long MCP payloads (large recent_messages or long tool arguments), end-to-end latency spikes. The slowness is not in the MCP tool execution itself but in the LLM composing the request. This makes large-context ingestion feel slow and discourages frequent updates.

## Reproduction
1. Provide a very long transcript to be ingested into `context_analyze_usage`.
2. Observe that the LLM spends noticeable time drafting the tool call; the tool returns quickly once called.

## Expected Behavior
- Tool usage should feel responsive even for large payloads.
- Users should be able to stream or chunk content without long drafting pauses.

## Actual Behavior
- Drafting the MCP request is slow when payloads are large; perceived latency is high.

## Impact
- Users may avoid keeping the MCP store current for long sessions.
- Perception that the MCP server is slow, even though the delay is client-side drafting.

## Proposed Solution (if known)
- Encourage chunked/streamed ingestion (smaller batches).
- Provide helper prompts/templates to minimize drafting time.
- Consider a “file upload or paste once” helper tool that accepts bulk text and stores it server-side without long inline drafting.

## Notes
- No server-side performance issue observed; the delay is LLM-side drafting time.

