# V2 Requirements

This directory contains feature improvements and enhancements that are deferred to v2, as they fall outside the v1 MVP scope.

## Classification Criteria

Items are classified as v2 requirements if they:

1. **Require semantic search or vector databases** - Explicitly deferred per architectural decisions
2. **Depend on advanced ML/AI capabilities** - Semantic embeddings, fuzzy matching, etc.
3. **Require significant architectural changes** - Beyond what can be achieved with prompt engineering and workflow improvements
4. **Add substantial dependencies** - Beyond the minimal v1 dependencies (mcp, pydantic, tiktoken)

## V1 vs V2 Scope

### V1 Scope (Bugfixes in `docs/v1/bugs/`)
- Keyword + metadata search improvements
- Workflow optimizations (combined tools, helpers)
- Prompt engineering improvements
- Protection/pinning tools (requirements call for this)
- Proactive warnings and thresholds
- Performance instrumentation
- Policy improvements (auto-fetch, consistent stashing)

### V2 Scope (Requirements in this directory)
- Semantic search and vector databases
- Fuzzy matching and advanced retrieval
- LLM-driven compression
- Advanced context reconstruction requiring semantic understanding
- Complex retrieval strategies beyond keyword search

## References

- [V1 Deferred Features](../../v1/design/08_deferred_features.md) - Features explicitly deferred to v2
- [Architectural Decisions](../../v1/design/03_architectural_decisions.md) - Decisions that define v1 scope
- [V0 Requirements](../../v0/requirements.md) - Original requirements document

