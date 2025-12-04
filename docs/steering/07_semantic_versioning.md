# Semantic Versioning

This project follows [Semantic Versioning 2.0.0](https://semver.org/) (SemVer) for version management.

## Version Format

```
MAJOR.MINOR.PATCH
```

Examples: `0.1.0`, `0.2.0`, `1.0.0`, `1.2.3`

## Version Components

### MAJOR (X.0.0)

Increment when you make **incompatible API changes** or breaking changes:

- Breaking changes to public APIs
- Major architectural changes
- Removing deprecated features
- Changing behavior in a way that breaks existing usage

**Conventional Commits**: Commits with `BREAKING CHANGE:` footer

Examples:
- `0.9.0` → `1.0.0` - First stable release
- `1.2.0` → `2.0.0` - Breaking API changes

### MINOR (0.X.0)

Increment when you add functionality in a **backward compatible** manner:

- New features
- New API endpoints or methods
- New configuration options
- Deprecations (without removal)

**Conventional Commits**: `feat` type commits

Examples:
- `0.1.0` → `0.2.0` - Added new feature
- `1.5.0` → `1.6.0` - Added new tool

### PATCH (0.0.X)

Increment when you make **backward compatible bug fixes**:

- Bug fixes
- Security patches
- Performance improvements (non-breaking)
- Documentation corrections

**Conventional Commits**: `fix` type commits

Examples:
- `0.1.0` → `0.1.1` - Fixed a bug
- `1.2.3` → `1.2.4` - Security patch

## Pre-release Versions

For development and testing:

- **Alpha**: `0.1.0-alpha.1`, `0.1.0-alpha.2`
- **Beta**: `0.1.0-beta.1`, `0.1.0-beta.2`
- **RC** (Release Candidate): `0.1.0-rc.1`, `0.1.0-rc.2`

## Version Management

### Version Location

The version is defined in two places (keep them in sync):

1. **`pyproject.toml`**:
   ```toml
   [project]
   version = "0.2.0"
   ```

2. **`src/out_of_context/__init__.py`**:
   ```python
   __version__ = "0.2.0"
   ```

### When to Bump Versions

**Always bump version before committing:**
- Feature commits (`feat`) → Increment MINOR
- Bug fix commits (`fix`) → Increment PATCH
- Breaking changes → Increment MAJOR

**Don't bump for:**
- Documentation only (`docs`)
- Style changes (`style`)
- Refactoring without behavior change (`refactor`)
- Test changes (`test`)
- Build/CI changes (`build`, `ci`)
- Chores (`chore`)

### Version Bump Workflow

1. **Determine change type** from conventional commit type
2. **Update version** in both locations:
   ```bash
   # Edit pyproject.toml
   version = "0.2.0"
   
   # Edit src/out_of_context/__init__.py
   __version__ = "0.2.0"
   ```
3. **Commit version bump** in the same commit as the change:
   ```
   feat(foundation): add project foundation
   
   Also bump version to 0.2.0
   ```

Or use a separate commit:
```
chore: bump version to 0.2.0
```

### Version in Development

During active development (pre-1.0.0):

- **0.x.y**: Unstable API, breaking changes may occur
- **1.0.0**: First stable release with stable API

We're currently in `0.x.y` range, so:
- Breaking changes increment MINOR (0.1.0 → 0.2.0)
- Features increment MINOR (0.1.0 → 0.2.0)
- Fixes increment PATCH (0.1.0 → 0.1.1)

### Release Checklist

When preparing a release:

1. ✅ All tests passing
2. ✅ Version bumped appropriately
3. ✅ Version synced in both locations
4. ✅ Changelog updated (if maintained)
5. ✅ Commit follows conventional commits
6. ✅ Tag created: `git tag v0.2.0`

## Version Validation

The build system validates version consistency:

```bash
hatch build  # Will fail if versions don't match
```

## Examples

### Feature Addition

```
Before: 0.1.0
Commit: feat(tools): add context analysis tool
After:  0.2.0
```

### Bug Fix

```
Before: 0.2.0
Commit: fix(storage): handle missing directory
After:  0.2.1
```

### Breaking Change

```
Before: 0.2.0
Commit: feat(api): redesign tool registry

BREAKING CHANGE: Tool handlers must accept app_state parameter
After:  0.3.0  (or 1.0.0 if we want to mark stable)
```

### Multiple Changes in Release

If multiple commits go into one release:
- Highest change type determines version bump
- `feat` + `fix` → MINOR bump
- `BREAKING` + `feat` → MAJOR bump

## References

- [Semantic Versioning 2.0.0](https://semver.org/)
- [Conventional Commits](06_conventional_commits.md) - See relationship section
- [Python Packaging User Guide - Version](https://packaging.python.org/en/latest/guides/distributing-packages-using-setuptools/#version)

