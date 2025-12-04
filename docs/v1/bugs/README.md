# Bug Documentation

This directory contains documentation for bugs discovered during development that are deferred to be fixed in a later session.

## Purpose

When complex bugs are detected during the pre-commit checklist but don't block the current feature:

1. **Document** the issue here instead of fixing immediately
2. **Continue** with the commit if the issue is non-critical
3. **Address** in a separate session or create a dedicated task

## File Naming

Use format: `YYYY-MM-DD-issue-description.md`

Examples:
- `2024-12-04-type-checking-storage-optional.md`
- `2024-12-04-async-cleanup-race-condition.md`

## Template

```markdown
# Issue: [Brief Description]

**Date**: YYYY-MM-DD
**Severity**: Low | Medium | High | Critical
**Component**: [component name]
**Status**: Open | In Progress | Fixed | Deferred

## Description
Brief description of the issue.

## Reproduction
Steps to reproduce the issue.

## Expected Behavior
What should happen.

## Actual Behavior
What actually happens.

## Environment
- Python version:
- Platform:
- Other relevant details:

## Impact
How does this affect the codebase?

## Proposed Solution (if known)
Brief description of potential fix approach.

## Notes
Any additional context or observations.
```

## Guidelines

- **Simple bugs**: Fix immediately before committing
- **Complex bugs**: Document here and defer
- **Critical bugs**: Fix before committing or document as blocking
- **Non-blocking**: Continue with commit, fix in next session

