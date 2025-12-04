# Out of Context

A Python project following standard development practices.

## Development Setup

This project uses:
- **mise** (or asdf) for Python version management
- **Hatch** for project and environment management
- **Ruff** for linting and formatting
- **MyPy** for type checking
- **Pytest** for testing

### Initial Setup

1. **Install Python version** (if using mise):
   ```bash
   mise install
   ```

2. **Create Hatch environment**:
   ```bash
   hatch env create
   ```

3. **Enter environment** (optional, for interactive work):
   ```bash
   hatch shell
   ```

4. **Update dependencies**:
   ```bash
   hatch run update-deps
   ```

### Quick Reference

```bash
# Run tests
hatch run test

# Lint and auto-fix
hatch run lint-fix

# Format code
hatch run fmt-fix

# Type checking
hatch run typecheck

# Run full release pipeline
hatch run release
```

## Steering Documentation

See `../steering_docs/` for comprehensive development guidelines:

- **Setup**: `01_setup.md` - Python, Hatch, project structure
- **Standards**: `02_coding_standards.md` - Ruff, MyPy, Pytest configuration
- **Workflow**: `03_development_workflow.md` - Scoping → Design → Implementation
- **Patterns**: `04_common_patterns.md` - Experiments, dependencies, typing
- **FastAPI+MCP**: `05_fastapi_mcp_integration.md` - FastAPI with MCP integration

## Project Structure

```
out_of_context/
  src/
    out_of_context/      # Main package code
  tests/                 # Test files
  docs/                  # Documentation
  artifacts/             # Test outputs and artifacts
```

