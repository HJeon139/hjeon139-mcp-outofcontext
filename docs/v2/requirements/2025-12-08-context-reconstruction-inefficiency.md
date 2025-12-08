# V2 Requirement: Context Reconstruction Requires Multiple Calls and Retrieves Excess Context

**Date**: 2025-12-08
**Severity**: Medium
**Component**: stashing, retrieval, search
**Status**: Deferred to V2
**Classification**: V2 - Requires semantic search and advanced retrieval strategies

## Description

After context was cleared, the agent attempted to reconstruct previous session context using the MCP server. The reconstruction process required **10+ search queries** and ultimately retrieved **26 segments (1,402 tokens)** that increased LLM context usage from ~22% to ~36%, but **failed to retrieve the exact context** that was needed (the git log summary conversation that occurred just before the GitHub prompt).

## Reproduction

1. Clear LLM context (simulating context reset)
2. Agent attempts to reconstruct previous work using MCP server
3. Agent performs multiple `context_search_stashed` calls with various queries:
   - "git log summary session context" → 0 results
   - "stash context MCP server testing" → 0 results
   - "design corpus search evaluation" → 0 results
   - "bug documentation" → 0 results
   - "design" → 17 results (design corpus segments)
   - "MCP" → 14 results (various MCP-related segments)
   - "github remote repository" → 0 results
   - "commit changes" → 0 results
   - "search evaluation recall" → 0 results
   - "test recall accuracy" → 0 results
   - "stash conversation prompt response" → 0 results
4. Agent uses `context_get_task_context` with task_id "design-corpus" → 26 segments retrieved
5. Context usage increases from 22% to 36% of LLM context window

## Expected Behavior

1. **Single or minimal queries** should retrieve relevant context
2. **Precise context retrieval** - should find the exact conversation/segments needed
3. **Contextual search** - queries like "what were we working on before X" should work
4. **Selective retrieval** - should be able to retrieve only the most relevant segments, not entire task contexts
5. **Recent context prioritization** - most recent stashed context should be easier to find

## Actual Behavior

1. **Multiple queries required** - 10+ different search attempts needed
2. **Low precision** - broad queries ("git log summary") returned 0 results even though relevant context existed
3. **Over-retrieval** - Retrieved 26 segments (1,402 tokens) when only a subset was needed
4. **Task-scoped retrieval only** - Had to know the exact task_id ("design-corpus") to get context, no way to search "recent" or "last session"
5. **Missing target context** - The specific conversation about git log summary (just before GitHub prompt) was not found
6. **Context bloat** - LLM context increased from 22% to 36%, suggesting inefficient retrieval

## Root Causes

1. **Keyword search limitations**: 
   - Current keyword search is too literal - "git log summary" doesn't match segments that contain "git", "log", "summary" separately
   - No semantic understanding of query intent
   - No fuzzy matching or synonym handling

2. **No temporal/recency search**:
   - Cannot search by "most recent" or "last session"
   - No way to find "what happened before X" without knowing exact task_id
   - Timestamp filtering exists but requires exact dates

3. **Task-centric organization**:
   - Context is organized by task_id, but agent doesn't always know which task_id to use
   - No cross-task search or "recent activity" view
   - Task boundaries may not align with conversation flow

4. **No relevance ranking**:
   - All matching segments returned equally
   - No way to retrieve "top 3 most relevant" segments
   - `limit` parameter exists but doesn't rank by relevance

5. **Over-retrieval in `context_get_task_context`**:
   - Returns all segments for a task, not just relevant ones
   - No filtering or ranking within task context

6. **Missing conversation context**:
   - The git log summary conversation may not have been stashed properly
   - Or it was stashed but with different keywords/metadata that don't match search queries

## Impact

- **Agent efficiency**: Multiple tool calls slow down context reconstruction
- **Context window waste**: Retrieving too much context reduces available space for new work
- **Recall failures**: Missing target context means agent loses important information
- **User experience**: Agent appears less capable when it can't reconstruct recent work
- **Trust**: If agent can't reliably retrieve stashed context, the tool's value is diminished

## Proposed Solutions

### Short-term (Prompt Engineering)

1. **Improve search query guidance**:
   - Update tool descriptions to suggest multiple query strategies
   - Recommend trying broader terms if specific queries fail
   - Suggest using task_id filtering when known

2. **Add retrieval best practices**:
   - Document that `context_get_task_context` retrieves all segments (use with caution)
   - Recommend using `limit` parameter to control retrieval size
   - Suggest retrieving segments and then filtering client-side

### Medium-term (Feature Enhancements)

1. **Temporal search**:
   - Add "recent" or "last N hours" search filter
   - Add "before_task" or "after_task" temporal filters
   - Prioritize recent segments in search results

2. **Relevance ranking**:
   - Implement TF-IDF or simple keyword frequency scoring
   - Return segments ranked by relevance score
   - Add "top_k" parameter that returns only most relevant segments

3. **Better search query handling**:
   - Tokenize queries and match against all tokens in segments
   - Support partial word matching
   - Consider query expansion (synonyms, related terms)

4. **Conversation context tracking**:
   - Ensure user prompts and assistant responses are consistently stashed
   - Add metadata tags like "conversation", "session", "recent" automatically
   - Track conversation flow with sequence numbers or timestamps

5. **Selective retrieval**:
   - Add `context_retrieve_relevant` tool that takes a query and returns top-k segments
   - Add filtering options to `context_get_task_context` (by type, date, tags)
   - Support retrieving segments by content similarity (even if keyword-based)

### Long-term (Architectural)

1. **Semantic search** (deferred feature, but would solve many issues):
   - Embedding-based similarity search
   - Better understanding of query intent
   - Contextual matching

2. **Conversation threading**:
   - Track conversation threads/sessions
   - Link related segments (prompt → response pairs)
   - Enable "retrieve conversation thread" functionality

3. **Smart retrieval**:
   - Agent can request "context about X" and system returns most relevant segments
   - Automatic context pruning after retrieval (remove less relevant segments)
   - Context summarization for large retrievals

## Metrics to Track

- **Search efficiency**: Average number of queries needed to find target context
- **Recall**: Percentage of relevant segments successfully retrieved
- **Precision**: Percentage of retrieved segments that are actually relevant
- **Context bloat**: Increase in context usage after retrieval
- **Retrieval latency**: Time to find and retrieve context

## Test Cases

1. **Temporal search**: "What were we working on in the last hour?"
2. **Conversation retrieval**: "Retrieve the conversation about git log summary"
3. **Selective retrieval**: "Find the 3 most relevant segments about design patterns"
4. **Cross-task search**: "Find all segments mentioning 'MCP server' across all tasks"
5. **Context reconstruction**: Clear context, then reconstruct previous session with minimal queries

## Notes

- The agent successfully retrieved the design corpus context (26 segments), demonstrating that stashing and retrieval works
- However, the specific conversation about git log summary was not found, suggesting either:
  - It wasn't stashed properly
  - It was stashed with different keywords/metadata
  - The search mechanism couldn't match the query to the stashed content
- The increase from 22% to 36% context usage suggests over-retrieval - we got more than needed
- Multiple search queries (10+) indicate the search interface is not intuitive or effective enough
- The fact that `context_get_task_context` returned 26 segments shows it's a "get all" operation, not a "get relevant" operation

