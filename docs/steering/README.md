# Steering Documentation

This directory contains development guidelines and standards for the project.

## Available Documents

### Commit and Version Management

- **[Conventional Commits](06_conventional_commits.md)** - Commit message format and standards
- **[Semantic Versioning](07_semantic_versioning.md)** - Version management guidelines
- **[Commit Workflow](08_commit_version_workflow.md)** - Step-by-step guide for making commits with version bumps

## Quick Links

### Making a Commit

1. Read [Conventional Commits](06_conventional_commits.md) for message format
2. Follow [Commit Workflow](08_commit_version_workflow.md) for step-by-step process
3. Check [Semantic Versioning](07_semantic_versioning.md) to determine version bump

### Setting Up Pre-commit Hooks

```bash
# Install pre-commit
pip install pre-commit

# Install hooks (validates commit messages)
pre-commit install --hook-type commit-msg
```

## Future Documents

Additional steering documentation may be added:

- Setup guides (Python, Hatch, project structure)
- Coding standards (Ruff, MyPy, Pytest)
- Development workflow (Scoping → Design → Implementation)
- Common patterns (Experiments, dependencies, typing)
- FastAPI/MCP integration patterns

## References

- [Conventional Commits Specification](https://www.conventionalcommits.org/)
- [Semantic Versioning 2.0.0](https://semver.org/)
- [Pre-commit Framework](https://pre-commit.com/)

