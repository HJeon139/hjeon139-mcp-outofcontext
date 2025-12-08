# Out of Context

An MCP (Model Context Protocol) server for managing large context windows in AI agent platforms. Helps agents handle context that exceeds token limits by analyzing usage, pruning old segments, and stashing context for later retrieval.

---

## Features

- **Context Analysis**: Monitor token usage, segment distribution, and context health
- **Garbage Collection**: Automatically identify and prune old or unused segments using GC heuristics
- **Stashing & Retrieval**: Archive context segments and retrieve them when needed
- **Task Management**: Organize context by tasks and switch between them seamlessly
- **Scalability**: Designed for millions of tokens with indexing and file sharding
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
      "command": "python",
      "args": ["-m", "hjeon139_mcp_outofcontext.main"],
      "env": {
        "OUT_OF_CONTEXT_STORAGE_PATH": ".out_of_context",
        "OUT_OF_CONTEXT_TOKEN_LIMIT": "1000000"
      }
    }
  }
}
```

### Verify Installation

In your MCP platform, check that tools like `context_analyze_usage` are available.

---

## Usage Examples

### Monitor Context Usage

```json
{
  "tool": "context_analyze_usage",
  "arguments": {
    "project_id": "my-project"
  }
}
```

Returns usage metrics, health score, and recommendations.

### Prune Old Context

```json
{
  "tool": "context_gc_analyze",
  "arguments": {
    "project_id": "my-project",
    "target_tokens": 100000
  }
}
```

Analyzes pruning candidates and generates a plan to free tokens.

### Stash Context

```json
{
  "tool": "context_stash",
  "arguments": {
    "query": "old documentation",
    "filters": {
      "type": "note",
      "created_before": "2024-01-01T00:00:00Z"
    }
  }
}
```

Moves matching segments to stashed storage.

### Retrieve Stashed Context

```json
{
  "tool": "context_retrieve_stashed",
  "arguments": {
    "query": "important function",
    "move_to_active": true
  }
}
```

Retrieves and restores stashed segments to active context.

---

## Documentation

- **[Installation Guide](docs/installation.md)** - Setup and configuration
- **[Usage Guide](docs/usage.md)** - Detailed usage instructions and workflows
- **[Development Guide](docs/development.md)** - Development setup and contribution guidelines
- **[API Documentation](docs/api/tools.md)** - Complete tool and model reference
- **[Demo Guide](docs/demo.md)** - Step-by-step demonstration scenarios

---

## Key Concepts

- **Segments**: Individual pieces of context (messages, code, logs, etc.)
- **Working Set**: Active segments currently in use
- **Stashed Storage**: Archived segments that can be retrieved later
- **Projects**: Isolated context spaces (typically one per codebase)
- **Tasks**: Sub-divisions within a project for organizing work

---

## Architecture

The server operates in **advisory mode**: platforms call tools with context metadata, the server analyzes and returns recommendations, and platforms apply changes to their own context.

**Key Components:**
- **Context Manager**: Orchestrates context operations
- **Analysis Engine**: Analyzes usage and generates recommendations
- **GC Engine**: Identifies pruning candidates using garbage collection heuristics
- **Storage Layer**: Manages segment storage with indexing and sharding
- **Tool Handlers**: MCP tool implementations

---

## Scalability

Designed for **millions of tokens**:

- **Inverted Index**: Fast keyword search (< 500ms for millions of tokens)
- **Token Caching**: Token counts cached in segment metadata
- **File Sharding**: Stashed segments stored in sharded files
- **LRU Cache**: Active segments use LRU eviction (max 10k segments)

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
hatch run test
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
│   ├── tools/                      # MCP tool handlers
│   ├── models/                     # Data models
│   ├── storage/                    # Storage layer
│   └── ...
├── tests/                          # Test files
├── docs/                           # Documentation
└── pyproject.toml                  # Project configuration
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
- **Design Documentation**: [docs/v1/design/](docs/v1/design/) - Architecture and design decisions

---

## Status

**Version:** 0.13.0

**Status:** Active development

**Features:**
- ✅ Context analysis and monitoring
- ✅ Garbage collection pruning
- ✅ Stashing and retrieval
- ✅ Task management
- ✅ Scalability enhancements (indexing, sharding, caching)

**Roadmap:**
- Vector DB for semantic search (v2)
- Advanced compression techniques (v2)
- Multi-server support (v2)

---

## Support

- **Documentation**: See [docs/](docs/) directory
- **Issues**: Open an issue on GitHub
- **Questions**: Use GitHub Discussions

---

## Acknowledgments

Built with:
- [MCP](https://github.com/modelcontextprotocol) - Model Context Protocol
- [Pydantic](https://pydantic.dev/) - Data validation
- [tiktoken](https://github.com/openai/tiktoken) - Token counting
