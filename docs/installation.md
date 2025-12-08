# Installation Guide

This guide will help you install and configure the Out of Context MCP server for managing large context windows in AI agent platforms.

---

## Prerequisites

Before installing, ensure you have:

- **Python 3.11+** - The server requires Python 3.11 or higher
- **Hatch** (optional, for development) - For building and managing the project
- **MCP-compatible platform** - One of:
  - Cursor (recommended)
  - Claude Desktop
  - Other platforms supporting MCP protocol

### Checking Python Version

```bash
python3 --version
# Should show Python 3.11 or higher
```

### Installing Hatch (Optional)

If you plan to build from source:

```bash
pip install hatch
```

---

## Installation

### Option 1: Install from PyPI (Recommended)

Once published:

```bash
pip install hjeon139-mcp-outofcontext
```

### Option 2: Install from Source

1. **Clone the repository:**

```bash
git clone <repository-url>
cd out_of_context
```

2. **Build the package:**

```bash
hatch build
```

3. **Install the wheel:**

```bash
pip install dist/hjeon139_mcp_outofcontext-*.whl
```

### Option 3: Development Installation

For development work:

```bash
# Clone repository
git clone <repository-url>
cd out_of_context

# Install in editable mode with dev dependencies
hatch env create
hatch run update-deps
```

---

## MCP Server Configuration

The server needs to be added to your MCP-compatible platform's configuration.

### Cursor Setup

1. **Open Cursor settings** (Cmd/Ctrl + ,)

2. **Navigate to MCP settings** (or add to your MCP configuration file)

3. **Add server configuration:**

```json
{
  "mcpServers": {
    "out-of-context": {
      "command": "python",
      "args": [
        "-m",
        "hjeon139_mcp_outofcontext.main"
      ],
      "env": {
        "OUT_OF_CONTEXT_STORAGE_PATH": ".out_of_context",
        "OUT_OF_CONTEXT_TOKEN_LIMIT": "1000000"
      }
    }
  }
}
```

4. **Restart Cursor** to load the new MCP server

### Claude Desktop Setup

1. **Locate Claude Desktop configuration file:**

   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
   - **Linux**: `~/.config/Claude/claude_desktop_config.json`

2. **Add server configuration:**

```json
{
  "mcpServers": {
    "out-of-context": {
      "command": "python",
      "args": [
        "-m",
        "hjeon139_mcp_outofcontext.main"
      ],
      "env": {
        "OUT_OF_CONTEXT_STORAGE_PATH": ".out_of_context",
        "OUT_OF_CONTEXT_TOKEN_LIMIT": "1000000"
      }
    }
  }
}
```

3. **Restart Claude Desktop**

### Other Platforms

For other MCP-compatible platforms, refer to their documentation for adding MCP servers. The server runs as a standard MCP server and should work with any platform supporting the MCP protocol.

---

## Configuration Options

The server can be configured via environment variables or a config file.

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OUT_OF_CONTEXT_STORAGE_PATH` | Storage directory path | `.out_of_context` |
| `OUT_OF_CONTEXT_TOKEN_LIMIT` | Maximum token limit | `1000000` |
| `OUT_OF_CONTEXT_MODEL` | Model identifier | `gpt-4` |
| `OUT_OF_CONTEXT_LOG_LEVEL` | Logging level | `INFO` |
| `OUT_OF_CONTEXT_MAX_ACTIVE_SEGMENTS` | LRU cache size | `10000` |
| `OUT_OF_CONTEXT_ENABLE_INDEXING` | Enable inverted index | `true` |
| `OUT_OF_CONTEXT_ENABLE_FILE_SHARDING` | Enable file sharding | `true` |
| `OUT_OF_CONTEXT_RECENT_MESSAGES_COUNT` | Recent messages to track | `10` |
| `OUT_OF_CONTEXT_RECENT_DECISION_HOURS` | Recent decision window | `1` |

### Config File

Create a config file at `.out_of_context/config.json` (project directory) or `~/.out_of_context/config.json` (home directory):

```json
{
  "storage_path": ".out_of_context",
  "token_limit": 1000000,
  "model": "gpt-4",
  "log_level": "INFO",
  "max_active_segments": 10000,
  "enable_indexing": true,
  "enable_file_sharding": true,
  "recent_messages_count": 10,
  "recent_decision_hours": 1
}
```

**Priority:** Environment variables override config file, which overrides defaults.

---

## Platform Integration

### Storage Path

The server stores context data in the directory specified by `storage_path`. By default, this is `.out_of_context` in your project directory.

**Important:** The storage path should be:
- Writable by the server process
- Excluded from version control (add to `.gitignore`)
- Persistent across sessions

### Project Detection

The server automatically detects the project directory from the MCP platform. If not available, it uses the `default` project ID.

---

## Verification

After installation, verify the server is working:

### 1. Test Server Connection

In your MCP platform, check that the server appears in the list of available MCP servers.

### 2. List Available Tools

Use your platform's tool discovery to see available tools. You should see tools like:
- `context_analyze_usage`
- `context_get_working_set`
- `context_gc_analyze`
- `context_stash`
- And more...

### 3. Run Test Tool Call

Try calling `context_analyze_usage`:

```json
{
  "project_id": "test-project"
}
```

You should receive a response with usage metrics (likely showing 0 usage for a new project).

### 4. Check Storage Directory

Verify the storage directory was created:

```bash
ls -la .out_of_context
```

You should see:
- `config.json` (if you created one)
- Project directories (created as needed)

---

## Troubleshooting

### Server Not Appearing

- **Check Python path:** Ensure `python` or `python3` is in your PATH
- **Check installation:** Verify the package is installed: `pip list | grep outofcontext`
- **Check logs:** Look for error messages in the platform's MCP logs

### Permission Errors

- **Storage path:** Ensure the storage directory is writable
- **Config file:** Check file permissions on config files

### Import Errors

- **Python version:** Ensure Python 3.11+ is being used
- **Dependencies:** Install missing dependencies: `pip install mcp pydantic tiktoken`

### Configuration Not Loading

- **Check priority:** Environment variables override config files
- **Check syntax:** Ensure JSON config files are valid
- **Check paths:** Verify config file paths are correct

---

## Next Steps

Once installed and verified:

1. **Read the Usage Guide** - Learn how to use the tools effectively
2. **Review Best Practices** - Understand when and how to manage context
3. **Try Demo Scenarios** - Follow the demo guide for hands-on examples

See [Usage Guide](usage.md) for detailed usage instructions.

