# Conventional Commits Standard

This project follows the [Conventional Commits](https://www.conventionalcommits.org/) specification to ensure consistent, meaningful commit messages.

## Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Required Components

1. **Type** (required): What kind of change this is
2. **Scope** (optional): What part of the codebase is affected
3. **Subject** (required): Short description of the change (imperative mood, lowercase, no period)
4. **Body** (optional): Detailed explanation
5. **Footer** (optional): Breaking changes, issue references

## Commit Types

Use one of these types:

- **`feat`**: A new feature (increments minor version)
- **`fix`**: A bug fix (increments patch version)
- **`docs`**: Documentation only changes
- **`style`**: Code style changes (formatting, missing semicolons, etc.)
- **`refactor`**: Code refactoring without feature changes or bug fixes
- **`perf`**: Performance improvements
- **`test`**: Adding or modifying tests
- **`build`**: Changes to build system or dependencies
- **`ci`**: Changes to CI configuration
- **`chore`**: Other changes that don't modify src or test files
- **`revert`**: Revert a previous commit

## Scope Examples

Scopes help identify what part of the codebase changed:

- `foundation` - Project foundation/infrastructure
- `models` - Data models
- `server` - MCP server
- `storage` - Storage layer
- `gc` - Garbage collection engine
- `tools` - MCP tools
- `tests` - Test infrastructure
- `deps` - Dependencies
- `config` - Configuration

## Examples

### Simple Feature

```
feat(foundation): add project foundation and core infrastructure
```

### Feature with Body

```
feat(tools): add context analysis tool

- Implement context_analyze_usage tool
- Add usage metrics calculation
- Return pruning recommendations

Closes #123
```

### Bug Fix

```
fix(storage): handle missing project directory gracefully

Previously, loading segments for a non-existent project would
raise an exception. Now returns empty list and logs a warning.

Fixes #456
```

### Breaking Change

```
feat(api): redesign tool registry interface

BREAKING CHANGE: Tool handlers must now accept app_state as first
parameter instead of accessing global state.

Migration: Update tool handlers to use dependency injection pattern.
```

### Documentation

```
docs(readme): update installation instructions
```

### Refactoring

```
refactor(gc): extract pruning score calculation to separate method
```

## Rules

1. **Subject line**:
   - Use imperative mood ("add" not "added" or "adds")
   - First letter lowercase
   - No period at the end
   - Maximum 72 characters

2. **Body** (if needed):
   - Explain what and why, not how
   - Wrap at 72 characters
   - Use bullet points for multiple changes

3. **Footer**:
   - Reference issues: `Closes #123`, `Fixes #456`
   - Breaking changes: `BREAKING CHANGE: <description>`

## Validation

Commit messages are validated using pre-commit hooks. To test locally:

```bash
# Validate commit message format
git commit -m "feat: test commit"
```

Invalid formats will be rejected automatically.

## Relationship to Semantic Versioning

- **`feat`** commits → Minor version bump (0.1.0 → 0.2.0)
- **`fix`** commits → Patch version bump (0.1.0 → 0.1.1)
- **`BREAKING CHANGE`** → Major version bump (0.1.0 → 1.0.0)
- Other types typically don't trigger version bumps

## References

- [Conventional Commits Specification](https://www.conventionalcommits.org/)
- [Semantic Versioning](https://semver.org/)

