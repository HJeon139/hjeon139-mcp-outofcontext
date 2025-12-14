# Phase 3: FastMCP Features (Optional)

Add optional FastMCP features like resources, prompts, and storage backends.

## Overview

After the core migration is validated (Phase 5), we can add optional FastMCP features that weren't available in the standard MCP SDK.

**Note**: This phase is optional and should only be undertaken after [Phase 5: Validation](phase-5-validation.md) is complete.

## Optional Features

### 3.1 Add Resources

We could expose contexts as MCP resources (similar to GET endpoints):

```python
@mcp.resource("context://{name}")
async def get_context_resource(name: str, ctx: Context = CurrentContext()) -> str:
    """Get context as a resource."""
    app_state: AppState = ctx.get_state("app_state")
    context = app_state.storage.load_context(name)
    return context.text  # Return markdown content
```

### 3.2 Add Prompts

Create reusable prompts for common operations:

```python
@mcp.prompt("search_context")
def search_context_prompt(query: str) -> str:
    """Search contexts prompt template."""
    return f"Search for contexts matching: {query}"
```

### 3.3 Add Storage Backend Support

Consider using FastMCP's storage backends for caching:

```python
from fastmcp.server.middleware.caching import ResponseCachingMiddleware
from key_value.aio.stores.disk import DiskStore

# Add caching middleware if beneficial
mcp.add_middleware(ResponseCachingMiddleware(
    cache_storage=DiskStore(directory=".out_of_context/cache"),
))
```

## Deliverables

- [ ] Resources added (if desired)
- [ ] Prompts added (if desired)
- [ ] Storage backend configured (if desired)
- [ ] All optional features tested

## Related Documentation

- [Overview - FastMCP Key Concepts](overview.md#fastmcp-key-concepts)
- [Phase 5: Validation](phase-5-validation.md)
- [Migration Checklist](migration-checklist.md#phase-3-additional-features-optional---after-migration-validated)
