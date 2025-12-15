# Phase 4: Development Auto-Reload

This phase covers enabling auto-reload for development workflows using hot module replacement with stdio transport.

## Overview

Phase 4 involves:
1. Setting up hot module replacement for stdio transport using `mcp-hmr`
2. Creating a development wrapper script for initialization
3. Documenting development workflows
4. Testing auto-reload functionality

**Note**: This phase is optional and should only be undertaken after [Phase 5: Validation](phase-5-validation.md) validates the basic migration works correctly.

## Steps

### 4.1 Install mcp-hmr

`mcp-hmr` (Hot Module Replacement) is a Python tool that provides auto-reload for MCP servers using stdio transport.

**Installation:**

```bash
pip install mcp-hmr
```

Or add to dev dependencies in `pyproject.toml`:

```toml
[project.optional-dependencies]
dev = [
    # ... existing dev dependencies ...
    "mcp-hmr>=0.1.0",
]
```

### 4.2 Create Development Wrapper Script

Create a development entry point that initializes the server and exports the FastMCP instance for `mcp-hmr` to use.

**Create `scripts/mcp_dev.py`:**

```python
"""Development entry point for mcp-hmr."""
from hjeon139_mcp_outofcontext.config import load_config
from hjeon139_mcp_outofcontext.fastmcp_server import (
    initialize_app_state,
    mcp,
    register_all_tools,
)

# Initialize before mcp-hmr takes over
config = load_config()
initialize_app_state(config)
register_all_tools()

# Export the mcp instance for mcp-hmr
__all__ = ["mcp"]
```

**Why a wrapper script?**
- `mcp-hmr` needs direct access to the FastMCP instance
- Our server requires initialization (config loading, AppState setup, tool registration)
- The wrapper ensures initialization happens before `mcp-hmr` takes control

### 4.3 Update Cursor Configuration for Development

For development with auto-reload, update your Cursor configuration to use `mcp-hmr`:

**Development Configuration (`.cursor/mcp.json`):**

```json
{
  "mcpServers": {
    "out-of-context": {
      "command": "mcp-hmr",
      "args": ["scripts.mcp_dev:mcp"],
      "env": {
        "OUT_OF_CONTEXT_STORAGE_PATH": ".out_of_context"
      }
    }
  }
}
```

**Production Configuration (keep using standard approach):**

```json
{
  "mcpServers": {
    "out-of-context": {
      "command": "hjeon139_mcp_outofcontext",
      "env": {
        "OUT_OF_CONTEXT_STORAGE_PATH": ".out_of_context"
      }
    }
  }
}
```

### 4.4 How It Works

1. `mcp-hmr` starts your MCP server as a subprocess
2. It watches your source files for changes
3. When changes are detected, it reloads only the changed modules (hot module replacement)
4. The connection to Cursor remains intact (no reconnection needed)
5. Tools are automatically updated

**Why stdio transport with mcp-hmr instead of HTTP transport?**

FastMCP's built-in auto-reload only works with HTTP transport, which requires:
- Manual server startup (Cursor doesn't start it)
- Using `url` instead of `command` in Cursor config
- More complex setup and process management

Using `mcp-hmr` with stdio transport provides:
- Cursor manages the server lifecycle (auto-start/stop)
- Simple `command`-based configuration
- Better integration with Cursor's workflow
- Same auto-reload benefits without HTTP complexity

## Benefits

- ✅ Auto-reload with stdio transport (no need to switch to HTTP)
- ✅ Maintains connection to Cursor (no reconnection needed)
- ✅ Fast reload (only changed modules are reloaded)
- ✅ Works seamlessly with FastMCP
- ✅ Better development experience

## Deliverables

- [ ] `mcp-hmr` installed (as dev dependency)
- [ ] Development wrapper script created (`scripts/mcp_dev.py`)
- [ ] Cursor configuration documented for development mode
- [ ] Auto-reload tested and working correctly
- [ ] Documentation updated with:
  - Development workflow instructions
  - Cursor configuration examples
  - Troubleshooting guide

## Testing

Test that auto-reload works:

1. Start Cursor with the development configuration
2. Make a change to a tool implementation
3. Verify the change is reflected without restarting Cursor
4. Check that the connection remains stable

## Troubleshooting

**Common Issues:**

1. **"No server info found" errors**:
   - Ensure `mcp-hmr` is installed: `pip install mcp-hmr`
   - Verify the wrapper script path is correct in Cursor config
   - Check that the FastMCP instance is properly exported (`__all__ = ["mcp"]`)

2. **Changes not reloading**:
   - Verify `mcp-hmr` is watching the correct files
   - Check that file changes are being saved
   - Restart Cursor if auto-reload isn't working

3. **Connection issues**:
   - Ensure the wrapper script initializes correctly (config, AppState, tools)
   - Check server logs for initialization errors
   - Verify environment variables are set correctly

## Alternative Approaches

If `mcp-hmr` doesn't work for your setup, you can use a file watcher script with `watchdog`:

```python
# scripts/dev_watch.py
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import subprocess
import sys
import time

class RestartHandler(FileSystemEventHandler):
    def __init__(self):
        self.process = None
        self.start_process()

    def start_process(self):
        if self.process:
            self.process.terminate()
            self.process.wait()
        cmd = [sys.executable, "-m", "hjeon139_mcp_outofcontext.main"]
        self.process = subprocess.Popen(cmd)

    def on_modified(self, event):
        if event.src_path.endswith('.py'):
            print(f"File changed: {event.src_path}, restarting...")
            self.start_process()

if __name__ == "__main__":
    path = "src"
    event_handler = RestartHandler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
```

**Note**: This approach will cause Cursor to disconnect/reconnect, unlike `mcp-hmr` which maintains the connection. Use `mcp-hmr` for the best developer experience.

## Next Steps

After Phase 4 is complete (if implemented), proceed to [Phase 6: Cleanup](phase-6-cleanup.md).

**Note**: If skipping Phase 4, proceed directly to [Phase 6: Cleanup](phase-6-cleanup.md) after Phase 5.

## Related Documentation

- [mcp-hmr GitHub Discussion](https://github.com/orgs/modelcontextprotocol/discussions/602)
- [FastMCP Documentation](https://gofastmcp.com)
- [Migration Checklist](migration-checklist.md#phase-4-development-auto-reload-optional)
