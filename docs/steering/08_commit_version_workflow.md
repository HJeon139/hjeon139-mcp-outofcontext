# Commit and Version Workflow

This document describes the standard workflow for making commits and managing versions in this project.

## Quick Reference

### Making a Commit

1. **Write your code changes**
2. **Determine commit type** (feat, fix, docs, etc.)
3. **Choose appropriate scope** (foundation, tools, storage, etc.)
4. **Write commit message** following conventional commits format
5. **Bump version if needed** (feat → minor, fix → patch)
6. **Stage and commit**

### Version Bump Decision Tree

```
Is it a new feature? → YES → Bump MINOR (0.1.0 → 0.2.0)
                     → NO
Is it a bug fix? → YES → Bump PATCH (0.1.0 → 0.1.1)
                → NO
Is it a breaking change? → YES → Bump MAJOR (0.1.0 → 1.0.0)
                         → NO
Is it docs/style/refactor/test/chore? → No version bump needed
```

## Detailed Workflow

### Step 1: Make Your Changes

Edit files, add features, fix bugs, etc.

### Step 2: Stage Changes

```bash
git add <files>
# or
git add -A  # Stage all changes
```

### Step 3: Determine Commit Type

Ask yourself:
- **New feature?** → `feat`
- **Bug fix?** → `fix`
- **Documentation?** → `docs`
- **Code style?** → `style`
- **Refactoring?** → `refactor`
- **Tests?** → `test`
- **Dependencies/build?** → `build`
- **CI/config?** → `ci`
- **Other?** → `chore`

### Step 4: Choose Scope

What part of the codebase changed?

- `foundation` - Core infrastructure
- `models` - Data models
- `server` - MCP server
- `storage` - Storage layer
- `gc` - Garbage collection
- `tools` - MCP tools
- `tests` - Test files
- `deps` - Dependencies
- `config` - Configuration
- Or omit scope if change spans multiple areas

### Step 5: Write Commit Message

Format: `<type>(<scope>): <subject>`

Examples:
- `feat(foundation): add project foundation`
- `fix(storage): handle missing directory`
- `docs(readme): update installation steps`
- `refactor(gc): extract scoring logic`

Add body if needed:
```
feat(tools): add context analysis tool

- Implement usage metrics calculation
- Return pruning recommendations
- Add comprehensive tests

Closes #123
```

### Step 6: Bump Version (if needed)

**For `feat` commits:**
```bash
# Update pyproject.toml
version = "0.2.0"  # Increment MINOR

# Update src/out_of_context/__init__.py
__version__ = "0.2.0"

# Stage version changes
git add pyproject.toml src/out_of_context/__init__.py
```

**For `fix` commits:**
```bash
# Update pyproject.toml
version = "0.1.1"  # Increment PATCH

# Update src/out_of_context/__init__.py
__version__ = "0.1.1"

# Stage version changes
git add pyproject.toml src/out_of_context/__init__.py
```

**For other types:** No version bump needed

### Step 7: Commit

```bash
git commit -m "feat(foundation): add project foundation"
```

The pre-commit hook will validate your commit message format.

### Step 8: Verify

Check your commit:
```bash
git log -1
```

Should show:
```
feat(foundation): add project foundation

- Detailed changes here
```

## Common Patterns

### Feature with Version Bump

```bash
# 1. Make changes
vim src/out_of_context/tools.py

# 2. Bump version (0.1.0 → 0.2.0)
vim pyproject.toml  # version = "0.2.0"
vim src/out_of_context/__init__.py  # __version__ = "0.2.0"

# 3. Stage all
git add -A

# 4. Commit
git commit -m "feat(tools): add context analysis tool"
```

### Bug Fix with Version Bump

```bash
# 1. Fix bug
vim src/out_of_context/storage.py

# 2. Bump version (0.2.0 → 0.2.1)
vim pyproject.toml  # version = "0.2.1"
vim src/out_of_context/__init__.py  # __version__ = "0.2.1"

# 3. Stage all
git add -A

# 4. Commit
git commit -m "fix(storage): handle missing project directory"
```

### Documentation Only (No Version Bump)

```bash
# 1. Update docs
vim README.md

# 2. Stage
git add README.md

# 3. Commit (no version bump)
git commit -m "docs(readme): update installation instructions"
```

### Breaking Change

```bash
# 1. Make breaking changes
vim src/out_of_context/api.py

# 2. Bump MAJOR version (0.2.0 → 1.0.0)
vim pyproject.toml  # version = "1.0.0"
vim src/out_of_context/__init__.py  # __version__ = "1.0.0"

# 3. Stage all
git add -A

# 4. Commit with BREAKING CHANGE
git commit -m "feat(api): redesign tool registry interface

BREAKING CHANGE: Tool handlers must now accept app_state parameter.
Migration guide available in docs/migration.md"
```

## Setting Up Pre-commit Hooks

To enable automatic commit message validation:

```bash
# Install pre-commit (if not already installed)
pip install pre-commit

# Install the hooks
pre-commit install --hook-type commit-msg
```

Now commit messages will be automatically validated!

## Troubleshooting

### Commit Message Rejected

If your commit message is rejected:
```
✖   Your commit message does not follow the Conventional Commits format.
```

Fix:
1. Check the format: `<type>(<scope>): <subject>`
2. Use lowercase subject
3. Use imperative mood ("add" not "added")
4. Remove period at end of subject

### Version Mismatch

If build fails with version mismatch:
```bash
# Check both locations
grep version pyproject.toml
grep __version__ src/out_of_context/__init__.py

# Sync them manually
```

## References

- [Conventional Commits](06_conventional_commits.md)
- [Semantic Versioning](07_semantic_versioning.md)
- [Pre-commit Framework](https://pre-commit.com/)

