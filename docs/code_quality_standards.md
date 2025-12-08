# Code Quality Standards

This document summarizes the quality gates used in this repository. The expectations mirror the checklist in `docs/v1/tasks/11_testing_qa.md` and are intended to be concise references for day-to-day development.

## Testing
- Target ≥ 80% coverage across `src/hjeon139_mcp_outofcontext`.
- All tests must be marked (`@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.performance`, `@pytest.mark.scalability`).
- Prefer fast unit tests; gate performance/scalability suites behind `RUN_PERFORMANCE_TESTS`/`RUN_SCALABILITY_TESTS` env vars.

## Static Analysis
- `hatch run lint-fix` and `hatch run fmt-fix` must pass with zero issues.
- `hatch run typecheck` must report zero MyPy errors.
- Complexity guardrails enforced via Ruff `C90` (C901) checks.

## Maintainability
- Keep functions ≤ 50 lines and cyclomatic complexity ≤ 10.
- Keep files ≤ ~400 lines; split modules when approaching the limit.
- No global state; rely on dependency injection for testability.

## Documentation and Naming
- Module, class, and public function docstrings are required.
- Use descriptive, PEP 8–compliant names; boolean flags should use `is_`/`has_`/`should_` prefixes.

## Pre-commit Quality Gates
- Add Ruff (lint + format), MyPy, and complexity checks to the hook set.
- Run `hatch run release` locally before submitting changes to exercise lint, format, type-check, tests, and build.

