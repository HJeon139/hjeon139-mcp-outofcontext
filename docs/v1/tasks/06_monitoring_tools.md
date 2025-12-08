# Task 06: Monitoring Tools Implementation

## Dependencies

- Task 05: Context Manager Implementation
- Task 06a: Storage Layer Scalability Enhancements (token caching affects metrics)

## Scope

Implement MCP tools for context monitoring and analysis. This includes:

- Implement `context_analyze_usage` tool
- Implement `context_get_working_set` tool
- Register tools with MCP server
- Validate tool parameters with Pydantic
- Return structured tool results

## Acceptance Criteria

- Tools are discoverable via MCP tool list
- Tools accept context descriptors from platforms
- Tools return usage metrics and recommendations
- Tools handle invalid parameters gracefully
- Tool descriptions explain usage clearly

## Implementation Details

### Tool: `context_analyze_usage`

**Purpose:** Analyze current context usage and return metrics, health score, and recommendations.

**Parameters:**
```python
{
    "context_descriptors": ContextDescriptors,  # Optional, platform provides
    "project_id": str,  # Required
    "task_id": Optional[str],  # Optional
    "token_limit": Optional[int]  # Optional, default 32000
}
```

**Returns:**
```python
{
    "usage_metrics": UsageMetrics,
    "health_score": HealthScore,
    "recommendations": List[Recommendation],
    "pruning_candidates_count": int
}
```

**Implementation:**
1. Validate parameters
2. Call `context_manager.analyze_context()`
   - Analysis engine uses cached token counts (from Task 06a)
   - Metrics computation is fast even with millions of tokens
3. Format results for MCP response
4. Return structured response

**Scalability Note:** Token counting uses cached values from segment metadata, ensuring < 100ms performance requirement is met.

### Tool: `context_get_working_set`

**Purpose:** Get current working set segments for the active task.

**Parameters:**
```python
{
    "project_id": str,  # Required
    "task_id": Optional[str]  # Optional, uses current task if not provided
}
```

**Returns:**
```python
{
    "working_set": WorkingSet,
    "segments": List[ContextSegment],
    "total_tokens": int,
    "segment_count": int
}
```

**Implementation:**
1. Validate parameters
2. Call `context_manager.get_working_set()`
3. Format segments for response
4. Return working set information

### Tool Registration

Register tools with MCP server using tool registry:

```python
def register_monitoring_tools(registry: ToolRegistry, context_manager: ContextManager):
    @registry.register("context_analyze_usage")
    def analyze_usage(params: Dict) -> Dict:
        # Validate and call handler
        pass
    
    @registry.register("context_get_working_set")
    def get_working_set(params: Dict) -> Dict:
        # Validate and call handler
        pass
```

### Parameter Validation

Use Pydantic models for validation:

```python
class AnalyzeUsageParams(BaseModel):
    context_descriptors: Optional[ContextDescriptors] = None
    project_id: str
    task_id: Optional[str] = None
    token_limit: Optional[int] = 32000
```

### Error Handling

Return structured errors:

```python
{
    "error": {
        "code": "INVALID_PARAMETER",
        "message": "project_id is required",
        "details": {...}
    }
}
```

### Tool Descriptions

Provide clear descriptions for tool discovery:

- Explain what the tool does
- Explain when to use it
- Provide example usage
- List required/optional parameters

## Testing Approach

### Unit Tests

- Test tool handlers with valid parameters
- Test parameter validation (invalid inputs)
- Test error handling
- Test response formatting

### Integration Tests

- Test tool registration with MCP server
- Test tool discovery via MCP protocol
- Test tool calls end-to-end
- Test with real MCP client

### Test Files

- `tests/test_tools_monitoring.py` - Monitoring tools tests

### Test Scenarios

1. Call `context_analyze_usage` with valid parameters
2. Call `context_analyze_usage` with missing project_id (error)
3. Call `context_get_working_set` for current task
4. Call `context_get_working_set` for specific task
5. Test tool discovery via MCP protocol
6. Test error responses for invalid inputs

## References

- [Integration Patterns](../design/05_integration_patterns.md) - Tool interface patterns
- [Interfaces and Data Models](../design/09_interfaces.md) - Tool interface specifications
- [Components](../design/04_components.md) - Tool Registry component
- [MCP Protocol Specification](https://modelcontextprotocol.io/) - MCP tool format

