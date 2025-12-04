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

5. **Setup pre-commit hooks** (optional, recommended):
   ```bash
   hatch run pre-commit install --hook-type commit-msg
   ```
   This automatically validates commit messages follow Conventional Commits format.

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

See [`docs/steering/`](docs/steering/) for comprehensive development guidelines:

- **Conventional Commits**: `06_conventional_commits.md` - Commit message standards
- **Semantic Versioning**: `07_semantic_versioning.md` - Version management guidelines
- **Commit Workflow**: `08_commit_version_workflow.md` - Step-by-step commit and version workflow

*Note: Additional steering docs (setup, standards, workflow, patterns) may be added as needed.*

## Project Structure

```
out_of_context/
  src/
    hjeon139_mcp_outofcontext/      # Main package code
  tests/                 # Test files
  docs/                  # Documentation
  artifacts/             # Test outputs and artifacts
```

