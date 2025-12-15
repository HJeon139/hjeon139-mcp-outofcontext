# Out of Context

An MCP (Model Context Protocol) server for managing context using simple CRUD operations. Stores contexts as markdown files (.mdc) with YAML frontmatter, allowing agents to save, retrieve, search, and manage context by name.

---

## Features

- **Simple CRUD Operations**: 5 basic tools for context management (put, list, get, search, delete)
- **Markdown Storage**: Contexts stored as .mdc files (markdown with YAML frontmatter)
- **Agent-Recognizable Names**: Use meaningful names instead of UUIDs
- **Bulk Operations**: Support for bulk put, get, and delete operations with robust parameter handling
- **Pydantic Validation**: Type-safe parameter validation with automatic schema generation
- **Text Search**: Search contexts by query string across metadata and content
- **MCP Integration**: Works with any MCP-compatible platform (Cursor, Claude Desktop, etc.)

---

## Quick Start

### Installation

```bash
pip install hjeon139-mcp-outofcontext
```

### MCP Server Configuration

Add to your MCP platform configuration (e.g., Cursor or Claude Desktop):

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

### Verify Installation

In your MCP platform, check that tools like `put_context`, `list_context`, `get_context`, `search_context`, and `delete_context` are available.

---

## Usage Examples

### Add Context

**Single operation:**
```json
{
  "tool": "put_context",
  "arguments": {
    "name": "api-design-notes",
    "text": "# API Design Notes\n\nKey decisions about the REST API...",
    "metadata": {
      "type": "note",
      "tags": ["api", "design"]
    }
  }
}
```

**Bulk operation:**
```json
{
  "tool": "put_context",
  "arguments": {
    "contexts": [
      {
        "name": "context-1",
        "text": "First context",
        "metadata": {"type": "note"}
      },
      {
        "name": "context-2",
        "text": "Second context"
      }
    ]
  }
}
```

### List Contexts

```json
{
  "tool": "list_context",
  "arguments": {
    "limit": 10
  }
}
```

Returns list of contexts sorted by creation date (newest first).

### Get Context

**Single operation:**
```json
{
  "tool": "get_context",
  "arguments": {
    "name": "api-design-notes"
  }
}
```

**Bulk operation:**
```json
{
  "tool": "get_context",
  "arguments": {
    "names": ["context-1", "context-2", "context-3"]
  }
}
```

### Search Contexts

```json
{
  "tool": "search_context",
  "arguments": {
    "query": "API design",
    "limit": 5
  }
}
```

Searches in both YAML frontmatter (metadata) and markdown body (text content).

### Delete Context

**Single operation:**
```json
{
  "tool": "delete_context",
  "arguments": {
    "name": "old-context"
  }
}
```

**Bulk operation:**
```json
{
  "tool": "delete_context",
  "arguments": {
    "names": ["context-1", "context-2"]
  }
}
```

---

## Storage Format

Contexts are stored as `.mdc` files (markdown with YAML frontmatter) in the `.out_of_context/contexts/` directory.

**File format:**
```markdown
---
name: api-design-notes
created_at: 2025-12-14T12:51:27.123456
type: note
tags: [api, design]
---

# API Design Notes

Key decisions about the REST API design...

- Use RESTful conventions
- Version in URL path
```

**Name requirements:**
- Filename-safe: alphanumeric characters, hyphens, and underscores only
- Unique: overwriting an existing name replaces the old context (with warning)

---

## Documentation

- **[Installation Guide](docs/installation.md)** - Setup and configuration
- **[Usage Guide](docs/usage.md)** - Detailed usage instructions
- **[Development Guide](docs/development.md)** - Development setup and contribution guidelines
- **[API Documentation](docs/api/tools.md)** - Complete tool reference

---

## Key Concepts

- **Context**: A markdown document with YAML frontmatter (metadata) and markdown body (content)
- **Name**: Agent-recognizable identifier (e.g., "api-design-notes", "bug-fix-context")
- **Storage**: Individual .mdc files in `.out_of_context/contexts/` directory
- **Bulk Operations**: Process multiple contexts in a single call (put, get, delete)

---

## Architecture

The server provides a simple file-based storage system built with FastMCP:

**Key Components:**
- **FastMCP Server**: Modern MCP server implementation with middleware support
- **MDCStorage**: Manages .mdc file operations (save, load, list, search, delete)
- **CRUD Tools**: 5 tool handlers using `@mcp.tool()` decorators for automatic registration
- **AppStateMiddleware**: Dependency injection pattern for clean state management

**Storage:**
- Each context is one .mdc file
- YAML frontmatter for metadata
- Markdown body for content
- Simple text-based search

---

## Development

### Setup

```bash
# Clone repository
git clone <repository-url>
cd out_of_context

# Create environment
hatch env create

# Install dependencies
hatch run update-deps
```

### Run Tests

```bash
# Unit tests
hatch run pytest -m 'unit'

# Integration tests
hatch run pytest -m 'integration'
```

### Code Quality

```bash
# Lint and format
hatch run lint-fix
hatch run fmt-fix

# Type check
hatch run typecheck

# Full release pipeline
hatch run release
```

See [Development Guide](docs/development.md) for detailed setup and contribution guidelines.

---

## Project Structure

```
out_of_context/
├── src/hjeon139_mcp_outofcontext/  # Main package
│   ├── fastmcp_server.py            # FastMCP instance + middleware
│   ├── main.py                      # Entry point
│   ├── tools/
│   │   ├── crud/                    # CRUD operations (put, get, delete)
│   │   └── query/                   # Query operations (list, search)
│   ├── storage/                     # MDC storage layer
│   ├── app_state.py                 # Application state
│   ├── config.py                    # Configuration
│   └── prompts.py                   # MCP prompts
├── tests/                           # Test files (195 tests)
├── docs/                            # Documentation
└── pyproject.toml                   # Project configuration
```

---

## Contributing

Contributions welcome! Please:

1. Follow [Conventional Commits](docs/steering/06_conventional_commits.md) format
2. Add tests for new functionality
3. Update documentation as needed
4. Run pre-commit checklist before submitting

See [Development Guide](docs/development.md) for detailed contribution guidelines.

---

## License

Apache 2.0 - See [LICENSE](LICENSE) file for details.

---

## References

- **MCP Protocol**: [Model Context Protocol](https://modelcontextprotocol.io/)
- **Steering Documentation**: [docs/steering/](docs/steering/) - Development guidelines

---

## Status

**Version:** 1.0.0 (Launch Release)

**Status:** Production Ready

**Features:**
- ✅ Basic CRUD operations (put, list, get, search, delete)
- ✅ Markdown file storage (.mdc format)
- ✅ Agent-recognizable names
- ✅ Bulk operations support with robust parameter handling
- ✅ Pydantic validation for type-safe parameters
- ✅ Automatic JSON schema generation for MCP clients
- ✅ Text search across metadata and content
- ✅ Built with FastMCP for improved developer experience

---

## Support

- **Documentation**: See [docs/](docs/) directory
- **Issues**: Open an issue on GitHub
- **Questions**: Use GitHub Discussions

---

## Acknowledgments

Built with:
- [FastMCP](https://github.com/jlowin/fastmcp) - FastMCP framework for MCP servers
- [Pydantic](https://pydantic.dev/) - Data validation
- [PyYAML](https://pyyaml.org/) - YAML parsing
