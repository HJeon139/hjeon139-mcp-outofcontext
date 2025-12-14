# Phase 4: HTTP Transport and Auto-Reload

This phase covers adding HTTP transport support and development mode with auto-reload.

## Overview

Phase 4 involves:
1. Supporting HTTP transport mode in addition to stdio
2. Creating a development entry point with auto-reload
3. Testing both transport modes

**Note**: This phase is optional and should only be undertaken after [Phase 5: Validation](phase-5-validation.md) validates the basic migration works correctly.

## Steps

### 4.1 Support HTTP Transport

Update entry point to support both stdio and HTTP:

```python
import os
from fastmcp import FastMCP

if __name__ == "__main__":
    transport = os.getenv("MCP_TRANSPORT", "stdio")
    
    if transport == "http":
        app = mcp.http_app()
        # Would be run via: uvicorn main:app --reload --host 0.0.0.0 --port 8000
    else:
        mcp.run()
```

However, for better separation of concerns, consider keeping separate entry points:
- `main.py` - stdio transport (production/default)
- `main_dev.py` - HTTP transport with auto-reload (development)

### 4.2 Development Mode with Auto-Reload

Create a development entry point for HTTP transport with auto-reload. See [Code Examples - main-http.py](code-examples/main-http.py) for the full implementation.

**Benefits:**
- Auto-reload on code changes (using `uvicorn --reload`)
- Faster development iteration
- HTTP endpoint for testing with multiple clients
- Better debugging experience

**Usage:**

```bash
# Run with auto-reload for development
python -m hjeon139_mcp_outofcontext.main_dev

# Or use uvicorn directly
uvicorn hjeon139_mcp_outofcontext.main_dev:app --reload --host 127.0.0.1 --port 8000
```

## Deliverables

- [ ] HTTP transport support added (optional)
- [ ] Development entry point created (`main_dev.py` or similar)
- [ ] Both stdio and HTTP transports tested
- [ ] Auto-reload working correctly
- [ ] Documentation updated with HTTP transport usage

## Next Steps

After Phase 4 is complete (if implemented), proceed to [Phase 6: Cleanup](phase-6-cleanup.md).

**Note**: If skipping Phase 4, proceed directly to [Phase 6: Cleanup](phase-6-cleanup.md) after Phase 5.

## Related Documentation

- [Overview - FastMCP Key Concepts - Transport Modes](overview.md#transport-modes)
- [Overview - FastMCP Key Concepts - Auto-Reload with Uvicorn](overview.md#auto-reload-with-uvicorn)
- [Code Examples - main-http.py](code-examples/main-http.py)
- [Migration Checklist](migration-checklist.md#phase-3-additional-features-optional---after-migration-validated)
