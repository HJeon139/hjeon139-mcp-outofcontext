# V2 Requirement: No semantic or fuzzy search fallback (keyword-only retrieval)

**Date**: 2025-12-08  
**Severity**: Low  
**Component**: retrieval  
**Status**: Deferred to V2
**Classification**: V2 - Semantic search explicitly deferred per architectural decisions

## Description
Search is keyword + metadata only. There is no semantic similarity or fuzzy matching, so near-miss queries or typos may fail to retrieve relevant stashed context. This limits recall for less precise queries.

## Impact
- Users must remember exact terms; near-misses or spelling variations can miss targets.
- Reduced recall in real-world usage where queries are imprecise.

## Proposed Solution (if known)
- Consider adding optional semantic/fuzzy path (e.g., lightweight fuzzy matching or deferred embeddings/SQLite FTS) while keeping minimal deps.
- At minimum, document limitations and recommend precise keywords/tags until an optional fuzzy/semantic layer is added.

