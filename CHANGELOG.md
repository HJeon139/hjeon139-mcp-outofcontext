# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- **BREAKING**: Default storage directory changed from `.out_of_context` to `out_of_context`
  - The hidden directory (`.out_of_context`) caused permission issues when agents tried to edit context files directly
  - The new non-hidden directory (`out_of_context`) resolves these permission issues
  - Migration is required if you have existing context files

### Migration Guide

If you have existing context files in `.out_of_context`, you need to migrate them:

#### Option 1: Automatic Migration (Recommended)

If you're not using a custom `OUT_OF_CONTEXT_STORAGE_PATH` environment variable, the server will automatically migrate your directory on startup.

#### Option 2: Manual Migration

If you have `OUT_OF_CONTEXT_STORAGE_PATH` set to `.out_of_context` in your MCP configuration:

1. **Update your MCP configuration** (e.g., `~/.cursor/mcp.json` or Claude Desktop config):
   ```json
   {
     "mcpServers": {
       "out-of-context": {
         "command": "hjeon139_mcp_outofcontext",
         "env": {
           "OUT_OF_CONTEXT_STORAGE_PATH": "out_of_context"
         }
       }
     }
   }
   ```

2. **Migrate your existing context files**:
   ```bash
   # From your project root directory
   mv .out_of_context out_of_context
   ```

   Or if you want to be more careful:
   ```bash
   # Check what will be moved
   ls -la .out_of_context/
   
   # Move the directory
   mv .out_of_context out_of_context
   
   # Verify the move
   ls -la out_of_context/
   ```

3. **Restart your MCP server** to pick up the new configuration

#### Option 3: Keep Using Old Path (Not Recommended)

If you must continue using `.out_of_context`, you can set:
```json
{
  "env": {
    "OUT_OF_CONTEXT_STORAGE_PATH": ".out_of_context"
  }
}
```

However, this is **not recommended** as it may cause permission issues when agents try to edit context files directly.

### Notes

- The migration preserves all context files and configuration
- If both `.out_of_context` and `out_of_context` exist, the server will use `out_of_context` and log a warning
- The server will warn you if it detects you're using the old path in your configuration

