# Task 10: MCP Server Integration and Tool Registration

## Dependencies

- Task 06: Monitoring Tools Implementation
- Task 06a: Storage Layer Scalability Enhancements
- Task 07: Pruning Tools Implementation
- Task 08: Stashing and Retrieval Tools Implementation
- Task 09: Task Management Tools Implementation

## Scope

Complete the MCP server implementation with full tool registration and integration. This includes:

- Complete MCP server implementation
- Register all tools with MCP SDK
- Implement tool dispatch and error handling
- Server startup and shutdown logic
- Configuration management (storage path, etc.)

## Acceptance Criteria

- Server starts and responds to MCP protocol
- All tools are registered and discoverable
- Tool calls are dispatched correctly
- Errors are returned in MCP format
- Server handles shutdown gracefully
- Configuration is loaded from environment/files

## Implementation Details

### MCP Server Implementation (`src/out_of_context/server.py`)

Complete the server implementation:

```python
class ContextManagementServer:
    def __init__(self, config: Config):
        self.config = config
        self.storage = StorageLayer(config.storage_path)
        self.gc_engine = GCEngine()
        self.analysis_engine = AnalysisEngine()
        self.context_manager = ContextManager(
            self.storage, self.gc_engine, self.analysis_engine
        )
        self.tool_registry = ToolRegistry()
        self._register_all_tools()
    
    def _register_all_tools(self):
        """Register all MCP tools."""
        register_monitoring_tools(self.tool_registry, self.context_manager)
        register_pruning_tools(self.tool_registry, self.context_manager)
        register_stashing_tools(self.tool_registry, self.context_manager)
        register_task_tools(self.tool_registry, self.context_manager)
    
    async def handle_tool_call(self, name: str, arguments: Dict) -> Dict:
        """Handle MCP tool call."""
        try:
            handler = self.tool_registry.get_handler(name)
            result = handler(arguments)
            return {"content": [{"type": "text", "text": json.dumps(result)}]}
        except Exception as e:
            return self._format_error(e)
```

### Tool Registration

Register all tools from previous tasks:

- Monitoring tools (Task 06)
- Pruning tools (Task 07)
- Stashing tools (Task 08)
- Task management tools (Task 09)

### Tool Dispatch

Implement tool call dispatch:

1. Receive tool call from MCP protocol
2. Validate tool name exists
3. Validate parameters
4. Dispatch to handler
5. Format response
6. Handle errors

### Error Handling

Format errors in MCP format:

```python
def _format_error(self, error: Exception) -> Dict:
    return {
        "isError": True,
        "content": [{
            "type": "text",
            "text": json.dumps({
                "error": {
                    "code": type(error).__name__,
                    "message": str(error)
                }
            })
        }]
    }
```

### Server Startup (`src/out_of_context/main.py`)

Create entry point:

```python
async def main():
    config = load_config()
    server = ContextManagementServer(config)
    
    # Initialize MCP server with STDIO transport
    async with mcp.Server() as mcp_server:
        # Register tools
        for tool_name in server.tool_registry.list_tools():
            mcp_server.register_tool(tool_name, server.handle_tool_call)
        
        # Run server
        await mcp_server.run()

if __name__ == "__main__":
    asyncio.run(main())
```

### Configuration Management (`src/out_of_context/config.py`)

Load configuration from:

1. Environment variables
2. Config file (`~/.out_of_context/config.json`)
3. Default values

```python
@dataclass
class Config:
    storage_path: str = "~/.out_of_context/storage.json"
    token_limit: int = 1000000  # Millions of tokens
    default_model: str = "gpt-4"
    log_level: str = "INFO"
    max_active_segments: int = 10000  # LRU cache size
    enable_indexing: bool = True  # Enable inverted index
    enable_file_sharding: bool = True  # Enable file sharding

def load_config() -> Config:
    """Load configuration from environment and files."""
    # Load from env vars
    storage_path = os.getenv("OUT_OF_CONTEXT_STORAGE_PATH", "~/.out_of_context/storage.json")
    # ... load other settings
    return Config(storage_path=storage_path, ...)
```

### Server Lifecycle

Handle startup and shutdown:

- **Startup**: Load config, initialize components, register tools
- **Runtime**: Handle tool calls, maintain state
- **Shutdown**: Save state, close connections, cleanup

### MCP Protocol Compliance

Ensure full MCP protocol compliance:

- Tool discovery (list_tools)
- Tool calls (call_tool)
- Error responses
- Protocol version handling

## Testing Approach

### Unit Tests

- Test server initialization
- Test tool registration
- Test tool dispatch
- Test error handling
- Test configuration loading

### Integration Tests

- Test with real MCP client
- Test tool discovery
- Test tool calls end-to-end
- Test server startup/shutdown
- Test protocol compliance

### Test Files

- `tests/test_server.py` - Server integration tests
- `tests/test_config.py` - Configuration tests

### Test Scenarios

1. Server starts and responds to protocol handshake
2. All tools discoverable via list_tools
3. Tool calls dispatched correctly
4. Errors returned in MCP format
5. Configuration loaded from environment
6. Server shutdown gracefully
7. Protocol version handling
8. Concurrent tool calls (if applicable)

## References

- [Integration Patterns](../design/05_integration_patterns.md) - MCP protocol integration
- [Components](../design/04_components.md) - Tool Registry component
- [MCP Protocol Specification](https://modelcontextprotocol.io/) - Full protocol details
- [MCP SDK Documentation](https://github.com/modelcontextprotocol/python-sdk) - SDK usage

