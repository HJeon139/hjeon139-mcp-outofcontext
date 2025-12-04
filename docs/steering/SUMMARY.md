# Steering Documentation Summary

This directory contains all development guidelines and standards for the project.

## Documentation Files

### Quick Reference
- **[Quick Start](00_quick_start.md)** - Fast reference for commits and versions

### Core Standards
- **[Conventional Commits](06_conventional_commits.md)** - Commit message format and standards
- **[Semantic Versioning](07_semantic_versioning.md)** - Version management guidelines
- **[Commit Workflow](08_commit_version_workflow.md)** - Step-by-step guide

## Configuration Files

### Pre-commit Hook
- **`.pre-commit-config.yaml`** - Validates commit messages automatically

### Cursor Rules
- **`.cursorrules`** - Guidelines for AI-assisted development in Cursor

## Key Principles

### Commit Messages
- Format: `<type>(<scope>): <subject>`
- Types: `feat`, `fix`, `docs`, `style`, `refactor`, etc.
- Scope: Identifies affected codebase area
- Subject: Imperative mood, lowercase, max 72 chars

### Version Bumping
- `feat` → Bump MINOR (0.1.0 → 0.2.0)
- `fix` → Bump PATCH (0.1.0 → 0.1.1)
- Breaking changes → Bump MAJOR (0.1.0 → 1.0.0)
- Update in: `pyproject.toml` and `src/out_of_context/__init__.py`

## Setup Instructions

### 1. Install Pre-commit

```bash
pip install pre-commit
```

Or add to dev dependencies (already in `pyproject.toml`):

```bash
hatch run update-deps
```

### 2. Install Git Hooks

```bash
pre-commit install --hook-type commit-msg
```

This will automatically validate commit messages to ensure they follow Conventional Commits format.

### 3. Test It

Try an invalid commit message:
```bash
git commit -m "update readme"  # ❌ Will be rejected
```

Try a valid commit message:
```bash
git commit -m "docs(readme): update installation steps"  # ✅ Will pass
```

## Usage

### Making a Feature Commit

```bash
# 1. Make changes
vim src/out_of_context/tools.py

# 2. Bump version (0.1.0 → 0.2.0)
vim pyproject.toml
vim src/out_of_context/__init__.py

# 3. Stage and commit
git add -A
git commit -m "feat(tools): add context analysis tool"
```

### Making a Bug Fix

```bash
# 1. Fix bug
vim src/out_of_context/storage.py

# 2. Bump version (0.2.0 → 0.2.1)
vim pyproject.toml
vim src/out_of_context/__init__.py

# 3. Stage and commit
git add -A
git commit -m "fix(storage): handle missing directory"
```

## Integration with Cursor

The `.cursorrules` file provides guidelines for AI-assisted development:

- Commit standards reminder
- Version management guidelines
- Code quality expectations
- File organization

Cursor will reference these rules when helping with commits and code changes.

## References

- [Conventional Commits Specification](https://www.conventionalcommits.org/)
- [Semantic Versioning 2.0.0](https://semver.org/)
- [Pre-commit Framework](https://pre-commit.com/)

