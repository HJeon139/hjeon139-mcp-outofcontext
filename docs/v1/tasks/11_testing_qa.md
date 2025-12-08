# Task 11: Testing and Quality Assurance

## Dependencies

- Task 10: MCP Server Integration and Tool Registration

## Scope

Achieve comprehensive test coverage and quality assurance. This includes:

- Achieve 80% test coverage target
- Integration tests for end-to-end workflows
- Performance tests for all operations
- Error handling and edge case testing
- Test documentation and examples

## Acceptance Criteria

- Test coverage ≥ 80%
- All performance targets met
- All error cases handled gracefully
- Integration tests pass
- Tests are maintainable and well-documented

## Implementation Details

### Test Coverage

Use pytest-cov to measure coverage:

```bash
pytest --cov=src/out_of_context --cov-report=html --cov-report=term
```

Target: ≥ 80% coverage across all modules.

### Integration Tests

Create end-to-end test scenarios:

1. **Full Context Management Workflow:**
   - Analyze context → Get pruning candidates → Prune → Stash → Search → Retrieve

2. **Task Management Workflow:**
   - Set task → Get task context → Create snapshot → Switch task → Retrieve snapshot

3. **Multi-Project Workflow:**
   - Create segments in multiple projects → Verify isolation

4. **Persistence Workflow:**
   - Store segments → Restart server → Verify segments loaded

### Performance Tests

Test all performance requirements at scale (millions of tokens):

1. **Context Analysis:** < 2s for millions of tokens
2. **Token Counting:** < 100ms for typical context (with caching)
3. **Search:** < 500ms for millions of tokens (with indexing)
4. **Storage Operations:** Non-blocking
5. **GC Analysis:** < 2s for millions of segments (with heap-based selection)

Create performance test suite:

```python
@pytest.mark.performance
def test_context_analysis_performance():
    """Test context analysis completes in < 2s."""
    segments = create_large_context(1000000)  # millions of tokens
    start = time.time()
    result = analysis_engine.analyze_context_usage(segments)
    duration = time.time() - start
    assert duration < 2.0

@pytest.mark.performance
def test_search_with_indexing():
    """Test search performance with inverted index."""
    # Create 1M segments with stashed storage
    storage = StorageLayer("/tmp/test")
    segments = create_test_segments(count=1000000, tokens_per_segment=10)
    
    # Index all segments
    for seg in segments:
        storage.stash_segment(seg, "test_project")
    
    # Search should be fast with indexing
    start = time.time()
    results = storage.search_stashed("test query", {}, "test_project")
    duration = time.time() - start
    
    assert duration < 0.5  # < 500ms
    assert len(results) > 0

@pytest.mark.performance
def test_token_counting_with_cache():
    """Test token counting uses cache for performance."""
    segment = ContextSegment(segment_id="1", text="test " * 10000)
    tokenizer = Tokenizer()
    
    # First count (no cache)
    start = time.time()
    count1 = tokenizer.count_segment_tokens(segment)
    duration1 = time.time() - start
    
    # Second count (cached)
    start = time.time()
    count2 = tokenizer.count_segment_tokens(segment)
    duration2 = time.time() - start
    
    assert count1 == count2
    assert duration2 < duration1  # Cached should be faster
    assert duration2 < 0.001  # Cache lookup should be < 1ms

@pytest.mark.performance
def test_gc_analysis_with_heap():
    """Test GC analysis uses heap-based selection."""
    # Create 1M segments
    segments = create_test_segments(count=1000000)
    gc_engine = GCEngine()
    
    # Analyze pruning candidates
    start = time.time()
    candidates = gc_engine.analyze_pruning_candidates(segments, roots=set())
    plan = gc_engine.generate_pruning_plan(candidates, target_tokens=100000)
    duration = time.time() - start
    
    assert duration < 2.0  # < 2s with heap-based selection
    assert len(plan.segments) > 0
```

### Scalability Tests

Test system behavior at scale:

```python
@pytest.mark.scalability
def test_memory_usage_at_scale():
    """Test memory usage with LRU eviction."""
    storage = StorageLayer("/tmp/test", max_active_segments=10000)
    
    # Add 100k segments (should evict to disk)
    segments = create_test_segments(count=100000)
    for seg in segments:
        storage.store_segment(seg, "test_project")
    
    # Check memory usage
    import sys
    memory_mb = sys.getsizeof(storage.active_segments) / (1024 * 1024)
    assert memory_mb < 500  # Should be reasonable with eviction

@pytest.mark.scalability
def test_file_sharding():
    """Test JSON file sharding works correctly."""
    storage = StorageLayer("/tmp/test")
    
    # Stash segments for multiple projects
    for project_id in ["proj1", "proj2", "proj3"]:
        segments = create_test_segments(count=10000)
        for seg in segments:
            storage.stash_segment(seg, project_id)
    
    # Verify separate files exist
    assert (Path("/tmp/test/stashed/proj1.json")).exists()
    assert (Path("/tmp/test/stashed/proj2.json")).exists()
    assert (Path("/tmp/test/stashed/proj3.json")).exists()
```

### Error Handling Tests

Test all error cases:

1. **Invalid Parameters:**
   - Missing required parameters
   - Invalid parameter types
   - Out of range values

2. **Missing Resources:**
   - Segment not found
   - Project not found
   - Task not found

3. **Storage Errors:**
   - Corrupt JSON file
   - Missing storage file
   - Permission errors
   - Disk full

4. **Edge Cases:**
   - Empty context
   - Single segment
   - All segments pinned
   - No pruning candidates

### Test Organization

Organize tests by component:

```
tests/
  test_models.py
  test_storage.py
  test_gc_engine.py
  test_analysis_engine.py
  test_context_manager.py
  test_tools_monitoring.py
  test_tools_pruning.py
  test_tools_stashing.py
  test_tools_tasks.py
  test_server.py
  test_config.py
  test_integration.py  # End-to-end tests
  test_performance.py  # Performance tests
```

### Test Fixtures

Create reusable test fixtures:

```python
@pytest.fixture
def sample_segments():
    """Create sample context segments for testing."""
    return [
        ContextSegment(segment_id="1", text="...", type="message", ...),
        ...
    ]

@pytest.fixture
def context_manager():
    """Create context manager with test storage."""
    storage = InMemoryStorage()  # Test double
    return ContextManager(storage, ...)
```

### Test Documentation

Document test approach:

- Test strategy document
- Test coverage report
- Performance benchmarks
- Known limitations

### Continuous Integration

Ensure tests run in CI:

- Run all tests on commit
- Check coverage threshold
- Run performance tests
- Generate coverage reports

## Testing Approach

### Coverage Analysis

1. Run coverage analysis
2. Identify gaps
3. Add missing tests
4. Verify ≥ 80% coverage

### Integration Test Scenarios

1. Full context management workflow
2. Task management workflow
3. Multi-project isolation
4. Persistence and recovery
5. Error recovery

### Performance Benchmarking

1. Measure all operations
2. Compare against requirements
3. Optimize if needed
4. Document benchmarks

### Error Case Testing

1. Test all error paths
2. Verify error messages
3. Test error recovery
4. Document error handling

### Test Files to Update

- All existing test files (add missing cases)
- `tests/test_integration.py` (new, end-to-end tests)
- `tests/test_performance.py` (new, performance tests)
- `tests/conftest.py` (shared fixtures)

### Test Execution

Run comprehensive test suite:

```bash
# All tests
hatch run test

# Unit tests only
hatch run test -m "not integration and not performance"

# Integration tests
hatch run test -m integration

# Performance tests
hatch run test -m performance

# Coverage report
hatch run test --cov=src/out_of_context --cov-report=html
```

## References

- [Constraints and Requirements](../design/07_constraints_requirements.md) - Performance requirements
- [Components](../design/04_components.md) - All components to test
- [Scalability Analysis](../design/10_scalability_analysis.md) - Scalability issues and test requirements
- [Storage Scalability Enhancements](06a_storage_scalability_enhancements.md) - Scalability features to test
- [pytest Documentation](https://docs.pytest.org/) - Testing framework
- [pytest-cov Documentation](https://pytest-cov.readthedocs.io/) - Coverage plugin

