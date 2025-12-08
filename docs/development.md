# Development Guide

This guide explains how to set up a development environment, run tests, and contribute to the Out of Context MCP server.

---

## Development Environment Setup

### Prerequisites

- **Python 3.11+** - Required Python version
- **Hatch** - Project and environment management
- **Git** - Version control

### Initial Setup

1. **Clone the repository:**

```bash
git clone <repository-url>
cd out_of_context
```

2. **Create Hatch environment:**

```bash
hatch env create
```

This creates a virtual environment with all dependencies.

3. **Enter environment (optional, for interactive work):**

```bash
hatch shell
```

4. **Install dependencies:**

```bash
hatch run update-deps
```

This installs the package in editable mode with all dev dependencies.

5. **Setup pre-commit hooks (optional, recommended):**

```bash
hatch run pre-commit install --hook-type commit-msg
```

This automatically validates commit messages follow Conventional Commits format.

---

## Running Tests

### Run All Tests

```bash
hatch run test
```

### Run with Coverage

```bash
hatch run test --cov
```

### Run Specific Test Categories

```bash
# Unit tests only
hatch run test -m unit

# Integration tests only
hatch run test -m integration

# Performance tests
hatch run test -m performance
```

### Run Specific Test File

```bash
hatch run test tests/test_storage.py
```

### Test Markers

Tests are marked with pytest markers:

- `@pytest.mark.unit` - Fast unit tests for core logic
- `@pytest.mark.integration` - Slower or integration tests
- `@pytest.mark.performance` - Performance-sensitive test scenarios
- `@pytest.mark.scalability` - Scale or load-focused test scenarios

---

## Code Style

### Linting

**Check for issues:**
```bash
hatch run lint-fix
```

This runs `ruff check --fix` to identify and auto-fix linting issues.

### Formatting

**Format code:**
```bash
hatch run fmt-fix
```

This runs `ruff format` to format code according to project standards.

### Type Checking

**Check types:**
```bash
hatch run typecheck
```

This runs `mypy` to check type annotations.

### Pre-Commit Checklist

Before committing, run the full release pipeline:

```bash
hatch run release
```

This runs:
1. `lint-fix` - Lint and auto-fix
2. `fmt-fix` - Format code
3. `typecheck` - Type checking
4. `pytest -m 'unit' --cov` - Unit tests with coverage
5. `hatch build -t wheel` - Build package

**All checks must pass before committing.**

---

## Project Structure

```
out_of_context/
├── src/
│   └── hjeon139_mcp_outofcontext/    # Main package code
│       ├── __init__.py               # Package initialization
│       ├── main.py                   # Entry point
│       ├── server.py                 # MCP server implementation
│       ├── config.py                 # Configuration management
│       ├── app_state.py              # Application state
│       ├── tool_registry.py          # Tool registration
│       ├── context_manager/          # Context management
│       ├── models/                   # Data models
│       ├── storage/                  # Storage layer
│       ├── tools/                    # MCP tool handlers
│       │   ├── monitoring.py        # Monitoring tools
│       │   ├── pruning/             # Pruning tools
│       │   ├── stashing/            # Stashing tools
│       │   └── tasks/               # Task management tools
│       ├── analysis_engine.py       # Analysis logic
│       ├── gc_engine.py             # Garbage collection
│       ├── inverted_index.py        # Search indexing
│       ├── lru_segment_cache.py     # LRU cache
│       └── tokenizer.py             # Token counting
├── tests/                            # Test files
│   ├── conftest.py                  # Pytest configuration
│   ├── test_*.py                    # Test modules
├── docs/                             # Documentation
│   ├── installation.md              # Installation guide
│   ├── usage.md                     # Usage guide
│   ├── development.md               # This file
│   ├── api/                         # API documentation
│   └── steering/                    # Development guidelines
├── pyproject.toml                   # Project configuration
└── README.md                        # Project README
```

### Module Organization

- **`models/`**: Pydantic models for data structures
- **`storage/`**: Storage layer implementations
- **`tools/`**: MCP tool handlers organized by category
- **`context_manager/`**: Context management orchestration
- **Core modules**: Analysis, GC, indexing, caching, tokenization

### Test Organization

- **`tests/`**: All test files
- **`conftest.py`**: Shared fixtures and configuration
- **Test files**: Mirror source structure (e.g., `test_storage.py` tests `storage/`)

---

## Contributing

### Development Workflow

1. **Create a feature branch:**
```bash
git checkout -b feat/my-feature
```

2. **Make changes:**
   - Write code following style guidelines
   - Add tests for new functionality
   - Update documentation as needed

3. **Run pre-commit checklist:**
```bash
hatch run release
```

4. **Commit changes:**
   - Follow Conventional Commits format
   - Include version bump if needed (see below)
   - Write clear commit messages

5. **Push and create pull request:**
   - Push branch to remote
   - Create pull request with description
   - Wait for code review

### Commit Message Format

Follow [Conventional Commits](https://www.conventionalcommits.org/) format:

```
<type>(<scope>): <subject>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `test`: Test changes
- `build`: Build system changes
- `ci`: CI/CD changes
- `chore`: Other changes

**Scopes:**
- `foundation`, `models`, `server`, `storage`, `gc`, `tools`, `tests`, `deps`, `config`

**Examples:**
```
feat(tools): add context analysis tool
fix(storage): handle missing directory gracefully
docs(readme): update installation instructions
```

### Version Bumping

**When to bump version:**
- `feat` commits → Bump **MINOR** version (0.1.0 → 0.2.0)
- `fix` commits → Bump **PATCH** version (0.1.0 → 0.1.1) ⚠️ **REQUIRED**
- Breaking changes → Bump **MAJOR** version (0.1.0 → 1.0.0)
- Other types → No version bump

**Update version in BOTH locations:**
1. `pyproject.toml`: `version = "0.2.0"`
2. `src/hjeon139_mcp_outofcontext/__init__.py`: `__version__ = "0.2.0"`

**Version bump must be included in the same commit as the code changes.**

### Code Review Process

1. **Pull request requirements:**
   - All tests pass
   - Code follows style guidelines
   - Documentation updated if needed
   - Version bumped if needed

2. **Review checklist:**
   - Code quality and style
   - Test coverage
   - Documentation completeness
   - Performance considerations
   - Backwards compatibility

3. **After approval:**
   - Maintainer merges PR
   - Changes are included in next release

### Pull Request Process

1. **Create PR with description:**
   - What changes were made
   - Why changes were needed
   - How to test changes

2. **Wait for review:**
   - Address review comments
   - Update PR as needed

3. **Merge:**
   - Squash and merge (preferred)
   - Or merge commit (if preserving history)

---

## Architecture Patterns

### Dependency Injection

**No global variables** - All state is instance-scoped:

```python
class AppState:
    def __init__(self, config: Config):
        self.storage = StorageLayer(config)
        self.gc_engine = GCEngine()
        # ...
```

**Tool handlers receive AppState:**
```python
async def handle_tool(
    app_state: AppState,
    project_id: str,
    **kwargs
) -> dict[str, Any]:
    # Use app_state.storage, app_state.gc_engine, etc.
    pass
```

### Lifecycle Management

**Explicit initialize/cleanup:**
```python
class StorageLayer:
    def initialize(self) -> None:
        # Setup storage
        
    def cleanup(self) -> None:
        # Cleanup resources
```

### Testable Architecture

**Can create multiple instances for testing:**
```python
def test_storage():
    config = Config(storage_path="/tmp/test")
    storage = StorageLayer(config)
    # Test with isolated instance
```

---

## Testing Standards

### Unit Testing

**Unit tests** test individual components in isolation:

- **Mark all unit tests** with `@pytest.mark.unit`
- **Use MagicMock** to test functions without directly calling dependencies
- **Use `@patch` decorator** instead of context manager for cleaner code
- **Test one thing per test** - each test should verify a single behavior
- **Use descriptive test names** that explain what is being tested
- **Isolate dependencies** - mock external services, file I/O, network calls

**Example unit test pattern:**
```python
from unittest.mock import MagicMock, patch
import pytest

@pytest.mark.unit
def test_function_with_mocked_dependency() -> None:
    """Test function behavior with mocked dependency."""
    # Arrange
    mock_dependency = MagicMock()
    mock_dependency.method.return_value = "expected"
    
    # Act
    result = function_under_test(mock_dependency)
    
    # Assert
    assert result == "expected"
    mock_dependency.method.assert_called_once()
```

**Using `@patch` decorator (preferred):**
```python
from unittest.mock import patch
import pytest

@pytest.mark.unit
@patch('module.ExternalService')
def test_with_patch_decorator(mock_service: MagicMock) -> None:
    """Test using patch decorator instead of context manager."""
    mock_service.return_value.method.return_value = "result"
    # Test implementation
```

### Integration Testing

**Integration tests** test component interactions:

- **Mark with `@pytest.mark.integration`**
- Test real interactions between components
- May use real file I/O, databases, or external services
- Slower than unit tests but verify end-to-end behavior

### Code Quality Standards

- **Type hints required** for all functions
- **All tests must pass** before committing
- **Follow FastAPI/MCP best practices**: no globals, dependency injection
- **Use ruff** for linting and formatting
- **NEVER use `# noqa` comments** - fix the underlying issue instead

---

## Debugging

### Running Server Locally

**Start server:**
```bash
hatch run python -m hjeon139_mcp_outofcontext.main
```

**With debug logging:**
```bash
OUT_OF_CONTEXT_LOG_LEVEL=DEBUG hatch run python -m hjeon139_mcp_outofcontext.main
```

### Testing Tools

**Test tool directly:**
```python
from hjeon139_mcp_outofcontext.app_state import AppState
from hjeon139_mcp_outofcontext.config import load_config
from hjeon139_mcp_outofcontext.tools.monitoring import handle_analyze_usage

config = load_config()
app_state = AppState(config)
result = await handle_analyze_usage(
    app_state,
    project_id="test-project"
)
print(result)
```

### Common Issues

**Import errors:**
- Ensure package is installed: `hatch run update-deps`
- Check Python version: `python3 --version` (must be 3.11+)

**Test failures:**
- Run tests individually to isolate issues
- Check test output for detailed error messages
- Verify test data and fixtures

**Type checking errors:**
- Review mypy output for specific issues
- Add type hints where missing
- Use `typing` module for complex types

---

## Documentation

### Writing Documentation

- **Markdown files** in `docs/` directory
- **API documentation** in `docs/api/`
- **Code comments** for complex logic
- **Docstrings** for all public functions and classes

### Documentation Standards

- **Clear and concise** - Explain what and why
- **Examples** - Include usage examples
- **Up-to-date** - Keep documentation current with code
- **Accessible** - Write for different skill levels

---

## References

- **Conventional Commits**: `docs/steering/06_conventional_commits.md`
- **Semantic Versioning**: `docs/steering/07_semantic_versioning.md`
- **Commit Workflow**: `docs/steering/08_commit_version_workflow.md`
- **Code Quality Standards**: `docs/code_quality_standards.md`

---

## Getting Help

- **Issues**: Open an issue on GitHub for bugs or feature requests
- **Discussions**: Use GitHub Discussions for questions
- **Documentation**: Check documentation in `docs/` directory

---

## Next Steps

- **Read Usage Guide**: Understand how the server is used
- **Review API Documentation**: Understand tool interfaces
- **Explore Codebase**: Familiarize yourself with the architecture
- **Run Tests**: Ensure everything works in your environment

See [Usage Guide](usage.md) for usage instructions and [API Documentation](api/tools.md) for detailed tool reference.

