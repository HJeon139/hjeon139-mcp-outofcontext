# Quick Start: Commit and Version Standards

This is a quick reference for committing code and managing versions. For detailed information, see the full documents.

## Commit Message Format

```
<type>(<scope>): <subject>
```

### Types

- `feat` - New feature (bump MINOR version)
- `fix` - Bug fix (bump PATCH version)
- `docs` - Documentation only
- `style` - Code style (formatting)
- `refactor` - Code refactoring
- `test` - Test changes
- `chore` - Other changes

### Examples

```bash
feat(tools): add context analysis tool
fix(storage): handle missing directory
docs(readme): update installation steps
```

## Version Bumping

**Before committing**, bump version if needed:

- `feat` → Bump MINOR (0.1.0 → 0.2.0)
- `fix` → Bump PATCH (0.1.0 → 0.1.1)
- Breaking changes → Bump MAJOR (0.1.0 → 1.0.0)
- Others → No bump needed

**Update in two places:**
1. `pyproject.toml`: `version = "0.2.0"`
2. `src/out_of_context/__init__.py`: `__version__ = "0.2.0"`

## Setup Pre-commit Hook (Recommended)

```bash
# Install pre-commit
pip install pre-commit

# Install the hook (validates commit messages)
pre-commit install --hook-type commit-msg
```

Now commit messages are automatically validated!

## Full Documentation

- [Conventional Commits](06_conventional_commits.md) - Complete commit format guide
- [Semantic Versioning](07_semantic_versioning.md) - Version management details
- [Commit Workflow](08_commit_version_workflow.md) - Step-by-step workflow

