# Task 11: Testing and Quality Assurance

## Dependencies

- Task 10: MCP Server Integration and Tool Registration

## Scope

Achieve comprehensive test coverage, quality assurance, and high standards for code readability and maintainability. This includes:

- Achieve 80% test coverage target
- Integration tests for end-to-end workflows
- Performance tests for all operations
- Error handling and edge case testing
- Test documentation and examples
- Code readability standards (naming, documentation, structure)
- Maintainability standards (complexity metrics, refactoring guidelines)
- Code review criteria and quality gates

## Acceptance Criteria

- Test coverage ≥ 80%
- All performance targets met
- All error cases handled gracefully
- Integration tests pass
- Tests are maintainable and well-documented
- All code meets readability standards (documentation, naming, structure)
- All code meets maintainability standards (complexity, file size, organization)
- Code review checklist passes for all changes
- Static analysis tools pass (ruff, mypy) with zero errors

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

## Code Readability Standards

### Documentation Requirements

**All public APIs must be documented:**

1. **Module-level docstrings:**
   - Purpose and responsibility of the module
   - Key concepts and usage patterns
   - Example usage when appropriate

2. **Class docstrings:**
   - Purpose and responsibility of the class
   - Key methods and their roles
   - Usage examples for complex classes

3. **Function/method docstrings:**
   - Clear description of what the function does
   - Parameter descriptions (type and purpose)
   - Return value description
   - Raises section for exceptions
   - Example usage for complex functions

**Example:**
```python
def analyze_context_usage(
    segments: list[ContextSegment],
    analysis_params: AnalysisParams,
) -> ContextUsageAnalysis:
    """
    Analyze context usage patterns to identify pruning candidates.
    
    Analyzes segment access patterns, recency, and importance to
    determine which segments are candidates for pruning.
    
    Args:
        segments: List of context segments to analyze
        analysis_params: Parameters controlling analysis behavior
        
    Returns:
        ContextUsageAnalysis containing pruning candidates and metrics
        
    Raises:
        ValueError: If segments list is empty or analysis_params invalid
        
    Example:
        >>> segments = [ContextSegment(...), ...]
        >>> params = AnalysisParams(max_age_days=7)
        >>> analysis = analyze_context_usage(segments, params)
        >>> print(f"Found {len(analysis.candidates)} candidates")
    """
    ...
```

### Naming Conventions

**Follow PEP 8 naming standards:**

1. **Functions and variables:** `snake_case`
2. **Classes:** `PascalCase`
3. **Constants:** `UPPER_SNAKE_CASE`
4. **Private attributes/methods:** `_leading_underscore`
5. **Type variables:** `T`, `K`, `V` for simple generics; `DescriptiveName` for complex

**Naming guidelines:**

- **Descriptive names:** Names should clearly indicate purpose
  - ✅ Good: `analyze_pruning_candidates`, `get_segment_by_id`
  - ❌ Bad: `analyze`, `get_seg`, `do_stuff`

- **Verb-noun pattern for functions:** Use verbs for actions
  - ✅ Good: `create_segment`, `update_metadata`, `delete_stashed`
  - ❌ Bad: `segment_creator`, `metadata_updater`

- **Noun pattern for classes:** Use nouns for entities
  - ✅ Good: `ContextManager`, `StorageLayer`, `GCEngine`
  - ❌ Bad: `ManageContext`, `StoreData`

- **Boolean names:** Use `is_`, `has_`, `should_` prefixes
  - ✅ Good: `is_pinned`, `has_children`, `should_prune`
  - ❌ Bad: `pinned`, `children`, `prune_flag`

- **Avoid abbreviations:** Use full words unless abbreviation is widely understood
  - ✅ Good: `context_manager`, `storage_layer`
  - ❌ Bad: `ctx_mgr`, `stg_lyr`

### Code Structure and Organization

**File organization:**

1. **File size limit:** Keep files under ~400 lines of code
   - Split large files into logical modules
   - Use subdirectories for related functionality
   - Group related handlers/functions into separate modules

2. **Import organization:**
   - Standard library imports
   - Third-party imports
   - Local application imports
   - Use `ruff` to enforce import sorting

3. **Class organization:**
   - Class docstring
   - Class constants
   - `__init__` and lifecycle methods
   - Public methods
   - Private methods
   - Properties

4. **Function organization:**
   - Keep functions focused on single responsibility
   - Extract complex logic into helper functions
   - Use early returns to reduce nesting

**Example structure:**
```python
"""Module docstring explaining purpose."""

from typing import ...
import ...

# Constants
DEFAULT_MAX_SIZE = 1000

class ExampleClass:
    """Class docstring."""
    
    def __init__(self, ...) -> None:
        """Initialize instance."""
        ...
    
    def public_method(self, ...) -> ...:
        """Public method docstring."""
        ...
    
    def _private_helper(self, ...) -> ...:
        """Private helper method."""
        ...
```

### Type Hints

**All functions must have complete type hints:**

1. **Function signatures:** All parameters and return types
2. **Variable annotations:** For complex types or when clarity is needed
3. **Generic types:** Use `typing` generics appropriately
4. **Type aliases:** Create aliases for complex repeated types

**Example:**
```python
from typing import TypeVar, Generic

T = TypeVar('T')
SegmentList = list[ContextSegment]

def process_segments(
    segments: SegmentList,
    filter_fn: Callable[[ContextSegment], bool],
) -> SegmentList:
    """Process segments with filter function."""
    return [s for s in segments if filter_fn(s)]
```

## Code Maintainability Standards

### Complexity Metrics

**Enforce complexity limits:**

1. **Cyclomatic complexity:** ≤ 10 per function
   - Use `ruff` rule `C901` to detect complex functions
   - Refactor complex functions into smaller, focused functions

2. **Function length:** ≤ 50 lines per function
   - Extract logic into helper functions
   - Use descriptive helper function names

3. **Class complexity:** ≤ 20 methods per class
   - Split large classes into focused components
   - Use composition over inheritance

4. **File size:** ≤ 400 lines per file
   - Split into logical modules
   - Use subdirectories for related functionality

**Measuring complexity:**
```bash
# Use ruff to check complexity
ruff check --select C901 src/

# Use radon for detailed complexity analysis
pip install radon
radon cc src/ --min B  # Show functions with complexity >= B
radon mi src/  # Maintainability index
```

### Refactoring Guidelines

**When to refactor:**

1. **Complexity threshold exceeded:** Function/class exceeds limits
2. **Code duplication:** DRY principle violations
3. **Unclear intent:** Code requires comments to understand
4. **Testability issues:** Difficult to test in isolation
5. **Performance concerns:** Identified bottlenecks

**Refactoring patterns:**

1. **Extract method:** Break complex functions into smaller functions
2. **Extract class:** Split large classes into focused components
3. **Rename for clarity:** Improve naming to reflect intent
4. **Simplify conditionals:** Use early returns, guard clauses
5. **Eliminate duplication:** Extract common logic

**Example refactoring:**
```python
# Before: Complex function
def analyze_and_prune(segments, params):
    candidates = []
    for seg in segments:
        if seg.last_accessed < params.max_age:
            score = calculate_score(seg)
            if score < params.threshold:
                candidates.append(seg)
    return candidates

# After: Extracted and simplified
def analyze_and_prune(
    segments: list[ContextSegment],
    params: AnalysisParams,
) -> list[ContextSegment]:
    """Analyze segments and return pruning candidates."""
    return [
        seg
        for seg in segments
        if _is_pruning_candidate(seg, params)
    ]

def _is_pruning_candidate(
    segment: ContextSegment,
    params: AnalysisParams,
) -> bool:
    """Check if segment is a pruning candidate."""
    if segment.last_accessed >= params.max_age:
        return False
    score = _calculate_score(segment)
    return score < params.threshold
```

### Code Organization Patterns

**Follow established patterns:**

1. **Dependency injection:** No global state, inject dependencies
2. **Interface segregation:** Small, focused interfaces
3. **Single responsibility:** Each class/function has one job
4. **Testable design:** Easy to test in isolation with mocks

**Example:**
```python
# Good: Dependency injection, testable
class ContextManager:
    def __init__(
        self,
        storage: IStorageLayer,
        analysis_engine: AnalysisEngine,
    ) -> None:
        self._storage = storage
        self._analysis = analysis_engine

# Bad: Global state, hard to test
class ContextManager:
    def __init__(self) -> None:
        self._storage = StorageLayer()  # Hard-coded dependency
```

### Static Analysis Requirements

**All code must pass static analysis:**

1. **Ruff linting:** Zero errors, zero warnings
   ```bash
   hatch run lint-fix  # Must pass with zero issues
   ```

2. **Ruff formatting:** Consistent code style
   ```bash
   hatch run fmt-fix  # Must pass
   ```

3. **MyPy type checking:** Zero type errors
   ```bash
   hatch run typecheck  # Must pass
   ```

4. **Complexity checks:** No functions exceeding limits
   ```bash
   ruff check --select C901 src/  # Must pass
   ```

### Code Review Checklist

**All code changes must pass this checklist:**

- [ ] **Documentation:**
  - [ ] All public functions have docstrings
  - [ ] Complex logic has inline comments explaining "why"
  - [ ] Module docstrings explain purpose

- [ ] **Naming:**
  - [ ] Names are descriptive and follow conventions
  - [ ] No abbreviations unless widely understood
  - [ ] Boolean names use `is_`/`has_`/`should_` prefixes

- [ ] **Type hints:**
  - [ ] All functions have complete type hints
  - [ ] Complex types use type aliases
  - [ ] Generic types used appropriately

- [ ] **Structure:**
  - [ ] File size ≤ 400 lines
  - [ ] Functions ≤ 50 lines
  - [ ] Cyclomatic complexity ≤ 10 per function
  - [ ] Imports organized correctly

- [ ] **Maintainability:**
  - [ ] No code duplication (DRY principle)
  - [ ] Functions have single responsibility
  - [ ] Dependencies injected (no globals)
  - [ ] Code is testable in isolation

- [ ] **Static analysis:**
  - [ ] Ruff linting passes (zero errors)
  - [ ] Ruff formatting passes
  - [ ] MyPy type checking passes
  - [ ] Complexity checks pass

- [ ] **Testing:**
  - [ ] New code has unit tests
  - [ ] Edge cases covered
  - [ ] Error cases tested
  - [ ] Tests are maintainable

### Quality Metrics and Reporting

**Track and report quality metrics:**

1. **Coverage metrics:**
   ```bash
   pytest --cov=src/hjeon139_mcp_outofcontext --cov-report=html
   ```

2. **Complexity metrics:**
   ```bash
   radon cc src/ --min B
   radon mi src/
   ```

3. **Static analysis results:**
   ```bash
   ruff check src/
   mypy src/
   ```

4. **File size analysis:**
   ```bash
   find src/ -name "*.py" -exec wc -l {} + | sort -rn
   ```

**Quality gates:**

- Coverage must be ≥ 80%
- All static analysis tools must pass
- No functions with complexity > 10
- No files > 400 lines
- All public APIs documented

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

### Code Quality Analysis

1. Run static analysis tools (ruff, mypy)
2. Check complexity metrics (cyclomatic complexity, file size)
3. Review code documentation coverage
4. Identify refactoring opportunities
5. Address all quality issues
6. Verify all quality gates pass

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

### Code Quality Files to Create/Update

- `.pre-commit-config.yaml` (pre-commit hooks for quality checks)
- `docs/code_quality_standards.md` (detailed quality standards document)
- Update `pyproject.toml` with additional ruff rules for complexity
- Add complexity checking to CI pipeline

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
hatch run test --cov=src/hjeon139_mcp_outofcontext --cov-report=html
```

### Quality Checks

Run comprehensive quality checks:

```bash
# Linting (must pass with zero errors)
hatch run lint-fix

# Formatting (must pass)
hatch run fmt-fix

# Type checking (must pass)
hatch run typecheck

# Complexity checking
ruff check --select C901 src/hjeon139_mcp_outofcontext

# Full quality pipeline
hatch run release  # Runs lint, format, typecheck, tests, build
```

### Pre-Commit Quality Gates

Set up pre-commit hooks to enforce quality:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.6.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.11.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
  - repo: local
    hooks:
      - id: complexity-check
        name: Complexity Check
        entry: ruff check --select C901
        language: system
        pass_filenames: false
```

## Implementation Checklist

### Testing Tasks

- [ ] Achieve ≥ 80% test coverage
- [ ] Create integration test suite
- [ ] Create performance test suite
- [ ] Test all error cases
- [ ] Document test strategy
- [ ] Set up CI test pipeline

### Code Quality Tasks

- [ ] Review all code for documentation completeness
- [ ] Ensure all functions have type hints
- [ ] Verify naming conventions across codebase
- [ ] Check and fix complexity violations
- [ ] Refactor files exceeding 400 lines
- [ ] Set up complexity checking in CI
- [ ] Create code review checklist document
- [ ] Set up pre-commit hooks for quality gates
- [ ] Document code quality standards
- [ ] Run full quality analysis and fix issues

### Quality Metrics to Track

- [ ] Test coverage percentage (target: ≥ 80%)
- [ ] Static analysis pass rate (target: 100%)
- [ ] Average cyclomatic complexity (target: ≤ 10)
- [ ] Files exceeding size limit (target: 0)
- [ ] Documentation coverage (target: 100% public APIs)
- [ ] Type hint coverage (target: 100%)

## References

- [Constraints and Requirements](../design/07_constraints_requirements.md) - Performance requirements
- [Components](../design/04_components.md) - All components to test
- [Scalability Analysis](../design/10_scalability_analysis.md) - Scalability issues and test requirements
- [Storage Scalability Enhancements](06a_storage_scalability_enhancements.md) - Scalability features to test
- [pytest Documentation](https://docs.pytest.org/) - Testing framework
- [pytest-cov Documentation](https://pytest-cov.readthedocs.io/) - Coverage plugin
- [Ruff Documentation](https://docs.astral.sh/ruff/) - Linting and formatting
- [MyPy Documentation](https://mypy.readthedocs.io/) - Type checking
- [Radon Documentation](https://radon.readthedocs.io/) - Complexity analysis
- [PEP 8 Style Guide](https://peps.python.org/pep-0008/) - Python style conventions
- [PEP 257 Docstring Conventions](https://peps.python.org/pep-0257/) - Docstring standards

