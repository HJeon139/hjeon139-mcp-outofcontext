# Bug: WorkingSet Model Missing `last_updated` Field

**Date**: 2025-12-04  
**Severity**: Medium  
**Component**: `models.py`, `context_manager.py`  
**Status**: Not Fixed

## Description

The `WorkingSet` model is missing the `last_updated: datetime` field that is specified in the design documentation.

## Design Specification

According to `docs/v1/tasks/05_context_manager.md` (lines 64-72), the WorkingSet should have:

```python
@dataclass
class WorkingSet:
    segments: List[ContextSegment]
    total_tokens: int
    task_id: Optional[str]
    project_id: str
    last_updated: datetime  # <-- Missing in implementation
```

## Current Implementation

In `src/hjeon139_mcp_outofcontext/models.py` (lines 109-116):

```python
class WorkingSet(BaseModel):
    """Working set abstraction."""

    segments: list[ContextSegment] = Field(description="Active segments")
    total_tokens: int = Field(description="Total token count")
    project_id: str = Field(description="Project identifier")
    task_id: str | None = Field(None, description="Task identifier")
    # Missing: last_updated: datetime
```

## Impact

- WorkingSet instances don't track when they were last updated
- Cannot determine staleness of cached working sets
- Design contract not fully implemented

## Location

- `src/hjeon139_mcp_outofcontext/models.py:109-116` - Model definition
- `src/hjeon139_mcp_outofcontext/context_manager.py:228-233` - WorkingSet creation (doesn't set last_updated)

## Fix Required

1. Add `last_updated: datetime` field to `WorkingSet` model in `models.py`
2. Update `ContextManager.get_working_set()` to set `last_updated=datetime.now()` when creating WorkingSet instances
3. Update `ContextManager._update_working_set()` to update `last_updated` when invalidating cache

## References

- Design: `docs/v1/tasks/05_context_manager.md`
- Design: `docs/v1/design/09_interfaces.md`
- Implementation: `src/hjeon139_mcp_outofcontext/models.py`
- Implementation: `src/hjeon139_mcp_outofcontext/context_manager.py`

