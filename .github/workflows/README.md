# GitHub Actions Workflows

This directory contains automated workflows for CI/CD.

## Workflows

### 1. CI (`ci.yml`)
**Trigger:** On every push to `main` and on all pull requests

**Purpose:** Run tests and code quality checks

**Jobs:**
- Linting (ruff)
- Formatting (ruff)
- Type checking (mypy)
- Unit tests (with coverage)
- Integration tests

**Matrix:** Tests on Python 3.11 and 3.12

### 2. Publish (`publish.yml`)
**Trigger:** On version tags (e.g., `v1.0.0`, `v1.0.1`)

**Purpose:** Automatically publish to PyPI when a new version is tagged

**Jobs:**
1. **Test** - Run full test suite
2. **Publish** - Build and publish to PyPI (only if tests pass)

**Authentication:** Uses PyPI Trusted Publishers (no API token needed)

### 3. Publish with Token (Example)
**File:** `publish-with-token.yml.example`

**Purpose:** Alternative workflow using API token instead of Trusted Publishers

**Setup:**
1. Rename to `publish.yml`
2. Add `PYPI_API_TOKEN` secret to GitHub repository

## Usage

### Publishing a New Version

1. **Update version** in both locations:
   - `pyproject.toml`
   - `src/hjeon139_mcp_outofcontext/__init__.py`

2. **Commit changes:**
   ```bash
   git add pyproject.toml src/hjeon139_mcp_outofcontext/__init__.py
   git commit -m "chore(release): bump version to X.Y.Z"
   ```

3. **Create and push tag:**
   ```bash
   git tag -a vX.Y.Z -m "Release vX.Y.Z"
   git push origin main --tags
   ```

4. **Watch the workflow:**
   - Go to: https://github.com/HJeon139/hjeon139-mcp-outofcontext/actions
   - The "Publish to PyPI" workflow will automatically run
   - If tests pass, package will be published to PyPI

### Manual Trigger

The publish workflow can also be manually triggered:
1. Go to Actions tab
2. Select "Publish to PyPI" workflow
3. Click "Run workflow"
4. Select the branch/tag to publish

## Setup PyPI Trusted Publishing

1. Go to https://pypi.org/manage/account/publishing/
2. Click "Add a new pending publisher"
3. Fill in:
   - PyPI Project Name: `hjeon139-mcp-outofcontext`
   - Owner: `HJeon139`
   - Repository: `hjeon139-mcp-outofcontext`
   - Workflow name: `publish.yml`
4. Save

Once set up, no API tokens are needed! GitHub and PyPI handle authentication automatically.

## Badges (Optional)

Add these badges to your main README.md:

```markdown
[![CI](https://github.com/HJeon139/hjeon139-mcp-outofcontext/actions/workflows/ci.yml/badge.svg)](https://github.com/HJeon139/hjeon139-mcp-outofcontext/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/hjeon139-mcp-outofcontext.svg)](https://badge.fury.io/py/hjeon139-mcp-outofcontext)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
```

